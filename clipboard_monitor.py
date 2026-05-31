"""
剪贴板监控 — Pillow 读图片 + PyQt6 读文字
"""

from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PIL import ImageGrab, Image
import hashlib, re, io
import database


def _get_text(cb) -> str:
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
    try:
        img = ImageGrab.grabclipboard()
    except Exception:
        return None
    if img is None:
        return None
    if isinstance(img, list):
        for path in img:
            try:
                pil_img = Image.open(path)
                buf = io.BytesIO()
                pil_img.save(buf, "PNG")
                return buf.getvalue()
            except Exception:
                pass
        return None
    if isinstance(img, Image.Image):
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()
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
            print("[监控] 已启动")

    def stop(self):
        if self._running:
            self._timer.stop()
            self._running = False

    def mark_as_seen(self):
        cb = QApplication.clipboard()
        self._last_text = _get_text(cb)
        data = _get_image_bytes()
        self._last_img_hash = hashlib.md5(data).hexdigest() if data else ""

    def _check(self):
        try:
            cb = QApplication.clipboard()
            mime = cb.mimeData()

            data = _get_image_bytes()
            if data:
                h = hashlib.md5(data).hexdigest()
                if h != self._last_img_hash:
                    self._last_img_hash = h
                    self._last_text = _get_text(cb)
                    if database.add_image_entry(data):
                        self.clipboard_changed.emit()
                        print("[剪贴板] 图片")
                return

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
