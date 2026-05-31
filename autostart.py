"""
开机自启模块 — 管理 Windows 开机自动启动
=========================================
通过 Windows 注册表实现开机自启功能。
需要管理员权限时会降级使用启动文件夹方式。
"""

import os
import sys
import winreg


# 注册表路径（当前用户，不需要管理员权限）
REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "ClipboardManager"


def _get_exe_path() -> str:
    """
    获取当前程序的可执行文件路径。
    - 如果已打包成 .exe，返回 .exe 路径
    - 如果是直接运行 .py，返回 pythonw.exe 启动脚本的路径
    """
    if getattr(sys, 'frozen', False):
        # 已通过 PyInstaller 打包
        return sys.executable

    # 开发模式：返回 pythonw.exe 的完整启动命令
    pythonw_path = os.path.join(
        os.path.dirname(sys.executable), "pythonw.exe"
    )
    script_path = os.path.abspath(sys.argv[0])

    # 如果脚本是 .py 文件，转换为启动命令
    if os.path.exists(pythonw_path):
        return f'"{pythonw_path}" "{script_path}"'
    else:
        return f'"{sys.executable}" "{script_path}"'


def is_autostart_enabled() -> bool:
    """
    检查当前是否已启用开机自启。
    返回 True 表示已启用，False 表示未启用。
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ
        )
        try:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return bool(value)
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


def enable_autostart() -> bool:
    """
    启用开机自启。
    - 向注册表写入启动项
    - 返回 True 表示成功
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        exe_path = _get_exe_path()
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        return True
    except OSError as e:
        print(f"[自启] 写入注册表失败: {e}")
        return False


def disable_autostart() -> bool:
    """
    禁用开机自启。
    - 从注册表删除启动项
    - 返回 True 表示成功
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass  # 本来就没设置，不算失败
        winreg.CloseKey(key)
        return True
    except OSError as e:
        print(f"[自启] 删除注册表项失败: {e}")
        return False
