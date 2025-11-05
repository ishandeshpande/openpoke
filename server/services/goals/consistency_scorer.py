"""Consistency score calculation for tracking overall user performance."""

import json
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List

from ...logging_config import logger
from .database import get_goals_database
from .habit_manager import get_habit_manager
from .progress_tracker import get_progress_tracker
from .models import ConsistencyScore


class ConsistencyScorer:
    """Calculates and manages user consistency scores."""

    def __init__(self):
        self._db = get_goals_database()
        self._habit_manager = get_habit_manager()
        self._progress_tracker = get_progress_tracker()

    def get_or_create_score(self, user_id: str = "default_user") -> ConsistencyScore:
        """Get existing score or create new one."""
        row = self._db.fetch_one(
            "SELECT * FROM consistency_score WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        
        if row:
            return self._row_to_score(row)
        
        # Create new score
        now = datetime.utcnow()
        self._db.execute(
            """
            INSERT INTO consistency_score (user_id, current_score, peak_score, updated_at, score_history)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, 50.0, 50.0, now.isoformat(), "[]"),
        )
        
        row = self._db.fetch_one(
            "SELECT * FROM consistency_score WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        return self._row_to_score(row)

    def calculate_and_update_score(
        self, user_id: str = "default_user", reason: str = "daily_update"
    ) -> ConsistencyScore:
        """
        Calculate current consistency score and update database.
        
        Score calculation (0-100):
        - Base: 50 points
        - Completion rate: 0-40 points
        - Streak bonus: 0-20 points
        - Progression bonus: 0-15 points
        - Excuse grace: 0-10 points
        - Trend modifier: -15 to +15 points
        
        Args:
            user_id: User identifier
            reason: Reason for score update
            
        Returns:
            Updated ConsistencyScore
        """
        current_score_obj = self.get_or_create_score(user_id)
        habits = self._habit_manager.list_habits(user_id, active_only=True)
        
        if not habits:
            # No habits yet, maintain default score
            return current_score_obj
        
        # Calculate components
        completion_points = self._calculate_completion_points(habits)
        streak_points = self._calculate_streak_points(habits)
        progression_points = self._calculate_progression_points(habits)
        excuse_grace = self._calculate_excuse_grace(habits)
        trend_modifier = self._calculate_trend_modifier(habits)
        
        # Calculate final score
        base_score = 50.0
        final_score = (
            base_score
            + completion_points
            + streak_points
            + progression_points
            + excuse_grace
            + trend_modifier
        )
        
        # Clamp to 0-100
        final_score = max(0.0, min(100.0, final_score))
        
        # Update peak if necessary
        peak_score = max(current_score_obj.peak_score, final_score)
        
        # Add to history
        history = current_score_obj.score_history.copy()
        history.append({
            "date": date.today().isoformat(),
            "score": round(final_score, 1),
            "reason": reason,
        })
        
        # Keep last 90 days of history
        if len(history) > 90:
            history = history[-90:]
        
        # Update database
        now = datetime.utcnow()
        self._db.execute(
            """
            UPDATE consistency_score
            SET current_score = ?, peak_score = ?, updated_at = ?, score_history = ?
            WHERE user_id = ?
            """,
            (final_score, peak_score, now.isoformat(), json.dumps(history), user_id),
        )
        
        logger.info(
            f"Consistency score updated",
            extra={
                "user_id": user_id,
                "score": final_score,
                "components": {
                    "completion": completion_points,
                    "streak": streak_points,
                    "progression": progression_points,
                    "excuse_grace": excuse_grace,
                    "trend": trend_modifier,
                },
            },
        )
        
        return self.get_or_create_score(user_id)

    def _calculate_completion_points(self, habits: List) -> float:
        """
        Calculate completion rate points (0-40).
        Weighted by difficulty (current vs target frequency).
        """
        if not habits:
            return 0.0
        
        total_weighted_completion = 0.0
        
        for habit in habits:
            # Get recent completion rate
            entries = self._progress_tracker.get_recent_progress(habit.id, 14)
            if not entries:
                continue
            
            completed = sum(1 for e in entries if e.completed)
            total = len(entries)
            completion_rate = completed / total if total > 0 else 0
            
            # Calculate difficulty multiplier (harder habits worth more)
            difficulty_multiplier = habit.current_frequency / habit.target_frequency
            difficulty_multiplier = max(0.5, difficulty_multiplier)  # Minimum 0.5
            
            weighted = completion_rate * difficulty_multiplier
            total_weighted_completion += weighted
        
        avg_weighted_completion = total_weighted_completion / len(habits)
        return avg_weighted_completion * 40

    def _calculate_streak_points(self, habits: List) -> float:
        """
        Calculate streak bonus points (0-20).
        Based on longest current streak across all habits.
        """
        if not habits:
            return 0.0
        
        max_streak = 0
        for habit in habits:
            streak = self._progress_tracker._calculate_streak(habit.id)
            max_streak = max(max_streak, streak)
        
        # Max points at 30-day streak
        streak_points = min(max_streak / 30 * 20, 20)
        return streak_points

    def _calculate_progression_points(self, habits: List) -> float:
        """
        Calculate progression bonus points (0-15).
        Based on average progress toward target across habits.
        """
        if not habits:
            return 0.0
        
        total_progression = 0.0
        for habit in habits:
            progression_ratio = habit.current_frequency / habit.target_frequency
            total_progression += progression_ratio
        
        avg_progression = total_progression / len(habits)
        return avg_progression * 15

    def _calculate_excuse_grace(self, habits: List) -> float:
        """
        Calculate excuse grace points (0-10).
        Rewards having legitimate excuses vs just failing.
        """
        if not habits:
            return 0.0
        
        total_failures = 0
        legitimate_excuses = 0
        
        for habit in habits:
            entries = self._progress_tracker.get_recent_progress(habit.id, 14)
            for entry in entries:
                if not entry.completed:
                    total_failures += 1
                    if entry.excuse_category in ["sick", "exam", "injury"]:
                        legitimate_excuses += 1
        
        if total_failures == 0:
            return 10.0  # Perfect, give full points
        
        excuse_ratio = legitimate_excuses / total_failures
        return excuse_ratio * 10

    def _calculate_trend_modifier(self, habits: List) -> float:
        """
        Calculate recent trend modifier (-15 to +15).
        Compares last 7 days to previous 7 days.
        """
        if not habits:
            return 0.0
        
        # Calculate completion rates for both weeks
        current_week_rate = 0.0
        previous_week_rate = 0.0
        
        for habit in habits:
            # Current week (last 7 days)
            current_entries = self._progress_tracker.get_recent_progress(habit.id, 7)
            current_completed = sum(1 for e in current_entries if e.completed)
            current_total = len(current_entries)
            current_rate = current_completed / current_total if current_total > 0 else 0
            current_week_rate += current_rate
            
            # Previous week (days 8-14)
            all_entries = self._progress_tracker.get_recent_progress(habit.id, 14)
            previous_entries = [e for e in all_entries if e.date < (date.today() - timedelta(days=7))]
            previous_completed = sum(1 for e in previous_entries if e.completed)
            previous_total = len(previous_entries)
            previous_rate = previous_completed / previous_total if previous_total > 0 else 0
            previous_week_rate += previous_rate
        
        # Average across habits
        current_week_rate /= len(habits)
        previous_week_rate /= len(habits)
        
        # Calculate modifier
        rate_change = current_week_rate - previous_week_rate
        trend_modifier = rate_change * 50  # Scale to -15 to +15 range
        
        return max(-15.0, min(15.0, trend_modifier))

    def get_score_breakdown(self, user_id: str = "default_user") -> Dict:
        """
        Get detailed breakdown of score components for debugging/display.
        
        Returns:
            Dictionary with score breakdown
        """
        habits = self._habit_manager.list_habits(user_id, active_only=True)
        score_obj = self.get_or_create_score(user_id)
        
        breakdown = {
            "current_score": score_obj.current_score,
            "peak_score": score_obj.peak_score,
            "components": {
                "base": 50.0,
                "completion": self._calculate_completion_points(habits),
                "streak": self._calculate_streak_points(habits),
                "progression": self._calculate_progression_points(habits),
                "excuse_grace": self._calculate_excuse_grace(habits),
                "trend": self._calculate_trend_modifier(habits),
            },
            "updated_at": score_obj.updated_at.isoformat(),
        }
        
        return breakdown

    def _row_to_score(self, row) -> ConsistencyScore:
        """Convert database row to ConsistencyScore model."""
        return ConsistencyScore(
            id=row["id"],
            user_id=row["user_id"],
            current_score=float(row["current_score"]),
            peak_score=float(row["peak_score"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            score_history=json.loads(row["score_history"]),
        )


# Singleton instance
_consistency_scorer: Optional[ConsistencyScorer] = None


def get_consistency_scorer() -> ConsistencyScorer:
    """Get the singleton consistency scorer instance."""
    global _consistency_scorer
    if _consistency_scorer is None:
        _consistency_scorer = ConsistencyScorer()
    return _consistency_scorer


__all__ = ["ConsistencyScorer", "get_consistency_scorer"]

