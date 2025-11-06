import asyncio
import time
import threading
from typing import Optional, Union, Dict, Tuple

from fastapi import status
from fastapi.responses import JSONResponse, PlainTextResponse

from ...agents.interaction_agent.runtime import InteractionAgentRuntime
from ...logging_config import logger
from ...models import ChatMessage, ChatRequest
from ...services.goals.auto_init import auto_initialize_habits
from ...utils import error_response

# Deduplication cache: (sender, message_content) -> timestamp
_message_dedup_cache: Dict[Tuple[str, str], float] = {}
_DEDUP_WINDOW_SECONDS = 5.0
_dedup_lock = threading.Lock()


# Extract the most recent user message from the chat request payload
def _extract_latest_user_message(payload: ChatRequest) -> Optional[ChatMessage]:
    for message in reversed(payload.messages):
        if message.role.lower().strip() == "user" and message.content.strip():
            return message
    return None


# Process incoming chat requests by routing them to the interaction agent runtime
async def handle_chat_request(payload: ChatRequest) -> Union[PlainTextResponse, JSONResponse]:
    """Handle a chat request using the InteractionAgentRuntime."""

    # Extract user message
    user_message = _extract_latest_user_message(payload)
    if user_message is None:
        return error_response("Missing user message", status_code=status.HTTP_400_BAD_REQUEST)

    user_content = user_message.content.strip()  # Already checked in _extract_latest_user_message

    logger.info("chat request", extra={
        "message_length": len(user_content),
        "source": payload.source,
        "sync_mode": payload.sync_mode
    })

    # Deduplication: prevent processing same message from same sender within window
    if payload.sender_phone and payload.source == "imessage":
        dedup_key = (payload.sender_phone, user_content)
        now = time.time()

        with _dedup_lock:
            # Check if we recently processed this exact message
            if dedup_key in _message_dedup_cache:
                last_time = _message_dedup_cache[dedup_key]
                if now - last_time < _DEDUP_WINDOW_SECONDS:
                    logger.info("Duplicate message detected - skipping", extra={
                        "sender": payload.sender_phone,
                        "time_since_last": f"{now - last_time:.2f}s"
                    })
                    # Return empty success to avoid errors on client
                    if payload.sync_mode:
                        return JSONResponse({"ok": True, "response": ""})
                    else:
                        return PlainTextResponse("", status_code=status.HTTP_202_ACCEPTED)

            # Update cache
            _message_dedup_cache[dedup_key] = now

            # Clean old entries (older than 30 seconds)
            if len(_message_dedup_cache) > 100:
                _message_dedup_cache.clear()

    # Store user's phone number if provided (for iMessage)
    if payload.sender_phone:
        from ..user_phone import get_user_phone_store
        phone_store = get_user_phone_store()
        existing_phone = phone_store.get_phone()
        if existing_phone != payload.sender_phone:
            phone_store.set_phone(payload.sender_phone)
            logger.info(f"Updated stored phone number")
    
    # Route to interaction agent
    try:
        runtime = InteractionAgentRuntime()
    except ValueError as ve:
        # Missing API key error
        logger.error("configuration error", extra={"error": str(ve)})
        return error_response(str(ve), status_code=status.HTTP_400_BAD_REQUEST)

    # For iMessage (sync_mode=True), wait for response and return it
    if payload.sync_mode:
        try:
            # Auto-initialize habits in background (don't await)
            asyncio.create_task(auto_initialize_habits())
            
            # Execute and wait for response
            result = await runtime.execute(user_message=user_content)
            
            if result.success:
                return JSONResponse({
                    "ok": True,
                    "response": result.response
                }, status_code=status.HTTP_200_OK)
            else:
                return JSONResponse({
                    "ok": False,
                    "error": result.error or "Unknown error"
                }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as exc:
            logger.error("chat task failed (sync)", extra={"error": str(exc)})
            return JSONResponse({
                "ok": False,
                "error": str(exc)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # For web (sync_mode=False), use existing async behavior
    async def _run_interaction() -> None:
        try:
            # Auto-initialize habits in background
            asyncio.create_task(auto_initialize_habits())
            
            await runtime.execute(user_message=user_content)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("chat task failed", extra={"error": str(exc)})

    asyncio.create_task(_run_interaction())

    return PlainTextResponse("", status_code=status.HTTP_202_ACCEPTED)
