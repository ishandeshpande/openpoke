"""Goals service package for habit tracking and management."""

from .habit_manager import HabitManager, get_habit_manager
from .progress_tracker import ProgressTracker, get_progress_tracker
from .context_manager import ContextManager, get_context_manager
from .progression_engine import ProgressionEngine, get_progression_engine
from .consistency_scorer import ConsistencyScorer, get_consistency_scorer
from .trigger_manager import GoalsTriggerManager, get_goals_trigger_manager
from .onboarding import OnboardingService, get_onboarding_service
from .habit_loader import HabitLoader, get_habit_loader
from .auto_init import auto_initialize_habits
from .database import GoalsDatabase, get_goals_database

__all__ = [
    "HabitManager",
    "get_habit_manager",
    "ProgressTracker",
    "get_progress_tracker",
    "ContextManager",
    "get_context_manager",
    "ProgressionEngine",
    "get_progression_engine",
    "ConsistencyScorer",
    "get_consistency_scorer",
    "GoalsTriggerManager",
    "get_goals_trigger_manager",
    "OnboardingService",
    "get_onboarding_service",
    "HabitLoader",
    "get_habit_loader",
    "auto_initialize_habits",
    "GoalsDatabase",
    "get_goals_database",
]

