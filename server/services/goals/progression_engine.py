"""Progression engine for automatically adjusting habit difficulty."""

from datetime import date, timedelta
from typing import List, Dict, Optional

from ...logging_config import logger
from .database import get_goals_database
from .habit_manager import get_habit_manager
from .progress_tracker import get_progress_tracker
from .context_manager import get_context_manager
from .models import Habit


class ProgressionEngine:
    """Manages progressive difficulty scaling for habits."""

    def __init__(self):
        self._db = get_goals_database()
        self._habit_manager = get_habit_manager()
        self._progress_tracker = get_progress_tracker()
        self._context_manager = get_context_manager()

    def evaluate_and_progress_habits(
        self, user_id: str = "default_user"
    ) -> Dict[int, str]:
        """
        Evaluate all habits and adjust difficulty based on performance.
        Should be run weekly (Sunday night or Monday morning).
        
        Returns:
            Dictionary mapping habit_id to progression decision message
        """
        habits = self._habit_manager.list_habits(user_id, active_only=True)
        results = {}
        
        for habit in habits:
            decision = self._evaluate_habit(habit, user_id)
            results[habit.id] = decision
            logger.info(
                f"Habit progression evaluated",
                extra={
                    "habit_id": habit.id,
                    "habit_name": habit.name,
                    "decision": decision,
                },
            )
        
        return results

    def _evaluate_habit(self, habit: Habit, user_id: str) -> str:
        """
        Evaluate a single habit and potentially progress it.
        
        Returns:
            String describing the progression decision
        """
        # Check if at target already
        if habit.current_frequency >= habit.target_frequency:
            return "Already at target frequency"
        
        # Calculate time since progression started
        days_at_current_level = (date.today() - habit.progression_start_date).days
        weeks_at_current_level = days_at_current_level // 7
        
        # Need at least 2 weeks at current level
        if weeks_at_current_level < 2:
            return f"Only {weeks_at_current_level} week(s) at current level, need 2"
        
        # Get performance for last 2 weeks
        week1_start = date.today() - timedelta(days=13)
        week1_end = date.today() - timedelta(days=7)
        week2_start = date.today() - timedelta(days=6)
        week2_end = date.today()
        
        week1_entries = self._progress_tracker.get_progress_range(
            habit.id, week1_start, week1_end
        )
        week2_entries = self._progress_tracker.get_progress_range(
            habit.id, week2_start, week2_end
        )
        
        # Filter out days with legitimate contexts (sick, exams, etc.)
        week1_valid = self._filter_contextual_days(week1_entries, habit.id, user_id)
        week2_valid = self._filter_contextual_days(week2_entries, habit.id, user_id)
        
        # Calculate success rates
        week1_completed = sum(1 for e in week1_valid if e.completed)
        week2_completed = sum(1 for e in week2_valid if e.completed)
        
        total_completed = week1_completed + week2_completed
        total_expected = habit.current_frequency * 2  # 2 weeks
        
        if total_expected == 0:
            return "No expected completions"
        
        success_rate = (total_completed / total_expected) * 100
        
        # Decision logic
        if success_rate >= 80:
            # Increase difficulty
            new_frequency = self._calculate_next_frequency(
                habit.current_frequency, habit.target_frequency
            )
            
            self._habit_manager.update_habit(
                habit.id,
                user_id=user_id,
                current_frequency=new_frequency,
                progression_start_date=date.today(),
            )
            
            return f"Increased from {habit.current_frequency}x to {new_frequency}x per week (success rate: {success_rate:.1f}%)"
        
        elif success_rate < 50:
            # Consider decreasing or maintaining
            if habit.current_frequency > 1:
                # Decrease slightly
                new_frequency = max(1, habit.current_frequency - 1)
                self._habit_manager.update_habit(
                    habit.id,
                    user_id=user_id,
                    current_frequency=new_frequency,
                    progression_start_date=date.today(),
                )
                return f"Decreased from {habit.current_frequency}x to {new_frequency}x per week (success rate: {success_rate:.1f}%)"
            else:
                # Already at minimum, maintain
                return f"Maintaining at {habit.current_frequency}x per week (success rate: {success_rate:.1f}%)"
        else:
            # Between 50-80%, maintain current level
            return f"Maintaining at {habit.current_frequency}x per week (success rate: {success_rate:.1f}%)"

    def _filter_contextual_days(
        self, entries: List, habit_id: int, user_id: str
    ) -> List:
        """
        Filter out entries from days with legitimate excuses (active contexts).
        
        Returns:
            Filtered list of entries
        """
        # Get all contexts for this habit
        contexts = self._context_manager.get_contexts_for_habit(habit_id, user_id)
        
        if not contexts:
            return entries
        
        # Build set of dates covered by contexts
        contextual_dates = set()
        for context in contexts:
            current = context.start_date
            end = context.resolved_date or date.today()
            while current <= end:
                contextual_dates.add(current)
                current += timedelta(days=1)
        
        # Filter entries
        return [e for e in entries if e.date not in contextual_dates]

    def _calculate_next_frequency(
        self, current: int, target: int
    ) -> int:
        """
        Calculate the next frequency level.
        Progresses in steps: typically +2 per progression.
        """
        if current >= target:
            return target
        
        # Increase by 2, but don't exceed target
        next_freq = min(current + 2, target)
        return next_freq

    def get_progression_status(
        self, habit_id: int, user_id: str = "default_user"
    ) -> Dict:
        """
        Get progression status for a habit.
        
        Returns:
            Dictionary with progression information
        """
        habit = self._habit_manager.get_habit(habit_id, user_id)
        
        if not habit:
            return {"error": "Habit not found"}
        
        days_at_level = (date.today() - habit.progression_start_date).days
        weeks_at_level = days_at_level // 7
        
        # Get recent performance
        recent_entries = self._progress_tracker.get_recent_progress(habit_id, 14)
        completed = sum(1 for e in recent_entries if e.completed)
        expected = habit.current_frequency * 2  # 2 weeks
        
        success_rate = (completed / expected * 100) if expected > 0 else 0
        
        return {
            "habit_id": habit_id,
            "habit_name": habit.name,
            "current_frequency": habit.current_frequency,
            "target_frequency": habit.target_frequency,
            "weeks_at_current_level": weeks_at_level,
            "success_rate": success_rate,
            "progress_percentage": (habit.current_frequency / habit.target_frequency * 100),
            "ready_for_evaluation": weeks_at_level >= 2,
        }


# Singleton instance
_progression_engine: Optional[ProgressionEngine] = None


def get_progression_engine() -> ProgressionEngine:
    """Get the singleton progression engine instance."""
    global _progression_engine
    if _progression_engine is None:
        _progression_engine = ProgressionEngine()
    return _progression_engine


__all__ = ["ProgressionEngine", "get_progression_engine"]

