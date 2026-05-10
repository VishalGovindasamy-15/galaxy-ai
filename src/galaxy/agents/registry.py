"""Agent registry — tracks all active agents.

Manages agent lifecycle: spawn, track, cleanup, enforce limits.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from galaxy.core.constants import IDLE_TIMEOUT_SECONDS, MAX_DOMAIN_AGENTS, MAX_WORKERS_PER_DOMAIN
from galaxy.core.exceptions import AgentLimitError
from galaxy.core.types import AgentStatus, AgentTier
from galaxy.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Central registry for all active agents."""

    def __init__(
        self,
        max_domain_agents: int = MAX_DOMAIN_AGENTS,
        max_workers_per_domain: int = MAX_WORKERS_PER_DOMAIN,
    ) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self.max_domain_agents = max_domain_agents
        self.max_workers_per_domain = max_workers_per_domain

    def register(self, agent: BaseAgent) -> None:
        """Register an agent. Enforces tier limits.

        Raises:
            AgentLimitError: If adding the agent would exceed limits.
        """
        # Check limits
        if agent.tier == AgentTier.DOMAIN:
            current = len(self.get_agents_by_tier(AgentTier.DOMAIN))
            if current >= self.max_domain_agents:
                raise AgentLimitError(
                    f"Domain agent limit reached ({self.max_domain_agents})"
                )

        if agent.tier == AgentTier.WORKER and agent.domain:
            current = len(self.get_agents_by_domain(agent.domain, AgentTier.WORKER))
            if current >= self.max_workers_per_domain:
                raise AgentLimitError(
                    f"Worker limit for domain '{agent.domain}' reached ({self.max_workers_per_domain})"
                )

        self._agents[agent.id] = agent
        logger.info("Registered agent: %s (%s/%s)", agent.name, agent.tier.value, agent.id)

    def unregister(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        if agent_id in self._agents:
            agent = self._agents.pop(agent_id)
            agent.status = AgentStatus.TERMINATED
            logger.info("Unregistered agent: %s", agent_id)
            return True
        return False

    def get(self, agent_id: str) -> BaseAgent | None:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_agents_by_tier(self, tier: AgentTier) -> list[BaseAgent]:
        """Get all agents of a specific tier."""
        return [a for a in self._agents.values() if a.tier == tier]

    def get_agents_by_domain(
        self, domain: str, tier: AgentTier | None = None,
    ) -> list[BaseAgent]:
        """Get all agents in a domain, optionally filtered by tier."""
        agents = [a for a in self._agents.values() if a.domain == domain]
        if tier:
            agents = [a for a in agents if a.tier == tier]
        return agents

    def get_active_agents(self) -> list[BaseAgent]:
        """Get all agents currently working."""
        return [
            a for a in self._agents.values()
            if a.status in (AgentStatus.WORKING, AgentStatus.VALIDATING, AgentStatus.RETRYING)
        ]

    def get_idle_agents(self) -> list[BaseAgent]:
        """Get all idle agents."""
        return [a for a in self._agents.values() if a.status == AgentStatus.IDLE]

    @property
    def count(self) -> int:
        """Total number of registered agents."""
        return len(self._agents)

    @property
    def active_count(self) -> int:
        """Number of currently active agents."""
        return len(self.get_active_agents())

    def cleanup_idle_agents(self, max_idle_seconds: int = IDLE_TIMEOUT_SECONDS) -> int:
        """Remove agents that have been idle too long.

        Returns:
            Number of agents cleaned up.
        """
        now = datetime.now(timezone.utc)
        to_remove: list[str] = []

        for agent in self._agents.values():
            if agent.status == AgentStatus.IDLE and agent.tier == AgentTier.WORKER:
                # Use agent's created_at from info as proxy
                age = (now - agent.info.created_at).total_seconds()
                if age > max_idle_seconds:
                    to_remove.append(agent.id)

        for agent_id in to_remove:
            self.unregister(agent_id)

        if to_remove:
            logger.info("Cleaned up %d idle agents", len(to_remove))
        return len(to_remove)

    def get_summary(self) -> dict[str, int]:
        """Get agent count summary by tier."""
        return {
            "master": len(self.get_agents_by_tier(AgentTier.MASTER)),
            "domain": len(self.get_agents_by_tier(AgentTier.DOMAIN)),
            "worker": len(self.get_agents_by_tier(AgentTier.WORKER)),
            "total": self.count,
            "active": self.active_count,
        }
