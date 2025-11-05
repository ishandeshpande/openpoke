"""Data models for goals system."""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Habit(BaseModel):
    """Habit data model."""
    id: Optional[int] = None
    user_id: str = "default_user"
    name: str
    description: Optional[str] = None
    target_frequency: int  # Times per week
    current_frequency: int  # Current progressive target
    check_in_time: str  # "HH:MM" or "anytime"
    follow_up_delay_minutes: int = 60
    created_at: datetime
    progression_start_date: date
    active: bool = True


class ProgressEntry(BaseModel):
    """Progress log entry."""
    id: Optional[int] = None
    habit_id: int
    date: date
    completed: bool
    excuse_given: Optional[str] = None
    excuse_category: Optional[str] = None  # sick/exam/travel/other
    checked_in_at: datetime
    agent_message: Optional[str] = None
    user_response: Optional[str] = None


class ContextMemory(BaseModel):
    """Context memory for user situations."""
    id: Optional[int] = None
    user_id: str = "default_user"
    context_type: str  # sick/exam_period/injury/travel
    description: str
    start_date: date
    expected_end_date: Optional[date] = None
    check_in_frequency_days: Optional[int] = None
    last_checked_at: Optional[datetime] = None
    resolved: bool = False
    resolved_date: Optional[date] = None
    related_habits: List[int] = Field(default_factory=list)  # Habit IDs
    created_at: datetime


class ConsistencyScore(BaseModel):
    """Consistency score tracking."""
    id: Optional[int] = None
    user_id: str = "default_user"
    current_score: float = 50.0
    peak_score: float = 50.0
    updated_at: datetime
    score_history: List[dict] = Field(default_factory=list)


class HabitStats(BaseModel):
    """Statistics for a habit."""
    habit_id: int
    habit_name: str
    current_frequency: int
    target_frequency: int
    completion_rate: float
    recent_completions: int
    recent_attempts: int
    current_streak: int


__all__ = [
    "Habit",
    "ProgressEntry",
    "ContextMemory",
    "ConsistencyScore",
    "HabitStats",
]

