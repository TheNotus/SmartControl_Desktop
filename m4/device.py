"""High-level typed API over GaiaClient for MOMENTUM 4."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import protocol as P
from .client import GaiaClient, GaiaError


@dataclass
class PairedDevice:
    index: int
    priority: int
    status: int  # 0 = disconnected, non-zero = connected
    name: str


@dataclass
class DeviceInfo:
    model: str = ""
    firmware: str = ""
    serial: str = ""
    hw_revision: str = ""
    gaia_version: str = ""


class Momentum4:
    def __init__(self, client: GaiaClient):
        self.c = client

    # ------------------------------------------------ info / dashboard
    def get_info(self) -> DeviceInfo:
        info = DeviceInfo()
        data = self.c.try_request(P.Cmd.GET_MODEL_ID)
        if data:
            info.model = data.decode("utf-8", "replace").strip("\x00 ")
        data = self.c.try_request(P.Cmd.GET_FW_VERSION)
        if data and len(data) >= 6:
            major = int.from_bytes(data[0:2], "big")
            minor = int.from_bytes(data[2:4], "big")
            patch = int.from_bytes(data[4:6], "big")
            info.firmware = f"{major}.{minor}.{patch}"
        data = self.c.try_request(P.Cmd.Q_SERIAL_NUMBER, vendor=P.VENDOR_QUALCOMM)
        if data:
            info.serial = data.decode("utf-8", "replace").strip("\x00 ")
        data = self.c.try_request(P.Cmd.GET_HW_REVISION)
        if data and len(data) >= 2:
            info.hw_revision = str(int.from_bytes(data[0:2], "big"))
        data = self.c.try_request(P.Cmd.Q_API_VERSION, vendor=P.VENDOR_QUALCOMM)
        if data and len(data) >= 2:
            info.gaia_version = f"{data[0]}.{data[1]}"
        return info

    def get_battery(self) -> Optional[int]:
        data = self.c.try_request(P.Cmd.GET_BATTERY)
        if not data:
            return None
        # M4 отвечает одним байтом уровня; TWS-варианты — [count, level, ...]
        return data[0] if len(data) == 1 else data[1]

    def get_charging_status(self) -> Optional[int]:
        data = self.c.try_request(P.Cmd.GET_CHARGING_STATUS)
        return data[0] if data else None

    def get_codec(self) -> Optional[int]:
        data = self.c.try_request(P.Cmd.GET_CODEC)
        return data[0] if data else None

    def get_physical_state(self) -> Optional[int]:
        data = self.c.try_request(P.Cmd.GET_PHYSICAL_STATE)
        return data[0] if data else None

    # ------------------------------------------------ noise control
    def get_anc_enabled(self) -> bool:
        data = self.c.request(P.Cmd.GET_ANC)
        return bool(data[0])

    def set_anc_enabled(self, on: bool):
        self.c.request(P.Cmd.SET_ANC, bytes([1 if on else 0]))

    def get_anc_modes(self) -> dict[int, int]:
        """Returns {mode: state} for anti-wind(1) / comfort(2) / adaptive(3).
        State: 0 = off, 1 = on, 2 = auto (наблюдалось у anti-wind)."""
        data = self.c.request(P.Cmd.GET_ANC_MODES)
        modes = {}
        for i in range(0, len(data) - 1, 2):
            modes[data[i]] = data[i + 1]
        return modes

    def set_anc_mode(self, mode: int, state: int):
        """state: 0 = off, 1 = on, 2 = auto (только для anti-wind)."""
        self.c.request(P.Cmd.SET_ANC_MODE, bytes([mode, state]))

    def get_anc_level(self) -> Optional[int]:
        data = self.c.try_request(P.Cmd.GET_ANC_LEVEL)
        return data[0] if data else None

    def set_anc_level(self, level: int):
        self.c.request(P.Cmd.SET_ANC_LEVEL, bytes([max(0, min(100, level))]))

    def get_transparency(self) -> bool:
        data = self.c.request(P.Cmd.GET_TRANSPARENCY)
        return bool(data[0])

    def set_transparency(self, on: bool):
        self.c.request(P.Cmd.SET_TRANSPARENCY, bytes([1 if on else 0]))

    def get_transparency_level(self) -> Optional[int]:
        data = self.c.try_request(P.Cmd.GET_TH_LEVEL)
        return data[0] if data else None

    def set_transparency_level(self, level: int):
        self.c.request(P.Cmd.SET_TH_LEVEL, bytes([max(0, min(100, level))]))

    def get_th_autopause(self) -> Optional[bool]:
        data = self.c.try_request(P.Cmd.GET_TH_AUTOPAUSE)
        return bool(data[0]) if data else None

    def set_th_autopause(self, pause_music: bool):
        self.c.request(P.Cmd.SET_TH_AUTOPAUSE, bytes([1 if pause_music else 0]))

    # ------------------------------------------------ sound / EQ
    def get_bass_boost(self) -> Optional[bool]:
        data = self.c.try_request(P.Cmd.GET_BASS_BOOST)
        return bool(data[0]) if data else None

    def set_bass_boost(self, on: bool):
        self.c.request(P.Cmd.SET_BASS_BOOST, bytes([1 if on else 0]))

    @staticmethod
    def _i8(b: int) -> int:
        return b - 256 if b > 127 else b

    @staticmethod
    def _i16(hi: int, lo: int) -> int:
        v = (hi << 8) | lo
        return v - 65536 if v > 32767 else v

    def get_eq_curve(self) -> Optional[list[int]]:
        """Итоговая 5-полосная кривая (включая Sound Check), только чтение."""
        data = self.c.try_request(P.Cmd.EQ_GET_CURVE, b"\x00", timeout=3.0)
        if data and len(data) == 5:
            return [self._i8(b) for b in data]
        return None

    def get_eq_band_freqs(self) -> list[Optional[int]]:
        freqs = []
        for band in range(5):
            data = self.c.try_request(P.Cmd.EQ_GET_BAND_FREQ, bytes([band]),
                                      timeout=2.0)
            freqs.append(int.from_bytes(data[1:3], "big")
                         if data and len(data) >= 3 else None)
        return freqs

    def get_user_eq(self) -> list[Optional[int]]:
        """Активные гейны полос (совпадают с итоговой кривой)."""
        curve = self.get_eq_curve()
        return curve if curve else [None] * 5

    def set_user_eq_band(self, band: int, gain: int):
        gain = max(-128, min(127, int(gain)))
        payload = bytes([band, gain & 0xFF])
        self.c.request(P.Cmd.EQ_SET_BAND_GAIN, payload)

    def set_user_eq(self, gains: list[int]):
        for band, gain in enumerate(gains[:5]):
            self.set_user_eq_band(band, gain)

    def probe_eq(self) -> dict[str, str]:
        """Диагностический дамп фичи EQ (только чтение)."""
        report = {}
        for name, cmd in [("итоговая кривая (0x1003)", P.Cmd.EQ_GET_CURVE),
                          ("частоты полос (0x100B)", P.Cmd.EQ_GET_BAND_FREQ),
                          ("добротности (0x100D)", P.Cmd.EQ_GET_BAND_Q),
                          ("диапазон (0x100F)", P.Cmd.EQ_GET_BAND_RANGE),
                          ("пользовательский EQ (0x1011)", P.Cmd.EQ_GET_USER_GAIN)]:
            parts = []
            if cmd == P.Cmd.EQ_GET_CURVE:
                data = self.c.try_request(cmd, b"\x00", timeout=2.0)
                parts.append(data.hex(" ") if data else "нет ответа")
            else:
                for band in range(5):
                    data = self.c.try_request(cmd, bytes([band]), timeout=2.0)
                    parts.append(data.hex(" ") if data else "—")
            report[name] = " | ".join(parts)
        return report

    # ------------------------------------------------ toggles & settings
    def _get_bool(self, cmd: int) -> Optional[bool]:
        data = self.c.try_request(cmd)
        return bool(data[0]) if data else None

    def _set_u8(self, cmd: int, value: int):
        self.c.request(cmd, bytes([value & 0xFF]))

    def get_smart_pause(self): return self._get_bool(P.Cmd.GET_SMART_PAUSE)
    def set_smart_pause(self, on): self._set_u8(P.Cmd.SET_SMART_PAUSE, int(on))

    def get_on_head_detection(self): return self._get_bool(P.Cmd.GET_ON_HEAD_DETECTION)
    def set_on_head_detection(self, on): self._set_u8(P.Cmd.SET_ON_HEAD_DETECTION, int(on))

    def get_auto_call(self): return self._get_bool(P.Cmd.GET_AUTO_CALL)
    def set_auto_call(self, on): self._set_u8(P.Cmd.SET_AUTO_CALL, int(on))

    def get_comfort_call(self): return self._get_bool(P.Cmd.GET_COMFORT_CALL)
    def set_comfort_call(self, on): self._set_u8(P.Cmd.SET_COMFORT_CALL, int(on))

    def get_low_latency(self): return self._get_bool(P.Cmd.GET_LOW_LATENCY)
    def set_low_latency(self, on): self._set_u8(P.Cmd.SET_LOW_LATENCY, int(on))

    def get_bt_compat(self): return self._get_bool(P.Cmd.GET_BT_COMPAT_MODE)
    def set_bt_compat(self, on): self._set_u8(P.Cmd.SET_BT_COMPAT_MODE, int(on))

    # 0x1607 == 1 означает включённую автоблокировку сенсора (touch lock);
    # 0 — сенсор работает как обычно.
    def get_touch_lock(self): return self._get_bool(P.Cmd.GET_TOUCH_LOCK)
    def set_touch_lock(self, on): self._set_u8(P.Cmd.SET_TOUCH_LOCK, int(on))

    def get_sidetone(self) -> Optional[int]:
        data = self.c.try_request(P.Cmd.GET_SIDETONE)
        return data[0] if data else None

    def set_sidetone(self, level: int):
        self._set_u8(P.Cmd.SET_SIDETONE, max(0, min(5, level)))

    def get_prompt_mode(self) -> Optional[int]:
        data = self.c.try_request(P.Cmd.GET_PROMPT_MODE)
        return data[0] if data else None

    def set_prompt_mode(self, mode: int):
        self._set_u8(P.Cmd.SET_PROMPT_MODE, mode)

    def get_prompt_language(self) -> Optional[int]:
        data = self.c.try_request(P.Cmd.GET_PROMPT_LANGUAGE)
        return data[0] if data else None

    def get_poweroff_timer(self) -> Optional[int]:
        """Returns auto power-off delay in seconds (0 = disabled)."""
        data = self.c.try_request(P.Cmd.GET_TIMER, bytes([0]))
        if data and len(data) >= 3:
            return int.from_bytes(data[1:3], "big")
        return None

    def set_poweroff_timer(self, seconds: int):
        self.c.request(P.Cmd.SET_TIMER, bytes([0]) + int(seconds).to_bytes(2, "big"))

    # ------------------------------------------------ touch control mapping
    def get_mmi_map(self) -> dict[tuple[int, int], int]:
        """Returns {(button, pattern): function} for everything the device reports."""
        mapping = {}
        for button in (0, 1):
            for pattern in sorted(P.MMI_PATTERNS):
                data = self.c.try_request(P.Cmd.MMI_GET, bytes([button, pattern]),
                                          timeout=2.0)
                if data and len(data) >= 3:
                    mapping[(data[0], data[1])] = data[2]
        return mapping

    def set_mmi(self, button: int, pattern: int, function: int):
        self.c.request(P.Cmd.MMI_SET, bytes([button, pattern, function]))

    def reset_mmi(self):
        self.c.request(P.Cmd.MMI_SET_DEFAULT)

    def is_default_mmi(self) -> Optional[bool]:
        return self._get_bool(P.Cmd.MMI_IS_DEFAULT)

    # ------------------------------------------------ paired devices
    def get_paired_devices(self) -> list[PairedDevice]:
        devices = []
        data = self.c.try_request(P.Cmd.PDL_SIZE)
        count = int.from_bytes(data[:2], "big") if data and len(data) >= 2 else 0
        for i in range(min(count, 16)):
            data = self.c.try_request(P.Cmd.PDL_DEVICE_INFO, bytes([i]), timeout=2.5)
            if data and len(data) >= 4:
                name = data[3:].decode("utf-8", "replace").strip("\x00 ")
                devices.append(PairedDevice(data[0], data[1], data[2], name))
        return devices

    def get_own_index(self) -> Optional[int]:
        data = self.c.try_request(P.Cmd.PDL_OWN_INDEX)
        return data[0] if data else None

    def pdl_connect(self, index: int):
        self.c.request(P.Cmd.PDL_CONNECT, bytes([index]), timeout=10.0)

    def pdl_disconnect(self, index: int):
        self.c.request(P.Cmd.PDL_DISCONNECT, bytes([index]), timeout=10.0)

    def pdl_delete(self, index: int):
        self.c.request(P.Cmd.PDL_DELETE, bytes([index]))

    # ------------------------------------------------ danger zone
    def factory_reset(self):
        self.c.request(P.Cmd.FACTORY_RESET, timeout=10.0)
