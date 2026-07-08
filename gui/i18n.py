"""Локализация интерфейса. Ключи — русские строки, значения — английский
перевод; при языке «ru» строки возвращаются как есть."""

LANG = "ru"


def set_language(lang: str):
    global LANG
    LANG = lang if lang in ("ru", "en") else "ru"


def tr(text: str) -> str:
    if LANG == "en":
        return _EN.get(text, text)
    return text


_EN = {
    # --- sidebar / pages ---
    "Обзор": "Overview",
    "Шумоподавление": "Noise control",
    "Звук": "Sound",
    "Сенсор и кнопки": "Touch & buttons",
    "Подключения": "Connections",
    "Система": "System",
    "Приложение": "App",

    # --- dashboard ---
    "Подключение · Bluetooth": "Connection · Bluetooth",
    "MAC-адрес, например 80:C3:BA:95:34:E0": "MAC address, e.g. 80:C3:BA:95:34:E0",
    "Найти": "Find",
    "Найти сопряжённые MOMENTUM 4 в Windows": "Find MOMENTUM 4 paired with Windows",
    "Подключить": "Connect",
    "Отключить": "Disconnect",
    "Подключение...": "Connecting...",
    "Автоподключение": "Auto-connect",
    "При запуске приложения и после обрыва связи":
        "On app start and after connection loss",
    "Наушники должны быть включены и сопряжены с этим компьютером.":
        "The headphones must be powered on and paired with this computer.",
    "Состояние": "Status",
    "Батарея": "Battery",
    "Зарядка": "Charging",
    "Аудиокодек": "Audio codec",
    "Кодек, которым звук передаётся прямо сейчас":
        "Codec currently used for audio streaming",
    "Датчик ношения": "Wear status",
    "Об устройстве": "About device",
    "Модель": "Model",
    "Прошивка": "Firmware",
    "Серийный номер": "Serial number",
    "Ревизия платы": "Hardware revision",

    # --- noise control ---
    "Активное шумоподавление": "Active noise cancellation",
    "Адаптивное шумоподавление": "Adaptive noise cancellation",
    "Наушники сами подстраивают глубину подавления под окружение":
        "Headphones adjust cancellation depth to your surroundings automatically",
    "Подавление шума ветра": "Wind noise reduction",
    "Снижает гул ветра на микрофонах. «Авто» — наушники включают его сами при ветре":
        "Reduces wind rumble on the microphones. Auto lets the headphones "
        "enable it when wind is detected",
    "Выключено": "Off",
    "Включено": "On",
    "Авто": "Auto",
    "Баланс шумоподавления": "Noise control balance",
    "Макс. ANC": "Max ANC",
    "Прозрачность": "Transparency",
    "Баланс: 0 — максимальное шумоподавление, 100 — полная прозрачность. "
    "Действует, когда адаптивный режим выключен.":
        "Balance: 0 — maximum noise cancellation, 100 — full transparency. "
        "Active when adaptive mode is off.",
    "Прозрачный режим": "Transparency mode",
    "Слышать окружение, не снимая наушников":
        "Hear your surroundings without taking the headphones off",
    "Уровень прозрачности": "Transparency level",
    "Насколько громко слышно окружение в прозрачном режиме":
        "How loud the surroundings are in transparency mode",
    "Пауза музыки": "Pause music",
    "Останавливать воспроизведение при включении прозрачного режима":
        "Pause playback when transparency mode is enabled",

    # --- sound ---
    "Режимы звука": "Sound modes",
    "Усиление низких частот": "Low frequency boost",
    "Эквалайзер · 5 полос · экспериментально": "Equalizer · 5 bands · experimental",
    "Применить": "Apply",
    "Записать положения ползунков в наушники": "Write slider values to the headphones",
    "Сбросить в 0": "Reset to 0",
    "Вернуть все полосы в 0": "Return all bands to 0",
    "Диагностика": "Diagnostics",
    "Прочитать параметры эквалайзера из наушников в журнал":
        "Read equalizer data from the headphones into the log",
    "Итоговая кривая: —": "Resulting curve: —",
    "Итоговая кривая (вместе с Sound Check): {values}":
        "Resulting curve (including Sound Check): {values}",
    "Экспериментальная функция. Значения в условных единицах — настраивайте "
    "на слух и нажимайте «Применить».":
        "Experimental feature. Values are in device units — tune by ear and "
        "press Apply.",
    "НЧ": "Low", "Н-СЧ": "L-Mid", "СЧ": "Mid", "В-СЧ": "H-Mid", "ВЧ": "High",
    "кГц": "kHz",
    "Гц": "Hz",
    "Звонки": "Calls",
    "Свой голос в звонках (Sidetone)": "Your voice during calls (sidetone)",
    "0 — не слышать себя, 5 — максимум": "0 — don't hear yourself, 5 — maximum",

    # --- touch & buttons ---
    "Сенсорная панель": "Touch panel",
    "Блокировка сенсора (Touch Lock)": "Touch lock",
    "Касания игнорируются — полезно под шапкой или капюшоном":
        "Touches are ignored — handy under a hat or hood",
    "Жесты": "Gestures",
    "Обновить": "Refresh",
    "Запросить список жестов заново": "Re-read the gesture list",
    "Сбросить к заводским": "Reset to defaults",
    "Вернуть заводское назначение жестов": "Restore default gesture mapping",
    "Показываются только жесты, которые наушники разрешают переназначать: "
    "на MOMENTUM 4 почти все жесты фиксированные.":
        "Only gestures the headphones allow to remap are shown: on MOMENTUM 4 "
        "almost all gestures are fixed.",
    "Наушники не разрешают переназначать жесты (ограничение прошивки "
    "MOMENTUM 4).":
        "The headphones do not allow gesture remapping (a MOMENTUM 4 firmware "
        "limitation).",
    "жест {n}": "gesture {n}",
    "код 0x{code}": "code 0x{code}",
    "1 касание": "1 tap",
    "2 касания": "2 taps",
    "3 касания": "3 taps",
    "Долгое нажатие": "Long press",
    "Долгое нажатие (отпускание)": "Long press (release)",
    "Очень долгое нажатие": "Very long press",
    "Очень долгое нажатие (отпускание)": "Very long press (release)",
    "Сверхдолгое нажатие": "Extra long press",
    "Сверхдолгое нажатие (отпускание)": "Extra long press (release)",
    "Удержание (повтор)": "Hold (repeat)",
    "Ничего": "Nothing",
    "Пауза / воспроизведение": "Play / pause",
    "Следующий трек": "Next track",
    "Предыдущий трек": "Previous track",
    "Громкость +": "Volume +",
    "Громкость −": "Volume −",
    "Голосовой ассистент": "Voice assistant",
    "Принять вызов": "Accept call",
    "Отклонить вызов": "Reject call",

    # --- connections ---
    "Мультипоинт · устройства в памяти наушников":
        "Multipoint · devices stored in the headphones",
    "Наушники держат до двух активных подключений одновременно":
        "The headphones keep up to two active connections at once",
    "Подключить выбранное устройство к наушникам":
        "Connect the selected device to the headphones",
    "Отключить выбранное устройство": "Disconnect the selected device",
    "Удалить": "Delete",
    "Убрать устройство из памяти наушников":
        "Remove the device from the headphones' memory",
    "подключено": "connected",
    "не подключено": "not connected",
    "  (этот ПК)": "  (this PC)",
    "Без имени": "Unnamed",
    "Статус USB не проверялся": "USB status not checked yet",
    "Проверить USB": "Check USB",
    "Показать, чем наушники видны в системе при подключении кабелем":
        "Show how the headphones appear in the system when connected by cable",
    "Проверка USB-устройств...": "Checking USB devices...",
    "Наушники не обнаружены на USB. Подключите их кабелем USB-C и нажмите "
    "«Проверить USB» ещё раз.":
        "Headphones not found on USB. Connect them with a USB-C cable and "
        "press Check USB again.",
    "Обнаружено USB-устройство: {names}.": "USB device found: {names}.",
    "Аудио по USB: ": "USB audio: ",
    "HID-интерфейс: ": "HID interface: ",
    "да": "yes",
    "нет": "no",
    "По USB-C наушники передают только звук и заряжаются — настройка возможна "
    "только по Bluetooth. Все настройки хранятся в самих наушниках и действуют "
    "при любом способе прослушивания.":
        "Over USB-C the headphones only stream audio and charge — "
        "configuration works over Bluetooth only. All settings are stored "
        "inside the headphones and apply however you listen.",

    # --- system ---
    "Ношение": "Wearing",
    "Датчик надевания": "On-head detection",
    "Наушники понимают, когда они на голове":
        "Headphones know when they are on your head",
    "Нужен для умной паузы и автоответа": "Required for smart pause and auto answer",
    "Умная пауза": "Smart pause",
    "Останавливать музыку, когда наушники сняты":
        "Pause music when the headphones are taken off",
    "Автоответ": "Auto answer",
    "Принимать входящий вызов при надевании наушников":
        "Answer an incoming call when you put the headphones on",
    "Мягче обработка звука во время разговора; слышно только в звонке":
        "Softer voice processing during calls; audible only in a call",
    "Голосовые подсказки": "Voice prompts",
    "Режим подсказок": "Prompt mode",
    "Голос и сигналы при включении, подключении и смене режимов":
        "Voice and tones on power-on, connection and mode changes",
    "Выключены": "Off",
    "Только сигналы": "Tones only",
    "Голос и сигналы": "Voice and tones",
    "Язык подсказок": "Prompt language",
    "Меняется только через мобильное приложение (загрузка языковых пакетов)":
        "Can only be changed in the mobile app (language packs download)",
    "Питание и связь": "Power & connection",
    "Автовыключение": "Auto power-off",
    "Выключать наушники при бездействии": "Turn the headphones off when idle",
    "Выключен": "Off",
    "5 минут": "5 minutes",
    "10 минут": "10 minutes",
    "15 минут": "15 minutes",
    "30 минут": "30 minutes",
    "1 час": "1 hour",
    "2 часа": "2 hours",
    "Низкая задержка": "Low latency",
    "Меньше рассинхрон в видео и играх, выше расход батареи":
        "Less audio delay in videos and games, higher battery drain",
    "Режим совместимости Bluetooth": "Bluetooth compatibility mode",
    "Стабильность соединения вместо максимального качества звука. Мгновенно "
    "ничего не меняет — применяется при следующем подключении наушников":
        "Connection stability instead of maximum audio quality. Takes effect "
        "on the next connection",
    "Английский": "English",
    "Немецкий": "German",
    "Французский": "French",
    "Испанский": "Spanish",
    "Китайский": "Chinese",
    "Японский": "Japanese",
    "Русский": "Russian",
    "Корейский": "Korean",
    "Не заряжается": "Not charging",
    "Заряжается": "Charging",
    "Заряжено": "Fully charged",
    "Неизвестно": "Unknown",
    "В чехле": "In case",
    "Сняты": "Off head",
    "Надеты": "On head",
    "код {n}": "code {n}",

    # --- app page ---
    "Оформление": "Appearance",
    "Стиль": "Style",
    "Меняет облик всего приложения": "Changes the look of the whole app",
    "Windows 11 (графит)": "Windows 11 (graphite)",
    "Фон окна": "Window background",
    "Непрозрачный": "Opaque",
    "Mica (полупрозрачный)": "Mica (translucent)",
    "Acrylic (размытие)": "Acrylic (blur)",
    "Mica и Acrylic — нативные эффекты Windows 11":
        "Mica and Acrylic are native Windows 11 effects",
    "Mica — лёгкая полупрозрачность, Acrylic — сильное размытие фона":
        "Mica — subtle translucency, Acrylic — strong background blur",
    "Язык": "Language",
    "Вступит в силу после перезапуска приложения":
        "Takes effect after the app restarts",
    "Смена языка": "Language change",
    "Перезапустить приложение сейчас, чтобы применить язык?":
        "Restart the app now to apply the language?",
    "Журнал": "Log",
    "Подробный лог обмена (hex)": "Verbose traffic log (hex)",
    "Показывать весь обмен с наушниками в hex":
        "Show all traffic with the headphones in hex",
    "Очистить": "Clear",
    "Опасная зона": "Danger zone",
    "Сброс наушников к заводским настройкам": "Factory reset the headphones",
    "Заводской сброс": "Factory reset",
    "Удаляет все настройки и список сопряжённых устройств в наушниках":
        "Erases all settings and the pairing list stored in the headphones",

    # --- tray / dialogs / log ---
    "Не подключено": "Not connected",
    "Подключено": "Connected",
    "● Подключено": "● Connected",
    "○ Не подключено": "○ Not connected",
    "ANC: включить": "ANC: on",
    "ANC: выключить": "ANC: off",
    "Открыть окно": "Open window",
    "Выход": "Quit",
    "Приложение продолжает работать в трее.": "The app keeps running in the tray.",
    "MOMENTUM 4 — батарея {n}%": "MOMENTUM 4 — battery {n}%",
    "Поиск сопряжённых MOMENTUM 4...": "Searching for paired MOMENTUM 4...",
    "Найдены наушники: {mac}": "Headphones found: {mac}",
    "Сопряжённые MOMENTUM 4 не найдены.": "No paired MOMENTUM 4 found.",
    "Не найдено": "Not found",
    "Сопряжённые MOMENTUM 4 не найдены.\nСначала выполните сопряжение "
    "наушников с Windows (Параметры → Bluetooth и устройства).":
        "No paired MOMENTUM 4 found.\nPair the headphones with Windows first "
        "(Settings → Bluetooth & devices).",
    "Подключение к {mac}...": "Connecting to {mac}...",
    "Подключено (RFCOMM канал {ch}). Загрузка состояния...":
        "Connected (RFCOMM channel {ch}). Loading state...",
    "Ошибка подключения: {e}": "Connection error: {e}",
    "Не удалось подключиться": "Connection failed",
    "Отключено (автоподключение приостановлено до нажатия «Подключить»)":
        "Disconnected (auto-connect paused until you press Connect)",
    "Состояние загружено.": "State loaded.",
    "Наушники не подключены.": "Headphones are not connected.",
    "EQ отправлен: {g}": "EQ sent: {g}",
    "EQ сброшен в 0.": "EQ reset to 0.",
    "Диагностика EQ (только чтение)...": "EQ diagnostics (read-only)...",
    "Диагностика EQ завершена.": "EQ diagnostics finished.",
    "Жест {p} -> {f}": "Gesture {p} -> {f}",
    "Сброс жестов": "Reset gestures",
    "Вернуть заводское назначение жестов?": "Restore default gesture mapping?",
    "Удаление": "Delete",
    "Удалить устройство №{i} из памяти наушников?":
        "Remove device #{i} from the headphones' memory?",
    "Наушники будут сброшены к заводским настройкам: все настройки и список "
    "сопряжённых устройств будут удалены, соединение разорвётся.\n\nПродолжить?":
        "The headphones will be reset to factory defaults: all settings and "
        "the pairing list will be erased, and the connection will drop."
        "\n\nContinue?",
    "Команда заводского сброса отправлена.": "Factory reset command sent.",
    "Ошибка: {e}": "Error: {e}",

    # --- client (m4) ---
    "Не удалось найти GAIA-канал RFCOMM. Убедитесь, что наушники включены и "
    "сопряжены с этим ПК.":
        "Could not find the GAIA RFCOMM channel. Make sure the headphones are "
        "powered on and paired with this PC.",
    "GAIA-канал найден: RFCOMM {ch}": "GAIA channel found: RFCOMM {ch}",
    "Нет подключения": "Not connected",
    "Нет ответа на команду 0x{cmd}": "No response to command 0x{cmd}",
    "Устройство отклонило команду 0x{cmd}: {reason}":
        "Device rejected command 0x{cmd}: {reason}",
    "Соединение разорвано": "Connection lost",
    "команда не поддерживается": "command not supported",
    "недостаточно прав": "insufficient permissions",
    "неверные параметры": "invalid parameters",
    "неверное состояние устройства": "invalid device state",
    "операция уже выполняется": "operation already in progress",
    "канал {ch}: {e}": "channel {ch}: {e}",
}
