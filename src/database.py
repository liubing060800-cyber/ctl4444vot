"""
Ctl 秘书机器人 - 数据库模块
使用 SQLite 存储用户数据、待办事项、笔记、提醒和日程
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
from config import DB_PATH


class Database:
    """SQLite 数据库操作类"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings TEXT DEFAULT '{}'
                )
            """)

            # 待办事项表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    priority INTEGER DEFAULT 1,
                    completed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # 笔记表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # 提醒表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    remind_at TIMESTAMP NOT NULL,
                    is_recurring INTEGER DEFAULT 0,
                    recurring_type TEXT,
                    is_completed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # 日程表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    location TEXT,
                    category TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_todos_user ON todos(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_time ON reminders(remind_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_user ON schedules(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_time ON schedules(start_time)")

    # ========== 用户管理 ==========

    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """添加或更新用户"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, last_name))

    def get_user(self, user_id: int) -> Optional[Dict]:
        """获取用户信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ========== 待办事项 (Todo) ==========

    def add_todo(self, user_id: int, content: str, category: str = "general", priority: int = 1) -> int:
        """添加待办事项，返回事项 ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO todos (user_id, content, category, priority)
                VALUES (?, ?, ?, ?)
            """, (user_id, content, category, priority))
            return cursor.lastrowid

    def get_todos(self, user_id: int, completed: bool = False, category: str = None) -> List[Dict]:
        """获取用户的待办事项列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM todos WHERE user_id = ? AND completed = ?"
            params = [user_id, 1 if completed else 0]
            if category:
                sql += " AND category = ?"
                params.append(category)
            sql += " ORDER BY priority DESC, created_at DESC"
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def complete_todo(self, todo_id: int, user_id: int) -> bool:
        """标记待办事项为已完成"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE todos SET completed = 1, completed_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            """, (todo_id, user_id))
            return cursor.rowcount > 0

    def delete_todo(self, todo_id: int, user_id: int) -> bool:
        """删除待办事项"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, user_id))
            return cursor.rowcount > 0

    def clear_completed(self, user_id: int) -> int:
        """清空已完成的待办事项，返回删除数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM todos WHERE user_id = ? AND completed = 1", (user_id,))
            return cursor.rowcount

    def get_todo_stats(self, user_id: int) -> Dict:
        """获取待办事项统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
                    COUNT(*) as total
                FROM todos WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else {"pending": 0, "completed": 0, "total": 0}

    # ========== 笔记 (Notes) ==========

    def add_note(self, user_id: int, content: str, title: str = None, tags: str = None) -> int:
        """添加笔记"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO notes (user_id, title, content, tags)
                VALUES (?, ?, ?, ?)
            """, (user_id, title, content, tags))
            return cursor.lastrowid

    def get_notes(self, user_id: int, search: str = None) -> List[Dict]:
        """获取用户笔记列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if search:
                cursor.execute("""
                    SELECT * FROM notes WHERE user_id = ? 
                    AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)
                    ORDER BY updated_at DESC
                """, (user_id, f"%{search}%", f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("""
                    SELECT * FROM notes WHERE user_id = ? ORDER BY updated_at DESC
                """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_note(self, note_id: int, user_id: int) -> Optional[Dict]:
        """获取单条笔记"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_note(self, note_id: int, user_id: int) -> bool:
        """删除笔记"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
            return cursor.rowcount > 0

    # ========== 提醒 (Reminders) ==========

    def add_reminder(self, user_id: int, content: str, remind_at: datetime,
                     is_recurring: bool = False, recurring_type: str = None) -> int:
        """添加提醒"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reminders (user_id, content, remind_at, is_recurring, recurring_type)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, content, remind_at, 1 if is_recurring else 0, recurring_type))
            return cursor.lastrowid

    def get_pending_reminders(self, user_id: int = None) -> List[Dict]:
        """获取待执行的提醒"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if user_id:
                cursor.execute("""
                    SELECT * FROM reminders 
                    WHERE user_id = ? AND is_completed = 0 AND remind_at <= ?
                    ORDER BY remind_at ASC
                """, (user_id, now))
            else:
                cursor.execute("""
                    SELECT * FROM reminders 
                    WHERE is_completed = 0 AND remind_at <= ?
                    ORDER BY remind_at ASC
                """, (now,))
            return [dict(row) for row in cursor.fetchall()]

    def get_user_reminders(self, user_id: int) -> List[Dict]:
        """获取用户的所有提醒"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reminders WHERE user_id = ? AND is_completed = 0
                ORDER BY remind_at ASC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def complete_reminder(self, reminder_id: int):
        """标记提醒为已完成"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reminders SET is_completed = 1 WHERE id = ?", (reminder_id,))

    def delete_reminder(self, reminder_id: int, user_id: int) -> bool:
        """删除提醒"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ? AND user_id = ?", (reminder_id, user_id))
            return cursor.rowcount > 0

    # ========== 日程 (Schedules) ==========

    def add_schedule(self, user_id: int, title: str, start_time: datetime,
                     end_time: datetime = None, description: str = None,
                     location: str = None, category: str = "general") -> int:
        """添加日程"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO schedules (user_id, title, description, start_time, end_time, location, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, title, description, start_time, end_time, location, category))
            return cursor.lastrowid

    def get_schedules(self, user_id: int, date: datetime = None) -> List[Dict]:
        """获取用户日程"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if date:
                date_str = date.strftime("%Y-%m-%d")
                cursor.execute("""
                    SELECT * FROM schedules 
                    WHERE user_id = ? AND DATE(start_time) = ?
                    ORDER BY start_time ASC
                """, (user_id, date_str))
            else:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    SELECT * FROM schedules 
                    WHERE user_id = ? AND start_time >= ?
                    ORDER BY start_time ASC LIMIT 20
                """, (user_id, now))
            return [dict(row) for row in cursor.fetchall()]

    def delete_schedule(self, schedule_id: int, user_id: int) -> bool:
        """删除日程"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schedules WHERE id = ? AND user_id = ?", (schedule_id, user_id))
            return cursor.rowcount > 0

    # ========== 今日概览 ==========

    def get_today_overview(self, user_id: int) -> Dict:
        """获取今日概览数据"""
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 今日待办
            cursor.execute("""
                SELECT COUNT(*) as count FROM todos 
                WHERE user_id = ? AND completed = 0
            """, (user_id,))
            pending_todos = cursor.fetchone()["count"]

            # 今日日程
            cursor.execute("""
                SELECT COUNT(*) as count FROM schedules 
                WHERE user_id = ? AND DATE(start_time) = ?
            """, (user_id, today))
            today_schedules = cursor.fetchone()["count"]

            # 今日提醒
            cursor.execute("""
                SELECT COUNT(*) as count FROM reminders 
                WHERE user_id = ? AND is_completed = 0 AND DATE(remind_at) = ?
            """, (user_id, today))
            today_reminders = cursor.fetchone()["count"]

            # 笔记总数
            cursor.execute("""
                SELECT COUNT(*) as count FROM notes WHERE user_id = ?
            """, (user_id,))
            total_notes = cursor.fetchone()["count"]

            return {
                "pending_todos": pending_todos,
                "today_schedules": today_schedules,
                "today_reminders": today_reminders,
                "total_notes": total_notes
            }


# 全局数据库实例
db = Database()
