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
            QLabel { background:#1E293B; color:#fff; border-radius:20px;
                padding:10px 24px; font-size:13px; font-weight:500; }
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
        super().__init__(None)
        self.setWindowTitle("📋 详情")
        self.resize(580, 520)
        self.setStyleSheet(styles.GLOBAL_STYLESHEET)
        ly = QVBoxLayout(self)
        ly.setContentsMargins(20, 20, 20, 20); ly.setSpacing(12)

        if entry["content_type"] == "image" and entry["image_path"]:
            s = QScrollArea(); s.setWidgetResizable(True)
            lb = QLabel(); lb.setPixmap(QPixmap(entry["image_path"]))
            lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lb.setStyleSheet("background:transparent;")
            s.setWidget(lb); ly.addWidget(s, 1)
        else:
            te = QTextEdit(); te.setReadOnly(True); te.setPlainText(entry["content"])
            te.setStyleSheet(f"""
                QTextEdit {{ border:1px solid {styles.C_BORDER}; border-radius:12px;
                padding:16px; font-size:14px; line-height:1.8; background:{styles.C_SURFACE}; }}
            """)
            ly.addWidget(te, 1)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.reject); bb.accepted.connect(self.accept)
        bb.button(QDialogButtonBox.StandardButton.Close).setStyleSheet(
            f"QPushButton{{background:{styles.C_ACCENT};color:#fff;border:none;"
            f"border-radius:8px;padding:8px 28px;font-size:13px;font-weight:500;}}"
            f"QPushButton:hover{{background:#3B5DE7;}}"
        )
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
        self.setStyleSheet(styles.card_style(self.pinned))

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 12)
        root.setSpacing(10)

        # -- 内容 --
        if self.ctype == "image" and self.ipath and os.path.exists(self.ipath):
            pm = QPixmap(self.ipath).scaledToWidth(min(lw - 64, 220), Qt.TransformationMode.SmoothTransformation)
            lb = QLabel()
            lb.setPixmap(pm)
            lb.setCursor(Qt.CursorShape.PointingHandCursor)
            lb.mousePressEvent = self._copy
            lb.setToolTip("🖱 单击复制 · 双击大图")
            lb.setStyleSheet("border-radius:8px; background:transparent;")
            root.addWidget(lb)
        else:
            txt = self.content.strip()
            lb = QLabel(txt)
            lb.setWordWrap(True)
            lb.setCursor(Qt.CursorShape.PointingHandCursor)
            lb.mousePressEvent = self._copy
            lb.setToolTip("🖱 单击复制 · 双击详情")
            lb.setStyleSheet(f"font-size:13px; color:{styles.C_TEXT}; line-height:1.8; background:transparent; padding:2px 0;")
            root.addWidget(lb)

        # -- 底部栏：时间 + 按钮 --
        bar = QHBoxLayout(); bar.setSpacing(8)
        ts = (entry.get("last_used_at") or entry.get("created_at") or "")[:16].replace("T", " ")
        tl = QLabel(ts)
        tl.setStyleSheet(f"color:{styles.C_TEXT_SUB}; font-size:11px; background:transparent;")
        bar.addWidget(tl); bar.addStretch()

        # 置顶
        if self.pinned:
            pb = QPushButton("📌 已置顶")
            pb.setStyleSheet(styles.pill_btn(styles.C_PINNED, styles.C_PINNED_BORDER, styles.C_PIN_COLOR))
        else:
            pb = QPushButton("📌 置顶")
            pb.setStyleSheet(styles.pill_btn(styles.C_SURFACE, styles.C_BORDER, styles.C_TEXT_SUB))
        pb.setFixedHeight(28); pb.setCursor(Qt.CursorShape.PointingHandCursor)
        pb.clicked.connect(lambda: self.pin_clicked.emit(self.eid))
        bar.addWidget(pb)

        # 删除
        db = QPushButton("🗑 删除")
        db.setFixedHeight(28); db.setCursor(Qt.CursorShape.PointingHandCursor)
        db.setStyleSheet(styles.pill_btn(styles.C_DANGER_LIGHT, "#FECACA", styles.C_DANGER))
        db.clicked.connect(lambda: self.delete_clicked.emit(self.eid))
        bar.addWidget(db)

        root.addLayout(bar)

    def _copy(self, *args):
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
        self._in_dialog = False
        self.setWindowTitle("📋 剪贴板历史")
        self.setMinimumSize(420, 480)
        self.resize(500, 660)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setStyleSheet(styles.GLOBAL_STYLESHEET)
        self._drag_pos = None
        self._setup()
        self.refresh()
        self.installEventFilter(self)

    def _setup(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # 标题栏
        tb = QFrame(); tb.setFixedHeight(42)
        tb.setStyleSheet(f"background:{styles.C_PRIMARY}; border-bottom:1px solid {styles.C_BORDER_LIGHT};")
        tl = QHBoxLayout(tb); tl.setContentsMargins(18, 0, 10, 0)
        t = QLabel("📋 剪贴板历史")
        t.setStyleSheet(f"font-size:14px; font-weight:600; color:{styles.C_TEXT}; background:transparent;")
        x = QPushButton("✕")
        x.setCursor(Qt.CursorShape.PointingHandCursor)
        x.setStyleSheet("QPushButton{background:transparent;border:none;font-size:18px;color:#94A3B8;} QPushButton:hover{background:#F1F5F9;border-radius:8px;color:#475569;}")
        x.clicked.connect(self.hide)
        tl.addWidget(t); tl.addStretch(); tl.addWidget(x)

        # 搜索
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  搜索剪贴板历史...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda: self._stimer.start(300))

        # 滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"QScrollArea{{background:{styles.C_PRIMARY};border:none;}}")

        self.container = QWidget()
        self.container.setStyleSheet("background:transparent;")
        self.items_layout = QVBoxLayout(self.container)
        self.items_layout.setContentsMargins(10, 8, 10, 8)
        self.items_layout.setSpacing(8)
        self.items_layout.addStretch()
        self.scroll.setWidget(self.container)

        # 底部
        bb = QFrame(); bb.setFixedHeight(42)
        bb.setStyleSheet(f"background:{styles.C_SURFACE};border-top:1px solid {styles.C_BORDER_LIGHT};")
        bl = QHBoxLayout(bb); bl.setContentsMargins(18, 0, 12, 0)
        self.count_lbl = QLabel("共 0 条")
        self.count_lbl.setStyleSheet(f"color:{styles.C_TEXT_SUB};font-size:11px;background:transparent;")
        clr = QPushButton("🗑 清空全部")
        clr.setCursor(Qt.CursorShape.PointingHandCursor)
        clr.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{styles.C_DANGER};font-size:12px;}} QPushButton:hover{{background:{styles.C_DANGER_LIGHT};border-radius:8px;}}")
        clr.clicked.connect(self._clear)
        bl.addWidget(self.count_lbl); bl.addStretch(); bl.addWidget(clr)

        self.toast = Toast(self)

        root.addWidget(tb); root.addWidget(self.search); root.addWidget(self.scroll, 1); root.addWidget(bb)

        self._stimer = QTimer(self, singleShot=True, timeout=self.refresh)
        self._htimer = QTimer(self, singleShot=True, timeout=self._try_hide)

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
        self._in_dialog = True
        r = QMessageBox.question(self, "确认", "删除所有非置顶记录？",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                 QMessageBox.StandardButton.No)
        self._in_dialog = False
        self._htimer.stop()  # 取消隐藏定时器
        if r == QMessageBox.StandardButton.Yes:
            n = database.delete_all(preserve_pinned=True)
            self.refresh(); self.toast.show_msg(f"🗑 已清空 {n} 条")

    # ========== 右键（事件过滤器捕获所有子控件的右键） ==========

    def eventFilter(self, obj, event):
        if event.type() == event.Type.ContextMenu:
            return self._show_menu(event.globalPos())
        return super().eventFilter(obj, event)

    def _show_menu(self, pos):
        child = self.childAt(self.mapFromGlobal(pos))
        while child and not isinstance(child, ItemWidget):
            child = child.parent()
        if not isinstance(child, ItemWidget):
            return False

        menu = QMenu(self)
        menu.setStyleSheet(styles.GLOBAL_STYLESHEET)
        a1 = QAction("📋 复制", menu)
        a1.triggered.connect(lambda checked, w=child: w._copy())
        a2 = QAction("🔍 查看详情", menu)
        a2.triggered.connect(lambda checked, eid=child.eid: self._detail(eid))
        a3 = QAction("📌 取消置顶" if child.pinned else "📌 置顶", menu)
        a3.triggered.connect(lambda checked, eid=child.eid: self._pin(eid))
        a4 = QAction("🗑 删除", menu)
        a4.triggered.connect(lambda checked, eid=child.eid: self._delete(eid))
        menu.addActions([a1, a2, a3]); menu.addSeparator(); menu.addAction(a4)
        menu.exec(pos)
        return True

    def mouseDoubleClickEvent(self, event):
        child = self.childAt(event.pos())
        while child and not isinstance(child, ItemWidget):
            child = child.parent()
        if isinstance(child, ItemWidget):
            self._detail(child.eid)

    def _detail(self, eid):
        e = database.get_entry_by_id(eid)
        if e:
            self._in_dialog = True
            dlg = DetailDialog(e, self)
            dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
            dlg.exec()
            self._in_dialog = False
            self._htimer.stop()

    # ========== 窗口显隐 ==========

    def toggle(self):
        if self.isVisible(): self.hide()
        else:
            self._htimer.stop()
            self.show(); self._pos(); self.refresh()

    def show_and_focus(self):
        self._htimer.stop()
        self.show(); self._pos(); self.raise_(); self.activateWindow()
        self.search.setFocus(); self.refresh()

    def _pos(self):
        s = QApplication.primaryScreen()
        if s:
            g = s.availableGeometry()
            self.move(g.right() - self.width() - 10, g.bottom() - self.height() - 10)

    def _try_hide(self):
        if self._in_dialog:
            return
        if QApplication.activeModalWidget() or QApplication.activePopupWidget():
            return
        if not self.isActiveWindow():
            self.hide()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._htimer.start(300)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._stimer.start(200)

    # ========== 标题栏拖动（边缘缩放由 nativeEvent 处理） ==========

    def mousePressEvent(self, event):
        if event.position().y() < 42:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            d = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + d)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
