"""
系统托盘模块 — 管理 Windows 系统托盘图标和菜单
=================================================
提供托盘图标显示、右键菜单（含自启开关）、左键单击切换主窗口等功能。
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFont, QAction
from PyQt6.QtCore import QSize, Qt
import autostart
import styles


def _create_tray_icon() -> QIcon:
    """
    用代码绘制一个简单的剪贴板托盘图标。
    生成 32×32 像素的图标，白色背景 + 蓝色剪贴板图案。
    """
    size = 32
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 绘制剪贴板主体（圆角矩形）
    painter.setPen(QPen(QColor("#1976D2"), 2))
    painter.setBrush(QBrush(QColor("#FFFFFF")))
    painter.drawRoundedRect(6, 4, 20, 24, 3, 3)

    # 绘制剪贴板顶部夹子
    painter.setBrush(QBrush(QColor("#E3F2FD")))
    painter.drawRoundedRect(12, 2, 8, 6, 2, 2)

    # 绘制内部横线（代表文字内容）
    painter.setPen(QPen(QColor("#BBDEFB"), 2))
    painter.drawLine(10, 14, 22, 14)
    painter.drawLine(10, 18, 22, 18)
    painter.drawLine(10, 22, 18, 22)

    painter.end()
    return QIcon(pixmap)


class TrayManager:
    """
    系统托盘管理器。
    - 创建和管理托盘图标
    - 构建右键菜单
    - 处理左键点击切换窗口
    """

    def __init__(self, main_window, app: QApplication):
        self.main_window = main_window
        self.app = app

        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self.main_window)
        self.tray_icon.setIcon(_create_tray_icon())
        self.tray_icon.setToolTip("📋 剪贴板历史管理器")

        # 创建右键菜单
        self.menu = self._build_menu()

        # 设置菜单
        self.tray_icon.setContextMenu(self.menu)

        # 左键点击 → 切换窗口显示
        self.tray_icon.activated.connect(self._on_tray_activated)

        # 显示托盘图标
        self.tray_icon.show()

        print("[托盘] 系统托盘已就绪")

    def _build_menu(self) -> QMenu:
        """构建托盘右键菜单"""
        menu = QMenu()
        menu.setStyleSheet(styles.GLOBAL_STYLESHEET)

        # === 显示历史 ===
        show_action = QAction("📋 显示历史", menu)
        show_action.triggered.connect(self.main_window.show_and_focus)
        menu.addAction(show_action)

        menu.addSeparator()

        # === 开机自启（带勾选状态） ===
        self.autostart_action = QAction("🚀 开机自启", menu)
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(autostart.is_autostart_enabled())
        self.autostart_action.triggered.connect(self._toggle_autostart)
        menu.addAction(self.autostart_action)

        menu.addSeparator()

        # === 退出 ===
        quit_action = QAction("❌ 退出", menu)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        return menu

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """
        处理托盘图标的点击事件。
        - 左键单击/双击 → 切换窗口显示
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 左键单击
            self.main_window.toggle()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # 左键双击 → 显示并聚焦
            self.main_window.show_and_focus()

    def _toggle_autostart(self, checked: bool):
        """切换开机自启状态"""
        if checked:
            success = autostart.enable_autostart()
            if not success:
                self.autostart_action.setChecked(False)
                print("[自启] 启用失败")
            else:
                print("[自启] 已启用开机自启")
        else:
            autostart.disable_autostart()
            print("[自启] 已禁用开机自启")

    def _quit_app(self):
        """退出应用程序"""
        print("[应用] 正在退出...")
        self.tray_icon.hide()
        self.app.quit()

    def update_autostart_state(self):
        """刷新菜单中自启选项的勾选状态"""
        self.autostart_action.setChecked(autostart.is_autostart_enabled())

    def show_notification(self, title: str, message: str):
        """显示系统通知气泡"""
        if self.tray_icon.supportsMessages():
            self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                3000  # 显示 3 秒
            )
