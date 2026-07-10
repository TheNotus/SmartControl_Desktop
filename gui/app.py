"""MOMENTUM 4 Control — главное окно приложения."""
from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from PySide6.QtCore import QObject, QProcess, QSettings, Qt, QTimer, Signal
from PySide6.QtGui import (QCloseEvent, QColor, QFont, QFontMetrics, QIcon,
                           QPainter, QPixmap)
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QScrollArea,
    QSlider, QStackedWidget, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from m4 import protocol as P
from m4.client import GaiaClient
from m4.device import Momentum4
from m4.discovery import check_usb, find_paired_momentum_mac
from . import i18n
from . import style as S
from .i18n import tr
from .win_effects import apply_backdrop

ORG = "M4Control"
APP = "M4Control"

POWEROFF_CHOICES = [
    ("Выключен", 0), ("5 минут", 300), ("10 минут", 600), ("15 минут", 900),
    ("30 минут", 1800), ("1 час", 3600), ("2 часа", 7200),
]

STYLE_NAMES = ["Windows 11 (графит)", "macOS"]
BG_NAMES = ["Непрозрачный", "Mica (полупрозрачный)", "Acrylic (размытие)"]
LANG_CODES = ("ru", "en")
LANG_NAMES = ["Русский", "English"]

# Единицы эквалайзера — 0.1 дБ, диапазон ±6 дБ
# (сверено с официальным приложением по логу обмена)


# --------------------------------------------------------------------------- helpers
class Bridge(QObject):
    """Runs blocking device calls in a worker thread, delivers results in GUI thread."""
    _done = Signal(object, object, object)  # callback, result, exception

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="m4-worker")
        self._done.connect(self._dispatch)
        self.default_error_handler = lambda exc: None

    def run(self, fn, ok=None, fail=None):
        def task():
            try:
                result = fn()
            except Exception as exc:  # noqa: BLE001
                self._done.emit(fail, None, exc)
                return
            self._done.emit(ok, result, None)
        self.pool.submit(task)

    def _dispatch(self, callback, result, exc):
        if exc is not None:
            (callback or self.default_error_handler)(exc)
        elif callback is not None:
            callback(result)


class Notifier(QObject):
    notification = Signal(int, int, bytes)
    disconnected = Signal(str)
    log = Signal(str)


class ToggleSwitch(QCheckBox):
    """Тумблер с бегунком; цвета берёт из текущей темы (style.SWITCH)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(40, 22)

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            p.setOpacity(0.4)
        on = self.isChecked()
        track = QColor(S.SWITCH["track_on" if on else "track_off"])
        p.setBrush(track)
        if not on:
            pen_color = QColor(S.SWITCH["track_off_border"])
            p.setPen(pen_color)
        else:
            p.setPen(Qt.NoPen)
        p.drawRoundedRect(1, 1, 38, 20, 10, 10)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(S.SWITCH["knob_on" if on else "knob_off"]))
        x = 22 if on else 4
        p.drawEllipse(x, 4, 14, 14)
        p.end()


def fluent_icon(glyph: str, size: int = 18, color: str = "#d9d9d9"):
    """Иконка из системного шрифта Segoe Fluent Icons; None, если глифа нет."""
    if not glyph:
        return None
    try:
        font = QFont("Segoe Fluent Icons")
        font.setPixelSize(size)
        if not QFontMetrics(font).inFont(glyph):
            return None
        pm = QPixmap(size + 6, size + 6)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setFont(font)
        p.setPen(QColor(color))
        p.drawText(pm.rect(), Qt.AlignCenter, glyph)
        p.end()
        return QIcon(pm)
    except Exception:  # noqa: BLE001
        return None


class Group:
    """Группа настроек: заголовок над скруглённой картой, внутри — строки
    «подпись слева, контрол справа», разделённые тонкими линиями."""

    def __init__(self, title: str | None = None):
        self.widget = QWidget()
        outer = QVBoxLayout(self.widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)
        if title:
            t = QLabel(title)
            t.setObjectName("groupTitle")
            outer.addWidget(t)
        self.frame = QFrame()
        self.frame.setObjectName("card")
        self.box = QVBoxLayout(self.frame)
        self.box.setContentsMargins(0, 2, 0, 2)
        self.box.setSpacing(0)
        outer.addWidget(self.frame)
        self._outer = outer

    def _separator(self):
        if self.box.count():
            sep = QFrame()
            sep.setObjectName("sep")
            sep.setFixedHeight(1)
            wrap = QWidget()
            lay = QHBoxLayout(wrap)
            lay.setContentsMargins(14, 0, 14, 0)
            lay.addWidget(sep)
            self.box.addWidget(wrap)

    def add_row(self, title: str, control: QWidget | None = None,
                hint_text: str | None = None,
                tooltip: str | None = None) -> QWidget:
        self._separator()
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(14, 9, 14, 9)
        h.setSpacing(12)
        left = QVBoxLayout()
        left.setSpacing(2)
        left.addWidget(QLabel(title))
        if hint_text:
            hl = QLabel(hint_text)
            hl.setObjectName("hint")
            hl.setWordWrap(True)
            left.addWidget(hl)
        h.addLayout(left, 1)
        if control is not None:
            h.addWidget(control, 0, Qt.AlignRight | Qt.AlignVCenter)
        if tooltip:
            row.setToolTip(tooltip)
        self.box.addWidget(row)
        return row

    def add_block(self, widget_or_layout, with_separator: bool = True,
                  tooltip: str | None = None):
        """Строка на всю ширину (журнал, список, эквалайзер...)."""
        if with_separator:
            self._separator()
        wrap = QWidget()
        if isinstance(widget_or_layout, QWidget):
            lay = QVBoxLayout(wrap)
            lay.setContentsMargins(14, 10, 14, 10)
            lay.addWidget(widget_or_layout)
        else:
            widget_or_layout.setContentsMargins(14, 10, 14, 10)
            wrap.setLayout(widget_or_layout)
        if tooltip:
            wrap.setToolTip(tooltip)
        self.box.addWidget(wrap)
        return wrap

    def add_footnote(self, text: str) -> QLabel:
        hl = QLabel(text)
        hl.setObjectName("hint")
        hl.setWordWrap(True)
        hl.setContentsMargins(4, 0, 4, 0)
        self._outer.addWidget(hl)
        return hl


def codec_name(codec) -> str:
    """Имя кодека; неизвестные значения показываем номером, а не прочерком —
    так пользователи смогут сообщить о новых кодеках прошивки."""
    if codec is None:
        return "—"
    known = P.CODECS.get(codec)
    if known:
        return known
    return tr("код {n}").format(n=codec)


def value_label(text: str = "—") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #b8b8b8;")
    lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return lbl


def set_checked_silent(widget, checked: bool):
    widget.blockSignals(True)
    widget.setChecked(bool(checked))
    widget.blockSignals(False)
    widget.update()


def make_app_icon() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#3a3a3a"))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(2, 2, 60, 60, 14, 14)
    p.setPen(QColor("#ffffff"))
    f = QFont("Segoe UI", 20, QFont.Bold)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignCenter, "M4")
    p.end()
    return QIcon(pm)


# --------------------------------------------------------------------------- main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MOMENTUM 4 Control")
        self.setWindowIcon(make_app_icon())
        self.resize(1000, 720)

        self.settings = QSettings(ORG, APP)
        self.bridge = Bridge(self)
        self.bridge.default_error_handler = self.show_error
        self.notifier = Notifier(self)
        self.notifier.notification.connect(self.on_notification)
        self.notifier.disconnected.connect(self.on_disconnected)
        self.notifier.log.connect(self.append_log)

        self.client: GaiaClient | None = None
        self.dev: Momentum4 | None = None
        self.verbose_log = False
        self._connecting = False        # защита от параллельных подключений
        self._user_disconnected = False  # «Отключить» нажал пользователь —
                                         # автоподключение не должно возвращать связь

        # прозрачные режимы требуют WA_TranslucentBackground до первого показа
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.ui_style = self.settings.value("ui_style", "win11")
        self.ui_bg = self.settings.value("ui_bg", self.settings.value("ui_mode", "opaque"))
        if self.ui_style not in S.UI_STYLES:
            self.ui_style = "win11"
        if self.ui_bg not in S.UI_BACKDROPS:
            self.ui_bg = "opaque"

        self._build_ui()
        self._build_tray()
        self.apply_theme(self.ui_style, self.ui_bg)

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(30000)
        self.poll_timer.timeout.connect(self.poll_status)

        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.setInterval(8000)
        self.reconnect_timer.timeout.connect(self.try_autoreconnect)

        mac = self.settings.value("mac", "")
        if mac:
            self.mac_edit.setText(mac)
        if self.settings.value("autoconnect", "true") == "true":
            set_checked_silent(self.autoconnect_cb, True)
            QTimer.singleShot(300, self.connect_device)
        self.reconnect_timer.start()

    # ----------------------------------------------------------------- UI skeleton
    def _build_ui(self):
        root = QWidget()
        root_lay = QHBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)
        self.setCentralWidget(root)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(205)
        side_lay = QVBoxLayout(sidebar)
        side_lay.setContentsMargins(0, 0, 0, 12)
        title = QLabel("MOMENTUM 4")
        title.setObjectName("appTitle")
        side_lay.addWidget(title)

        self.stack = QStackedWidget()
        pages = [
            (tr("Обзор"), "", self._page_dashboard()),
            (tr("Шумоподавление"), "", self._page_noise()),
            (tr("Звук"), "", self._page_sound()),
            (tr("Подключения"), "", self._page_connections()),
            (tr("Система"), "", self._page_system()),
            (tr("Приложение"), "", self._page_app()),
        ]
        self.nav_buttons = []
        for i, (name, glyph, page) in enumerate(pages):
            btn = QPushButton(name)
            icon = fluent_icon(glyph)
            if icon:
                btn.setIcon(icon)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(partial(self.switch_page, i))
            side_lay.addWidget(btn)
            self.nav_buttons.append(btn)
            self.stack.addWidget(page)
        side_lay.addStretch(1)

        self.conn_label = QLabel(tr("○ Не подключено"))
        self.conn_label.setStyleSheet("color: #8f8f8f;")
        self.conn_label.setContentsMargins(18, 0, 0, 0)
        side_lay.addWidget(self.conn_label)

        root_lay.addWidget(sidebar)
        root_lay.addWidget(self.stack, 1)
        self.nav_buttons[0].setChecked(True)

    def switch_page(self, index: int):
        for i, b in enumerate(self.nav_buttons):
            b.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    @staticmethod
    def _scroll_page(title: str) -> tuple[QWidget, QVBoxLayout]:
        outer = QScrollArea()
        outer.setWidgetResizable(True)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(26, 22, 26, 24)
        lay.setSpacing(16)
        t = QLabel(title)
        t.setObjectName("pageTitle")
        lay.addWidget(t)
        outer.setWidget(inner)
        return outer, lay

    # ----------------------------------------------------------------- pages
    def _page_dashboard(self) -> QWidget:
        page, lay = self._scroll_page(tr("Обзор"))

        g = Group(tr("Подключение · Bluetooth"))
        conn_row = QHBoxLayout()
        self.mac_edit = QLineEdit()
        self.mac_edit.setPlaceholderText(tr("MAC-адрес, например 80:C3:BA:95:34:E0"))
        find_btn = QPushButton(tr("Найти"))
        find_btn.setToolTip(tr("Найти сопряжённые MOMENTUM 4 в Windows"))
        find_btn.clicked.connect(self.autodetect_mac)
        self.connect_btn = QPushButton(tr("Подключить"))
        self.connect_btn.setObjectName("primary")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_row.addWidget(self.mac_edit, 1)
        conn_row.addWidget(find_btn)
        conn_row.addWidget(self.connect_btn)
        g.add_block(conn_row, with_separator=False)
        self.autoconnect_cb = ToggleSwitch()
        self.autoconnect_cb.toggled.connect(
            lambda v: self.settings.setValue("autoconnect", "true" if v else "false"))
        g.add_row(tr("Автоподключение"),
                  self.autoconnect_cb,
                  tr("При запуске приложения и после обрыва связи"))
        g.add_footnote(tr("Наушники должны быть включены и сопряжены с этим компьютером."))
        lay.addWidget(g.widget)

        g = Group(tr("Состояние"))
        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)
        self.battery_bar.setValue(0)
        self.battery_bar.setFormat("%p%")
        self.battery_bar.setFixedWidth(240)
        g.add_row(tr("Батарея"), self.battery_bar)
        self.charge_label = value_label()
        g.add_row(tr("Зарядка"), self.charge_label)
        self.codec_label = value_label()
        g.add_row(tr("Аудиокодек"), self.codec_label,
                  tooltip=tr("Кодек, которым звук передаётся прямо сейчас"))
        self.wear_label = value_label()
        g.add_row(tr("Датчик ношения"), self.wear_label)
        lay.addWidget(g.widget)

        g = Group(tr("Об устройстве"))
        self.info_labels = {}
        for key, name in [("model", tr("Модель")), ("firmware", tr("Прошивка")),
                          ("serial", tr("Серийный номер")),
                          ("hw_revision", tr("Ревизия платы"))]:
            lbl = value_label()
            self.info_labels[key] = lbl
            g.add_row(name, lbl)
        lay.addWidget(g.widget)
        lay.addStretch(1)
        return page

    def _page_noise(self) -> QWidget:
        page, lay = self._scroll_page(tr("Шумоподавление"))

        g = Group(tr("Активное шумоподавление"))
        self.anc_cb = ToggleSwitch()
        self.anc_cb.toggled.connect(self.on_anc_toggled)
        g.add_row(tr("Шумоподавление"), self.anc_cb)
        self.adaptive_cb = ToggleSwitch()
        self.adaptive_cb.toggled.connect(lambda v: self.run_set(
            lambda d: d.set_anc_mode(P.ANC_MODE_ADAPTIVE, int(v)),
            self.adaptive_cb, not v))
        g.add_row(tr("Адаптивное шумоподавление"), self.adaptive_cb,
                  tr("Наушники сами подстраивают глубину подавления под окружение"))
        self.wind_combo = QComboBox()
        self.wind_combo.addItems([tr("Выключено"), tr("Включено"), tr("Авто")])
        self.wind_combo.setFixedWidth(200)
        self.wind_combo.activated.connect(lambda i: self.run_set(
            lambda d: d.set_anc_mode(P.ANC_MODE_ANTIWIND, i)))
        g.add_row(tr("Подавление шума ветра"), self.wind_combo,
                  tooltip=tr("Снижает гул ветра на микрофонах. «Авто» — наушники "
                             "включают его сами при ветре"))

        balance = QVBoxLayout()
        bal_top = QHBoxLayout()
        bal_top.addWidget(QLabel(tr("Баланс шумоподавления")))
        bal_top.addStretch(1)
        self.anc_level_label = value_label()
        bal_top.addWidget(self.anc_level_label)
        balance.addLayout(bal_top)
        bal_row = QHBoxLayout()
        left_lbl = QLabel(tr("Макс. ANC"))
        left_lbl.setObjectName("hint")
        right_lbl = QLabel(tr("Прозрачность"))
        right_lbl.setObjectName("hint")
        self.anc_level = QSlider(Qt.Horizontal)
        self.anc_level.setRange(0, 100)
        self.anc_level.setSingleStep(5)
        self.anc_level.sliderReleased.connect(self.on_anc_level_changed)
        self.anc_level.valueChanged.connect(
            lambda v: self.anc_level_label.setText(str(v)))
        bal_row.addWidget(left_lbl)
        bal_row.addWidget(self.anc_level, 1)
        bal_row.addWidget(right_lbl)
        balance.addLayout(bal_row)
        g.add_block(balance)
        g.add_footnote(tr("Баланс: 0 — максимальное шумоподавление, 100 — полная "
                          "прозрачность. Действует, когда адаптивный режим выключен."))
        lay.addWidget(g.widget)

        g = Group(tr("Прозрачный режим"))
        self.transparency_cb = ToggleSwitch()
        self.transparency_cb.toggled.connect(self.on_transparency_toggled)
        g.add_row(tr("Прозрачный режим"), self.transparency_cb,
                  tr("Слышать окружение, не снимая наушников"))
        self.th_level = QSlider(Qt.Horizontal)
        self.th_level.setRange(0, 100)
        self.th_level.setFixedWidth(240)
        self.th_level.sliderReleased.connect(self.on_th_level_changed)
        self.th_level_label = value_label()
        self.th_level.valueChanged.connect(
            lambda v: self.th_level_label.setText(str(v)))
        th_wrap = QHBoxLayout()
        th_wrap.setSpacing(10)
        th_wrap.addWidget(self.th_level)
        th_wrap.addWidget(self.th_level_label)
        th_widget = QWidget()
        th_widget.setLayout(th_wrap)
        g.add_row(tr("Уровень прозрачности"), th_widget,
                  tooltip=tr("Насколько громко слышно окружение в прозрачном режиме"))
        self.autopause_cb = ToggleSwitch()
        self.autopause_cb.toggled.connect(self.on_autopause_toggled)
        g.add_row(tr("Пауза музыки"), self.autopause_cb,
                  tr("Останавливать воспроизведение при включении прозрачного режима"))
        lay.addWidget(g.widget)
        lay.addStretch(1)
        return page

    def _page_sound(self) -> QWidget:
        page, lay = self._scroll_page(tr("Звук"))

        g = Group(tr("Режимы звука"))
        self.bass_cb = ToggleSwitch()
        self.bass_cb.toggled.connect(self.on_bass_toggled)
        g.add_row("Bass Boost", self.bass_cb, tr("Усиление низких частот"))
        g.add_footnote(tr("Официальное приложение отключает Bass Boost при активной "
                          "Sound Personalization. Наушники это состояние не сообщают, "
                          "поэтому здесь переключатель доступен всегда."))
        lay.addWidget(g.widget)

        g = Group(tr("Эквалайзер · 5 полос"))
        self.eq_sliders = []
        self.eq_value_labels = []
        self.eq_freq_labels = []
        eq_row = QHBoxLayout()
        eq_row.setSpacing(18)
        band_names = [tr("НЧ"), tr("Н-СЧ"), tr("СЧ"), tr("В-СЧ"), tr("ВЧ")]
        for i in range(5):
            col = QVBoxLayout()
            col.setSpacing(4)
            val = QLabel("0.0")
            val.setAlignment(Qt.AlignHCenter)
            val.setStyleSheet("color: #b8b8b8;")
            s = QSlider(Qt.Vertical)
            s.setRange(-60, 60)
            s.setValue(0)
            s.setFixedHeight(130)
            s.setEnabled(False)
            s.valueChanged.connect(partial(
                lambda lbl, v: lbl.setText(f"{v / 10:.1f}"), val))
            f = QLabel(band_names[i])
            f.setObjectName("hint")
            f.setAlignment(Qt.AlignHCenter)
            col.addWidget(val)
            col.addWidget(s, alignment=Qt.AlignHCenter)
            col.addWidget(f)
            self.eq_sliders.append(s)
            self.eq_value_labels.append(val)
            self.eq_freq_labels.append(f)
            eq_row.addLayout(col)
        eq_row.addStretch(1)

        eq_col = QVBoxLayout()
        eq_col.setSpacing(10)
        eq_col.addLayout(eq_row)
        btn_row = QHBoxLayout()
        self.eq_apply_btn = QPushButton(tr("Применить"))
        self.eq_apply_btn.setObjectName("primary")
        self.eq_apply_btn.setEnabled(False)
        self.eq_apply_btn.setToolTip(tr("Записать положения ползунков в наушники"))
        self.eq_apply_btn.clicked.connect(self.on_apply_eq)
        self.eq_zero_btn = QPushButton(tr("Сбросить в 0"))
        self.eq_zero_btn.setEnabled(False)
        self.eq_zero_btn.setToolTip(tr("Вернуть все полосы в 0"))
        self.eq_zero_btn.clicked.connect(self.on_zero_eq)
        self.eq_probe_btn = QPushButton(tr("Диагностика"))
        self.eq_probe_btn.setToolTip(
            tr("Прочитать параметры эквалайзера из наушников в журнал"))
        self.eq_probe_btn.clicked.connect(self.on_probe_eq)
        btn_row.addWidget(self.eq_apply_btn)
        btn_row.addWidget(self.eq_zero_btn)
        btn_row.addWidget(self.eq_probe_btn)
        btn_row.addStretch(1)
        eq_col.addLayout(btn_row)
        self.eq_curve_label = QLabel(tr("Итоговая кривая: —"))
        self.eq_curve_label.setObjectName("hint")
        eq_col.addWidget(self.eq_curve_label)
        g.add_block(eq_col, with_separator=False)
        g.add_footnote(tr("Диапазон ±6 дБ, полосы 63 Гц – 8 кГц — как в официальном "
                          "приложении. Изменения применяются кнопкой «Применить»."))
        lay.addWidget(g.widget)

        g = Group(tr("Звонки"))
        self.sidetone = QSlider(Qt.Horizontal)
        self.sidetone.setRange(0, 5)
        self.sidetone.setPageStep(1)
        self.sidetone.setFixedWidth(240)
        self.sidetone.sliderReleased.connect(self.on_sidetone_changed)
        self.sidetone_label = value_label()
        self.sidetone.valueChanged.connect(
            lambda v: self.sidetone_label.setText(str(v)))
        st_wrap = QHBoxLayout()
        st_wrap.setSpacing(10)
        st_wrap.addWidget(self.sidetone)
        st_wrap.addWidget(self.sidetone_label)
        st_widget = QWidget()
        st_widget.setLayout(st_wrap)
        g.add_row(tr("Свой голос в звонках (Sidetone)"), st_widget,
                  tr("0 — не слышать себя, 5 — максимум"))
        lay.addWidget(g.widget)
        lay.addStretch(1)
        return page

    def _page_connections(self) -> QWidget:
        page, lay = self._scroll_page(tr("Подключения"))

        g = Group(tr("Мультипоинт · устройства в памяти наушников"))
        self.pdl_list = QListWidget()
        self.pdl_list.setMinimumHeight(150)
        self.pdl_list.setToolTip(
            tr("Наушники держат до двух активных подключений одновременно"))
        pdl_col = QVBoxLayout()
        pdl_col.setSpacing(10)
        pdl_col.addWidget(self.pdl_list)
        row = QHBoxLayout()
        self.pdl_refresh = QPushButton(tr("Обновить"))
        self.pdl_refresh.clicked.connect(self.load_paired_devices)
        self.pdl_connect = QPushButton(tr("Подключить"))
        self.pdl_connect.setToolTip(tr("Подключить выбранное устройство к наушникам"))
        self.pdl_connect.clicked.connect(lambda: self.pdl_action("connect"))
        self.pdl_disconnect = QPushButton(tr("Отключить"))
        self.pdl_disconnect.setToolTip(tr("Отключить выбранное устройство"))
        self.pdl_disconnect.clicked.connect(lambda: self.pdl_action("disconnect"))
        self.pdl_delete = QPushButton(tr("Удалить"))
        self.pdl_delete.setObjectName("danger")
        self.pdl_delete.setToolTip(tr("Убрать устройство из памяти наушников"))
        self.pdl_delete.clicked.connect(lambda: self.pdl_action("delete"))
        for b in (self.pdl_refresh, self.pdl_connect, self.pdl_disconnect,
                  self.pdl_delete):
            row.addWidget(b)
        row.addStretch(1)
        pdl_col.addLayout(row)
        g.add_block(pdl_col, with_separator=False)
        lay.addWidget(g.widget)

        g = Group("USB")
        self.usb_label = QLabel(tr("Статус USB не проверялся"))
        self.usb_label.setWordWrap(True)
        usb_col = QVBoxLayout()
        usb_col.setSpacing(10)
        usb_col.addWidget(self.usb_label)
        usb_btn = QPushButton(tr("Проверить USB"))
        usb_btn.setToolTip(
            tr("Показать, чем наушники видны в системе при подключении кабелем"))
        usb_btn.clicked.connect(self.on_check_usb)
        usb_col.addWidget(usb_btn, alignment=Qt.AlignLeft)
        g.add_block(usb_col, with_separator=False)
        g.add_footnote(tr("По USB-C наушники передают только звук и заряжаются — "
                          "настройка возможна только по Bluetooth. Все настройки "
                          "хранятся в самих наушниках и действуют при любом способе "
                          "прослушивания."))
        lay.addWidget(g.widget)
        lay.addStretch(1)
        return page

    def _page_system(self) -> QWidget:
        page, lay = self._scroll_page(tr("Система"))

        g = Group(tr("Сенсорная панель"))
        self.touch_cb = ToggleSwitch()
        self.touch_cb.toggled.connect(self.on_touch_toggled)
        g.add_row(tr("Блокировка сенсора (Touch Lock)"), self.touch_cb,
                  tr("Касания игнорируются — полезно под шапкой или капюшоном"))
        lay.addWidget(g.widget)

        g = Group(tr("Ношение"))
        self.onhead_cb = ToggleSwitch()
        self.onhead_cb.toggled.connect(lambda v: self.run_set(
            lambda d: d.set_on_head_detection(v), self.onhead_cb, not v))
        g.add_row(tr("Датчик надевания"), self.onhead_cb,
                  tr("Наушники понимают, когда они на голове"),
                  tooltip=tr("Нужен для умной паузы и автоответа"))
        self.smartpause_cb = ToggleSwitch()
        self.smartpause_cb.toggled.connect(lambda v: self.run_set(
            lambda d: d.set_smart_pause(v), self.smartpause_cb, not v))
        g.add_row(tr("Умная пауза"), self.smartpause_cb,
                  tr("Останавливать музыку, когда наушники сняты"))
        lay.addWidget(g.widget)

        g = Group(tr("Звонки"))
        self.autocall_cb = ToggleSwitch()
        self.autocall_cb.toggled.connect(lambda v: self.run_set(
            lambda d: d.set_auto_call(v), self.autocall_cb, not v))
        g.add_row(tr("Автоответ"), self.autocall_cb,
                  tr("Принимать входящий вызов при надевании наушников"))
        self.comfortcall_cb = ToggleSwitch()
        self.comfortcall_cb.toggled.connect(lambda v: self.run_set(
            lambda d: d.set_comfort_call(v), self.comfortcall_cb, not v))
        g.add_row("Comfort Call", self.comfortcall_cb,
                  tr("Мягче обработка звука во время разговора; слышно только в звонке"))
        lay.addWidget(g.widget)

        g = Group(tr("Голосовые подсказки"))
        self.prompt_combo = QComboBox()
        self.prompt_combo.addItems([tr("Выключены"), tr("Только сигналы"),
                                    tr("Голос и сигналы")])
        self.prompt_combo.setFixedWidth(200)
        self.prompt_combo.activated.connect(self.on_prompt_mode_changed)
        g.add_row(tr("Режим подсказок"), self.prompt_combo,
                  tooltip=tr("Голос и сигналы при включении, подключении и "
                             "смене режимов"))
        self.lang_label = value_label()
        g.add_row(tr("Язык подсказок"), self.lang_label,
                  tr("Меняется только через мобильное приложение (загрузка "
                     "языковых пакетов)"))
        lay.addWidget(g.widget)

        g = Group(tr("Питание и связь"))
        self.poweroff_combo = QComboBox()
        for name, _ in POWEROFF_CHOICES:
            self.poweroff_combo.addItem(tr(name))
        self.poweroff_combo.setFixedWidth(200)
        self.poweroff_combo.activated.connect(self.on_poweroff_changed)
        g.add_row(tr("Автовыключение"), self.poweroff_combo,
                  tr("Выключать наушники при бездействии"))
        self.lowlatency_cb = ToggleSwitch()
        self.lowlatency_cb.toggled.connect(lambda v: self.run_set(
            lambda d: d.set_low_latency(v), self.lowlatency_cb, not v))
        g.add_row(tr("Низкая задержка"), self.lowlatency_cb,
                  tr("Меньше рассинхрон в видео и играх, выше расход батареи"))
        self.btcompat_cb = ToggleSwitch()
        self.btcompat_cb.toggled.connect(lambda v: self.run_set(
            lambda d: d.set_bt_compat(v), self.btcompat_cb, not v))
        g.add_row(tr("Режим совместимости Bluetooth"), self.btcompat_cb,
                  tr("Стабильность соединения вместо максимального качества звука. "
                     "Мгновенно ничего не меняет — применяется при следующем "
                     "подключении наушников"))
        lay.addWidget(g.widget)
        lay.addStretch(1)
        return page

    def _page_app(self) -> QWidget:
        page, lay = self._scroll_page(tr("Приложение"))

        g = Group(tr("Оформление"))
        self.ui_style_combo = QComboBox()
        self.ui_style_combo.addItems([tr(n) for n in STYLE_NAMES])
        self.ui_style_combo.setFixedWidth(220)
        self.ui_style_combo.activated.connect(
            lambda i: self.apply_theme(S.UI_STYLES[i], self.ui_bg))
        g.add_row(tr("Стиль"), self.ui_style_combo,
                  tr("Меняет облик всего приложения"))
        self.ui_bg_combo = QComboBox()
        self.ui_bg_combo.addItems([tr(n) for n in BG_NAMES])
        self.ui_bg_combo.setFixedWidth(220)
        self.ui_bg_combo.activated.connect(
            lambda i: self.apply_theme(self.ui_style, S.UI_BACKDROPS[i]))
        g.add_row(tr("Фон окна"), self.ui_bg_combo,
                  tr("Mica и Acrylic — нативные эффекты Windows 11"),
                  tooltip=tr("Mica — лёгкая полупрозрачность, Acrylic — сильное "
                             "размытие фона"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(LANG_NAMES)
        self.lang_combo.setFixedWidth(220)
        current_lang = self.settings.value("lang", "ru")
        if current_lang in LANG_CODES:
            self.lang_combo.setCurrentIndex(LANG_CODES.index(current_lang))
        self.lang_combo.activated.connect(self.on_language_changed)
        g.add_row(tr("Язык"), self.lang_combo,
                  tr("Вступит в силу после перезапуска приложения"))
        lay.addWidget(g.widget)

        g = Group(tr("Журнал"))
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(230)
        log_col = QVBoxLayout()
        log_col.setSpacing(10)
        log_col.addWidget(self.log_view)
        row = QHBoxLayout()
        self.verbose_cb = ToggleSwitch()
        self.verbose_cb.setToolTip(tr("Показывать весь обмен с наушниками в hex"))
        self.verbose_cb.toggled.connect(lambda v: setattr(self, "verbose_log", v))
        row.addWidget(self.verbose_cb)
        row.addWidget(QLabel(tr("Подробный лог обмена (hex)")))
        row.addStretch(1)
        clear_btn = QPushButton(tr("Очистить"))
        clear_btn.clicked.connect(self.log_view.clear)
        row.addWidget(clear_btn)
        log_col.addLayout(row)
        g.add_block(log_col, with_separator=False)
        lay.addWidget(g.widget)

        g = Group(tr("Опасная зона"))
        reset_btn = QPushButton(tr("Сброс наушников к заводским настройкам"))
        reset_btn.setObjectName("danger")
        g.add_row(tr("Заводской сброс"), reset_btn,
                  tr("Удаляет все настройки и список сопряжённых устройств в наушниках"))
        reset_btn.clicked.connect(self.on_factory_reset)
        lay.addWidget(g.widget)
        lay.addStretch(1)
        return page

    # ----------------------------------------------------------------- tray
    def _build_tray(self):
        self.tray = QSystemTrayIcon(make_app_icon(), self)
        menu = QMenu()
        self.tray_status = menu.addAction(tr("Не подключено"))
        self.tray_status.setEnabled(False)
        menu.addSeparator()
        self.tray_anc_on = menu.addAction(tr("ANC: включить"))
        self.tray_anc_on.triggered.connect(lambda: self.quick_anc(True))
        self.tray_anc_off = menu.addAction(tr("ANC: выключить"))
        self.tray_anc_off.triggered.connect(lambda: self.quick_anc(False))
        self.tray_transp = menu.addAction(tr("Прозрачный режим"))
        self.tray_transp.triggered.connect(self.quick_transparency)
        menu.addSeparator()
        show_action = menu.addAction(tr("Открыть окно"))
        show_action.triggered.connect(self.show_window)
        quit_action = menu.addAction(tr("Выход"))
        quit_action.triggered.connect(self.quit_app)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("MOMENTUM 4 Control")
        self.tray.activated.connect(
            lambda reason: self.show_window()
            if reason == QSystemTrayIcon.Trigger else None)
        self.tray.show()

    def show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self._really_quit = True
        if self.client:
            self.client.close()
        QApplication.quit()

    def restart_app(self):
        self._really_quit = True
        if self.client:
            self.client.close()
        if getattr(sys, "frozen", False):
            QProcess.startDetached(sys.executable, sys.argv[1:])
        else:
            QProcess.startDetached(sys.executable,
                                   [os.path.abspath(sys.argv[0])])
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent):
        if getattr(self, "_really_quit", False):
            event.accept()
            return
        event.ignore()
        self.hide()
        self.tray.showMessage("MOMENTUM 4 Control",
                              tr("Приложение продолжает работать в трее."),
                              QSystemTrayIcon.Information, 2500)

    def quick_anc(self, on: bool):
        if self.dev:
            self.run_set(lambda d: d.set_anc_enabled(on), self.anc_cb, not on)
            set_checked_silent(self.anc_cb, on)

    def quick_transparency(self):
        if self.dev:
            self.run_set(lambda d: d.set_transparency(True),
                         self.transparency_cb, False)
            set_checked_silent(self.transparency_cb, True)

    # ----------------------------------------------------------------- connection
    def autodetect_mac(self):
        self.append_log(tr("Поиск сопряжённых MOMENTUM 4..."))
        self.bridge.run(find_paired_momentum_mac, ok=self._on_mac_found)

    def _on_mac_found(self, mac):
        if mac:
            self.mac_edit.setText(mac)
            self.settings.setValue("mac", mac)
            self.append_log(tr("Найдены наушники: {mac}").format(mac=mac))
        else:
            self.append_log(tr("Сопряжённые MOMENTUM 4 не найдены."))
            QMessageBox.information(
                self, tr("Не найдено"),
                tr("Сопряжённые MOMENTUM 4 не найдены.\nСначала выполните сопряжение "
                   "наушников с Windows (Параметры → Bluetooth и устройства)."))

    def toggle_connection(self):
        if self.dev is not None or (self.client and self.client.connected):
            self.disconnect_device()
        else:
            self._user_disconnected = False
            self.connect_device()

    def connect_device(self):
        if self._connecting:
            # вотчдог: если попытка висит слишком долго — разрешаем новую
            if time.monotonic() - self._connect_started < 120:
                self.append_log(tr("Подключение уже выполняется..."))
                return
            self._connecting = False
        if self.client and self.client.connected:
            return
        mac = self.mac_edit.text().strip()
        if not mac:
            self.autodetect_mac()
            QTimer.singleShot(2500, lambda: self.mac_edit.text() and self.connect_device())
            return
        self.settings.setValue("mac", mac)
        self._connecting = True
        self._connect_started = time.monotonic()
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText(tr("Подключение..."))
        self.append_log(tr("Подключение к {mac}...").format(mac=mac))

        client = GaiaClient(
            mac,
            on_notification=lambda v, p, d: self.notifier.notification.emit(v, p, bytes(d)),
            on_disconnect=lambda msg: self.notifier.disconnected.emit(msg),
            on_log=lambda msg: self.notifier.log.emit(msg) if self.verbose_log or
            not msg.startswith(("TX", "RX")) else None,
        )

        try:
            saved_channel = int(self.settings.value("rfcomm_channel", 0)) or None
        except (TypeError, ValueError):
            saved_channel = None

        def do_connect():
            channel = client.connect(preferred_channel=saved_channel)
            client.register_notifications()
            return channel

        self.bridge.run(do_connect,
                        ok=lambda ch: self._on_connected(client, ch),
                        fail=self._on_connect_failed)

    def _on_connected(self, client: GaiaClient, channel: int):
        self._connecting = False
        self.settings.setValue("rfcomm_channel", channel)
        self.client = client
        self.dev = Momentum4(client)
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText(tr("Отключить"))
        self.conn_label.setText(tr("● Подключено"))
        self.conn_label.setStyleSheet("color: #ffffff;")
        self.tray_status.setText(tr("Подключено"))
        self.append_log(tr("Подключено (RFCOMM канал {ch}). Загрузка состояния...")
                        .format(ch=channel))
        self.poll_timer.start()
        self.load_full_state()

    def _on_connect_failed(self, exc: Exception):
        self._connecting = False
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText(tr("Подключить"))
        hint_text = tr("Проверьте, что наушники включены и находятся рядом. "
                       "Если запущена вторая копия приложения на этом ПК — "
                       "закройте её.")
        self.append_log(tr("Ошибка подключения: {e}").format(e=exc))
        self.append_log(hint_text)
        if not self.isHidden():
            QMessageBox.warning(self, tr("Не удалось подключиться"),
                                f"{exc}\n\n{hint_text}")

    def disconnect_device(self):
        self._user_disconnected = True
        if self.client:
            client = self.client
            self.client = None
            self.dev = None
            self.bridge.run(client.close)
        self.on_disconnected(
            tr("Отключено (автоподключение приостановлено до нажатия «Подключить»)"))

    def on_disconnected(self, message: str):
        self.poll_timer.stop()
        self.dev = None
        if self.client and not self.client.connected:
            self.client = None
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText(tr("Подключить"))
        self.conn_label.setText(tr("○ Не подключено"))
        self.conn_label.setStyleSheet("color: #8f8f8f;")
        self.tray_status.setText(tr("Не подключено"))
        self.append_log(message)

    def try_autoreconnect(self):
        if (self.dev is None and not self._connecting
                and not self._user_disconnected
                and self.autoconnect_cb.isChecked()
                and self.mac_edit.text().strip()
                and self.connect_btn.text() == tr("Подключить")):
            self.connect_device()

    # ----------------------------------------------------------------- state loading
    def load_full_state(self):
        dev = self.dev
        if not dev:
            return

        def load():
            state = {}
            state["info"] = dev.get_info()
            state["battery"] = dev.get_battery()
            state["charging"] = dev.get_charging_status()
            state["codec"] = dev.get_codec()
            state["wear"] = dev.get_physical_state()
            state["anc"] = dev.c.try_request(P.Cmd.GET_ANC)
            state["anc_modes"] = dev.c.try_request(P.Cmd.GET_ANC_MODES)
            state["anc_level"] = dev.get_anc_level()
            state["transparency"] = dev.c.try_request(P.Cmd.GET_TRANSPARENCY)
            state["th_level"] = dev.get_transparency_level()
            state["autopause"] = dev.get_th_autopause()
            state["bass"] = dev.get_bass_boost()
            state["eq_user"] = dev.get_user_eq()
            state["eq_curve"] = dev.get_eq_curve()
            state["eq_freqs"] = dev.get_eq_band_freqs()
            state["sidetone"] = dev.get_sidetone()
            state["touch"] = dev.get_touch_lock()
            state["onhead"] = dev.get_on_head_detection()
            state["smartpause"] = dev.get_smart_pause()
            state["autocall"] = dev.get_auto_call()
            state["comfortcall"] = dev.get_comfort_call()
            state["lowlatency"] = dev.get_low_latency()
            state["btcompat"] = dev.get_bt_compat()
            state["prompt_mode"] = dev.get_prompt_mode()
            state["prompt_lang"] = dev.get_prompt_language()
            state["poweroff"] = dev.get_poweroff_timer()
            return state

        self.bridge.run(load, ok=self._apply_state)
        self.load_paired_devices()

    def _apply_state(self, s: dict):
        info = s["info"]
        self.info_labels["model"].setText(info.model or "—")
        self.info_labels["firmware"].setText(info.firmware or "—")
        self.info_labels["serial"].setText(info.serial or "—")
        self.info_labels["hw_revision"].setText(info.hw_revision or "—")

        if s["battery"] is not None:
            self.battery_bar.setValue(s["battery"])
            self.tray.setToolTip(tr("MOMENTUM 4 — батарея {n}%").format(n=s["battery"]))
        self.charge_label.setText(tr(P.CHARGING.get(s["charging"], "—")))
        self.codec_label.setText(codec_name(s["codec"]))
        self.wear_label.setText(tr(P.PHYSICAL_STATE.get(s["wear"], "—")))

        if s["anc"]:
            set_checked_silent(self.anc_cb, bool(s["anc"][0]))
        if s["anc_modes"] and len(s["anc_modes"]) >= 6:
            data = s["anc_modes"]
            states = {data[i]: data[i + 1] for i in range(0, 6, 2)}
            set_checked_silent(self.adaptive_cb,
                               bool(states.get(P.ANC_MODE_ADAPTIVE)))
            wind = states.get(P.ANC_MODE_ANTIWIND, 0)
            self.wind_combo.setCurrentIndex(wind if wind in (0, 1, 2) else 0)
        if s["anc_level"] is not None:
            self.anc_level.blockSignals(True)
            self.anc_level.setValue(s["anc_level"])
            self.anc_level.blockSignals(False)
            self.anc_level_label.setText(str(s["anc_level"]))
        if s["transparency"]:
            set_checked_silent(self.transparency_cb, bool(s["transparency"][0]))
        if s["th_level"] is not None:
            self.th_level.blockSignals(True)
            self.th_level.setValue(s["th_level"])
            self.th_level.blockSignals(False)
            self.th_level_label.setText(str(s["th_level"]))
        if s["autopause"] is not None:
            set_checked_silent(self.autopause_cb, s["autopause"])
        if s["bass"] is not None:
            set_checked_silent(self.bass_cb, s["bass"])
        self._apply_eq_state(s["eq_user"], s["eq_curve"], s["eq_freqs"])
        if s["sidetone"] is not None:
            self.sidetone.blockSignals(True)
            self.sidetone.setValue(s["sidetone"])
            self.sidetone.blockSignals(False)
            self.sidetone_label.setText(str(s["sidetone"]))
        for key, cb in [("touch", self.touch_cb), ("onhead", self.onhead_cb),
                        ("smartpause", self.smartpause_cb),
                        ("autocall", self.autocall_cb),
                        ("comfortcall", self.comfortcall_cb),
                        ("lowlatency", self.lowlatency_cb),
                        ("btcompat", self.btcompat_cb)]:
            if s[key] is not None:
                set_checked_silent(cb, s[key])
        if s["prompt_mode"] is not None and 0 <= s["prompt_mode"] <= 2:
            self.prompt_combo.setCurrentIndex(s["prompt_mode"])
        if s["prompt_lang"] is not None:
            self.lang_label.setText(
                tr(P.LANGUAGES.get(s["prompt_lang"], ""))
                or tr("код {n}").format(n=s["prompt_lang"]))
        if s["poweroff"] is not None:
            idx = min(range(len(POWEROFF_CHOICES)),
                      key=lambda i: abs(POWEROFF_CHOICES[i][1] - s["poweroff"]))
            self.poweroff_combo.setCurrentIndex(idx)
        self.append_log(tr("Состояние загружено."))

    def poll_status(self):
        dev = self.dev
        if not dev:
            return

        def load():
            return (dev.get_battery(), dev.get_charging_status(), dev.get_codec(),
                    dev.get_physical_state())

        def apply(res):
            battery, charging, codec, wear = res
            if battery is None and charging is None and codec is None and wear is None:
                # наушники перестали отвечать (например, их переподключили
                # в Windows) — рвём соединение, автоподключение восстановит
                self.force_reconnect()
                return
            if battery is not None:
                self.battery_bar.setValue(battery)
                self.tray.setToolTip(tr("MOMENTUM 4 — батарея {n}%").format(n=battery))
            self.charge_label.setText(tr(P.CHARGING.get(charging, "—")))
            self.codec_label.setText(codec_name(codec))
            self.wear_label.setText(tr(P.PHYSICAL_STATE.get(wear, "—")))

        self.bridge.run(load, ok=apply, fail=lambda e: None)

    def force_reconnect(self):
        """Принудительный разрыв «мёртвого» соединения без блокировки
        автоподключения."""
        if self.client:
            client = self.client
            self.client = None
            self.dev = None
            self.bridge.run(client.close)
        self.on_disconnected(tr("Связь потеряна, переподключение..."))

    # ----------------------------------------------------------------- notifications
    def on_notification(self, vendor: int, pdu: int, data: bytes):
        if pdu == P.notification_of(P.Cmd.GET_BATTERY) and data:
            level = data[0] if len(data) == 1 else data[1]
            self.battery_bar.setValue(level)
            self.tray.setToolTip(tr("MOMENTUM 4 — батарея {n}%").format(n=level))
        elif pdu == P.notification_of(P.Cmd.GET_CHARGING_STATUS) and data:
            self.charge_label.setText(tr(P.CHARGING.get(data[0], "—")))
        elif pdu == P.notification_of(P.Cmd.GET_ANC) and data:
            set_checked_silent(self.anc_cb, bool(data[0]))
        elif pdu == P.notification_of(P.Cmd.GET_ANC_LEVEL) and data:
            self.anc_level.blockSignals(True)
            self.anc_level.setValue(data[0])
            self.anc_level.blockSignals(False)
        elif pdu == P.notification_of(P.Cmd.GET_ANC_MODES) and len(data) >= 6:
            states = {data[i]: data[i + 1] for i in range(0, 6, 2)}
            set_checked_silent(self.adaptive_cb, bool(states.get(P.ANC_MODE_ADAPTIVE)))
            wind = states.get(P.ANC_MODE_ANTIWIND, 0)
            if wind in (0, 1, 2):
                self.wind_combo.setCurrentIndex(wind)
        elif pdu == P.notification_of(P.Cmd.GET_TRANSPARENCY) and data:
            set_checked_silent(self.transparency_cb, bool(data[0]))
        elif pdu == P.notification_of(P.Cmd.GET_TH_LEVEL) and data:
            self.th_level.blockSignals(True)
            self.th_level.setValue(data[0])
            self.th_level.blockSignals(False)
        elif pdu == P.notification_of(P.Cmd.GET_PHYSICAL_STATE) and data:
            self.wear_label.setText(tr(P.PHYSICAL_STATE.get(data[0], "—")))
        elif pdu == P.notification_of(P.Cmd.GET_CODEC) and data:
            self.codec_label.setText(codec_name(data[0]))
        elif pdu == P.notification_of(P.Cmd.GET_BASS_BOOST) and data:
            set_checked_silent(self.bass_cb, bool(data[0]))
        elif pdu == P.notification_of(P.Cmd.EQ_GET_BAND_GAIN) and len(data) == 5:
            curve = [b - 256 if b > 127 else b for b in data]
            self._apply_eq_state(curve, curve, None)

    # ----------------------------------------------------------------- setting handlers
    def run_set(self, fn, revert_widget=None, revert_value=None):
        """Runs a setter on the device; on failure reverts the widget and shows error."""
        dev = self.dev
        if dev is None:
            if revert_widget is not None:
                set_checked_silent(revert_widget, revert_value)
            self.append_log(tr("Наушники не подключены."))
            return

        def fail(exc):
            if revert_widget is not None:
                set_checked_silent(revert_widget, revert_value)
            self.show_error(exc)

        self.bridge.run(lambda: fn(dev), fail=fail)

    def on_anc_toggled(self, on: bool):
        self.run_set(lambda d: d.set_anc_enabled(on), self.anc_cb, not on)

    def on_anc_level_changed(self):
        level = self.anc_level.value()
        self.run_set(lambda d: d.set_anc_level(level))

    def on_transparency_toggled(self, on: bool):
        self.run_set(lambda d: d.set_transparency(on), self.transparency_cb, not on)

    def on_th_level_changed(self):
        level = self.th_level.value()
        self.run_set(lambda d: d.set_transparency_level(level))

    def on_autopause_toggled(self, on: bool):
        self.run_set(lambda d: d.set_th_autopause(on), self.autopause_cb, not on)

    def on_bass_toggled(self, on: bool):
        self.run_set(lambda d: d.set_bass_boost(on), self.bass_cb, not on)

    def on_sidetone_changed(self):
        level = self.sidetone.value()
        self.run_set(lambda d: d.set_sidetone(level))

    def on_prompt_mode_changed(self, index: int):
        self.run_set(lambda d: d.set_prompt_mode(index))

    def on_poweroff_changed(self, index: int):
        seconds = POWEROFF_CHOICES[index][1]
        self.run_set(lambda d: d.set_poweroff_timer(seconds))

    def on_touch_toggled(self, on: bool):
        self.run_set(lambda d: d.set_touch_lock(on), self.touch_cb, not on)

    def on_language_changed(self, index: int):
        lang = LANG_CODES[index]
        if lang == self.settings.value("lang", "ru"):
            return
        self.settings.setValue("lang", lang)
        answer = QMessageBox.question(
            self, tr("Смена языка"),
            tr("Перезапустить приложение сейчас, чтобы применить язык?"))
        if answer == QMessageBox.Yes:
            self.restart_app()

    # ----------------------------------------------------------------- EQ
    @staticmethod
    def _fmt_freq(hz) -> str:
        if hz is None:
            return "?"
        if hz >= 1000:
            return f"{hz / 1000:.1f} {tr('кГц')}".replace(".0", "")
        return f"{hz} {tr('Гц')}"

    @staticmethod
    def _fmt_curve(curve) -> str:
        return ", ".join(f"{v / 10:.1f}" for v in curve) + " " + tr("дБ")

    def _apply_eq_state(self, user_gains, curve, freqs):
        if freqs:
            for lbl, hz in zip(self.eq_freq_labels, freqs):
                if hz:
                    lbl.setText(self._fmt_freq(hz))
        if curve:
            self.eq_curve_label.setText(
                tr("Итоговая кривая (вместе с Sound Check): {values}")
                .format(values=self._fmt_curve(curve)))
        if user_gains and all(g is not None for g in user_gains):
            for s, g in zip(self.eq_sliders, user_gains):
                s.blockSignals(True)
                s.setValue(max(-60, min(60, g)))
                s.blockSignals(False)
                s.setEnabled(True)
            for lbl, g in zip(self.eq_value_labels, user_gains):
                lbl.setText(f"{g / 10:.1f}")
            self.eq_apply_btn.setEnabled(True)
            self.eq_zero_btn.setEnabled(True)

    def on_apply_eq(self):
        gains = [s.value() for s in self.eq_sliders]
        self.run_set(lambda d: (d.normalize_eq_bands(), d.set_user_eq(gains)))
        self.append_log(tr("EQ отправлен: {g}").format(
            g=", ".join(f"{v / 10:.1f}" for v in gains) + " " + tr("дБ")))
        QTimer.singleShot(700, self.refresh_eq_curve)

    def on_zero_eq(self):
        for s in self.eq_sliders:
            s.blockSignals(True)
            s.setValue(0)
            s.blockSignals(False)
        for lbl in self.eq_value_labels:
            lbl.setText("0.0")
        self.run_set(lambda d: d.set_user_eq([0, 0, 0, 0, 0]))
        self.append_log(tr("EQ сброшен в 0."))
        QTimer.singleShot(700, self.refresh_eq_curve)

    def refresh_eq_curve(self):
        dev = self.dev
        if not dev:
            return

        def load():
            return dev.get_eq_curve(), dev.get_eq_band_freqs()

        def apply(res):
            curve, freqs = res
            if curve:
                self.eq_curve_label.setText(
                    tr("Итоговая кривая (вместе с Sound Check): {values}")
                    .format(values=self._fmt_curve(curve)))
            if freqs:
                for lbl, hz in zip(self.eq_freq_labels, freqs):
                    if hz:
                        lbl.setText(self._fmt_freq(hz))

        self.bridge.run(load, ok=apply, fail=lambda e: None)

    def on_probe_eq(self):
        dev = self.dev
        if not dev:
            self.append_log(tr("Наушники не подключены."))
            return
        self.eq_probe_btn.setEnabled(False)
        self.append_log(tr("Диагностика EQ (только чтение)..."))

        def done(report: dict):
            self.eq_probe_btn.setEnabled(True)
            for name, value in report.items():
                self.append_log(f"  {name}: {value}")
            self.append_log(tr("Диагностика EQ завершена."))
            self.switch_page(5)

        def fail(exc):
            self.eq_probe_btn.setEnabled(True)
            self.show_error(exc)

        self.bridge.run(dev.probe_eq, ok=done, fail=fail)

    # ----------------------------------------------------------------- paired devices
    def load_paired_devices(self):
        dev = self.dev
        if not dev:
            return

        def load():
            return dev.get_paired_devices(), dev.get_own_index()

        def apply(res):
            devices, own = res
            self.pdl_list.clear()
            for d in devices:
                status = tr("подключено") if d.status else tr("не подключено")
                suffix = tr("  (этот ПК)") if own is not None and d.index == own else ""
                item = QListWidgetItem(
                    f"{d.index}: {d.name or tr('Без имени')} — {status}{suffix}")
                item.setData(Qt.UserRole, d.index)
                self.pdl_list.addItem(item)

        self.bridge.run(load, ok=apply, fail=lambda e: None)

    def pdl_action(self, action: str):
        item = self.pdl_list.currentItem()
        if not item or not self.dev:
            return
        index = item.data(Qt.UserRole)
        if action == "delete":
            if QMessageBox.question(
                    self, tr("Удаление"),
                    tr("Удалить устройство №{i} из памяти наушников?")
                    .format(i=index)) != QMessageBox.Yes:
                return
            self.run_set(lambda d: d.pdl_delete(index))
        elif action == "connect":
            self.run_set(lambda d: d.pdl_connect(index))
        elif action == "disconnect":
            self.run_set(lambda d: d.pdl_disconnect(index))
        QTimer.singleShot(1500, self.load_paired_devices)

    # ----------------------------------------------------------------- USB
    def on_check_usb(self):
        self.usb_label.setText(tr("Проверка USB-устройств..."))

        def apply(status):
            if not status.present:
                self.usb_label.setText(
                    tr("Наушники не обнаружены на USB. Подключите их кабелем USB-C и "
                       "нажмите «Проверить USB» ещё раз."))
                return
            parts = [tr("Обнаружено USB-устройство: {names}.")
                     .format(names=", ".join(status.names))]
            parts.append(tr("Аудио по USB: ") + (tr("да") if status.audio else tr("нет")))
            parts.append(tr("HID-интерфейс: ") + (tr("да") if status.hid else tr("нет")))
            self.usb_label.setText("\n".join(parts))
            self.append_log("USB: " + " | ".join(parts))

        self.bridge.run(check_usb, ok=apply)

    # ----------------------------------------------------------------- service
    def on_factory_reset(self):
        if not self.dev:
            self.append_log(tr("Наушники не подключены."))
            return
        answer = QMessageBox.warning(
            self, tr("Заводской сброс"),
            tr("Наушники будут сброшены к заводским настройкам: все настройки и список "
               "сопряжённых устройств будут удалены, соединение разорвётся."
               "\n\nПродолжить?"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            self.run_set(lambda d: d.factory_reset())
            self.append_log(tr("Команда заводского сброса отправлена."))

    def append_log(self, text: str):
        self.log_view.appendPlainText(text)

    def show_error(self, exc: Exception):
        self.append_log(tr("Ошибка: {e}").format(e=exc))

    # ----------------------------------------------------------------- оформление
    def apply_theme(self, style: str, bg: str):
        self.ui_style = style
        self.ui_bg = bg
        self.settings.setValue("ui_style", style)
        self.settings.setValue("ui_bg", bg)
        QApplication.instance().setStyleSheet(S.build_qss(style, bg))
        self.ui_style_combo.setCurrentIndex(S.UI_STYLES.index(style))
        self.ui_bg_combo.setCurrentIndex(S.UI_BACKDROPS.index(bg))
        if self.isVisible():
            apply_backdrop(self, bg)

    def showEvent(self, event):
        super().showEvent(event)
        apply_backdrop(self, self.ui_bg)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    settings = QSettings(ORG, APP)
    i18n.set_language(settings.value("lang", "ru"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
