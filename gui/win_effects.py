"""Нативные эффекты окна Windows 11: тёмный заголовок, Mica/Acrylic-подложка.

Ключевой момент: у окна со стандартной рамкой альфа-канал содержимого Qt
учитывается DWM только после DwmExtendFrameIntoClientArea(-1) («лист стекла»
на всю клиентскую область). Без этого подложка видна лишь на рамке окна,
а интерфейс остаётся непрозрачным.
"""
from __future__ import annotations

import ctypes

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38

# значения DWM_SYSTEMBACKDROP_TYPE
_BACKDROP = {"opaque": 1, "mica": 2, "acrylic": 3}   # 1 = none


class _MARGINS(ctypes.Structure):
    _fields_ = [("cxLeftWidth", ctypes.c_int),
                ("cxRightWidth", ctypes.c_int),
                ("cyTopHeight", ctypes.c_int),
                ("cyBottomHeight", ctypes.c_int)]


def apply_backdrop(widget, mode: str) -> bool:
    """Включает подложку DWM для окна. Возвращает False, если система
    не поддерживает (Windows 10 и старше) — окно остаётся непрозрачным."""
    try:
        hwnd = int(widget.winId())
        dwm = ctypes.windll.dwmapi

        dark = ctypes.c_int(1)
        dwm.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                                  ctypes.byref(dark), ctypes.sizeof(dark))

        glass = mode in ("mica", "acrylic")
        margins = _MARGINS(-1, -1, -1, -1) if glass else _MARGINS(0, 0, 0, 0)
        dwm.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

        value = ctypes.c_int(_BACKDROP.get(mode, 1))
        result = dwm.DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE,
                                           ctypes.byref(value),
                                           ctypes.sizeof(value))
        widget.update()
        return result == 0
    except Exception:  # noqa: BLE001
        return False
