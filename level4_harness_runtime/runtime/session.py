"""Append-only session log and model-history projection.

The important Harness idea is that runtime state should not live only in local
variables.  Durable facts are recorded as events, and model history can be
reconstructed from them.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SessionLog:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.events: list[dict[str, Any]] = []
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, **data: Any) -> dict[str, Any]:
        event = {
            "seq": len(self.events) + 1,
            "time": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "data": data,
        }
        self.events.append(event)
        if self.path:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def derive_messages(self) -> list[dict[str, Any]]:
        """Project OpenAI-compatible chat history from durable events."""
        messages: list[dict[str, Any]] = []
        for event in self.events:
            data = event["data"]
            if event["type"] == "user/message":
                messages.append({"role": "user", "content": data["content"]})
            elif event["type"] == "assistant/message":
                msg: dict[str, Any] = {
                    "role": "assistant",
                    "content": data.get("content"),
                }
                if data.get("tool_calls"):
                    msg["tool_calls"] = data["tool_calls"]
                messages.append(msg)
            elif event["type"] == "tool/result":
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": data["tool_call_id"],
                        "content": data["content"],
                    }
                )
        return messages

    def last_user_text(self) -> str:
        for event in reversed(self.events):
            if event["type"] == "user/message":
                return str(event["data"].get("content", ""))
        return ""

    def recent_tool_text(self, limit: int = 4) -> str:
        items: list[str] = []
        for event in reversed(self.events):
            if event["type"] == "tool/result":
                items.append(str(event["data"].get("content", "")))
                if len(items) >= limit:
                    break
        return "\n".join(reversed(items))

    def model_context_snapshots(self) -> list[dict[str, Any]]:
        return [e for e in self.events if e["type"] == "model/context"]
