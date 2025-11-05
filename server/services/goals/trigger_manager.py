"""Trigger management for goal-related events."""

from datetime import datetime, time, date, timedelta
from typing import Optional, List, Dict
from zoneinfo import ZoneInfo

from ...logging_config import logger
from ...services.triggers import get_trigger_service
from ...utils.timezones import get_user_timezone_name
from .habit_manager import get_habit_manager
from .context_manager import get_context_manager


# Trigger type constants
HABIT_CHECKIN = "HABIT_CHECKIN"
HABIT_FOLLOWUP = "HABIT_FOLLOWUP"
WEEKLY_PROGRESSION = "WEEKLY_PROGRESSION"
CONTEXT_REFRESH = "CONTEXT_REFRESH"


class GoalsTriggerManager:
    """Manages triggers for goal-related events."""

    def __init__(self):
        self._trigger_service = get_trigger_service()
        self._habit_manager = get_habit_manager()
        self._context_manager = get_context_manager()

    def create_habit_checkin_trigger(
        self,
        habit_id: int,
        check_in_time: str,
        user_id: str = "default_user",
    ) -> int:
        """
        Create a daily check-in trigger for a habit.
        
        Args:
            habit_id: ID of the habit
            check_in_time: Time to check in (HH:MM format or "anytime")
            user_id: User identifier
            
        Returns:
            Trigger ID
        """
        habit = self._habit_manager.get_habit(habit_id, user_id)
        if not habit:
            raise ValueError(f"Habit {habit_id} not found")
        
        # Get user timezone
        user_tz = get_user_timezone_name()
        
        # Determine trigger time
        if check_in_time == "anytime":
            # Default to 10 AM for "anytime" habits
            trigger_time = time(10, 0)
        else:
            # Parse HH:MM format
            hour, minute = map(int, check_in_time.split(":"))
            trigger_time = time(hour, minute)
        
        # Create start datetime
        now = datetime.now(ZoneInfo(user_tz))
        today = now.date()
        start_dt = datetime.combine(today, trigger_time, tzinfo=ZoneInfo(user_tz))
        
        # If time has passed today, start tomorrow
        if start_dt <= now:
            start_dt = start_dt + timedelta(days=1)
        
        # Create daily recurrence
        recurrence = "FREQ=DAILY;INTERVAL=1"
        
        # Payload with habit info
        payload = f"""Check in with user about habit: {habit.name}

Habit ID: {habit_id}
Type: {HABIT_CHECKIN}
Current Frequency: {habit.current_frequency}x per week
Target Frequency: {habit.target_frequency}x per week

Ask the user if they have completed this habit today. Be supportive and context-aware."""
        
        trigger = self._trigger_service.create_trigger(
            agent_name="habit-tracker",
            payload=payload,
            recurrence_rule=recurrence,
            start_time=start_dt.isoformat(),
            timezone_name=user_tz,
            status="active",
        )
        
        logger.info(
            f"Created habit check-in trigger",
            extra={
                "trigger_id": trigger.id,
                "habit_id": habit_id,
                "habit_name": habit.name,
                "check_in_time": check_in_time,
            },
        )
        
        return trigger.id

    def create_habit_followup_trigger(
        self,
        habit_id: int,
        original_checkin_time: str,
        delay_minutes: int,
        user_id: str = "default_user",
    ) -> int:
        """
        Create a one-time follow-up trigger if user hasn't responded.
        
        Args:
            habit_id: ID of the habit
            original_checkin_time: Original check-in time
            delay_minutes: Minutes to wait before follow-up
            user_id: User identifier
            
        Returns:
            Trigger ID
        """
        habit = self._habit_manager.get_habit(habit_id, user_id)
        if not habit:
            raise ValueError(f"Habit {habit_id} not found")
        
        user_tz = get_user_timezone_name()
        
        # Calculate follow-up time
        now = datetime.now(ZoneInfo(user_tz))
        followup_time = now + timedelta(minutes=delay_minutes)
        
        payload = f"""Follow up with user about habit: {habit.name}

Habit ID: {habit_id}
Type: {HABIT_FOLLOWUP}

Send a gentle follow-up asking if they completed this habit today. Keep it friendly and non-pushy."""
        
        trigger = self._trigger_service.create_trigger(
            agent_name="habit-tracker",
            payload=payload,
            start_time=followup_time.isoformat(),
            timezone_name=user_tz,
            status="active",
        )
        
        logger.info(
            f"Created habit follow-up trigger",
            extra={
                "trigger_id": trigger.id,
                "habit_id": habit_id,
                "delay_minutes": delay_minutes,
            },
        )
        
        return trigger.id

    def create_weekly_progression_trigger(
        self, user_id: str = "default_user"
    ) -> int:
        """
        Create a weekly trigger for evaluating habit progression.
        Runs Sunday at 11 PM.
        
        Args:
            user_id: User identifier
            
        Returns:
            Trigger ID
        """
        user_tz = get_user_timezone_name()
        
        # Create recurrence for Sunday at 11 PM
        # BYDAY=SU means Sunday
        recurrence = "FREQ=WEEKLY;BYDAY=SU"
        
        # Calculate next Sunday at 11 PM
        now = datetime.now(ZoneInfo(user_tz))
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0 and now.hour >= 23:
            days_until_sunday = 7
        
        next_sunday = now.date() + timedelta(days=days_until_sunday)
        start_dt = datetime.combine(
            next_sunday,
            time(23, 0),
            tzinfo=ZoneInfo(user_tz)
        )
        
        payload = f"""Weekly habit progression evaluation

Type: {WEEKLY_PROGRESSION}
User ID: {user_id}

Evaluate all habits for progression. Check performance over the last 2 weeks and adjust difficulty levels accordingly. 
Send encouraging messages about progressions to the user."""
        
        trigger = self._trigger_service.create_trigger(
            agent_name="habit-tracker",
            payload=payload,
            recurrence_rule=recurrence,
            start_time=start_dt.isoformat(),
            timezone_name=user_tz,
            status="active",
        )
        
        logger.info(
            f"Created weekly progression trigger",
            extra={
                "trigger_id": trigger.id,
                "user_id": user_id,
            },
        )
        
        return trigger.id

    def create_context_refresh_trigger(
        self,
        context_id: int,
        check_in_days: int = 1,
        user_id: str = "default_user",
    ) -> int:
        """
        Create a trigger to check in on a context (e.g., "Are you still sick?").
        
        Args:
            context_id: ID of the context
            check_in_days: Days between check-ins
            user_id: User identifier
            
        Returns:
            Trigger ID
        """
        context = self._context_manager.get_context(context_id, user_id)
        if not context:
            raise ValueError(f"Context {context_id} not found")
        
        user_tz = get_user_timezone_name()
        
        # Create recurrence based on check-in frequency
        recurrence = f"FREQ=DAILY;INTERVAL={check_in_days}"
        
        # Start tomorrow at 10 AM
        now = datetime.now(ZoneInfo(user_tz))
        tomorrow = now.date() + timedelta(days=1)
        start_dt = datetime.combine(
            tomorrow,
            time(10, 0),
            tzinfo=ZoneInfo(user_tz)
        )
        
        payload = f"""Context check-in: {context.description}

Context ID: {context_id}
Type: {CONTEXT_REFRESH}
Context Type: {context.context_type}

Check in with the user about this context. Ask if they're still dealing with it or if things have improved."""
        
        trigger = self._trigger_service.create_trigger(
            agent_name="habit-tracker",
            payload=payload,
            recurrence_rule=recurrence,
            start_time=start_dt.isoformat(),
            timezone_name=user_tz,
            status="active",
        )
        
        logger.info(
            f"Created context refresh trigger",
            extra={
                "trigger_id": trigger.id,
                "context_id": context_id,
                "check_in_days": check_in_days,
            },
        )
        
        return trigger.id

    def setup_all_habit_triggers(self, user_id: str = "default_user") -> Dict[int, int]:
        """
        Set up check-in triggers for all active habits.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary mapping habit_id to trigger_id
        """
        habits = self._habit_manager.list_habits(user_id, active_only=True)
        trigger_ids = {}
        
        for habit in habits:
            try:
                trigger_id = self.create_habit_checkin_trigger(
                    habit.id,
                    habit.check_in_time,
                    user_id,
                )
                trigger_ids[habit.id] = trigger_id
            except Exception as e:
                logger.error(
                    f"Failed to create trigger for habit {habit.id}",
                    extra={"error": str(e)},
                )
        
        return trigger_ids

    def setup_weekly_progression_trigger(self, user_id: str = "default_user") -> int:
        """
        Set up the weekly progression evaluation trigger.
        
        Args:
            user_id: User identifier
            
        Returns:
            Trigger ID
        """
        return self.create_weekly_progression_trigger(user_id)


# Singleton instance
_goals_trigger_manager: Optional[GoalsTriggerManager] = None


def get_goals_trigger_manager() -> GoalsTriggerManager:
    """Get the singleton goals trigger manager instance."""
    global _goals_trigger_manager
    if _goals_trigger_manager is None:
        _goals_trigger_manager = GoalsTriggerManager()
    return _goals_trigger_manager


__all__ = [
    "GoalsTriggerManager",
    "get_goals_trigger_manager",
    "HABIT_CHECKIN",
    "HABIT_FOLLOWUP",
    "WEEKLY_PROGRESSION",
    "CONTEXT_REFRESH",
]

