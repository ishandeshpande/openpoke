"""Auto-initialization service for habit onboarding."""

from typing import Optional, Set
from ...logging_config import logger
from .habit_manager import get_habit_manager
from .onboarding import get_onboarding_service


# Track which users have been checked for initialization
_initialized_users: Set[str] = set()


async def auto_initialize_habits(user_id: str = "default_user") -> bool:
    """
    Automatically initialize habits for a user if they don't have any.
    
    This is called on first interaction to set up default habits
    from the JSON config file. Checks each time if habits exist.
    
    Args:
        user_id: User identifier
        
    Returns:
        True if habits were initialized, False if they already existed
    """
    global _initialized_users
    
    try:
        habit_manager = get_habit_manager()
        existing_habits = habit_manager.list_habits(user_id, active_only=True)
        
        # If user already has habits, skip initialization
        if len(existing_habits) > 0:
            logger.debug(
                f"User {user_id} already has {len(existing_habits)} habits, skipping auto-init"
            )
            # Mark as initialized now that we confirmed habits exist
            _initialized_users.add(user_id)
            return False
        
        # Skip if we've already tried to initialize this user (prevents infinite retries)
        if user_id in _initialized_users:
            logger.warning(
                f"User {user_id} has no habits but initialization already attempted. "
                f"Check logs for initialization errors."
            )
            return False
        
        # Mark as checked to prevent concurrent initialization attempts
        _initialized_users.add(user_id)
        
        # User has no habits - auto-initialize with defaults
        logger.info(f"Auto-initializing habits for user {user_id}")
        
        onboarding_service = get_onboarding_service()
        result = onboarding_service.setup_user_with_goals(user_id=user_id)
        
        if result.get("habits_created", 0) > 0:
            logger.info(
                f"Successfully auto-initialized {result['habits_created']} habits for user {user_id}"
            )
            return True
        else:
            logger.error(
                f"Auto-initialization completed but no habits created for user {user_id}",
                extra={"result": result}
            )
            # Remove from set so it can retry on next message
            _initialized_users.discard(user_id)
            return False
            
    except Exception as e:
        logger.error(
            f"Failed to auto-initialize habits for user {user_id}: {e}",
            exc_info=True
        )
        # Remove from set so it can retry on next message
        _initialized_users.discard(user_id)
        return False


__all__ = ["auto_initialize_habits"]

