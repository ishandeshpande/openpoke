"""Progress tracking service for habit completion logging."""

from datetime import datetime, date, timedelta
from typing import List, Optional

from ...logging_config import logger
from .database import get_goals_database
from .models import ProgressEntry, HabitStats


class ProgressTracker:
    """Tracks habit completion progress."""

    def __init__(self):
        self._db = get_goals_database()

    def log_progress(
        self,
        habit_id: int,
        completed: bool,
        date_of_entry: Optional[date] = None,
        excuse_given: Optional[str] = None,
        excuse_category: Optional[str] = None,
        agent_message: Optional[str] = None,
        user_response: Optional[str] = None,
    ) -> ProgressEntry:
        """
        Log a progress entry for a habit.
        
        Args:
            habit_id: ID of the habit
            completed: Whether the habit was completed
            date_of_entry: Date of the entry (defaults to today)
            excuse_given: Optional excuse text
            excuse_category: Category of excuse (sick/exam/travel/other)
            agent_message: What the AI asked
            user_response: User's response
            
        Returns:
            Created ProgressEntry
        """
        if date_of_entry is None:
            date_of_entry = date.today()
        
        now = datetime.utcnow()
        
        sql = """
        INSERT INTO progress_log (
            habit_id, date, completed, excuse_given, excuse_category,
            checked_in_at, agent_message, user_response
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self._db.execute(
            sql,
            (
                habit_id,
                date_of_entry.isoformat(),
                1 if completed else 0,
                excuse_given,
                excuse_category,
                now.isoformat(),
                agent_message,
                user_response,
            ),
        )
        
        row = self._db.fetch_one(
            "SELECT * FROM progress_log WHERE habit_id = ? ORDER BY id DESC LIMIT 1",
            (habit_id,),
        )
        
        return self._row_to_progress(row)

    def get_progress_for_date(
        self, habit_id: int, target_date: date
    ) -> Optional[ProgressEntry]:
        """Get progress entry for a specific date."""
        row = self._db.fetch_one(
            "SELECT * FROM progress_log WHERE habit_id = ? AND date = ?",
            (habit_id, target_date.isoformat()),
        )
        return self._row_to_progress(row) if row else None

    def get_progress_range(
        self, habit_id: int, start_date: date, end_date: date
    ) -> List[ProgressEntry]:
        """Get progress entries for a date range."""
        rows = self._db.fetch_all(
            """
            SELECT * FROM progress_log 
            WHERE habit_id = ? AND date >= ? AND date <= ?
            ORDER BY date DESC
            """,
            (habit_id, start_date.isoformat(), end_date.isoformat()),
        )
        return [self._row_to_progress(row) for row in rows]

    def get_recent_progress(self, habit_id: int, days: int = 7) -> List[ProgressEntry]:
        """Get recent progress entries."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        return self.get_progress_range(habit_id, start_date, end_date)

    def calculate_completion_rate(
        self, habit_id: int, days: int = 14
    ) -> float:
        """
        Calculate completion rate for a habit over recent days.
        
        Returns:
            Completion rate as a percentage (0-100)
        """
        entries = self.get_recent_progress(habit_id, days)
        if not entries:
            return 0.0
        
        completed = sum(1 for e in entries if e.completed)
        return (completed / len(entries)) * 100

    def get_habit_stats(self, habit_id: int, days: int = 14) -> Optional[HabitStats]:
        """Get statistics for a habit."""
        from .habit_manager import get_habit_manager
        
        habit_manager = get_habit_manager()
        habit = habit_manager.get_habit(habit_id)
        
        if not habit:
            return None
        
        entries = self.get_recent_progress(habit_id, days)
        completed = sum(1 for e in entries if e.completed)
        total = len(entries)
        completion_rate = (completed / total * 100) if total > 0 else 0.0
        
        # Calculate current streak
        streak = self._calculate_streak(habit_id)
        
        return HabitStats(
            habit_id=habit_id,
            habit_name=habit.name,
            current_frequency=habit.current_frequency,
            target_frequency=habit.target_frequency,
            completion_rate=completion_rate,
            recent_completions=completed,
            recent_attempts=total,
            current_streak=streak,
        )

    def _calculate_streak(self, habit_id: int) -> int:
        """Calculate current streak of consecutive days with completion."""
        # Get entries from today backwards
        entries = self.get_recent_progress(habit_id, 90)  # Check last 90 days
        
        if not entries:
            return 0
        
        # Sort by date descending
        entries_by_date = {e.date: e for e in entries}
        
        streak = 0
        current_date = date.today()
        
        # Count backwards from today
        while current_date in entries_by_date:
            if entries_by_date[current_date].completed:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak

    def get_all_progress_today(self, user_id: str = "default_user") -> List[tuple]:
        """
        Get today's progress for all habits.
        
        Returns:
            List of tuples: (habit_id, habit_name, completed)
        """
        today = date.today()
        
        rows = self._db.fetch_all(
            """
            SELECT h.id, h.name, p.completed
            FROM habits h
            LEFT JOIN progress_log p ON h.id = p.habit_id AND p.date = ?
            WHERE h.user_id = ? AND h.active = 1
            ORDER BY h.id
            """,
            (today.isoformat(), user_id),
        )
        
        return [(row["id"], row["name"], bool(row["completed"]) if row["completed"] is not None else None) for row in rows]

    def _row_to_progress(self, row) -> ProgressEntry:
        """Convert database row to ProgressEntry model."""
        return ProgressEntry(
            id=row["id"],
            habit_id=row["habit_id"],
            date=date.fromisoformat(row["date"]),
            completed=bool(row["completed"]),
            excuse_given=row["excuse_given"],
            excuse_category=row["excuse_category"],
            checked_in_at=datetime.fromisoformat(row["checked_in_at"]),
            agent_message=row["agent_message"],
            user_response=row["user_response"],
        )


# Singleton instance
_progress_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """Get the singleton progress tracker instance."""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker


__all__ = ["ProgressTracker", "get_progress_tracker"]

