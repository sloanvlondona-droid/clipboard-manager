"""
剪贴板历史管理器 — 程序入口
============================
一个 Windows 上的永久剪贴板历史记录工具。

功能：
  - 自动记录所有复制的文本内容
  - 搜索、置顶、删除历史记录
  - 系统托盘常驻运行
  - 支持开机自启
  - 白色简洁主题

使用方法：
  - 直接运行: python main.py
  - 打包成 exe: pyinstaller --onefile --windowed main.py
"""

import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# 导入自定义模块
import database
from clipboard_monitor import ClipboardMonitor
from main_window import MainWindow
from tray_manager import TrayManager
import autostart


def main():
    """应用程序主入口"""

    # === 1. 创建 QApplication ===
    # 高 DPI 支持（让界面在 4K 屏幕上不模糊）
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("ClipboardManager")
    app.setOrganizationName("ClipboardManager")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出程序，托盘继续运行

    # === 2. 初始化数据库 ===
    print("[启动] 正在初始化数据库...")
    database.init_database()
    print(f"[启动] 数据库路径: {database.DB_PATH}")

    # === 3. 创建主窗口（初始隐藏） ===
    print("[启动] 正在创建主窗口...")
    # 先创建 monitor，让 main_window 持有引用（防止自复制）
    monitor = ClipboardMonitor()
    main_window = MainWindow(monitor=monitor)
    # 主窗口创建后不立即显示，等用户点击托盘图标再显示

    # === 4. 创建系统托盘 ===
    print("[启动] 正在创建系统托盘...")
    tray = TrayManager(main_window, app)

    # === 5. 启动剪贴板监控 ===
    print("[启动] 正在启动剪贴板监控...")
    monitor.clipboard_changed.connect(main_window.refresh)
    monitor.start()

    # === 6. 检查开机自启状态 ===
    if autostart.is_autostart_enabled():
        print("[启动] 开机自启: 已启用")
    else:
        print("[启动] 开机自启: 未启用（可在托盘菜单中开启）")

    # === 7. 启动完成提示 ===
    print("[启动] 剪贴板历史管理器已就绪！")
    print("[启动] 点击系统托盘图标打开窗口")
    print("-" * 40)

    # 显示启动通知
    tray.show_notification(
        "📋 剪贴板管理器",
        "已启动，正在后台监控剪贴板。\n点击托盘图标查看历史记录。"
    )

    # === 8. 进入事件循环 ===
    try:
        exit_code = app.exec()
    finally:
        # 退出前清理
        monitor.stop()
        print("[退出] 剪贴板历史管理器已关闭")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
