# MOMENTUM 4 Control

Неофициальное Windows-приложение для настройки **Sennheiser MOMENTUM 4** по
Bluetooth — аналог мобильного Smart Control для ПК. Интерфейс на русском и
английском.

## Возможности

- Батарея, зарядка, активный кодек, датчик ношения, информация об устройстве
- Шумоподавление: ANC, адаптивный режим, анти-ветер, баланс «ANC ↔
  прозрачность», прозрачный режим с уровнем
- Bass Boost, 5-полосный эквалайзер (±6 дБ, 63 Гц – 8 кГц, как в официальном
  приложении), громкость своего голоса в звонках
- Блокировка сенсора, умная пауза, автоответ, автовыключение, низкая
  задержка и другие настройки
- Мультипоинт: управление устройствами в памяти наушников
- Быстрые переключения из трея
- Темы: Windows 11 (графит) / macOS, фон Непрозрачный / Mica / Acrylic
  <img width="1002" height="752" alt="изображение" src="https://github.com/user-attachments/assets/f3e92713-6fd8-4ed7-91f3-8ad557f434da" />
  <img width="1002" height="752" alt="изображение" src="https://github.com/user-attachments/assets/10d23859-2de4-46ae-b0a9-79eee623457e" />

## Запуск

**Готовый exe** — скачайте `M4Control.exe` из [Releases](../../releases) и
запустите. Наушники должны быть сопряжены с Windows.

**Из исходников** — Python 3.9+, затем `install.bat` и `start.bat`.
Собрать exe самому: `build.bat`.

## Как это работает

Протокол Qualcomm GAIA v3 поверх Bluetooth RFCOMM (vendor `0x0495`); таблица
команд — в [m4/protocol.py](m4/protocol.py). Часть команд восстановлена из
схемы официального приложения, часть найдена на живом устройстве. Спасибо
проектам [zaval/sennheiser-desktop-client](https://github.com/zaval/sennheiser-desktop-client)
и [f3Y0/momentum4-control](https://github.com/f3Y0/momentum4-control).

Настройка по USB невозможна — по кабелю наушники только играют звук и
заряжаются; все настройки хранятся в самих наушниках.

Диагностика без GUI: `py -3 diagnose.py`.

## Лицензия

[MIT](LICENSE). Неофициальный проект, не связан с Sennheiser/Sonova;
используйте на свой риск.
