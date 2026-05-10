"""Base agent class — foundation for Master, Domain, and Worker agents.

Every agent has:
- An identity (id, name, tier)
- Access to the model router (for LLM calls)
- Access to the tool registry (for tool use)
- Access to the event bus (for communication)
- Checkpoint/restore capability
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from galaxy.core.types import AgentInfo, AgentStatus, AgentTier
from galaxy.events import Event
from galaxy.events.bus import EventBus
from galaxy.models.providers import ChatMessage, ChatResponse
from galaxy.models.router import ModelRouter

logger = logging.getLogger(__name__)


@dataclass
class AgentCheckpoint:
    """Serializable snapshot of agent state for persistence."""

    agent_id: str
    name: str
    tier: str
    status: str
    model: str
    domain: str
    current_task: str
    tasks_completed: int
    tasks_failed: int
    total_tokens: int
    conversation_history: list[dict[str, str]]
    metadata: dict[str, Any]
    timestamp: str


class BaseAgent:
    """Abstract base agent that all Galaxy agents inherit from.

    Provides:
    - LLM invocation via model router
    - Tool execution
    - Event publishing
    - Checkpoint serialization/deserialization
    """

    def __init__(
        self,
        name: str,
        tier: AgentTier,
        model_router: ModelRouter,
        event_bus: EventBus,
        domain: str = "",
        agent_id: str | None = None,
    ) -> None:
        self.id = agent_id or uuid.uuid4().hex[:12]
        self.name = name
        self.tier = tier
        self.model_router = model_router
        self.event_bus = event_bus
        self.domain = domain

        # State
        self.status = AgentStatus.IDLE
        self.current_task: str = ""
        self.conversation_history: list[ChatMessage] = []
        self.tasks_completed: int = 0
        self.tasks_failed: int = 0
        self.total_tokens: int = 0
        self._metadata: dict[str, Any] = {}

    @property
    def info(self) -> AgentInfo:
        """Get current agent info snapshot."""
        model_config = self.model_router.get_model_for_tier(self.tier)
        return AgentInfo(
            id=self.id,
            name=self.name,
            tier=self.tier,
            status=self.status,
            model=model_config.model,
            current_task=self.current_task,
            domain=self.domain,
            tasks_completed=self.tasks_completed,
            tasks_failed=self.tasks_failed,
            total_tokens=self.total_tokens,
        )

    async def invoke_llm(
        self,
        messages: list[ChatMessage] | None = None,
        system_prompt: str = "",
        user_message: str = "",
        tools: list[dict[str, Any]] | None = None,
    ) -> ChatResponse:
        """Invoke the LLM via the model router.

        Can use either explicit messages or system_prompt + user_message shortcut.

        Args:
            messages: Full message list (if provided, ignores system_prompt/user_message).
            system_prompt: System prompt for the model.
            user_message: User message to send.
            tools: Tool definitions for function calling.

        Returns:
            ChatResponse from the model.
        """
        if messages is None:
            messages = []
            if system_prompt:
                messages.append(ChatMessage(role="system", content=system_prompt))
            if user_message:
                messages.append(ChatMessage(role="user", content=user_message))

        # Add conversation history context
        full_messages = list(self.conversation_history) + messages

        response = await self.model_router.chat(
            tier=self.tier,
            messages=full_messages,
            tools=tools,
        )

        # Track tokens
        self.total_tokens += response.total_tokens

        # Store in conversation history
        if user_message:
            self.conversation_history.append(
                ChatMessage(role="user", content=user_message)
            )
        if response.content:
            self.conversation_history.append(
                ChatMessage(role="assistant", content=response.content)
            )

        return response

    async def emit_event(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """Publish an event on the event bus."""
        await self.event_bus.publish(Event(
            type=event_type,
            source=self.id,
            payload=payload or {},
        ))

    def to_checkpoint(self) -> AgentCheckpoint:
        """Serialize agent state for checkpointing."""
        model_config = self.model_router.get_model_for_tier(self.tier)
        return AgentCheckpoint(
            agent_id=self.id,
            name=self.name,
            tier=self.tier.value,
            status=self.status.value,
            model=model_config.model,
            domain=self.domain,
            current_task=self.current_task,
            tasks_completed=self.tasks_completed,
            tasks_failed=self.tasks_failed,
            total_tokens=self.total_tokens,
            conversation_history=[
                {"role": m.role, "content": m.content}
                for m in self.conversation_history[-20:]  # Keep last 20 messages
            ],
            metadata=self._metadata,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint: AgentCheckpoint,
        model_router: ModelRouter,
        event_bus: EventBus,
    ) -> BaseAgent:
        """Restore agent from checkpoint."""
        agent = cls(
            name=checkpoint.name,
            tier=AgentTier(checkpoint.tier),
            model_router=model_router,
            event_bus=event_bus,
            domain=checkpoint.domain,
            agent_id=checkpoint.agent_id,
        )
        agent.status = AgentStatus(checkpoint.status)
        agent.current_task = checkpoint.current_task
        agent.tasks_completed = checkpoint.tasks_completed
        agent.tasks_failed = checkpoint.tasks_failed
        agent.total_tokens = checkpoint.total_tokens
        agent.conversation_history = [
            ChatMessage(role=m["role"], content=m["content"])
            for m in checkpoint.conversation_history
        ]
        agent._metadata = checkpoint.metadata
        return agent

    def reset_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} name={self.name} tier={self.tier.value}>"
