@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Сборка M4Control.exe...
py -3 -m pip install -r requirements.txt pyinstaller --quiet --disable-pip-version-check
py -3 -m PyInstaller --noconfirm --onefile --windowed --name M4Control --icon assets\icon.ico main.py
if exist dist\M4Control.exe (
    echo.
    echo Готово: dist\M4Control.exe
) else (
    echo.
    echo Сборка не удалась.
)
pause
