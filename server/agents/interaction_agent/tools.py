"""Tool definitions for interaction agent."""

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Optional

from ...logging_config import logger
from ...services.conversation import get_conversation_log
from ...services.execution import get_agent_roster, get_execution_agent_logs
from ...services.goals import get_habit_manager, get_progress_tracker, get_consistency_scorer
from ..execution_agent.batch_manager import ExecutionBatchManager
from datetime import date


@dataclass
class ToolResult:
    """Standardized payload returned by interaction-agent tools."""

    success: bool
    payload: Any = None
    user_message: Optional[str] = None
    recorded_reply: bool = False

# Tool schemas for LLM function calling
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "send_message_to_agent",
            "description": "Deliver instructions to a specific execution agent. Creates a new agent if the name doesn't exist in the roster, or reuses an existing one.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Human-readable agent name describing its purpose (e.g., 'Vercel Job Offer', 'Email to Sharanjeet'). This name will be used to identify and potentially reuse the agent."
                    },
                    "instructions": {"type": "string", "description": "Instructions for the agent to execute."},
                },
                "required": ["agent_name", "instructions"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message_to_user",
            "description": "Deliver a natural-language response directly to the user. Use this for updates, confirmations, or any assistant response the user should see immediately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Plain-text message that will be shown to the user and recorded in the conversation log.",
                    },
                },
                "required": ["message"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Wait silently when a message is already in conversation history to avoid duplicating responses. Adds a <wait> log entry that is not visible to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why waiting (e.g., 'Message already sent', 'Draft already created').",
                    },
                },
                "required": ["reason"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_habit_progress",
            "description": "Mark a habit as complete or incomplete. Use this when the user mentions completing habits (e.g., 'I went to the gym', 'I cooked dinner', 'didn't sleep well'). Accepts habit names with fuzzy matching.",
            "parameters": {
                "type": "object",
                "properties": {
                    "habit_name": {
                        "type": "string",
                        "description": "Name or keyword for the habit (e.g., 'gym', 'dinner', 'sleep')",
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
                        "description": "Category of excuse if applicable: sick, exam, travel, or other",
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
            "name": "get_todays_habits",
            "description": "Get the user's habits for today with their completion status. Use this to see what habits they're tracking and which ones are done.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_consistency_score",
            "description": "Get the user's consistency score (0-100) with detailed breakdown. Use when user asks about their consistency score, performance, or how they're doing overall.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
]

_EXECUTION_BATCH_MANAGER = ExecutionBatchManager()


# Create or reuse execution agent and dispatch instructions asynchronously
def send_message_to_agent(agent_name: str, instructions: str) -> ToolResult:
    """Send instructions to an execution agent."""
    roster = get_agent_roster()
    roster.load()
    existing_agents = set(roster.get_agents())
    is_new = agent_name not in existing_agents

    if is_new:
        roster.add_agent(agent_name)

    get_execution_agent_logs().record_request(agent_name, instructions)

    action = "Created" if is_new else "Reused"
    logger.info(f"{action} agent: {agent_name}")

    async def _execute_async() -> None:
        try:
            result = await _EXECUTION_BATCH_MANAGER.execute_agent(agent_name, instructions)
            status = "SUCCESS" if result.success else "FAILED"
            logger.info(f"Agent '{agent_name}' completed: {status}")
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Agent '{agent_name}' failed: {str(exc)}")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.error("No running event loop available for async execution")
        return ToolResult(success=False, payload={"error": "No event loop available"})

    loop.create_task(_execute_async())

    return ToolResult(
        success=True,
        payload={
            "status": "submitted",
            "agent_name": agent_name,
            "new_agent_created": is_new,
        },
    )


# Send immediate message to user and record in conversation history
def send_message_to_user(message: str) -> ToolResult:
    """Record a user-visible reply in the conversation log."""
    log = get_conversation_log()
    log.record_reply(message)

    return ToolResult(
        success=True,
        payload={"status": "delivered"},
        user_message=message,
        recorded_reply=True,
    )


# Record silent wait state to avoid duplicate responses
def wait(reason: str) -> ToolResult:
    """Wait silently and add a wait log entry that is not visible to the user."""
    log = get_conversation_log()
    
    # Record a dedicated wait entry so the UI knows to ignore it
    log.record_wait(reason)
    

    return ToolResult(
        success=True,
        payload={
            "status": "waiting",
            "reason": reason,
        },
        recorded_reply=True,
    )


# Log habit progress directly
def log_habit_progress(
    habit_name: str,
    completed: bool,
    excuse_text: Optional[str] = None,
    excuse_category: Optional[str] = None,
) -> ToolResult:
    """Mark a habit as complete or incomplete by name."""
    try:
        habit_manager = get_habit_manager()
        habits = habit_manager.list_habits("default_user", active_only=True)
        
        if not habits:
            return ToolResult(
                success=False,
                payload={"error": "No active habits found. User needs to set up habits first."},
            )
        
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
            return ToolResult(
                success=False,
                payload={
                    "error": f"No habit found matching '{habit_name}'. Available habits: {', '.join(habit_names)}",
                    "available_habits": habit_names,
                },
            )
        
        # Log the progress
        tracker = get_progress_tracker()
        scorer = get_consistency_scorer()
        
        entry = tracker.log_progress(
            habit_id=matched_habit.id,
            completed=completed,
            excuse_given=excuse_text,
            excuse_category=excuse_category,
        )
        
        # Update consistency score
        try:
            scorer.calculate_and_update_score(reason="habit_checkin")
        except Exception as score_err:
            logger.warning(f"Failed to update consistency score: {score_err}")
        
        return ToolResult(
            success=True,
            payload={
                "entry_id": entry.id,
                "habit_name": matched_habit.name,
                "completed": completed,
                "message": f"Marked '{matched_habit.name}' as {'complete' if completed else 'incomplete'}",
            },
        )
        
    except Exception as e:
        logger.error(f"Error logging habit progress: {e}", exc_info=True)
        return ToolResult(
            success=False,
            payload={"error": str(e)},
        )


# Get today's habits with their status
def get_todays_habits() -> ToolResult:
    """Get the user's habits for today with completion status."""
    try:
        habit_manager = get_habit_manager()
        tracker = get_progress_tracker()
        
        habits = habit_manager.list_habits("default_user", active_only=True)
        today = date.today()
        
        if not habits:
            return ToolResult(
                success=True,
                payload={
                    "habits": [],
                    "message": "No habits configured yet.",
                },
            )
        
        result = []
        for habit in habits:
            today_progress = tracker.get_progress_for_date(habit.id, today)
            stats = tracker.get_habit_stats(habit.id, days=7)
            
            result.append({
                "habit_id": habit.id,
                "name": habit.name,
                "description": habit.description,
                "current_frequency": habit.current_frequency,
                "target_frequency": habit.target_frequency,
                "check_in_time": habit.check_in_time,
                "checked_in_today": today_progress is not None,
                "completed_today": today_progress.completed if today_progress else None,
                "recent_completion_rate": stats.completion_rate if stats else 0,
                "current_streak": stats.current_streak if stats else 0,
            })
        
        return ToolResult(
            success=True,
            payload={
                "habits": result,
                "date": today.isoformat(),
                "habits_count": len(result),
            },
        )
        
    except Exception as e:
        logger.error(f"Error getting today's habits: {e}", exc_info=True)
        return ToolResult(
            success=False,
            payload={"error": str(e)},
        )


# Get consistency score with breakdown
def get_consistency_score() -> ToolResult:
    """Get user's consistency score with detailed breakdown."""
    try:
        scorer = get_consistency_scorer()
        breakdown = scorer.get_score_breakdown("default_user")
        
        return ToolResult(
            success=True,
            payload=breakdown,
        )
        
    except Exception as e:
        logger.error(f"Error getting consistency score: {e}", exc_info=True)
        return ToolResult(
            success=False,
            payload={"error": str(e)},
        )


# Return predefined tool schemas for LLM function calling
def get_tool_schemas():
    """Return OpenAI-compatible tool schemas."""
    return TOOL_SCHEMAS


# Route tool calls to appropriate handlers with argument validation and error handling
def handle_tool_call(name: str, arguments: Any) -> ToolResult:
    """Handle tool calls from interaction agent."""
    try:
        if isinstance(arguments, str):
            args = json.loads(arguments) if arguments.strip() else {}
        elif isinstance(arguments, dict):
            args = arguments
        else:
            return ToolResult(success=False, payload={"error": "Invalid arguments format"})

        if name == "send_message_to_agent":
            return send_message_to_agent(**args)
        if name == "send_message_to_user":
            return send_message_to_user(**args)
        if name == "wait":
            return wait(**args)
        if name == "log_habit_progress":
            return log_habit_progress(**args)
        if name == "get_todays_habits":
            return get_todays_habits(**args)
        if name == "get_consistency_score":
            return get_consistency_score(**args)

        logger.warning("unexpected tool", extra={"tool": name})
        return ToolResult(success=False, payload={"error": f"Unknown tool: {name}"})
    except json.JSONDecodeError:
        return ToolResult(success=False, payload={"error": "Invalid JSON"})
    except TypeError as exc:
        return ToolResult(success=False, payload={"error": f"Missing required arguments: {exc}"})
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("tool call failed", extra={"tool": name, "error": str(exc)})
        return ToolResult(success=False, payload={"error": "Failed to execute"})
