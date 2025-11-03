from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from ..config import get_settings

AnthropicBaseURL = "https://api.anthropic.com/v1"


class AnthropicError(RuntimeError):
    """Raised when the Anthropic API returns an error response."""


def _headers(*, api_key: Optional[str] = None) -> Dict[str, str]:
    settings = get_settings()
    key = (api_key or settings.anthropic_api_key or "").strip()
    if not key:
        raise AnthropicError("Missing Anthropic API key")

    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    return headers


def _build_messages(messages: List[Dict[str, str]], system: Optional[str]) -> List[Dict[str, str]]:
    if system:
        return [{"role": "system", "content": system}, *messages]
    return messages


def _handle_response_error(exc: httpx.HTTPStatusError) -> None:
    response = exc.response
    detail: str
    try:
        payload = response.json()
        detail = payload.get("error") or payload.get("message") or json.dumps(payload)
    except Exception:
        detail = response.text
    raise AnthropicError(f"Anthropic request failed ({response.status_code}): {detail}") from exc


async def request_chat_completion(
    *,
    model: str,
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    api_key: Optional[str] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    base_url: str = AnthropicBaseURL,
) -> Dict[str, Any]:
    """Request a chat completion and return the raw JSON payload using Anthropic's Messages API."""

    # Convert OpenAI-style messages to Anthropic format
    anthropic_messages = _convert_messages_to_anthropic(messages)
    
    # Convert OpenAI-style tools to Anthropic format
    anthropic_tools = None
    if tools:
        anthropic_tools = _convert_tools_to_anthropic(tools)
    
    payload: Dict[str, object] = {
        "model": model,
        "messages": anthropic_messages,
        "max_tokens": 4096,
    }
    
    if system:
        payload["system"] = system
    
    if anthropic_tools:
        payload["tools"] = anthropic_tools

    url = f"{base_url.rstrip('/')}/messages"

    # Debug logging
    import logging
    logger = logging.getLogger("openpoke.server")
    logger.info(f"Anthropic API call - model: {model}, messages: {len(anthropic_messages)}, tools: {len(anthropic_tools) if anthropic_tools else 0}")
    
    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            response = await client.post(
                url,
                headers=_headers(api_key=api_key),
                json=payload,
                timeout=120.0,
            )
            logger.info(f"Anthropic response status: {response.status_code}")
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                _handle_response_error(exc)
            
            # Convert Anthropic response to OpenAI-compatible format
            anthropic_response = response.json()
            return _convert_anthropic_to_openai_format(anthropic_response)
        except httpx.HTTPStatusError as exc:  # pragma: no cover - handled above
            _handle_response_error(exc)
        except httpx.HTTPError as exc:
            logger.error(f"Anthropic HTTP error: {exc}")
            raise AnthropicError(f"Anthropic request failed: {exc}") from exc
        except Exception as exc:
            logger.error(f"Unexpected error in Anthropic call: {exc}", exc_info=True)
            raise AnthropicError(f"Anthropic request failed: {exc}") from exc

    raise AnthropicError("Anthropic request failed: unknown error")


def _convert_messages_to_anthropic(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert OpenAI-style messages to Anthropic format with proper role alternation."""
    anthropic_messages = []
    
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        # Skip system messages as they're handled separately
        if role == "system":
            continue
        
        # Handle assistant messages with tool calls
        if role == "assistant":
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                # Build content blocks for tool uses
                content_blocks = []
                if content:
                    content_blocks.append({"type": "text", "text": content})
                
                for tool_call in tool_calls:
                    func = tool_call.get("function", {})
                    args = func.get("arguments", "{}")
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}
                    
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tool_call.get("id", ""),
                        "name": func.get("name", ""),
                        "input": args
                    })
                
                anthropic_messages.append({
                    "role": "assistant",
                    "content": content_blocks
                })
            else:
                # Regular assistant message
                anthropic_messages.append({
                    "role": "assistant",
                    "content": content or ""
                })
        
        # Handle tool result messages
        elif role == "tool":
            tool_call_id = msg.get("tool_call_id", "")
            anthropic_messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": content
                }]
            })
        
        # Handle user messages
        else:
            anthropic_messages.append({
                "role": role,
                "content": content or ""
            })
    
    return anthropic_messages


def _convert_tools_to_anthropic(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert OpenAI-style tool schemas to Anthropic format."""
    anthropic_tools = []
    
    for tool in tools:
        if tool.get("type") == "function":
            func = tool.get("function", {})
            anthropic_tools.append({
                "name": func.get("name", ""),
                "description": func.get("description", ""),
                "input_schema": func.get("parameters", {})
            })
    
    return anthropic_tools


def _convert_anthropic_to_openai_format(anthropic_response: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Anthropic Messages API response to OpenAI-compatible format."""
    content_blocks = anthropic_response.get("content", [])
    
    # Extract text and tool calls
    text_content = ""
    tool_calls = []
    
    for block in content_blocks:
        if block.get("type") == "text":
            text_content += block.get("text", "")
        elif block.get("type") == "tool_use":
            tool_calls.append({
                "id": block.get("id", ""),
                "type": "function",
                "function": {
                    "name": block.get("name", ""),
                    "arguments": json.dumps(block.get("input", {}))
                }
            })
    
    message = {
        "role": "assistant",
        "content": text_content or "",
    }
    
    if tool_calls:
        message["tool_calls"] = tool_calls
    
    return {
        "id": anthropic_response.get("id", ""),
        "object": "chat.completion",
        "created": 0,
        "model": anthropic_response.get("model", ""),
        "choices": [{
            "index": 0,
            "message": message,
            "finish_reason": anthropic_response.get("stop_reason", "stop")
        }],
        "usage": anthropic_response.get("usage", {})
    }


__all__ = ["AnthropicError", "request_chat_completion", "AnthropicBaseURL"]
