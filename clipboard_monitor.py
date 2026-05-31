"""
剪贴板监控 — 用 Pillow 读图片（兼容性远优于 PyQt6）
"""

from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PIL import ImageGrab, Image
import hashlib
import re
import io
import database


def _get_text(cb) -> str:
    """提取文字"""
    t = cb.text()
    if t and t.strip():
        return t
    m = cb.mimeData()
    if m.hasHtml():
        h = m.html()
        if h:
            c = re.sub(r'<[^>]+>', ' ', h)
            c = re.sub(r'\s+', ' ', c).strip()
            if c:
                return c
    return ""


def _get_image_bytes() -> bytes | None:
    """用 Pillow 从 Windows 剪贴板读取图片"""
    try:
        img = ImageGrab.grabclipboard()
    except Exception as e:
        print(f"[调试] ImageGrab 异常: {e}", flush=True)
        return None

    if img is None:
        return None

    if isinstance(img, list):
        print(f"[调试] 剪贴板是文件列表: {img}", flush=True)
        for path in img:
            try:
                pil_img = Image.open(path)
                buf = io.BytesIO()
                pil_img.save(buf, "PNG")
                print(f"[调试] 从文件读取图片: {path}", flush=True)
                return buf.getvalue()
            except Exception as e:
                print(f"[调试] 文件读取失败: {e}", flush=True)
        return None

    if isinstance(img, Image.Image):
        print(f"[调试] Pillow 获取图片: {img.size}, {img.mode}", flush=True)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()

    print(f"[调试] 未知类型: {type(img)}", flush=True)
    return None


class ClipboardMonitor(QObject):

    clipboard_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_text = ""
        self._last_img_hash = ""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check)
        self._running = False

    def start(self):
        if not self._running:
            self._last_text = ""
            self._last_img_hash = ""
            self._timer.start(500)
            self._running = True
            print("[监控] 已启动（Pillow 图片检测）")

    def stop(self):
        if self._running:
            self._timer.stop()
            self._running = False

    def mark_as_seen(self):
        """将从历史复制的内容标记为'已见过'，防止重复记录"""
        cb = QApplication.clipboard()
        self._last_text = _get_text(cb)
        data = _get_image_bytes()
        self._last_img_hash = hashlib.md5(data).hexdigest() if data else ""

    def _check(self):
        try:
            cb = QApplication.clipboard()
            mime = cb.mimeData()

            # --- 图片（Pillow 检测）---
            data = _get_image_bytes()
            if data:
                h = hashlib.md5(data).hexdigest()
                if h != self._last_img_hash:
                    self._last_img_hash = h
                    self._last_text = _get_text(cb)
                    ok = database.add_image_entry(data)
                    print(f"[调试] 图片保存: {ok}, hash={h[:12]}", flush=True)
                    if ok:
                        self.clipboard_changed.emit()
                else:
                    print(f"[调试] 图片跳过(重复)", flush=True)
                return

            # --- 文件 ---
            if mime.hasUrls():
                paths = [u.toLocalFile() for u in mime.urls() if u.toLocalFile()]
                if paths:
                    t = "📁 " + "\n".join(paths)
                    if t != self._last_text:
                        self._last_text = t
                        self._last_img_hash = ""
                        if database.add_text_entry(t):
                            self.clipboard_changed.emit()
                            print(f"[剪贴板] 文件: {len(paths)}个")
                return

            # --- 文字 ---
            t = _get_text(cb)
            if t and t != self._last_text:
                self._last_text = t
                self._last_img_hash = ""
                if database.add_text_entry(t):
                    self.clipboard_changed.emit()
                    print(f"[剪贴板] 文本({len(t)}字)")

        except Exception as e:
            import traceback
            traceback.print_exc()
