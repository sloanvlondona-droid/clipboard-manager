"""
数据库模块 — 管理 SQLite 数据库的创建和读写操作
================================================
负责剪贴板历史记录的持久化存储，包括增删改查和搜索功能。
支持文本和图片两种内容类型。
"""

import sqlite3
import hashlib
import os
import uuid
from datetime import datetime


# 数据库文件和图片存储目录
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clipboard_history.db")
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clipboard_images")


def get_connection():
    """获取数据库连接（自动创建数据库文件如果不存在）"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_database():
    """初始化数据库，创建表结构和索引（如果不存在）"""
    # 确保图片存储目录存在
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

    conn = get_connection()
    cursor = conn.cursor()

    # 创建表（新字段：content_type 区分文字/图片，image_path 存图片路径）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clipboard_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL DEFAULT '',
            content_type TEXT NOT NULL DEFAULT 'text',
            image_path TEXT DEFAULT NULL,
            content_hash TEXT NOT NULL UNIQUE,
            pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 兼容旧表：尝试添加新字段（如果表已存在但缺少字段的话）
    for col, col_def in [
        ("content_type", "TEXT NOT NULL DEFAULT 'text'"),
        ("image_path", "TEXT DEFAULT NULL"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE clipboard_history ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass  # 字段已存在，忽略

    # 创建索引
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_content ON clipboard_history(content)",
        "CREATE INDEX IF NOT EXISTS idx_created_at ON clipboard_history(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_pinned ON clipboard_history(pinned)",
        "CREATE INDEX IF NOT EXISTS idx_content_type ON clipboard_history(content_type)",
    ]:
        try:
            cursor.execute(idx_sql)
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


def _hash_bytes(data: bytes) -> str:
    """计算二进制数据的 MD5 哈希值"""
    return hashlib.md5(data).hexdigest()


def add_text_entry(text: str) -> bool:
    """
    添加一条文本剪贴板记录。
    - 如果内容已存在，更新 last_used_at
    - 返回 True 表示新增了记录
    """
    content_hash = _hash_bytes(text.encode("utf-8"))
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO clipboard_history (content, content_type, content_hash) VALUES (?, 'text', ?)",
            (text, content_hash)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        cursor.execute(
            "UPDATE clipboard_history SET last_used_at = CURRENT_TIMESTAMP WHERE content_hash = ?",
            (content_hash,)
        )
        conn.commit()
        conn.close()
        return False


def add_image_entry(image_bytes: bytes) -> bool:
    """
    添加一条图片剪贴板记录。
    - 将图片保存到 images/ 目录
    - 在数据库中记录图片路径
    - 返回 True 表示新增了记录
    """
    content_hash = _hash_bytes(image_bytes)
    conn = get_connection()
    cursor = conn.cursor()

    # 检查是否已存在
    cursor.execute("SELECT id FROM clipboard_history WHERE content_hash = ?", (content_hash,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            "UPDATE clipboard_history SET last_used_at = CURRENT_TIMESTAMP WHERE content_hash = ?",
            (content_hash,)
        )
        conn.commit()
        conn.close()
        return False

    # 保存图片文件
    image_filename = f"{uuid.uuid4().hex}.png"
    image_path = os.path.join(IMAGES_DIR, image_filename)

    with open(image_path, "wb") as f:
        f.write(image_bytes)

    # 插入数据库记录
    try:
        cursor.execute(
            "INSERT INTO clipboard_history (content, content_type, image_path, content_hash) VALUES (?, 'image', ?, ?)",
            ("[图片]", image_path, content_hash)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_all_entries(search_text: str = "", limit: int = 200, offset: int = 0) -> list:
    """
    获取剪贴板历史列表。
    - 置顶优先，按最近使用时间倒序
    - 支持模糊搜索（仅搜文本内容）
    """
    conn = get_connection()
    cursor = conn.cursor()

    if search_text:
        cursor.execute(
            """
            SELECT id, content, content_type, image_path, pinned, created_at, last_used_at
            FROM clipboard_history
            WHERE content LIKE ?
            ORDER BY pinned DESC, last_used_at DESC
            LIMIT ? OFFSET ?
            """,
            (f"%{search_text}%", limit, offset)
        )
    else:
        cursor.execute(
            """
            SELECT id, content, content_type, image_path, pinned, created_at, last_used_at
            FROM clipboard_history
            ORDER BY pinned DESC, last_used_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )

    rows = cursor.fetchall()
    conn.close()

    entries = []
    for row in rows:
        entries.append({
            "id": row[0],
            "content": row[1],
            "content_type": row[2],
            "image_path": row[3],
            "pinned": bool(row[4]),
            "created_at": row[5],
            "last_used_at": row[6],
        })
    return entries


def get_total_count(search_text: str = "") -> int:
    """获取记录总数"""
    conn = get_connection()
    cursor = conn.cursor()

    if search_text:
        cursor.execute(
            "SELECT COUNT(*) FROM clipboard_history WHERE content LIKE ?",
            (f"%{search_text}%",)
        )
    else:
        cursor.execute("SELECT COUNT(*) FROM clipboard_history")

    count = cursor.fetchone()[0]
    conn.close()
    return count


def delete_entry(entry_id: int) -> bool:
    """删除指定 ID 的记录（如果是图片，同时删除图片文件）"""
    conn = get_connection()
    cursor = conn.cursor()

    # 先获取图片路径（如果有的话）
    cursor.execute("SELECT image_path FROM clipboard_history WHERE id = ?", (entry_id,))
    row = cursor.fetchone()
    if row and row[0]:
        image_path = row[0]
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass

    cursor.execute("DELETE FROM clipboard_history WHERE id = ?", (entry_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def delete_all(preserve_pinned: bool = True) -> int:
    """
    清空所有记录。
    - preserve_pinned=True：保留置顶的记录
    - 同时清理对应的图片文件
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 获取要删除的图片路径
    if preserve_pinned:
        cursor.execute("SELECT image_path FROM clipboard_history WHERE pinned = 0 AND content_type = 'image'")
    else:
        cursor.execute("SELECT image_path FROM clipboard_history WHERE content_type = 'image'")

    for row in cursor.fetchall():
        if row[0] and os.path.exists(row[0]):
            try:
                os.remove(row[0])
            except OSError:
                pass

    if preserve_pinned:
        cursor.execute("DELETE FROM clipboard_history WHERE pinned = 0")
    else:
        cursor.execute("DELETE FROM clipboard_history")

    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def toggle_pin(entry_id: int) -> bool:
    """切换记录的置顶状态，返回切换后的状态"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT pinned FROM clipboard_history WHERE id = ?", (entry_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return False

    new_pinned = 0 if row[0] else 1
    cursor.execute(
        "UPDATE clipboard_history SET pinned = ? WHERE id = ?",
        (new_pinned, entry_id)
    )
    conn.commit()
    conn.close()
    return bool(new_pinned)


def get_entry_by_id(entry_id: int) -> dict | None:
    """获取单条记录的完整信息"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, content, content_type, image_path, pinned, created_at, last_used_at FROM clipboard_history WHERE id = ?",
        (entry_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None
    return {
        "id": row[0],
        "content": row[1],
        "content_type": row[2],
        "image_path": row[3],
        "pinned": bool(row[4]),
        "created_at": row[5],
        "last_used_at": row[6],
    }
