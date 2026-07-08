@echo off
chcp 65001 >nul
echo Установка зависимостей MOMENTUM 4 Control...
py -3 -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo.
    echo Ошибка установки. Проверьте, что установлен Python 3.9+ (python.org).
    pause
    exit /b 1
)
echo.
echo Готово! Запускайте приложение через start.bat
pause
