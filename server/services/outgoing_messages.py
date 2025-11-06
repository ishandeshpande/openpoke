"""Service for managing outgoing messages that need to be sent via iMessage."""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..config import DATA_DIR
from ..logging_config import logger


_OUTGOING_DB_PATH = DATA_DIR / "outgoing_messages.db"


@dataclass
class OutgoingMessage:
    """Represents a message that needs to be sent to a user."""

    id: int
    recipient: str
    message: str
    created_at: str
    sent_at: Optional[str] = None
    error: Optional[str] = None


class OutgoingMessageQueue:
    """Queue for managing outgoing messages that need to be sent via iMessage."""

    def __init__(self, db_path: Path = _OUTGOING_DB_PATH):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create the database schema if it doesn't exist."""
        with self._lock:
            try:
                self._db_path.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(str(self._db_path))
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS outgoing_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recipient TEXT NOT NULL,
                        message TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        sent_at TEXT,
                        error TEXT
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sent_at
                    ON outgoing_messages(sent_at)
                """)
                conn.commit()
                conn.close()
            except Exception as exc:
                logger.error(f"Failed to create outgoing messages schema: {exc}")
                raise

    def enqueue(self, recipient: str, message: str) -> int:
        """Add a message to the queue to be sent."""
        with self._lock:
            try:
                conn = sqlite3.connect(str(self._db_path))
                cursor = conn.cursor()

                # Check for duplicate pending messages (same recipient and message, not sent yet)
                cursor.execute(
                    """
                    SELECT id FROM outgoing_messages
                    WHERE recipient = ? AND message = ? AND sent_at IS NULL
                    """,
                    (recipient, message)
                )
                existing = cursor.fetchone()
                if existing:
                    logger.info(
                        f"Duplicate message detected, skipping enqueue",
                        extra={
                            "existing_id": existing[0],
                            "recipient": recipient,
                            "message_preview": message[:50] + "..." if len(message) > 50 else message
                        }
                    )
                    conn.close()
                    return existing[0]

                now = datetime.now(timezone.utc).isoformat()
                cursor.execute(
                    """
                    INSERT INTO outgoing_messages (recipient, message, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (recipient, message, now)
                )
                message_id = cursor.lastrowid
                conn.commit()
                conn.close()

                logger.info(
                    f"Enqueued outgoing message",
                    extra={
                        "message_id": message_id,
                        "recipient": recipient,
                        "message_preview": message[:50] + "..." if len(message) > 50 else message
                    }
                )

                return message_id
            except Exception as exc:
                logger.error(f"Failed to enqueue message: {exc}")
                raise

    def get_pending(self, limit: int = 10) -> List[OutgoingMessage]:
        """Get pending messages that haven't been sent yet."""
        with self._lock:
            try:
                conn = sqlite3.connect(str(self._db_path))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, recipient, message, created_at, sent_at, error
                    FROM outgoing_messages
                    WHERE sent_at IS NULL
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (limit,)
                )
                rows = cursor.fetchall()
                conn.close()

                return [
                    OutgoingMessage(
                        id=row["id"],
                        recipient=row["recipient"],
                        message=row["message"],
                        created_at=row["created_at"],
                        sent_at=row["sent_at"],
                        error=row["error"]
                    )
                    for row in rows
                ]
            except Exception as exc:
                logger.error(f"Failed to get pending messages: {exc}")
                raise

    def mark_sent(self, message_id: int) -> None:
        """Mark a message as successfully sent."""
        with self._lock:
            try:
                conn = sqlite3.connect(str(self._db_path))
                now = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    """
                    UPDATE outgoing_messages
                    SET sent_at = ?
                    WHERE id = ?
                    """,
                    (now, message_id)
                )
                conn.commit()
                conn.close()

                logger.info(f"Marked message {message_id} as sent")
            except Exception as exc:
                logger.error(f"Failed to mark message as sent: {exc}")
                raise

    def mark_failed(self, message_id: int, error: str) -> None:
        """Mark a message as failed with an error."""
        with self._lock:
            try:
                conn = sqlite3.connect(str(self._db_path))
                now = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    """
                    UPDATE outgoing_messages
                    SET sent_at = ?, error = ?
                    WHERE id = ?
                    """,
                    (now, error, message_id)
                )
                conn.commit()
                conn.close()

                logger.warning(f"Marked message {message_id} as failed: {error}")
            except Exception as exc:
                logger.error(f"Failed to mark message as failed: {exc}")
                raise

    def clear_all(self) -> None:
        """Clear all messages from the queue (for testing)."""
        with self._lock:
            try:
                conn = sqlite3.connect(str(self._db_path))
                conn.execute("DELETE FROM outgoing_messages")
                conn.commit()
                conn.close()
                logger.info("Cleared all outgoing messages")
            except Exception as exc:
                logger.error(f"Failed to clear outgoing messages: {exc}")
                raise


# Singleton instance
_outgoing_queue: Optional[OutgoingMessageQueue] = None


def get_outgoing_message_queue() -> OutgoingMessageQueue:
    """Get the singleton outgoing message queue instance."""
    global _outgoing_queue
    if _outgoing_queue is None:
        _outgoing_queue = OutgoingMessageQueue()
    return _outgoing_queue


__all__ = ["OutgoingMessage", "OutgoingMessageQueue", "get_outgoing_message_queue"]
