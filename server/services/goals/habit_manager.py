"""Habit management service."""

import json
from datetime import datetime, date
from typing import List, Optional
from pathlib import Path

from ...logging_config import logger
from .database import get_goals_database
from .models import Habit


class HabitManager:
    """Manages CRUD operations for habits."""

    def __init__(self):
        self._db = get_goals_database()

    def create_habit(
        self,
        name: str,
        target_frequency: int,
        check_in_time: str = "anytime",
        description: Optional[str] = None,
        user_id: str = "default_user",
        follow_up_delay_minutes: int = 60,
    ) -> Habit:
        """
        Create a new habit with progressive starting frequency.
        
        Args:
            name: Habit name (e.g., "Cook dinner")
            target_frequency: Final goal frequency per week
            check_in_time: Time to check in (HH:MM format or "anytime")
            description: Optional description
            user_id: User identifier
            follow_up_delay_minutes: Minutes to wait before follow-up
            
        Returns:
            Created Habit object
        """
        # Calculate starting frequency (40-50% of target)
        starting_frequency = max(1, int(target_frequency * 0.45))
        
        now = datetime.utcnow()
        today = date.today()
        
        sql = """
        INSERT INTO habits (
            user_id, name, description, target_frequency, current_frequency,
            check_in_time, follow_up_delay_minutes, created_at, progression_start_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self._db.execute(
            sql,
            (
                user_id,
                name,
                description,
                target_frequency,
                starting_frequency,
                check_in_time,
                follow_up_delay_minutes,
                now.isoformat(),
                today.isoformat(),
            ),
        )
        
        # Fetch the created habit
        row = self._db.fetch_one(
            "SELECT * FROM habits WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        
        return self._row_to_habit(row)

    def get_habit(self, habit_id: int, user_id: str = "default_user") -> Optional[Habit]:
        """Get a habit by ID."""
        row = self._db.fetch_one(
            "SELECT * FROM habits WHERE id = ? AND user_id = ?",
            (habit_id, user_id),
        )
        return self._row_to_habit(row) if row else None

    def list_habits(self, user_id: str = "default_user", active_only: bool = True) -> List[Habit]:
        """List all habits for a user."""
        if active_only:
            rows = self._db.fetch_all(
                "SELECT * FROM habits WHERE user_id = ? AND active = 1 ORDER BY id",
                (user_id,),
            )
        else:
            rows = self._db.fetch_all(
                "SELECT * FROM habits WHERE user_id = ? ORDER BY id",
                (user_id,),
            )
        return [self._row_to_habit(row) for row in rows]

    def update_habit(
        self,
        habit_id: int,
        user_id: str = "default_user",
        name: Optional[str] = None,
        description: Optional[str] = None,
        target_frequency: Optional[int] = None,
        current_frequency: Optional[int] = None,
        check_in_time: Optional[str] = None,
        follow_up_delay_minutes: Optional[int] = None,
        progression_start_date: Optional[date] = None,
    ) -> bool:
        """Update a habit's fields."""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if target_frequency is not None:
            updates.append("target_frequency = ?")
            params.append(target_frequency)
        if current_frequency is not None:
            updates.append("current_frequency = ?")
            params.append(current_frequency)
        if check_in_time is not None:
            updates.append("check_in_time = ?")
            params.append(check_in_time)
        if follow_up_delay_minutes is not None:
            updates.append("follow_up_delay_minutes = ?")
            params.append(follow_up_delay_minutes)
        if progression_start_date is not None:
            updates.append("progression_start_date = ?")
            params.append(progression_start_date.isoformat())
        
        if not updates:
            return False
        
        params.extend([habit_id, user_id])
        sql = f"UPDATE habits SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
        
        cursor = self._db.execute(sql, params)
        return cursor.rowcount > 0

    def delete_habit(self, habit_id: int, user_id: str = "default_user") -> bool:
        """Soft delete a habit by marking it inactive."""
        cursor = self._db.execute(
            "UPDATE habits SET active = 0 WHERE id = ? AND user_id = ?",
            (habit_id, user_id),
        )
        return cursor.rowcount > 0

    def calculate_starting_frequency(self, target_frequency: int) -> int:
        """Calculate starting frequency for a habit (40-50% of target)."""
        return max(1, int(target_frequency * 0.45))

    def _row_to_habit(self, row) -> Habit:
        """Convert database row to Habit model."""
        return Habit(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            description=row["description"],
            target_frequency=row["target_frequency"],
            current_frequency=row["current_frequency"],
            check_in_time=row["check_in_time"],
            follow_up_delay_minutes=row["follow_up_delay_minutes"],
            created_at=datetime.fromisoformat(row["created_at"]),
            progression_start_date=date.fromisoformat(row["progression_start_date"]),
            active=bool(row["active"]),
        )


# Singleton instance
_habit_manager: Optional[HabitManager] = None


def get_habit_manager() -> HabitManager:
    """Get the singleton habit manager instance."""
    global _habit_manager
    if _habit_manager is None:
        _habit_manager = HabitManager()
    return _habit_manager


__all__ = ["HabitManager", "get_habit_manager"]

