#!/usr/bin/env python3
"""MOMENTUM 4 Control — неофициальное Windows-приложение для настройки
Sennheiser MOMENTUM 4 по Bluetooth (протокол GAIA v3)."""
import sys

if sys.version_info < (3, 9):
    raise SystemExit("Нужен Python 3.9 или новее (Bluetooth-сокеты Windows).")

from gui.app import main

if __name__ == "__main__":
    main()
