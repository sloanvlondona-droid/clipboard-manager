"""
样式模块 — 现代白色主题
"""

# ========== 配色 ==========
C_PRIMARY       = "#FFFFFF"
C_SURFACE       = "#F8F9FB"
C_HOVER         = "#F0F4FF"
C_PINNED        = "#FFFDF5"
C_PINNED_BORDER = "#FCE68A"
C_TEXT          = "#1E293B"
C_TEXT_SUB      = "#94A3B8"
C_BORDER        = "#E2E8F0"
C_BORDER_LIGHT  = "#F1F5F9"
C_ACCENT        = "#4F6EF7"
C_ACCENT_LIGHT  = "#EEF1FF"
C_DANGER        = "#EF4444"
C_DANGER_LIGHT  = "#FEF2F2"
C_PIN_COLOR     = "#E67E00"

# 旧名兼容
COLOR_BG_PRIMARY    = C_PRIMARY
COLOR_BG_SECONDARY  = C_SURFACE
COLOR_BG_HOVER      = C_HOVER
COLOR_BG_PINNED     = C_PINNED
COLOR_TEXT_PRIMARY  = C_TEXT
COLOR_TEXT_SECONDARY= C_TEXT_SUB
COLOR_BORDER        = C_BORDER
COLOR_ACCENT        = C_ACCENT
COLOR_ACCENT_HOVER  = "#3B5DE7"
COLOR_DANGER        = C_DANGER
COLOR_DANGER_HOVER  = "#DC2626"
COLOR_PIN           = C_PIN_COLOR

# ========== 全局样式 ==========
GLOBAL_STYLESHEET = f"""
QWidget {{
    font-family: "Microsoft YaHei UI", "Segoe UI", system-ui;
    font-size: 13px;
    color: {C_TEXT};
    background-color: {C_PRIMARY};
}}

QLineEdit {{
    background: {C_SURFACE};
    border: 2px solid {C_BORDER_LIGHT};
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 13px;
    margin: 6px 10px;
}}
QLineEdit:focus {{
    border-color: {C_ACCENT};
    background: #FFFFFF;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: #CBD5E1;
    border-radius: 3px;
    min-height: 40px;
}}
QScrollBar::handle:vertical:hover {{
    background: #94A3B8;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

QMenu {{
    background: {C_PRIMARY};
    border: 1px solid {C_BORDER};
    border-radius: 12px;
    padding: 6px;
}}
QMenu::item {{
    padding: 8px 32px 8px 16px;
    border-radius: 8px; margin: 2px 4px;
}}
QMenu::item:selected {{ background: {C_HOVER}; }}
QMenu::separator {{ height: 1px; background: {C_BORDER}; margin: 4px 8px; }}

QDialog {{
    background: {C_PRIMARY};
}}
QTextEdit {{
    border: 1px solid {C_BORDER};
    border-radius: 10px;
    padding: 12px;
    font-size: 14px;
}}
"""


def card_style(pinned: bool = False) -> str:
    """列表项卡片样式"""
    if pinned:
        return f"""
            background: {C_PINNED};
            border: 1px solid {C_PINNED_BORDER};
            border-radius: 12px;
        """
    return f"""
        background: {C_PRIMARY};
        border: 1px solid {C_BORDER};
        border-radius: 12px;
    """


def pill_btn(bg: str, border: str, color: str) -> str:
    """药丸形按钮"""
    return f"""
        QPushButton {{
            background: {bg};
            border: 1px solid {border};
            border-radius: 14px;
            font-size: 11px;
            font-weight: 500;
            padding: 3px 14px;
            color: {color};
        }}
        QPushButton:hover {{
            opacity: 0.85;
        }}
    """
