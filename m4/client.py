"""RFCOMM GAIA v3 client for MOMENTUM 4 (Windows, Python >= 3.9).

Uses the built-in AF_BLUETOOTH socket support of CPython on Windows.
Windows cannot resolve an RFCOMM channel from the GAIA service UUID
(0000fdce-...) without a raw SDP query, so we probe the usual channels
and verify each candidate with a real GAIA request (GET_ANC), the same
approach proven by f3Y0/momentum4-control.
"""
from __future__ import annotations

import socket
import threading
import time
from typing import Callable, Optional

from . import protocol as P

try:
    from gui.i18n import tr
except Exception:  # noqa: BLE001 — модуль используется и без GUI
    def tr(text):
        return text

RFCOMM_CHANNELS = [2, 1, 3, 15, 14, 12, 4, 5, 6, 7, 8, 9, 10, 11, 13]


class GaiaError(Exception):
    def __init__(self, pdu: int, code: int):
        self.pdu = pdu
        self.code = code
        reason = tr(P.GAIA_ERRORS.get(code, "")) or tr("код {n}").format(n=code)
        super().__init__(tr("Устройство отклонило команду 0x{cmd}: {reason}").format(
            cmd=f"{pdu & ~P.ERROR_MASK:04X}", reason=reason))


class GaiaClient:
    """Thread-safe request/response client with notification callback."""

    def __init__(self, mac: str,
                 on_notification: Optional[Callable[[int, int, bytes], None]] = None,
                 on_disconnect: Optional[Callable[[str], None]] = None,
                 on_log: Optional[Callable[[str], None]] = None):
        self.mac = mac
        self.on_notification = on_notification
        self.on_disconnect = on_disconnect
        self.on_log = on_log or (lambda s: None)
        self.sock: Optional[socket.socket] = None
        self.channel: Optional[int] = None
        self._buffer = b""
        self._lock = threading.Lock()          # serializes requests
        self._pending_lock = threading.Lock()
        self._pending: dict[int, "_Waiter"] = {}
        self._reader: Optional[threading.Thread] = None
        self._closing = False

    # ------------------------------------------------------------- connect
    def connect(self, per_channel_timeout: float = 4.0,
                preferred_channel: int | None = None) -> int:
        errors = []
        channels = list(RFCOMM_CHANNELS)
        if preferred_channel in channels:
            channels.remove(preferred_channel)
            channels.insert(0, preferred_channel)
        for ch in channels:
            sock = None
            try:
                sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM,
                                     socket.BTPROTO_RFCOMM)
                sock.settimeout(per_channel_timeout)
                sock.connect((self.mac, ch))
                self.sock = sock
                self.channel = ch
                self._buffer = b""
                self._closing = False
                self._start_reader()
                # verify this is the GAIA channel with a real request;
                # сразу после переподключения в Windows устройство может
                # отвечать не с первого раза — пробуем дважды
                payload = None
                for attempt in (1, 2):
                    try:
                        payload = self.request(P.Cmd.GET_ANC, timeout=3.0)
                        break
                    except TimeoutError:
                        if attempt == 2:
                            raise
                if payload is not None and len(payload) >= 1:
                    self.on_log(tr("GAIA-канал найден: RFCOMM {ch}").format(ch=ch))
                    return ch
                raise RuntimeError("empty response")
            except GaiaError:
                # device answered in GAIA framing -> channel is right anyway
                self.on_log(tr("GAIA-канал найден: RFCOMM {ch}").format(ch=ch))
                return ch
            except Exception as exc:  # noqa: BLE001
                errors.append(tr("канал {ch}: {e}").format(ch=ch, e=exc))
                self._teardown(silent=True)
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass
        raise ConnectionError(
            tr("Не удалось найти GAIA-канал RFCOMM. Убедитесь, что наушники "
               "включены и сопряжены с этим ПК.")
            + "\n" + "\n".join(errors[:4]))

    def close(self):
        self._closing = True
        self._teardown(silent=True)

    @property
    def connected(self) -> bool:
        return self.sock is not None

    # ------------------------------------------------------------- requests
    def request(self, cmd: int, payload: bytes = b"",
                vendor: int = P.VENDOR_SENNHEISER, timeout: float = 5.0) -> bytes:
        """Send a command and wait for its response (or raise GaiaError)."""
        if self.sock is None:
            raise ConnectionError(tr("Нет подключения"))
        waiter = _Waiter()
        keys = [(vendor, P.response_of(cmd)), (vendor, P.error_of(cmd))]
        with self._pending_lock:
            for k in keys:
                self._pending[k] = waiter
        try:
            frame = P.build_frame(cmd, payload, vendor)
            self.on_log(f"TX {frame.hex(' ')}")
            with self._lock:
                self.sock.sendall(frame)
            if not waiter.event.wait(timeout):
                raise TimeoutError(tr("Нет ответа на команду 0x{cmd}")
                                   .format(cmd=f"{cmd:04X}"))
            pdu, data = waiter.result
            if P.is_error(pdu):
                raise GaiaError(pdu, data[0] if data else -1)
            return data
        finally:
            with self._pending_lock:
                for k in keys:
                    self._pending.pop(k, None)

    def try_request(self, cmd: int, payload: bytes = b"",
                    vendor: int = P.VENDOR_SENNHEISER, timeout: float = 3.0) -> Optional[bytes]:
        """Like request() but returns None on any failure."""
        try:
            return self.request(cmd, payload, vendor, timeout)
        except Exception:  # noqa: BLE001
            return None

    def register_notifications(self):
        for feature in P.FEATURES_TO_REGISTER:
            self.try_request(P.Cmd.REGISTER_NOTIFICATION, bytes([feature]), timeout=2.0)

    # ------------------------------------------------------------- internals
    def _start_reader(self):
        self._reader = threading.Thread(target=self._read_loop, daemon=True,
                                        name="gaia-reader")
        self._reader.start()

    def _read_loop(self):
        sock = self.sock
        while sock is not None and not self._closing:
            try:
                sock.settimeout(None)
                chunk = sock.recv(1024)
            except OSError:
                break
            if not chunk:
                break
            self._buffer += chunk
            packets, self._buffer = P.parse_frames(self._buffer)
            for vendor, pdu, data in packets:
                self.on_log(f"RX v=0x{vendor:04X} pdu=0x{pdu:04X} data={data.hex(' ')}")
                with self._pending_lock:
                    waiter = self._pending.get((vendor, pdu))
                if waiter is not None:
                    waiter.result = (pdu, data)
                    waiter.event.set()
                elif P.is_notification(pdu) and self.on_notification:
                    try:
                        self.on_notification(vendor, pdu, data)
                    except Exception:  # noqa: BLE001
                        pass
            if sock is not self.sock:
                break
        if not self._closing:
            self._teardown(silent=False)

    def _teardown(self, silent: bool):
        sock, self.sock = self.sock, None
        self.channel = None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        # release anyone waiting
        with self._pending_lock:
            for waiter in self._pending.values():
                waiter.result = (P.ERROR_MASK, b"\xff")
                waiter.event.set()
            self._pending.clear()
        if not silent and self.on_disconnect:
            self.on_disconnect(tr("Соединение разорвано"))


class _Waiter:
    __slots__ = ("event", "result")

    def __init__(self):
        self.event = threading.Event()
        self.result: tuple[int, bytes] = (0, b"")
