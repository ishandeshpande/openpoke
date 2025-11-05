"""Onboarding service for setting up new users with goals."""

from typing import List, Dict, Any
from datetime import date

from ...logging_config import logger
from .habit_manager import get_habit_manager
from .trigger_manager import get_goals_trigger_manager
from .habit_loader import get_habit_loader


class OnboardingService:
    """Handles user onboarding and initial goal setup."""

    def __init__(self):
        self._habit_manager = get_habit_manager()
        self._trigger_manager = get_goals_trigger_manager()
        self._habit_loader = get_habit_loader()

    def setup_user_with_goals(
        self,
        user_id: str = "default_user",
    ) -> Dict[str, Any]:
        """
        Set up a new user with their initial goals from the default habits JSON.
        
        This implements the progressive onboarding approach:
        - Loads default habits from JSON config
        - Calculates realistic starting frequencies (40-50% of target)
        - Creates habits with progressive difficulty
        - Sets up check-in triggers
        - Sets up weekly progression evaluation
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with created habits and trigger IDs
        """
        # Load default habits from JSON config
        try:
            goals = self._habit_loader.load_default_habits()
        except Exception as e:
            logger.error(f"Failed to load default habits: {e}")
            return {
                "user_id": user_id,
                "habits_created": 0,
                "habits": [],
                "triggers": [],
                "errors": [{
                    "error": f"Failed to load default habits: {str(e)}",
                }],
            }
        created_habits = []
        trigger_ids = []
        errors = []
        
        logger.info(
            f"Starting onboarding for user {user_id} with {len(goals)} goals"
        )
        
        # Create each habit
        for goal in goals:
            try:
                habit = self._habit_manager.create_habit(
                    name=goal["name"],
                    target_frequency=goal["target_frequency"],
                    check_in_time=goal.get("check_in_time", "anytime"),
                    description=goal.get("description"),
                    user_id=user_id,
                    follow_up_delay_minutes=goal.get("follow_up_delay_minutes", 60),
                )
                
                created_habits.append({
                    "id": habit.id,
                    "name": habit.name,
                    "target_frequency": habit.target_frequency,
                    "current_frequency": habit.current_frequency,
                    "check_in_time": habit.check_in_time,
                    "progression_start_date": habit.progression_start_date.isoformat(),
                })
                
                # Create check-in trigger for this habit
                try:
                    trigger_id = self._trigger_manager.create_habit_checkin_trigger(
                        habit.id,
                        habit.check_in_time,
                        user_id,
                    )
                    trigger_ids.append({
                        "habit_id": habit.id,
                        "trigger_id": trigger_id,
                        "type": "HABIT_CHECKIN",
                    })
                except Exception as e:
                    logger.error(
                        f"Failed to create trigger for habit {habit.id}: {e}"
                    )
                    errors.append({
                        "habit_id": habit.id,
                        "error": f"Trigger creation failed: {str(e)}",
                    })
                
            except Exception as e:
                logger.error(f"Failed to create habit {goal['name']}: {e}")
                errors.append({
                    "goal_name": goal["name"],
                    "error": f"Habit creation failed: {str(e)}",
                })
        
        # Create weekly progression trigger
        progression_trigger_id = None
        try:
            progression_trigger_id = self._trigger_manager.setup_weekly_progression_trigger(
                user_id
            )
            trigger_ids.append({
                "habit_id": None,
                "trigger_id": progression_trigger_id,
                "type": "WEEKLY_PROGRESSION",
            })
        except Exception as e:
            logger.error(f"Failed to create weekly progression trigger: {e}")
            errors.append({
                "error": f"Weekly progression trigger failed: {str(e)}",
            })
        
        # Generate onboarding message
        message = self._generate_onboarding_message(created_habits, user_id)
        
        result = {
            "user_id": user_id,
            "habits_created": len(created_habits),
            "habits": created_habits,
            "triggers": trigger_ids,
            "onboarding_message": message,
        }
        
        if errors:
            result["errors"] = errors
        
        logger.info(
            f"Onboarding complete for user {user_id}: "
            f"{len(created_habits)} habits, {len(trigger_ids)} triggers"
        )
        
        return result

    def _generate_onboarding_message(
        self, habits: List[Dict], user_id: str
    ) -> str:
        """Generate a welcoming onboarding message explaining the progressive approach."""
        if not habits:
            return "Welcome! Let me know what habits you'd like to build."
        
        message_parts = [
            "Welcome! I'm excited to help you build these habits! 🌟",
            "",
            "Here's how we'll work together:",
            "",
        ]
        
        for habit in habits:
            message_parts.append(
                f"📌 **{habit['name']}** - Starting at {habit['current_frequency']}x per week, "
                f"building up to {habit['target_frequency']}x per week"
            )
        
        message_parts.extend([
            "",
            "**The Progressive Approach:**",
            "We're starting with achievable frequencies so you can build momentum and consistency. "
            "As you hit your targets for 2 weeks in a row, we'll gradually increase the difficulty.",
            "",
            "**What to Expect:**",
            "- I'll check in with you daily about your habits at the times you specified",
            "- If you miss a check-in, I'll send a gentle follow-up",
            "- I'll track your consistency score and celebrate your wins!",
            "- Every week, we'll evaluate your progress and adjust if needed",
            "",
            "**Life Happens:**",
            "If you're sick, have exams, or other challenges - just let me know! "
            "I'll factor that in and be more understanding during tough times.",
            "",
            "Let's build great habits together! 💪",
        ])
        
        return "\n".join(message_parts)


# Singleton instance
_onboarding_service = None


def get_onboarding_service() -> OnboardingService:
    """Get the singleton onboarding service instance."""
    global _onboarding_service
    if _onboarding_service is None:
        _onboarding_service = OnboardingService()
    return _onboarding_service


__all__ = ["OnboardingService", "get_onboarding_service"]

