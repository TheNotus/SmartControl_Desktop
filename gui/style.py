"""Две полные темы оформления:

- win11 — минималистичный монохромный графит в стиле Параметров Windows 11;
- macos — тёмная тема в стиле Системных настроек macOS (синий акцент,
  сгруппированные списки, крупные скругления).

Каждая тема имеет три фона: opaque / mica / acrylic (подложку рисует DWM).
"""

UI_STYLES = ("win11", "macos")
UI_BACKDROPS = ("opaque", "mica", "acrylic")

# Текущие цвета тумблеров/акцентов — обновляются в build_qss,
# их читает ToggleSwitch при отрисовке.
SWITCH = {
    "track_off": "#454545",
    "track_off_border": "#5a5a5a",
    "track_on": "#e8e8e8",
    "knob_off": "#cfcfcf",
    "knob_on": "#1a1a1a",
}

_TEMPLATE = """
* { font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
    font-size: 10pt; color: #f2f2f2; }

QMainWindow, QDialog { background: @WIN_BG@; }

#sidebar { background: @SIDE_BG@; border-right: 1px solid @BORDER@; }
#sidebar QPushButton {
    color: #d6d6d6; background: transparent; border: none;
    padding: 8px 14px; text-align: left; border-radius: @CTRL_R@; margin: 1px 10px;
}
#sidebar QPushButton:hover { background: rgba(255,255,255,14); color: #ffffff; }
#sidebar QPushButton:checked { background: @NAV_SEL@; color: @NAV_SEL_TEXT@; }

#appTitle { color: #ffffff; font-size: 12pt; font-weight: 600; padding: 14px; }

QLabel { color: #ececec; background: transparent; }
QLabel#pageTitle { color: #ffffff; font-size: 15pt; font-weight: 600; }
QLabel#hint { color: #969696; font-size: 8.5pt; }
QLabel#groupTitle { color: @GROUP_TITLE@; font-size: @GROUP_TITLE_SIZE@;
    font-weight: 600; margin-left: 4px; }

QFrame#card { background: @CARD_BG@; border: 1px solid @BORDER@;
    border-radius: @CARD_R@; }
QFrame#sep { background: @SEP@; border: none; }

QPushButton {
    background: rgba(255,255,255,16); color: #ffffff;
    border: 1px solid @BORDER@; border-radius: @CTRL_R@; padding: 5px 14px;
}
QPushButton:hover { background: rgba(255,255,255,26); }
QPushButton:pressed { background: rgba(255,255,255,9); }
QPushButton:disabled { color: #6f6f6f; background: rgba(255,255,255,6); }
QPushButton#primary { background: @ACCENT@; border-color: @ACCENT@;
    color: @ACCENT_TEXT@; font-weight: 600; }
QPushButton#primary:hover { background: @ACCENT_HOVER@; }
QPushButton#primary:disabled { background: rgba(255,255,255,28); color: #808080; }
QPushButton#danger { background: transparent; border-color: rgba(255,105,97,110);
    color: #ff8d85; }
QPushButton#danger:hover { background: rgba(255,105,97,26); }

QLineEdit, QComboBox, QSpinBox {
    background: @INPUT_BG@; color: #ffffff; border: 1px solid @BORDER@;
    border-radius: @CTRL_R@; padding: 4px 10px;
    selection-background-color: rgba(255,255,255,70);
}
QComboBox::drop-down { border: none; width: 26px; }
QComboBox::down-arrow { width: 0; height: 0;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid #b8b8b8; margin-right: 10px; }
QComboBox QAbstractItemView {
    background: #272727; color: #ffffff; border: 1px solid #3f3f3f;
    border-radius: 8px; selection-background-color: @SELECT_BG@;
    outline: none; padding: 4px;
}

QCheckBox { color: #ececec; spacing: 10px; background: transparent; }

QSlider { background: transparent; min-height: 22px; }
QSlider::groove:horizontal { height: 4px; background: rgba(255,255,255,34);
    border-radius: 2px; }
QSlider::handle:horizontal { width: 16px; height: 16px; margin: -6px 0;
    border-radius: 8px; background: #ffffff; }
QSlider::handle:horizontal:hover { background: #d9d9d9; }
QSlider::sub-page:horizontal { background: @ACCENT_SOFT@; border-radius: 2px; }
QSlider::groove:vertical { width: 4px; background: rgba(255,255,255,34);
    border-radius: 2px; }
QSlider::handle:vertical { width: 16px; height: 16px; margin: 0 -6px;
    border-radius: 8px; background: #ffffff; }
QSlider::add-page:vertical { background: @ACCENT_SOFT@; border-radius: 2px; }

QProgressBar {
    background: @INPUT_BG@; border: 1px solid @BORDER@; border-radius: 7px;
    height: 14px; text-align: center; color: #ffffff; font-size: 8pt;
}
QProgressBar::chunk { background: @ACCENT_SOFT@; border-radius: 6px; }

QPlainTextEdit, QListWidget {
    background: @LOG_BG@; color: #cfcfcf; border: 1px solid @BORDER@;
    border-radius: @CTRL_R@; font-family: Consolas, monospace; font-size: 9pt;
}
QListWidget { font-family: 'Segoe UI Variable Text', 'Segoe UI';
    font-size: 10pt; }
QListWidget::item { padding: 7px; border-radius: 5px; }
QListWidget::item:selected { background: @SELECT_BG@; color: #ffffff; }

QMenu { background: #272727; color: #ffffff; border: 1px solid #3f3f3f;
    border-radius: 10px; padding: 5px; }
QMenu::item { padding: 6px 24px; border-radius: 5px; }
QMenu::item:selected { background: @SELECT_BG@; }
QMenu::item:disabled { color: #8a8a8a; }
QMenu::separator { height: 1px; background: #3f3f3f; margin: 4px 8px; }

QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: rgba(255,255,255,55);
    border-radius: 4px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QScrollBar:horizontal { background: transparent; height: 8px; }
QScrollBar::handle:horizontal { background: rgba(255,255,255,55);
    border-radius: 4px; }

QMessageBox { background: #232323; }
QToolTip { background: #272727; color: #ffffff; border: 1px solid #3f3f3f; }
"""

_BACKDROP_COLORS = {
    # (style, backdrop) -> фоновые токены
    ("win11", "opaque"): {
        "@WIN_BG@": "#202020", "@SIDE_BG@": "#1b1b1b", "@CARD_BG@": "#2b2b2b",
        "@INPUT_BG@": "#1f1f1f", "@LOG_BG@": "#191919",
        "@BORDER@": "#3a3a3a", "@SEP@": "#3a3a3a",
    },
    ("win11", "mica"): {
        "@WIN_BG@": "rgba(28,28,28,150)", "@SIDE_BG@": "rgba(14,14,14,110)",
        "@CARD_BG@": "rgba(255,255,255,14)", "@INPUT_BG@": "rgba(0,0,0,95)",
        "@LOG_BG@": "rgba(0,0,0,110)",
        "@BORDER@": "rgba(255,255,255,24)", "@SEP@": "rgba(255,255,255,20)",
    },
    ("win11", "acrylic"): {
        "@WIN_BG@": "rgba(20,20,20,70)", "@SIDE_BG@": "rgba(8,8,8,85)",
        "@CARD_BG@": "rgba(255,255,255,17)", "@INPUT_BG@": "rgba(0,0,0,100)",
        "@LOG_BG@": "rgba(0,0,0,120)",
        "@BORDER@": "rgba(255,255,255,28)", "@SEP@": "rgba(255,255,255,22)",
    },
    ("macos", "opaque"): {
        "@WIN_BG@": "#262626", "@SIDE_BG@": "#212121", "@CARD_BG@": "#2f2f31",
        "@INPUT_BG@": "#232325", "@LOG_BG@": "#1d1d1f",
        "@BORDER@": "rgba(255,255,255,20)", "@SEP@": "rgba(255,255,255,22)",
    },
    ("macos", "mica"): {
        "@WIN_BG@": "rgba(30,30,32,150)", "@SIDE_BG@": "rgba(18,18,20,100)",
        "@CARD_BG@": "rgba(255,255,255,15)", "@INPUT_BG@": "rgba(0,0,0,95)",
        "@LOG_BG@": "rgba(0,0,0,110)",
        "@BORDER@": "rgba(255,255,255,24)", "@SEP@": "rgba(255,255,255,20)",
    },
    ("macos", "acrylic"): {
        "@WIN_BG@": "rgba(22,22,24,70)", "@SIDE_BG@": "rgba(10,10,12,75)",
        "@CARD_BG@": "rgba(255,255,255,18)", "@INPUT_BG@": "rgba(0,0,0,100)",
        "@LOG_BG@": "rgba(0,0,0,120)",
        "@BORDER@": "rgba(255,255,255,28)", "@SEP@": "rgba(255,255,255,22)",
    },
}

_STYLE_TOKENS = {
    "win11": {
        "@CARD_R@": "8px", "@CTRL_R@": "6px",
        "@ACCENT@": "#ffffff", "@ACCENT_HOVER@": "#e2e2e2",
        "@ACCENT_TEXT@": "#1a1a1a", "@ACCENT_SOFT@": "rgba(255,255,255,130)",
        "@SELECT_BG@": "rgba(255,255,255,30)",
        "@NAV_SEL@": "rgba(255,255,255,26)", "@NAV_SEL_TEXT@": "#ffffff",
        "@GROUP_TITLE@": "#ffffff", "@GROUP_TITLE_SIZE@": "10.5pt",
    },
    "macos": {
        "@CARD_R@": "10px", "@CTRL_R@": "7px",
        "@ACCENT@": "#0a84ff", "@ACCENT_HOVER@": "#2f96ff",
        "@ACCENT_TEXT@": "#ffffff", "@ACCENT_SOFT@": "#0a84ff",
        "@SELECT_BG@": "#0a84ff",
        "@NAV_SEL@": "#0a84ff", "@NAV_SEL_TEXT@": "#ffffff",
        "@GROUP_TITLE@": "#9a9a9f", "@GROUP_TITLE_SIZE@": "9pt",
    },
}

_SWITCH_COLORS = {
    "win11": {
        # QColor понимает только #AARRGGBB, не css-rgba
        "track_off": "#00000000", "track_off_border": "#8a8a8a",
        "track_on": "#e8e8e8", "knob_off": "#cfcfcf", "knob_on": "#1c1c1c",
    },
    "macos": {
        "track_off": "#3a3a3c", "track_off_border": "#48484a",
        "track_on": "#0a84ff", "knob_off": "#ffffff", "knob_on": "#ffffff",
    },
}


def build_qss(style: str, backdrop: str) -> str:
    style = style if style in UI_STYLES else "win11"
    backdrop = backdrop if backdrop in UI_BACKDROPS else "opaque"
    SWITCH.update(_SWITCH_COLORS[style])
    qss = _TEMPLATE
    for token, value in {**_BACKDROP_COLORS[(style, backdrop)],
                         **_STYLE_TOKENS[style]}.items():
        qss = qss.replace(token, value)
    return qss
