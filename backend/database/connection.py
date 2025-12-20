# backend/database/connection.py
import sqlite3,sys
from contextlib import contextmanager
from typing import Generator, Tuple
from backend.config import DB_PATH

@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """获取数据库连接（上下文管理器）"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        yield conn
    finally:
        if conn:
            conn.close()

def check_db_connection() -> Tuple[bool, str]:
    """检查数据库连接状态"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            return True, f"数据库连接正常，找到 {len(tables)} 个表"
    except Exception as e:
        return False, f"数据库连接失败: {str(e)}"

def close_connection(conn: sqlite3.Connection):
    """关闭数据库连接"""
    if conn:
        conn.close()