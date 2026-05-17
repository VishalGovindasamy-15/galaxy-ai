"""Task Planner — creates dependency-aware execution DAG.

Stage 2 of the cognitive pipeline. Takes an ExpandedSpec and produces
an ExecutionPlan with topologically-sorted task nodes.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from galaxy.cognitive.types import (
    ExpandedSpec,
    ExecutionPlan,
    PipelineStage,
    PlanNode,
    StageResult,
)

logger = logging.getLogger(__name__)


class TaskPlanner:
    """Converts expanded specs into dependency-aware execution plans.

    Analyzes feature dependencies and creates a DAG of tasks
    that can be executed by domain agents and workers.
    """

    def plan(self, spec: ExpandedSpec) -> ExecutionPlan:
        """Create an execution plan from an expanded spec.

        Args:
            spec: The expanded engineering specification.

        Returns:
            ExecutionPlan with dependency-sorted task nodes.
        """
        nodes: list[PlanNode] = []

        # Create infrastructure nodes first (no dependencies)
        infra_ids: list[str] = []
        if any("database" in d for d in spec.domains) or any("sql" in t.lower() for t in spec.tech_stack):
            node = PlanNode(
                name="Database Setup",
                domain="database",
                description="Create database models and migrations",
                priority=1,
                estimated_chunks=3,
            )
            nodes.append(node)
            infra_ids.append(node.id)

        if any("auth" in d for d in spec.domains):
            node = PlanNode(
                name="Authentication System",
                domain="auth",
                description="Implement authentication and authorization",
                dependencies=infra_ids.copy(),
                priority=1,
                estimated_chunks=4,
            )
            nodes.append(node)

        # Create feature nodes
        feature_deps = [n.id for n in nodes]  # Features depend on infra
        for i, feature in enumerate(spec.features):
            node = PlanNode(
                name=feature[:60],
                domain=self._assign_domain(feature, spec.domains),
                description=feature,
                dependencies=feature_deps[:2],  # Depend on infra, not each other
                priority=2,
                estimated_chunks=self._estimate_chunks(feature),
            )
            nodes.append(node)

        # Create testing node (depends on all features)
        if any("testing" in d for d in spec.domains) or any("test" in t.lower() for t in spec.tech_stack):
            feature_ids = [n.id for n in nodes if n.priority == 2]
            node = PlanNode(
                name="Test Suite",
                domain="testing",
                description="Write tests for all components",
                dependencies=feature_ids,
                priority=3,
                estimated_chunks=len(feature_ids) * 2,
            )
            nodes.append(node)

        # Create devops node (depends on everything)
        if any("devops" in d for d in spec.domains):
            all_ids = [n.id for n in nodes]
            node = PlanNode(
                name="DevOps Setup",
                domain="devops",
                description="Docker, CI/CD, deployment configuration",
                dependencies=all_ids,
                priority=4,
                estimated_chunks=2,
            )
            nodes.append(node)

        # Topological sort
        execution_order = self._topological_sort(nodes)

        plan = ExecutionPlan(
            nodes=nodes,
            execution_order=execution_order,
            domains=list(set(n.domain for n in nodes)),
            estimated_total_chunks=sum(n.estimated_chunks for n in nodes),
        )

        logger.debug(
            "Created plan: %d nodes, %d domains, %d estimated chunks",
            len(nodes), len(plan.domains), plan.estimated_total_chunks,
        )
        return plan

    def plan_to_stage_result(self, spec: ExpandedSpec) -> StageResult:
        """Plan and wrap in a StageResult."""
        start = time.monotonic()
        plan = self.plan(spec)
        duration = (time.monotonic() - start) * 1000

        result = StageResult(
            stage=PipelineStage.PLAN,
            input_data=spec.to_prompt(),
            metadata=plan.to_dict(),
        )
        output = "\n".join(f"[{n.domain}] {n.name}" for n in plan.nodes)
        result.complete(output, duration)
        return result

    def _assign_domain(self, feature: str, available_domains: list[str]) -> str:
        """Assign a feature to the most appropriate domain."""
        feature_lower = feature.lower()
        domain_keywords = {
            "auth": ["auth", "login", "jwt", "user", "session"],
            "backend": ["api", "endpoint", "route", "crud", "service"],
            "frontend": ["ui", "component", "page", "react", "view"],
            "database": ["model", "schema", "migration", "query"],
            "testing": ["test", "spec", "coverage"],
            "devops": ["docker", "deploy", "ci"],
        }
        for domain, keywords in domain_keywords.items():
            if any(kw in feature_lower for kw in keywords):
                if domain in available_domains:
                    return domain
        return available_domains[0] if available_domains else "backend"

    def _estimate_chunks(self, feature: str) -> int:
        """Estimate number of code chunks for a feature."""
        # Simple heuristic based on description length and complexity keywords
        complexity_keywords = ["system", "integration", "pipeline", "workflow"]
        base = 2
        if any(kw in feature.lower() for kw in complexity_keywords):
            base += 2
        if len(feature) > 50:
            base += 1
        return base

    def _topological_sort(self, nodes: list[PlanNode]) -> list[str]:
        """Topological sort of plan nodes."""
        node_map = {n.id: n for n in nodes}
        visited: set[str] = set()
        order: list[str] = []

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            node = node_map.get(node_id)
            if node:
                for dep_id in node.dependencies:
                    if dep_id in node_map:
                        visit(dep_id)
            order.append(node_id)

        for node in nodes:
            visit(node.id)

        return order
