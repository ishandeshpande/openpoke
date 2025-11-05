"""Database schema and connection management for goals system."""

import sqlite3
import threading
from pathlib import Path
from typing import Optional

from ...logging_config import logger


class GoalsDatabase:
    """Manages SQLite database connection and schema for goals system."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._ensure_directory()
        self._ensure_schema()

    def _ensure_directory(self) -> None:
        """Ensure the database directory exists."""
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.warning(
                "goals database directory creation failed",
                extra={"error": str(exc)},
            )

    def _connect(self) -> sqlite3.Connection:
        """Create a new database connection."""
        conn = sqlite3.connect(self._db_path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Create database tables if they don't exist."""
        schema_sql = """
        -- Habits table
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            name TEXT NOT NULL,
            description TEXT,
            target_frequency INTEGER NOT NULL,
            current_frequency INTEGER NOT NULL,
            check_in_time TEXT NOT NULL,
            follow_up_delay_minutes INTEGER NOT NULL DEFAULT 60,
            created_at TEXT NOT NULL,
            progression_start_date TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );

        -- Progress log table
        CREATE TABLE IF NOT EXISTS progress_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            completed INTEGER NOT NULL,
            excuse_given TEXT,
            excuse_category TEXT,
            checked_in_at TEXT NOT NULL,
            agent_message TEXT,
            user_response TEXT,
            FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
        );

        -- Context memory table
        CREATE TABLE IF NOT EXISTS context_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            context_type TEXT NOT NULL,
            description TEXT NOT NULL,
            start_date TEXT NOT NULL,
            expected_end_date TEXT,
            check_in_frequency_days INTEGER,
            last_checked_at TEXT,
            resolved INTEGER NOT NULL DEFAULT 0,
            resolved_date TEXT,
            related_habits TEXT,
            created_at TEXT NOT NULL
        );

        -- Consistency score table
        CREATE TABLE IF NOT EXISTS consistency_score (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            current_score REAL NOT NULL DEFAULT 50.0,
            peak_score REAL NOT NULL DEFAULT 50.0,
            updated_at TEXT NOT NULL,
            score_history TEXT NOT NULL DEFAULT '[]'
        );

        -- Indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_habits_user_id ON habits(user_id);
        CREATE INDEX IF NOT EXISTS idx_habits_active ON habits(active);
        CREATE INDEX IF NOT EXISTS idx_progress_log_habit_date ON progress_log(habit_id, date);
        CREATE INDEX IF NOT EXISTS idx_progress_log_date ON progress_log(date);
        CREATE INDEX IF NOT EXISTS idx_context_memory_user_resolved ON context_memory(user_id, resolved);
        CREATE INDEX IF NOT EXISTS idx_consistency_score_user ON consistency_score(user_id);
        """

        with self._lock, self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.executescript(schema_sql)
            logger.info("Goals database schema ensured")

    def get_connection(self) -> sqlite3.Connection:
        """Get a new database connection."""
        return self._connect()

    def execute(self, sql: str, params=None):
        """Execute a SQL statement with thread safety."""
        with self._lock, self._connect() as conn:
            if params:
                return conn.execute(sql, params)
            return conn.execute(sql)

    def execute_many(self, sql: str, params_list):
        """Execute a SQL statement multiple times with different parameters."""
        with self._lock, self._connect() as conn:
            return conn.executemany(sql, params_list)

    def fetch_one(self, sql: str, params=None) -> Optional[sqlite3.Row]:
        """Fetch a single row."""
        with self._lock, self._connect() as conn:
            if params:
                return conn.execute(sql, params).fetchone()
            return conn.execute(sql).fetchone()

    def fetch_all(self, sql: str, params=None) -> list:
        """Fetch all rows."""
        with self._lock, self._connect() as conn:
            if params:
                return conn.execute(sql, params).fetchall()
            return conn.execute(sql).fetchall()


# Singleton instance
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_GOALS_DB_PATH = _DATA_DIR / "goals.db"

_goals_db: Optional[GoalsDatabase] = None


def get_goals_database() -> GoalsDatabase:
    """Get the singleton goals database instance."""
    global _goals_db
    if _goals_db is None:
        _goals_db = GoalsDatabase(_GOALS_DB_PATH)
    return _goals_db


__all__ = ["GoalsDatabase", "get_goals_database"]

