"""GAIA v3 protocol framing and command table for Sennheiser MOMENTUM 4.

Frame layout over RFCOMM (big-endian):
    FF 03 <len:u16> <vendor:u16> <pdu:u16> <payload...>

PDU id structure: [feature:7][type:2][specific:7]
    type 0 = command, 1 = notification, 2 = response, 3 = error
So for a command C:  response = C | 0x0100, notification = C | 0x0080,
error = C | 0x0180.

Command ids were recovered from the schema shipped inside the official
Sennheiser Smart Control app (see README, credits to zaval/sennheiser-desktop-client
and f3Y0/momentum4-control).
"""
from __future__ import annotations

MAGIC = b"\xFF\x03"

VENDOR_SENNHEISER = 0x0495
VENDOR_QUALCOMM = 0x001D

RESPONSE_BIT = 0x0100
NOTIFICATION_BIT = 0x0080
ERROR_MASK = 0x0180


def build_frame(pdu: int, payload: bytes = b"", vendor: int = VENDOR_SENNHEISER) -> bytes:
    return (
        MAGIC
        + len(payload).to_bytes(2, "big")
        + vendor.to_bytes(2, "big")
        + pdu.to_bytes(2, "big")
        + payload
    )


def parse_frames(buffer: bytes):
    """Returns (list of (vendor, pdu, payload), remaining buffer)."""
    packets = []
    offset = 0
    while len(buffer) - offset >= 8:
        if buffer[offset:offset + 2] != MAGIC:
            nxt = buffer.find(MAGIC, offset + 1)
            if nxt == -1:
                return packets, buffer[-1:]
            offset = nxt
            continue
        payload_len = int.from_bytes(buffer[offset + 2:offset + 4], "big")
        total = 8 + payload_len
        if len(buffer) - offset < total:
            break
        vendor = int.from_bytes(buffer[offset + 4:offset + 6], "big")
        pdu = int.from_bytes(buffer[offset + 6:offset + 8], "big")
        packets.append((vendor, pdu, buffer[offset + 8:offset + total]))
        offset += total
    return packets, buffer[offset:]


def response_of(cmd: int) -> int:
    return cmd | RESPONSE_BIT


def error_of(cmd: int) -> int:
    return cmd | ERROR_MASK


def notification_of(cmd: int) -> int:
    return cmd | NOTIFICATION_BIT


def is_response(pdu: int) -> bool:
    return (pdu >> 7) & 0x3 == 2


def is_notification(pdu: int) -> bool:
    return (pdu >> 7) & 0x3 == 1


def is_error(pdu: int) -> bool:
    return (pdu >> 7) & 0x3 == 3


def feature_of(pdu: int) -> int:
    return pdu >> 9


class Cmd:
    """GAIA command ids (vendor Sennheiser 0x0495 unless noted)."""

    # ---- core (vendor Qualcomm 0x001D) ----
    Q_API_VERSION = 0x0000            # -> u8 major, u8 minor
    Q_SERIAL_NUMBER = 0x0003          # -> string
    Q_GET_ASSISTANT = 0x0600          # -> u8 provider (0 none, 2 google, 3 amazon)
    Q_SET_ASSISTANT = 0x0601

    REGISTER_NOTIFICATION = 0x0007    # payload: u8 feature id

    # ---- service / info ----
    FACTORY_RESET = 0x0040
    GET_PRIMARY_SIDE = 0x0041         # -> u8 (0 both, 1 left, 2 right)
    GET_HW_REVISION = 0x1200          # -> u16, u16
    GET_FW_VERSION = 0x1201           # -> u16 major, u16 minor, u16 patch
    GET_FW_VERSIONS_RAW = 0x1202      # -> bytes
    GET_MODEL_ID = 0x1206             # -> string

    # ---- battery / config timers (feature 3) ----
    SET_TIMER = 0x0600                # u8 timer id (0 = power-off), u16 seconds
    GET_TIMER = 0x0601                # u8 timer id -> u8 id, u16 seconds
    GET_CHARGING_STATUS = 0x0602      # -> u8 (0 discon, 1 charging, 2 complete)
    GET_BATTERY = 0x0603              # -> u8 count, u8 level...

    # ---- wear / device (feature 2) ----
    SET_ON_HEAD_DETECTION = 0x0400
    GET_ON_HEAD_DETECTION = 0x0401
    GET_PHYSICAL_STATE = 0x0402       # -> u8 (0 ?, 1 in case, 2 off head, 3 on head)
    SET_BT_COMPAT_MODE = 0x0405       # u8 (1 = better compatibility, 0 = better audio)
    GET_BT_COMPAT_MODE = 0x0406

    # ---- audio settings (feature 4) ----
    GET_CODEC = 0x0800                # -> u8, see CODECS
    SET_PROMPT_MODE = 0x0801          # u8 (0 off, 1 tones, 2 voice+tones)
    GET_PROMPT_MODE = 0x0802
    SET_SIDETONE = 0x0805             # u8 0..5
    GET_SIDETONE = 0x0806
    GET_PROMPT_LANGUAGE = 0x0807      # -> u8, see LANGUAGES
    GET_PROMPT_LANGUAGES_AVAIL = 0x0808
    SET_AUTO_CALL = 0x080A            # u8 0/1  (auto answer calls)
    GET_AUTO_CALL = 0x080B
    SET_SMART_PAUSE = 0x080C          # u8 0/1
    GET_SMART_PAUSE = 0x080D
    SET_COMFORT_CALL = 0x0814         # u8 0/1
    GET_COMFORT_CALL = 0x0815
    SET_LOW_LATENCY = 0x0817          # u8 0/1
    GET_LOW_LATENCY = 0x0818

    # ---- user EQ (feature 8) ----
    EQ_GET_BAND_GAIN = 0x1002         # [band] -> i8 gain of resulting curve
    EQ_GET_CURVE = 0x1003             # [0] -> 5 x i8 (итоговая кривая, read-only)
    SET_BASS_BOOST = 0x1008           # u8 0/1
    GET_BASS_BOOST = 0x1009
    EQ_SET_BAND_FREQ = 0x100A         # (band u8, freq u16 Hz)
    EQ_GET_BAND_FREQ = 0x100B         # [band] -> (band, freq u16)
    EQ_SET_BAND_Q = 0x100C            # (band u8, q u16 * 4096)
    EQ_GET_BAND_Q = 0x100D
    EQ_SET_BAND_RANGE = 0x100E        # (band u8, u8)
    EQ_GET_BAND_RANGE = 0x100F
    EQ_SET_USER_GAIN = 0x1010         # (band u8, gain i16) — записываемая таблица
    EQ_GET_USER_GAIN = 0x1011         # [band] -> (band, gain i16)
    EQ_SET_UNKNOWN12 = 0x1012
    EQ_GET_UNKNOWN13 = 0x1013         # -> 2 bytes

    # ---- paired devices list (feature 10) ----
    PDL_SIZE = 0x1400                 # -> u16 count
    PDL_DEVICE_INFO = 0x1401          # u8 idx -> u8 idx, u8 prio, u8 status, string name
    PDL_CONNECT = 0x1402              # u8 idx
    PDL_DISCONNECT = 0x1403           # u8 idx
    PDL_CONNECTION_STATUS = 0x1404    # u8 idx -> u8 idx, u8 status
    PDL_DELETE = 0x1405               # u8 idx
    PDL_OWN_INDEX = 0x1407            # -> u8 idx
    PDL_MAX_CONNECTIONS = 0x1409      # -> u8

    # ---- MMI / touch controls (feature 11) ----
    MMI_SET = 0x1600                  # u8 button, u8 pattern, u8 function
    MMI_GET = 0x1601                  # u8 button, u8 pattern -> ..., u8 function
    MMI_SET_DEFAULT = 0x1604
    MMI_IS_DEFAULT = 0x1605           # -> u8 bool
    SET_TOUCH_LOCK = 0x1606           # u8 (1 = touchpad enabled, 0 = locked)
    GET_TOUCH_LOCK = 0x1607

    # ---- transparent hearing (feature 12) ----
    SET_TH_AUTOPAUSE = 0x1800         # u8 (0 keep music, 1 pause music)
    GET_TH_AUTOPAUSE = 0x1801
    SET_TH_LEVEL = 0x1802             # u8 0..100 (уровень прозрачности)
    GET_TH_LEVEL = 0x1803
    SET_TRANSPARENCY = 0x1804         # u8 0/1 (вкл/выкл)
    GET_TRANSPARENCY = 0x1805

    # ---- ANC (feature 13) ----
    SET_ANC_MODE = 0x1A00             # u8 mode (1 anti-wind, 2 comfort, 3 adaptive), u8 state
    GET_ANC_MODES = 0x1A01            # -> 6 bytes: (mode, state) x3
    # Баланс шумоподавления (в схеме зовётся ANC_Transparency):
    # 0 = максимальное ANC, 100 = полная прозрачность
    SET_ANC_LEVEL = 0x1A02            # u8 0..100
    GET_ANC_LEVEL = 0x1A03
    SET_ANC = 0x1A04                  # u8 0/1
    GET_ANC = 0x1A05


# Ids used with REGISTER_NOTIFICATION. This is an internal Sennheiser enum that
# does NOT match the PDU feature number (4 -> battery events, 8 -> audio
# settings, 10 -> user EQ dump, 13 -> transparent hearing). Registering every
# id is harmless, so the whole range is swept.
FEATURES_TO_REGISTER = tuple(range(0, 17))

CODECS = {
    0: "SBC", 1: "AAC", 2: "aptX", 3: "aptX-LL", 4: "MP3", 5: "aptX-HD",
    6: "Faststream", 7: "LHDC", 8: "aptX Adaptive", 9: "aptX Lossless",
    10: "LC3", 255: "—",
}

LANGUAGES = {
    0: "Английский", 1: "Немецкий", 2: "Французский", 3: "Испанский",
    4: "Китайский", 5: "Японский", 6: "Русский", 7: "Корейский",
}

CHARGING = {0: "Не заряжается", 1: "Заряжается", 2: "Заряжено"}

PHYSICAL_STATE = {0: "Неизвестно", 1: "В чехле", 2: "Сняты", 3: "Надеты"}

ANC_MODE_ANTIWIND = 1
ANC_MODE_COMFORT = 2
ANC_MODE_ADAPTIVE = 3

MMI_PATTERNS = {
    0x01: "1 касание",
    0x02: "2 касания",
    0x03: "3 касания",
    0x04: "Долгое нажатие",
    0x05: "Долгое нажатие (отпускание)",
    0x06: "Очень долгое нажатие",
    0x07: "Очень долгое нажатие (отпускание)",
    0x08: "Сверхдолгое нажатие",
    0x09: "Сверхдолгое нажатие (отпускание)",
    0x00: "Удержание (повтор)",
}

MMI_FUNCTIONS = {
    0x00: "Ничего",
    0x01: "Пауза / воспроизведение",
    0x02: "Следующий трек",
    0x03: "Предыдущий трек",
    0x04: "Громкость +",
    0x05: "Громкость −",
    0x06: "Прозрачный режим",
    0x07: "Голосовой ассистент",
    0x80: "Принять вызов",
    0x81: "Отклонить вызов",
}

GAIA_ERRORS = {
    0x00: "OK",
    0x01: "команда не поддерживается",
    0x02: "недостаточно прав",
    0x03: "неверные параметры",
    0x04: "неверное состояние устройства",
    0x05: "операция уже выполняется",
}
