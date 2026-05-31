"""
样式模块 — 白色主题 + 现代化 UI
"""

# ========== 配色 ==========
COLOR_BG_PRIMARY    = "#FFFFFF"
COLOR_BG_SECONDARY  = "#F8F9FA"
COLOR_BG_HOVER      = "#EEF2FF"
COLOR_BG_PINNED     = "#FFF9E6"
COLOR_TEXT_PRIMARY  = "#2C3E50"
COLOR_TEXT_SECONDARY= "#94A3B8"
COLOR_BORDER        = "#E8ECF0"
COLOR_ACCENT        = "#4F6EF7"
COLOR_ACCENT_HOVER  = "#3B5DE7"
COLOR_DANGER        = "#EF4444"
COLOR_DANGER_HOVER  = "#DC2626"
COLOR_PIN           = "#F59E0B"

# ========== 全局样式表 ==========
GLOBAL_STYLESHEET = f"""
QWidget {{
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 13px;
    color: {COLOR_TEXT_PRIMARY};
    background-color: {COLOR_BG_PRIMARY};
}}

QLineEdit {{
    background-color: {COLOR_BG_SECONDARY};
    border: 2px solid transparent;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    margin: 8px 10px;
    color: {COLOR_TEXT_PRIMARY};
}}
QLineEdit:focus {{
    border-color: {COLOR_ACCENT};
    background-color: #FFFFFF;
}}

QPushButton {{
    background-color: {COLOR_BG_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 12px;
    color: {COLOR_TEXT_PRIMARY};
}}
QPushButton:hover {{
    background-color: {COLOR_BG_HOVER};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: #D0D5DD;
    border-radius: 3px;
    min-height: 36px;
}}
QScrollBar::handle:vertical:hover {{
    background: #B0B5BD;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QLabel#statusBar {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: 11px;
    padding: 4px 12px;
    background-color: {COLOR_BG_SECONDARY};
    border-top: 1px solid {COLOR_BORDER};
}}

QMenu {{
    background-color: {COLOR_BG_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    padding: 6px;
}}
QMenu::item {{
    padding: 8px 32px 8px 16px;
    border-radius: 6px;
    margin: 2px;
}}
QMenu::item:selected {{
    background-color: {COLOR_BG_HOVER};
}}
QMenu::separator {{
    height: 1px;
    background: {COLOR_BORDER};
    margin: 4px 8px;
}}
"""


def get_pinned_item_style() -> str:
    return f"""
        background-color: {COLOR_BG_PINNED};
        border: 1px solid #FCD34D;
        border-radius: 10px;
    """


def get_action_button_style(color: str = COLOR_ACCENT) -> str:
    return f"""
        QPushButton {{
            background-color: transparent;
            border: none;
            color: {color};
            font-size: 14px;
            padding: 2px 6px;
            border-radius: 4px;
            min-width: 24px;
            max-width: 28px;
            min-height: 24px;
            max-height: 28px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BG_HOVER};
        }}
    """
