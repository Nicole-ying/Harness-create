"""Reusable teaching Harness: Agent loop + session + capabilities + plugins."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from .events import EventBus
from .plugin import PluginManager
from .registries import ContextRegistry, ToolRegistry
from .session import SessionLog


class AgentHarness:
    def __init__(
        self,
        *,
        llm: Any,
        base_prompt: str,
        max_steps: int = 8,
        session_path: Path | None = None,
    ) -> None:
        self.llm = llm
        self.max_steps = max_steps
        self.events = EventBus()
        self.session = SessionLog(session_path)
        self.tools = ToolRegistry()
        self.context = ContextRegistry(base_prompt)
        self.plugins = PluginManager(
            tools=self.tools,
            context=self.context,
            events=self.events,
            session=self.session,
        )

    async def mount(self, plugin: Any) -> None:
        await self.plugins.mount(plugin)

    async def close(self) -> None:
        await self.plugins.close()

    async def __aenter__(self) -> "AgentHarness":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    async def run_turn(self, user_text: str) -> str:
        self.session.append("turn/start", user_text=user_text)
        await self.events.emit("turn/start", {"user_text": user_text})
        self.session.append("user/message", content=user_text)

        for step_index in range(1, self.max_steps + 1):
            system_prompt = await self.context.build(self.session)
            tool_schemas = self.tools.schemas()

            # Record the exact model-visible context snapshot.  The model request
            # can therefore be inspected/replayed from the session log.
            self.session.append(
                "model/context",
                step=step_index,
                system_prompt=system_prompt,
                tools=tool_schemas,
            )

            messages = [
                {"role": "system", "content": system_prompt},
                *self.session.derive_messages(),
            ]
            pre_payload = {
                "step": step_index,
                "messages": messages,
                "tools": tool_schemas,
            }
            await self.events.emit("agent/pre-step", pre_payload)

            response = await asyncio.to_thread(
                self.llm.completion,
                messages=pre_payload["messages"],
                tools=pre_payload["tools"] or None,
                tool_choice="auto" if pre_payload["tools"] else None,
            )
            choice = response.choices[0]
            message = choice.message

            await self.events.emit(
                "agent/post-step",
                {
                    "step": step_index,
                    "finish_reason": choice.finish_reason,
                    "message": message,
                },
            )

            tool_calls = []
            for call in message.tool_calls or []:
                tool_calls.append(
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                )

            self.session.append(
                "assistant/message",
                content=message.content,
                finish_reason=choice.finish_reason,
                tool_calls=tool_calls,
            )

            if not tool_calls:
                answer = message.content or ""
                self.session.append("turn/end", status="completed", answer=answer)
                await self.events.emit("turn/end", {"status": "completed", "answer": answer})
                return answer

            for call in tool_calls:
                name = call["function"]["name"]
                raw_arguments = call["function"]["arguments"]
                try:
                    arguments = json.loads(raw_arguments or "{}")
                    if not isinstance(arguments, dict):
                        raise TypeError("Tool arguments must decode to a JSON object")
                except Exception as exc:
                    arguments = {}
                    tool_text = json.dumps(
                        {"error": f"Invalid tool arguments: {type(exc).__name__}: {exc}"},
                        ensure_ascii=False,
                    )
                else:
                    self.session.append(
                        "tool/call",
                        tool_call_id=call["id"],
                        name=name,
                        arguments=arguments,
                    )
                    payload = {
                        "tool_call_id": call["id"],
                        "name": name,
                        "arguments": arguments,
                    }
                    await self.events.emit("tools/pre-execute", payload)
                    try:
                        tool_text = await self.tools.execute(name, payload["arguments"])
                    except Exception as exc:
                        tool_text = json.dumps(
                            {"error": f"{type(exc).__name__}: {exc}"},
                            ensure_ascii=False,
                        )
                    post_payload = {**payload, "result": tool_text}
                    await self.events.emit("tools/post-execute", post_payload)
                    tool_text = str(post_payload["result"])

                self.session.append(
                    "tool/result",
                    tool_call_id=call["id"],
                    name=name,
                    content=tool_text,
                )

        self.session.append("turn/end", status="max_steps_exceeded")
        await self.events.emit("turn/end", {"status": "max_steps_exceeded"})
        raise RuntimeError(
            f"Harness exceeded max_steps={self.max_steps} without a final answer"
        )
