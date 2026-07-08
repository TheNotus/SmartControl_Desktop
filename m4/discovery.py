"""Discovery of paired MOMENTUM 4 devices (Bluetooth MAC) and USB presence.

Uses PowerShell PnP queries — no extra dependencies, no admin rights.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Optional

CREATE_NO_WINDOW = 0x08000000


def _powershell(command: str, timeout: int = 20) -> str:
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=timeout,
            creationflags=CREATE_NO_WINDOW,
        )
        return out.stdout or ""
    except Exception:  # noqa: BLE001
        return ""


def find_paired_momentum_mac() -> Optional[str]:
    """Returns the MAC of a paired MOMENTUM 4 as 'AA:BB:CC:DD:EE:FF', or None."""
    out = _powershell(
        "Get-PnpDevice -Class Bluetooth | "
        "Where-Object { $_.FriendlyName -match 'MOMENTUM' } | "
        "Select-Object -ExpandProperty InstanceId")
    m = re.search(r"DEV_([0-9A-F]{12})", out, re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1).upper()
    return ":".join(raw[i:i + 2] for i in range(0, 12, 2))


@dataclass
class UsbStatus:
    present: bool
    audio: bool
    hid: bool
    names: list[str]


def check_usb() -> UsbStatus:
    """Checks whether MOMENTUM 4 is currently attached over USB and which
    interfaces (audio / HID) it exposes."""
    out = _powershell(
        "Get-PnpDevice -PresentOnly | "
        "Where-Object { $_.FriendlyName -match 'MOMENTUM|Sennheiser' -and "
        "($_.InstanceId -like 'USB*' -or $_.InstanceId -like 'HID*' -or "
        "$_.InstanceId -like 'SWD\\\\MMDEVAPI*') } | "
        "ForEach-Object { $_.InstanceId + '|' + $_.FriendlyName + '|' + $_.Class }")
    present = audio = hid = False
    names: list[str] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        instance, _, rest = line.partition("|")
        name, _, cls = rest.partition("|")
        if instance.upper().startswith(("USB", "HID")):
            present = True
            if name not in names:
                names.append(name)
            if cls.strip().lower() in ("audioendpoint", "media"):
                audio = True
            if instance.upper().startswith("HID"):
                hid = True
    return UsbStatus(present=present, audio=audio, hid=hid, names=names)
