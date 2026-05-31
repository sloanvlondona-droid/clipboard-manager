"""
主窗口 — 剪贴板历史管理器
圆角窗口 · 自复制防护 · 细化 UI
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QFrame, QMenu, QMessageBox,
    QApplication, QTextEdit, QDialog,
    QDialogButtonBox, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QAction, QCursor, QPixmap, QImage
import os
import database
import styles


# ========== Toast ==========

class Toast(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background: rgba(50,50,50,220); color: #fff;
                border-radius: 8px; padding: 10px 24px;
                font-size: 13px; font-weight: 500;
            }
        """)
        self.hide()
        self._t = QTimer(self, singleShot=True, timeout=self.hide)

    def show_msg(self, text, duration=1500):
        self.setText(text); self.adjustSize(); self.show(); self.raise_()
        r = self.parent().rect()
        self.move((r.width() - self.width()) // 2, r.height() - 70)
        self._t.start(duration)


# ========== 详情弹窗（不关闭主窗口） ==========

class DetailDialog(QDialog):
    def __init__(self, entry, parent=None):
        super().__init__(None)  # 无 parent，独立窗口
        self.setWindowTitle("详情")
        self.resize(550, 500)
        self.setStyleSheet(styles.GLOBAL_STYLESHEET)
        ly = QVBoxLayout(self)
        ly.setContentsMargins(16, 16, 16, 16)

        if entry["content_type"] == "image" and entry["image_path"]:
            s = QScrollArea(); s.setWidgetResizable(True)
            lb = QLabel(); lb.setPixmap(QPixmap(entry["image_path"]))
            lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s.setWidget(lb); ly.addWidget(s, 1)
        else:
            te = QTextEdit(); te.setReadOnly(True); te.setPlainText(entry["content"])
            te.setStyleSheet("""
                QTextEdit { border: 1px solid #E8E8E8; border-radius: 8px;
                padding: 14px; font-size: 14px; line-height: 1.8;
                background: #FAFAFA; }
            """)
            ly.addWidget(te, 1)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.reject); bb.accepted.connect(self.accept)
        bb.setStyleSheet("QPushButton { padding: 8px 24px; border-radius: 6px; font-size: 13px; }")
        ly.addWidget(bb)


# ========== 列表项 ==========

class ItemWidget(QFrame):

    pin_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    copied = pyqtSignal()

    def __init__(self, entry, list_width=400):
        super().__init__()
        self.eid = entry["id"]
        self.content = entry["content"]
        self.ctype = entry.get("content_type", "text")
        self.ipath = entry.get("image_path")
        self.pinned = entry["pinned"]
        self._build(entry, list_width)

    def _build(self, entry, lw):
        self.setFixedWidth(lw - 16)
        # 卡片样式
        if self.pinned:
            self.setStyleSheet("""
                ItemWidget { background: #FFF9E6; border: 1px solid #FCD34D;
                    border-radius: 10px; }
            """)
        else:
            self.setStyleSheet("""
                ItemWidget { background: #FFFFFF; border: 1px solid #E8ECF0;
                    border-radius: 10px; }
                ItemWidget:hover { background: #F8FAFD; border-color: #D0D8E8; }
            """)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 10)
        root.setSpacing(8)

        # -- 内容 --
        if self.ctype == "image" and self.ipath and os.path.exists(self.ipath):
            pm = QPixmap(self.ipath).scaledToWidth(min(lw - 60, 200), Qt.TransformationMode.SmoothTransformation)
            lb = QLabel()
            lb.setPixmap(pm)
            lb.setCursor(Qt.CursorShape.PointingHandCursor)
            lb.mousePressEvent = self._copy
            lb.setToolTip("🖱 单击复制 · 双击查看大图")
            lb.setStyleSheet("border-radius: 8px; padding: 4px; background: transparent;")
            root.addWidget(lb)
        else:
            txt = self.content.strip()
            lb = QLabel(txt)
            lb.setWordWrap(True)
            lb.setCursor(Qt.CursorShape.PointingHandCursor)
            lb.mousePressEvent = self._copy
            lb.setToolTip("🖱 单击复制 · 双击查看详情")
            lb.setStyleSheet("""
                font-size: 13px; color: #2C3E50; line-height: 1.7;
                background: transparent; padding: 2px 0;
            """)
            root.addWidget(lb)

        # -- 底部栏 --
        bar = QHBoxLayout(); bar.setSpacing(8)
        ts = (entry.get("last_used_at") or entry.get("created_at") or "")[:16].replace("T", " ")
        tl = QLabel(ts)
        tl.setStyleSheet("color: #94A3B8; font-size: 11px; background: transparent;")
        bar.addWidget(tl); bar.addStretch()

        # 置顶按钮
        pin_text = "📌 已置顶" if self.pinned else "📌 置顶"
        pin_bg = "#FFF9E6" if self.pinned else "#F8F9FA"
        pin_border = "#FCD34D" if self.pinned else "#E8ECF0"
        pin_color = "#E65100" if self.pinned else "#94A3B8"
        pb = QPushButton(pin_text)
        pb.setFixedHeight(28)
        pb.setCursor(Qt.CursorShape.PointingHandCursor)
        pb.setStyleSheet(f"""
            QPushButton {{ background: {pin_bg}; border: 1px solid {pin_border};
                border-radius: 14px; font-size: 11px; padding: 2px 14px;
                color: {pin_color}; font-weight: 500; }}
            QPushButton:hover {{ background: #FFF3D6; border-color: #FBBF24; }}
        """)
        pb.clicked.connect(lambda: self.pin_clicked.emit(self.eid))
        bar.addWidget(pb)

        # 删除按钮
        db = QPushButton("🗑 删除")
        db.setFixedHeight(28)
        db.setCursor(Qt.CursorShape.PointingHandCursor)
        db.setStyleSheet("""
            QPushButton { background: #FFF5F5; border: 1px solid #FECACA;
                border-radius: 14px; font-size: 11px; padding: 2px 14px;
                color: #EF4444; font-weight: 500; }
            QPushButton:hover { background: #FEE2E2; border-color: #FCA5A5; }
        """)
        db.clicked.connect(lambda: self.delete_clicked.emit(self.eid))
        bar.addWidget(db)

        root.addLayout(bar)

    def _copy(self, event=None):
        cb = QApplication.clipboard()
        if self.ctype == "image" and self.ipath and os.path.exists(self.ipath):
            img = QImage(self.ipath)
            if not img.isNull():
                cb.setImage(img)
        else:
            cb.setText(self.content)
        self.copied.emit()


# ========== 主窗口 ==========

class MainWindow(QWidget):

    def __init__(self, parent=None, monitor=None):
        super().__init__(parent)
        self.monitor = monitor
        self.setWindowTitle("📋 剪贴板历史")
        self.setMinimumSize(420, 480)
        self.resize(500, 660)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Popup
        )
        self.setStyleSheet(styles.GLOBAL_STYLESHEET)
        self._setup()
        self.refresh()

    def _setup(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # 标题栏
        tb = QFrame(); tb.setFixedHeight(40)
        tb.setStyleSheet(f"background: {styles.COLOR_BG_PRIMARY}; border-bottom: 1px solid {styles.COLOR_BORDER};")
        tl = QHBoxLayout(tb); tl.setContentsMargins(16, 0, 10, 0)
        t = QLabel("📋 剪贴板历史")
        t.setStyleSheet("font-size: 14px; font-weight: 600; color: #333; background: transparent;")
        x = QPushButton("✕")
        x.setCursor(Qt.CursorShape.PointingHandCursor)
        x.setStyleSheet("QPushButton{background:transparent;border:none;font-size:18px;color:#BBB;} QPushButton:hover{background:#F5F5F5;border-radius:6px;color:#666;}")
        x.clicked.connect(self.hide)
        tl.addWidget(t); tl.addStretch(); tl.addWidget(x)

        # 搜索
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  搜索历史...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda: self._stimer.start(300))

        # 滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea{background:#FFF;border:none;}")

        self.container = QWidget()
        self.container.setStyleSheet("background:transparent;")
        self.items_layout = QVBoxLayout(self.container)
        self.items_layout.setContentsMargins(8, 6, 8, 6)
        self.items_layout.setSpacing(6)
        self.items_layout.addStretch()
        self.scroll.setWidget(self.container)

        # 底部
        bb = QFrame(); bb.setFixedHeight(40)
        bb.setStyleSheet(f"background:{styles.COLOR_BG_SECONDARY};border-top:1px solid {styles.COLOR_BORDER};")
        bl = QHBoxLayout(bb); bl.setContentsMargins(16, 0, 12, 0)
        self.count_lbl = QLabel("共 0 条")
        self.count_lbl.setStyleSheet(f"color:{styles.COLOR_TEXT_SECONDARY};font-size:11px;background:transparent;")
        clr = QPushButton("🗑 清空全部")
        clr.setCursor(Qt.CursorShape.PointingHandCursor)
        clr.setStyleSheet("QPushButton{background:transparent;border:none;color:#D32F2F;font-size:12px;} QPushButton:hover{background:#FFEBEE;border-radius:6px;}")
        clr.clicked.connect(self._clear)
        bl.addWidget(self.count_lbl); bl.addStretch(); bl.addWidget(clr)

        self.toast = Toast(self)

        root.addWidget(tb); root.addWidget(self.search); root.addWidget(self.scroll, 1); root.addWidget(bb)

        self._stimer = QTimer(self, singleShot=True, timeout=self.refresh)
        self._htimer = QTimer(self, singleShot=True, timeout=self._try_hide)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._stimer.start(200)

    # ========== 刷新 ==========

    def refresh(self):
        try:
            q = self.search.text().strip()
            entries = database.get_all_entries(search_text=q)
            total = database.get_total_count(search_text=q)

            while self.items_layout.count() > 1:
                w = self.items_layout.takeAt(0)
                if w.widget():
                    w.widget().deleteLater()

            lw = max(self.scroll.viewport().width(), 420)

            for e in entries:
                iw = ItemWidget(e, lw)
                iw.pin_clicked.connect(self._pin)
                iw.delete_clicked.connect(self._delete)
                iw.copied.connect(self._on_copy)
                self.items_layout.insertWidget(self.items_layout.count() - 1, iw)

            self.count_lbl.setText(f"共 {total} 条")
        except Exception as ex:
            import traceback; traceback.print_exc()

    # ========== 操作 ==========

    def _pin(self, eid):
        database.toggle_pin(eid); self.refresh(); self.toast.show_msg("📌 已切换置顶")

    def _delete(self, eid):
        database.delete_entry(eid); self.refresh(); self.toast.show_msg("🗑 已删除")

    def _on_copy(self):
        """复制后通知 monitor 忽略本次变化，防止重复记录"""
        if self.monitor:
            self.monitor.mark_as_seen()
        self.toast.show_msg("✅ 已复制到剪贴板")

    def _clear(self):
        r = QMessageBox.question(self, "确认", "删除所有非置顶记录？",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                 QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            n = database.delete_all(preserve_pinned=True)
            self.refresh(); self.toast.show_msg(f"🗑 已清空 {n} 条")

    # ========== 右键 ==========

    def contextMenuEvent(self, event):
        pos = event.globalPos()
        child = self.childAt(self.mapFromGlobal(pos))
        while child and not isinstance(child, ItemWidget):
            child = child.parent()
        if not isinstance(child, ItemWidget):
            return

        menu = QMenu(self)
        menu.setStyleSheet(styles.GLOBAL_STYLESHEET)
        a1 = QAction("📋 复制", menu); a1.triggered.connect(child._copy)
        a2 = QAction("🔍 查看详情", menu)
        a2.triggered.connect(lambda: self._detail(child.eid))
        a3 = QAction("📌 取消置顶" if child.pinned else "📌 置顶", menu)
        a3.triggered.connect(lambda: self._pin(child.eid))
        a4 = QAction("🗑 删除", menu); a4.triggered.connect(lambda: self._delete(child.eid))
        menu.addActions([a1, a2, a3]); menu.addSeparator(); menu.addAction(a4)
        menu.exec(pos)

    def mouseDoubleClickEvent(self, event):
        child = self.childAt(event.pos())
        while child and not isinstance(child, ItemWidget):
            child = child.parent()
        if isinstance(child, ItemWidget):
            self._detail(child.eid)

    def _detail(self, eid):
        e = database.get_entry_by_id(eid)
        if e:
            dlg = DetailDialog(e, None)  # 独立窗口，不绑定父窗口
            dlg.exec()

    # ========== 窗口显隐 ==========

    def toggle(self):
        if self.isVisible(): self.hide()
        else: self.show(); self._pos(); self.refresh()

    def show_and_focus(self):
        self.show(); self._pos(); self.raise_(); self.activateWindow()
        self.search.setFocus(); self.refresh()

    def _pos(self):
        s = QApplication.primaryScreen()
        if s:
            g = s.availableGeometry()
            self.move(g.right() - self.width() - 10, g.bottom() - self.height() - 10)

    def _try_hide(self):
        if QApplication.activeModalWidget() or QApplication.activePopupWidget():
            return
        if not self.isActiveWindow():
            self.hide()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._htimer.start(300)
