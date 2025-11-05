"""Goals API endpoints for habit tracking."""

from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..logging_config import logger
from ..services.goals import (
    get_habit_manager,
    get_progress_tracker,
    get_context_manager,
    get_consistency_scorer,
    get_progression_engine,
    get_goals_trigger_manager,
    get_onboarding_service,
)


router = APIRouter(prefix="/goals", tags=["goals"])


# Request/Response Models
class CreateHabitRequest(BaseModel):
    name: str
    target_frequency: int
    check_in_time: str = "anytime"
    description: Optional[str] = None
    user_id: str = "default_user"
    follow_up_delay_minutes: int = 60


class UpdateHabitRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_frequency: Optional[int] = None
    current_frequency: Optional[int] = None
    check_in_time: Optional[str] = None
    follow_up_delay_minutes: Optional[int] = None
    user_id: str = "default_user"


class CreateContextRequest(BaseModel):
    context_type: str
    description: str
    expected_end_date: Optional[str] = None
    check_in_frequency_days: Optional[int] = None
    related_habits: List[int] = []
    user_id: str = "default_user"


class OnboardingRequest(BaseModel):
    user_id: str = "default_user"


@router.post("/habits")
async def create_habit(request: CreateHabitRequest) -> Dict[str, Any]:
    """Create a new habit."""
    try:
        habit_manager = get_habit_manager()
        trigger_manager = get_goals_trigger_manager()
        
        habit = habit_manager.create_habit(
            name=request.name,
            target_frequency=request.target_frequency,
            check_in_time=request.check_in_time,
            description=request.description,
            user_id=request.user_id,
            follow_up_delay_minutes=request.follow_up_delay_minutes,
        )
        
        # Create check-in trigger for this habit
        try:
            trigger_id = trigger_manager.create_habit_checkin_trigger(
                habit.id,
                habit.check_in_time,
                habit.user_id,
            )
        except Exception as e:
            logger.warning(f"Failed to create trigger for habit: {e}")
            trigger_id = None
        
        return {
            "habit": {
                "id": habit.id,
                "name": habit.name,
                "description": habit.description,
                "target_frequency": habit.target_frequency,
                "current_frequency": habit.current_frequency,
                "check_in_time": habit.check_in_time,
                "follow_up_delay_minutes": habit.follow_up_delay_minutes,
                "created_at": habit.created_at.isoformat(),
                "progression_start_date": habit.progression_start_date.isoformat(),
                "active": habit.active,
            },
            "trigger_id": trigger_id,
        }
    
    except Exception as e:
        logger.error(f"Error creating habit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/habits")
async def list_habits(
    user_id: str = Query("default_user"),
    active_only: bool = Query(True)
) -> Dict[str, Any]:
    """List all habits for a user."""
    try:
        habit_manager = get_habit_manager()
        habits = habit_manager.list_habits(user_id, active_only)
        
        habits_data = []
        for habit in habits:
            habits_data.append({
                "id": habit.id,
                "name": habit.name,
                "description": habit.description,
                "target_frequency": habit.target_frequency,
                "current_frequency": habit.current_frequency,
                "check_in_time": habit.check_in_time,
                "follow_up_delay_minutes": habit.follow_up_delay_minutes,
                "created_at": habit.created_at.isoformat(),
                "progression_start_date": habit.progression_start_date.isoformat(),
                "active": habit.active,
            })
        
        return {"habits": habits_data}
    
    except Exception as e:
        logger.error(f"Error listing habits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/habits/{habit_id}")
async def get_habit(
    habit_id: int,
    user_id: str = Query("default_user")
) -> Dict[str, Any]:
    """Get a specific habit."""
    try:
        habit_manager = get_habit_manager()
        habit = habit_manager.get_habit(habit_id, user_id)
        
        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        return {
            "habit": {
                "id": habit.id,
                "name": habit.name,
                "description": habit.description,
                "target_frequency": habit.target_frequency,
                "current_frequency": habit.current_frequency,
                "check_in_time": habit.check_in_time,
                "follow_up_delay_minutes": habit.follow_up_delay_minutes,
                "created_at": habit.created_at.isoformat(),
                "progression_start_date": habit.progression_start_date.isoformat(),
                "active": habit.active,
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting habit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/habits/{habit_id}")
async def update_habit(
    habit_id: int,
    request: UpdateHabitRequest
) -> Dict[str, Any]:
    """Update a habit."""
    try:
        habit_manager = get_habit_manager()
        
        success = habit_manager.update_habit(
            habit_id,
            user_id=request.user_id,
            name=request.name,
            description=request.description,
            target_frequency=request.target_frequency,
            current_frequency=request.current_frequency,
            check_in_time=request.check_in_time,
            follow_up_delay_minutes=request.follow_up_delay_minutes,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Habit not found or no changes made")
        
        # Get updated habit
        habit = habit_manager.get_habit(habit_id, request.user_id)
        
        return {
            "habit": {
                "id": habit.id,
                "name": habit.name,
                "description": habit.description,
                "target_frequency": habit.target_frequency,
                "current_frequency": habit.current_frequency,
                "check_in_time": habit.check_in_time,
                "follow_up_delay_minutes": habit.follow_up_delay_minutes,
                "created_at": habit.created_at.isoformat(),
                "progression_start_date": habit.progression_start_date.isoformat(),
                "active": habit.active,
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating habit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/habits/{habit_id}")
async def delete_habit(
    habit_id: int,
    user_id: str = Query("default_user")
) -> Dict[str, str]:
    """Delete (deactivate) a habit."""
    try:
        habit_manager = get_habit_manager()
        success = habit_manager.delete_habit(habit_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        return {"message": "Habit deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting habit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress")
async def get_progress(
    habit_id: int = Query(...),
    days: int = Query(14),
    user_id: str = Query("default_user")
) -> Dict[str, Any]:
    """Get progress history for a habit."""
    try:
        tracker = get_progress_tracker()
        entries = tracker.get_recent_progress(habit_id, days)
        
        progress_data = []
        for entry in entries:
            progress_data.append({
                "id": entry.id,
                "habit_id": entry.habit_id,
                "date": entry.date.isoformat(),
                "completed": entry.completed,
                "excuse_given": entry.excuse_given,
                "excuse_category": entry.excuse_category,
                "checked_in_at": entry.checked_in_at.isoformat(),
            })
        
        # Get stats
        stats = tracker.get_habit_stats(habit_id, days)
        
        return {
            "progress": progress_data,
            "stats": {
                "completion_rate": stats.completion_rate if stats else 0,
                "current_streak": stats.current_streak if stats else 0,
                "recent_completions": stats.recent_completions if stats else 0,
                "recent_attempts": stats.recent_attempts if stats else 0,
            } if stats else None,
        }
    
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/today")
async def get_progress_today(
    user_id: str = Query("default_user")
) -> Dict[str, Any]:
    """Get today's progress for all habits."""
    try:
        tracker = get_progress_tracker()
        progress = tracker.get_all_progress_today(user_id)
        
        progress_data = []
        for habit_id, habit_name, completed in progress:
            progress_data.append({
                "habit_id": habit_id,
                "habit_name": habit_name,
                "completed": completed,
            })
        
        return {
            "date": date.today().isoformat(),
            "progress": progress_data,
        }
    
    except Exception as e:
        logger.error(f"Error getting today's progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consistency")
async def get_consistency(
    user_id: str = Query("default_user")
) -> Dict[str, Any]:
    """Get consistency score for a user."""
    try:
        scorer = get_consistency_scorer()
        score = scorer.get_or_create_score(user_id)
        
        return {
            "user_id": user_id,
            "current_score": score.current_score,
            "peak_score": score.peak_score,
            "updated_at": score.updated_at.isoformat(),
            "score_history": score.score_history[-30:],  # Last 30 days
        }
    
    except Exception as e:
        logger.error(f"Error getting consistency score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consistency/breakdown")
async def get_consistency_breakdown(
    user_id: str = Query("default_user")
) -> Dict[str, Any]:
    """Get detailed breakdown of consistency score."""
    try:
        scorer = get_consistency_scorer()
        breakdown = scorer.get_score_breakdown(user_id)
        
        return breakdown
    
    except Exception as e:
        logger.error(f"Error getting consistency breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context")
async def create_context(request: CreateContextRequest) -> Dict[str, Any]:
    """Record a context memory."""
    try:
        context_manager = get_context_manager()
        
        expected_end_date = None
        if request.expected_end_date:
            expected_end_date = date.fromisoformat(request.expected_end_date)
        
        context = context_manager.create_context(
            context_type=request.context_type,
            description=request.description,
            user_id=request.user_id,
            expected_end_date=expected_end_date,
            check_in_frequency_days=request.check_in_frequency_days,
            related_habits=request.related_habits,
        )
        
        return {
            "context": {
                "id": context.id,
                "context_type": context.context_type,
                "description": context.description,
                "start_date": context.start_date.isoformat(),
                "expected_end_date": context.expected_end_date.isoformat() if context.expected_end_date else None,
                "check_in_frequency_days": context.check_in_frequency_days,
                "resolved": context.resolved,
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/active")
async def get_active_contexts(
    user_id: str = Query("default_user")
) -> Dict[str, Any]:
    """Get active contexts for a user."""
    try:
        context_manager = get_context_manager()
        contexts = context_manager.get_active_contexts(user_id)
        
        contexts_data = []
        for ctx in contexts:
            contexts_data.append({
                "id": ctx.id,
                "context_type": ctx.context_type,
                "description": ctx.description,
                "start_date": ctx.start_date.isoformat(),
                "expected_end_date": ctx.expected_end_date.isoformat() if ctx.expected_end_date else None,
                "check_in_frequency_days": ctx.check_in_frequency_days,
                "related_habits": ctx.related_habits,
                "resolved": ctx.resolved,
            })
        
        return {"contexts": contexts_data}
    
    except Exception as e:
        logger.error(f"Error getting active contexts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/context/{context_id}/resolve")
async def resolve_context(
    context_id: int,
    user_id: str = Query("default_user")
) -> Dict[str, str]:
    """Mark a context as resolved."""
    try:
        context_manager = get_context_manager()
        success = context_manager.resolve_context(context_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Context not found")
        
        return {"message": "Context resolved successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progression/{habit_id}")
async def get_progression_status(
    habit_id: int,
    user_id: str = Query("default_user")
) -> Dict[str, Any]:
    """Get progression status for a habit."""
    try:
        progression_engine = get_progression_engine()
        status = progression_engine.get_progression_status(habit_id, user_id)
        
        return status
    
    except Exception as e:
        logger.error(f"Error getting progression status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/progression/evaluate")
async def evaluate_progression(
    user_id: str = Query("default_user")
) -> Dict[str, Any]:
    """Manually trigger progression evaluation (normally runs weekly)."""
    try:
        progression_engine = get_progression_engine()
        results = progression_engine.evaluate_and_progress_habits(user_id)
        
        return {"results": results}
    
    except Exception as e:
        logger.error(f"Error evaluating progression: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/onboarding")
async def onboard_user(request: OnboardingRequest) -> Dict[str, Any]:
    """
    Onboard a new user with default habits from JSON config.
    
    This sets up habits with progressive starting frequencies,
    creates check-in triggers, and returns a welcome message.
    All habits are loaded from the default_habits.json config file.
    """
    try:
        onboarding_service = get_onboarding_service()
        
        result = onboarding_service.setup_user_with_goals(
            user_id=request.user_id,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error during onboarding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/onboarding/force")
async def force_onboard_user(request: OnboardingRequest) -> Dict[str, Any]:
    """
    Force onboarding even if user already has habits.
    This will NOT duplicate habits - it skips if habits exist.
    Useful for debugging initialization issues.
    """
    try:
        from ..services.goals.auto_init import auto_initialize_habits, _initialized_users
        
        # Clear the user from initialized set to allow retry
        _initialized_users.discard(request.user_id)
        
        # Try to initialize
        result = await auto_initialize_habits(request.user_id)
        
        # Get current habits
        habit_manager = get_habit_manager()
        habits = habit_manager.list_habits(request.user_id, active_only=True)
        
        return {
            "initialized": result,
            "habits_count": len(habits),
            "habits": [{"id": h.id, "name": h.name, "current_freq": h.current_frequency, "target_freq": h.target_frequency} for h in habits],
            "message": f"Initialization {'succeeded' if result else 'was not needed (habits already exist)'}"
        }
    
    except Exception as e:
        logger.error(f"Error during force onboarding: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
