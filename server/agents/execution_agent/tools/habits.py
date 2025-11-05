"""Habit insight tools for the execution agent."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from server.logging_config import logger
from server.services.goals import (
    get_goals_trigger_manager,
    get_habit_manager,
    get_onboarding_service,
    get_progress_tracker,
    get_consistency_scorer,
)
from server.services.triggers import get_trigger_service


_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "getHabitsOverview",
            "description": (
                "Return the user's current habits with today's status, recent performance "
                "stats, and trigger coverage. Automatically seeds default habits when "
                "none exist so the assistant always has data to share."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier (defaults to 'default_user').",
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "logHabitProgressByName",
            "description": (
                "Log progress for a habit by its name (e.g., 'gym', 'dinner', 'sleep'). "
                "This is the PREFERRED way to mark habits as complete. Uses fuzzy matching "
                "to find the habit by name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "habit_name": {
                        "type": "string",
                        "description": "Name or keyword for the habit (e.g., 'gym', 'dinner', 'sleep', 'cook')",
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Whether the habit was completed (true) or not (false)",
                    },
                    "excuse_text": {
                        "type": "string",
                        "description": "Optional text explaining why the habit wasn't completed",
                    },
                    "excuse_category": {
                        "type": "string",
                        "description": "Category of excuse if applicable (sick/exam/travel/other)",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User identifier (defaults to 'default_user')",
                    },
                },
                "required": ["habit_name", "completed"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "logHabitProgress",
            "description": (
                "Log progress for a habit by its ID. Use logHabitProgressByName instead "
                "unless you already have the exact habit ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "habit_id": {
                        "type": "integer",
                        "description": "ID of the habit to log progress for",
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Whether the habit was completed (true) or not (false)",
                    },
                    "excuse_text": {
                        "type": "string",
                        "description": "Optional text explaining why the habit wasn't completed",
                    },
                    "excuse_category": {
                        "type": "string",
                        "description": "Category of excuse if applicable (sick/exam/travel/other)",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User identifier (defaults to 'default_user')",
                    },
                },
                "required": ["habit_id", "completed"],
                "additionalProperties": False,
            },
        },
    },
]


def get_schemas() -> List[Dict[str, Any]]:
    """Expose tool schemas for registration."""

    return _SCHEMAS


def build_registry(agent_name: str) -> Dict[str, Any]:
    """Build callable registry for habit tools."""

    return {
        "getHabitsOverview": _get_habits_overview_tool,
        "logHabitProgressByName": _log_habit_progress_by_name_tool,
        "logHabitProgress": _log_habit_progress_tool,
    }


def _ensure_habits(user_id: str) -> Tuple[List[Any], bool]:
    """Guarantee at least the default habits exist, returning them.

    Returns a tuple of (habits, initialized_now) where initialized_now is True when
    default habits were created during this call.
    """

    habit_manager = get_habit_manager()
    habits = habit_manager.list_habits(user_id, active_only=True)
    if habits:
        return habits, False

    onboarding = get_onboarding_service()
    try:
        result = onboarding.setup_user_with_goals(user_id=user_id)
        logger.info(
            "Auto-initialized habits for execution agent overview",
            extra={
                "user_id": user_id,
                "created": result.get("habits_created", 0),
            },
        )
    except Exception as exc:
        logger.error(
            "Failed to auto-initialize habits during overview",
            extra={"user_id": user_id, "error": str(exc)},
        )
        return [], False

    return habit_manager.list_habits(user_id, active_only=True), True


def _parse_habit_id(payload: str) -> Optional[int]:
    """Extract habit id from a trigger payload if present."""

    marker = "Habit ID:"
    if marker not in payload:
        return None
    try:
        after = payload.split(marker, 1)[1]
        digits = after.strip().splitlines()[0].strip()
        return int(digits)
    except Exception:  # pragma: no cover - best effort parsing
        return None


def _ensure_triggers(habits: List[Any]) -> Tuple[int, Optional[str]]:
    """Ensure each habit has at least one trigger, returning trigger count and warning."""

    trigger_service = get_trigger_service()
    try:
        records = trigger_service.list_triggers(agent_name="goals-agent")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(
            "Failed to list triggers while building habit overview",
            extra={"error": str(exc)},
        )
        return 0, str(exc)

    existing_habit_ids = {
        habit_id
        for habit_id in (
            _parse_habit_id(record.payload)
            for record in records
        )
        if habit_id is not None
    }

    missing_habit_ids = [h.id for h in habits if h.id not in existing_habit_ids]
    if missing_habit_ids:
        manager = get_goals_trigger_manager()
        for habit_id in missing_habit_ids:
            try:
                habit = next((h for h in habits if h.id == habit_id), None)
                if habit is None:
                    continue
                manager.create_habit_checkin_trigger(
                    habit_id=habit.id,
                    check_in_time=habit.check_in_time,
                    user_id=habit.user_id,
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Failed to backfill trigger for habit",
                    extra={"habit_id": habit_id, "error": str(exc)},
                )

        try:
            records = trigger_service.list_triggers(agent_name="goals-agent")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Failed to refresh trigger list after backfill",
                extra={"error": str(exc)},
            )
            return len(existing_habit_ids), str(exc)

    return len(records), None


def _build_habit_payload(habit, today_summary, stats) -> Dict[str, Any]:
    """Convert Habit + stats into a JSON-safe payload."""

    payload: Dict[str, Any] = {
        "id": habit.id,
        "name": habit.name,
        "description": habit.description,
        "check_in_time": habit.check_in_time,
        "current_frequency": habit.current_frequency,
        "target_frequency": habit.target_frequency,
        "created_at": habit.created_at.isoformat(),
        "progression_start_date": habit.progression_start_date.isoformat(),
    }

    if today_summary is not None:
        payload.update(
            {
                "checked_in_today": True,
                "completed_today": bool(today_summary.completed),
            }
        )
    else:
        payload.update(
            {
                "checked_in_today": False,
                "completed_today": None,
            }
        )

    if stats is not None:
        payload.update(
            {
                "recent_completion_rate": stats.completion_rate,
                "current_streak": stats.current_streak,
                "recent_completions": stats.recent_completions,
                "recent_attempts": stats.recent_attempts,
            }
        )
    else:
        payload.update(
            {
                "recent_completion_rate": 0.0,
                "current_streak": 0,
                "recent_completions": 0,
                "recent_attempts": 0,
            }
        )

    return payload


def _get_habits_overview_tool(*, user_id: str = "default_user") -> Dict[str, Any]:
    """Implementation backing the getHabitsOverview tool."""

    try:
        habits, auto_initialized = _ensure_habits(user_id)
        if not habits:
            return {
                "success": False,
                "error": "No habits are configured for the user and initialization failed.",
            }

        tracker = get_progress_tracker()
        today = date.today()

        habit_payloads: List[Dict[str, Any]] = []
        for habit in habits:
            today_progress = tracker.get_progress_for_date(habit.id, today)
            stats = tracker.get_habit_stats(habit.id, days=14)
            habit_payloads.append(_build_habit_payload(habit, today_progress, stats))

        trigger_count, trigger_warning = _ensure_triggers(habits)

        result: Dict[str, Any] = {
            "success": True,
            "user_id": user_id,
            "habits_count": len(habit_payloads),
            "auto_initialized": auto_initialized,
            "trigger_count": trigger_count,
            "habits": habit_payloads,
        }

        if trigger_warning:
            result["trigger_warning"] = trigger_warning

        return result

    except Exception as exc:  # pragma: no cover - defensive
        logger.error(
            "getHabitsOverview tool failed",
            extra={"user_id": user_id, "error": str(exc)},
        )
        return {
            "success": False,
            "error": str(exc),
        }


def _log_habit_progress_by_name_tool(
    *,
    habit_name: str,
    completed: bool,
    excuse_text: Optional[str] = None,
    excuse_category: Optional[str] = None,
    user_id: str = "default_user",
) -> Dict[str, Any]:
    """
    Log progress for a habit by its name (fuzzy matching).
    
    This is a convenience function that finds the habit by name
    and then logs progress for it.
    """
    try:
        habit_manager = get_habit_manager()
        habits = habit_manager.list_habits(user_id, active_only=True)
        
        if not habits:
            return {
                "success": False,
                "error": "No active habits found. User may need to be onboarded first.",
            }
        
        # Find matching habit (case-insensitive partial match)
        habit_name_lower = habit_name.lower()
        matched_habit = None
        
        for habit in habits:
            if habit_name_lower in habit.name.lower() or habit.name.lower() in habit_name_lower:
                matched_habit = habit
                break
        
        if not matched_habit:
            # Return list of available habits
            habit_names = [h.name for h in habits]
            return {
                "success": False,
                "error": f"No habit found matching '{habit_name}'. Available habits: {', '.join(habit_names)}",
                "available_habits": habit_names,
            }
        
        # Use the existing log_progress function
        return _log_habit_progress_tool(
            habit_id=matched_habit.id,
            completed=completed,
            excuse_text=excuse_text,
            excuse_category=excuse_category,
            user_id=user_id,
        )
        
    except Exception as e:
        error_msg = f"Error logging progress by name: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg,
        }


def _log_habit_progress_tool(
    *,
    habit_id: int,
    completed: bool,
    excuse_text: Optional[str] = None,
    excuse_category: Optional[str] = None,
    user_id: str = "default_user",
) -> Dict[str, Any]:
    """
    Log progress for a habit check-in by habit ID.
    """
    try:
        # Verify habit exists first
        habit_manager = get_habit_manager()
        habit = habit_manager.get_habit(habit_id, user_id)
        
        if not habit:
            error_msg = f"Habit with ID {habit_id} not found. The habit may have been deleted or doesn't exist yet."
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        tracker = get_progress_tracker()
        scorer = get_consistency_scorer()
        
        entry = tracker.log_progress(
            habit_id=habit_id,
            completed=completed,
            excuse_given=excuse_text,
            excuse_category=excuse_category,
        )
        
        # Update consistency score
        try:
            scorer.calculate_and_update_score(reason="habit_checkin")
        except Exception as score_err:
            logger.warning(f"Failed to update consistency score: {score_err}")
            # Continue anyway - progress was logged
        
        return {
            "success": True,
            "entry_id": entry.id,
            "habit_name": habit.name,
            "completed": completed,
            "message": f"Progress logged successfully for '{habit.name}'",
        }
    except Exception as e:
        error_msg = f"Error logging progress for habit {habit_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg,
        }


__all__ = ["build_registry", "get_schemas"]

