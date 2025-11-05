"""Context memory management for tracking user situations (sick, exams, etc.)."""

import json
from datetime import datetime, date, timedelta
from typing import List, Optional

from ...logging_config import logger
from .database import get_goals_database
from .models import ContextMemory


class ContextManager:
    """Manages context memory for user situations."""

    def __init__(self):
        self._db = get_goals_database()

    def create_context(
        self,
        context_type: str,
        description: str,
        user_id: str = "default_user",
        expected_end_date: Optional[date] = None,
        check_in_frequency_days: Optional[int] = None,
        related_habits: Optional[List[int]] = None,
    ) -> ContextMemory:
        """
        Create a new context memory entry.
        
        Args:
            context_type: Type of context (sick/exam_period/injury/travel)
            description: Description of the situation
            user_id: User identifier
            expected_end_date: When the context is expected to end (required for exams, optional for sickness)
            check_in_frequency_days: How often to check (1-2 for sickness, None for dated events)
            related_habits: List of habit IDs affected by this context
            
        Returns:
            Created ContextMemory
        """
        if related_habits is None:
            related_habits = []
        
        now = datetime.utcnow()
        today = date.today()
        
        # Set default check-in frequency based on context type
        if check_in_frequency_days is None:
            if context_type in ["sick", "injury"]:
                check_in_frequency_days = 1  # Check daily for health issues
            elif context_type in ["exam_period", "travel"]:
                check_in_frequency_days = None  # No periodic checks for dated events
        
        sql = """
        INSERT INTO context_memory (
            user_id, context_type, description, start_date, expected_end_date,
            check_in_frequency_days, last_checked_at, related_habits, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self._db.execute(
            sql,
            (
                user_id,
                context_type,
                description,
                today.isoformat(),
                expected_end_date.isoformat() if expected_end_date else None,
                check_in_frequency_days,
                now.isoformat(),
                json.dumps(related_habits),
                now.isoformat(),
            ),
        )
        
        row = self._db.fetch_one(
            "SELECT * FROM context_memory WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        
        return self._row_to_context(row)

    def get_context(self, context_id: int, user_id: str = "default_user") -> Optional[ContextMemory]:
        """Get a context memory by ID."""
        row = self._db.fetch_one(
            "SELECT * FROM context_memory WHERE id = ? AND user_id = ?",
            (context_id, user_id),
        )
        return self._row_to_context(row) if row else None

    def get_active_contexts(self, user_id: str = "default_user") -> List[ContextMemory]:
        """Get all active (unresolved) contexts for a user."""
        today = date.today()
        
        # Get unresolved contexts
        rows = self._db.fetch_all(
            """
            SELECT * FROM context_memory 
            WHERE user_id = ? AND resolved = 0
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        
        contexts = [self._row_to_context(row) for row in rows]
        
        # Auto-resolve contexts that have passed their end date
        for context in contexts[:]:  # Copy list to modify during iteration
            if context.expected_end_date and context.expected_end_date < today:
                self.resolve_context(context.id, user_id)
                contexts.remove(context)
        
        return contexts

    def get_contexts_needing_checkin(self, user_id: str = "default_user") -> List[ContextMemory]:
        """
        Get contexts that need a check-in based on their frequency.
        
        Returns:
            List of contexts that should be checked on
        """
        contexts = self.get_active_contexts(user_id)
        needing_checkin = []
        
        now = datetime.utcnow()
        
        for context in contexts:
            # Skip if no check-in frequency (dated events)
            if context.check_in_frequency_days is None:
                continue
            
            # Check if enough time has passed since last check
            if context.last_checked_at:
                time_since_check = now - context.last_checked_at
                if time_since_check.days >= context.check_in_frequency_days:
                    needing_checkin.append(context)
            else:
                # Never checked, add it
                needing_checkin.append(context)
        
        return needing_checkin

    def update_context_check(self, context_id: int, user_id: str = "default_user") -> bool:
        """Update the last checked timestamp for a context."""
        now = datetime.utcnow()
        cursor = self._db.execute(
            """
            UPDATE context_memory 
            SET last_checked_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (now.isoformat(), context_id, user_id),
        )
        return cursor.rowcount > 0

    def resolve_context(
        self, context_id: int, user_id: str = "default_user"
    ) -> bool:
        """Mark a context as resolved."""
        today = date.today()
        cursor = self._db.execute(
            """
            UPDATE context_memory 
            SET resolved = 1, resolved_date = ?
            WHERE id = ? AND user_id = ?
            """,
            (today.isoformat(), context_id, user_id),
        )
        return cursor.rowcount > 0

    def get_contexts_for_habit(
        self, habit_id: int, user_id: str = "default_user"
    ) -> List[ContextMemory]:
        """Get active contexts that affect a specific habit."""
        active_contexts = self.get_active_contexts(user_id)
        return [c for c in active_contexts if habit_id in c.related_habits]

    def _row_to_context(self, row) -> ContextMemory:
        """Convert database row to ContextMemory model."""
        return ContextMemory(
            id=row["id"],
            user_id=row["user_id"],
            context_type=row["context_type"],
            description=row["description"],
            start_date=date.fromisoformat(row["start_date"]),
            expected_end_date=(
                date.fromisoformat(row["expected_end_date"])
                if row["expected_end_date"]
                else None
            ),
            check_in_frequency_days=row["check_in_frequency_days"],
            last_checked_at=(
                datetime.fromisoformat(row["last_checked_at"])
                if row["last_checked_at"]
                else None
            ),
            resolved=bool(row["resolved"]),
            resolved_date=(
                date.fromisoformat(row["resolved_date"])
                if row["resolved_date"]
                else None
            ),
            related_habits=json.loads(row["related_habits"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )


# Singleton instance
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get the singleton context manager instance."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


__all__ = ["ContextManager", "get_context_manager"]

