# MOMENTUM 4 Control

Неофициальное Windows-приложение для настройки **Sennheiser MOMENTUM 4** по
Bluetooth — аналог мобильного Smart Control для ПК. Интерфейс на русском и
английском.

## Возможности

- Батарея, зарядка, активный кодек, датчик ношения, информация об устройстве
- Шумоподавление: ANC, адаптивный режим, анти-ветер, баланс «ANC ↔
  прозрачность», прозрачный режим с уровнем
- Bass Boost, 5-полосный эквалайзер (экспериментально), громкость своего
  голоса в звонках
- Блокировка сенсора, умная пауза, автоответ, автовыключение, низкая
  задержка и другие настройки
- Мультипоинт: управление устройствами в памяти наушников
- Быстрые переключения из трея
- Темы: Windows 11 (графит) / macOS, фон Непрозрачный / Mica / Acrylic
  <img width="1000" height="754" alt="изображение" src="https://github.com/user-attachments/assets/1aa6b7cb-7bbb-4c59-9820-3aab8f4d20dd" />
  <img width="1008" height="750" alt="изображение" src="https://github.com/user-attachments/assets/d8741e23-91f8-47c7-aa9a-e9ae0e5a1ea4" />
  <img width="1009" height="756" alt="изображение" src="https://github.com/user-attachments/assets/6245f3a9-dcba-4d63-a6fc-2a1da8bb5f5b" />
  <img width="1005" height="758" alt="изображение" src="https://github.com/user-attachments/assets/664580e2-b563-44d0-b5ec-225a133268fb" />

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
