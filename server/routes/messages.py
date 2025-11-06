"""API routes for outgoing message management."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

from ..services import get_outgoing_message_queue

router = APIRouter(prefix="/messages", tags=["messages"])


class OutgoingMessageResponse(BaseModel):
    """Response model for outgoing messages."""

    id: int
    recipient: str
    message: str
    created_at: str


class PendingMessagesResponse(BaseModel):
    """Response model for pending messages."""

    ok: bool = True
    messages: List[OutgoingMessageResponse]


class MessageStatusUpdate(BaseModel):
    """Request model for updating message status."""

    message_id: int
    success: bool
    error: str | None = None


@router.get("/pending", response_model=PendingMessagesResponse)
def get_pending_messages(limit: int = 10) -> PendingMessagesResponse:
    """Get pending outgoing messages that need to be sent."""
    queue = get_outgoing_message_queue()
    pending = queue.get_pending(limit=limit)

    return PendingMessagesResponse(
        messages=[
            OutgoingMessageResponse(
                id=msg.id,
                recipient=msg.recipient,
                message=msg.message,
                created_at=msg.created_at
            )
            for msg in pending
        ]
    )


@router.post("/status", response_class=JSONResponse)
def update_message_status(update: MessageStatusUpdate) -> JSONResponse:
    """Update the status of an outgoing message after sending attempt."""
    queue = get_outgoing_message_queue()

    if update.success:
        queue.mark_sent(update.message_id)
        return JSONResponse({"ok": True, "message": "Message marked as sent"})
    else:
        error_text = update.error or "Unknown error"
        queue.mark_failed(update.message_id, error_text)
        return JSONResponse({"ok": True, "message": "Message marked as failed"})


__all__ = ["router"]
