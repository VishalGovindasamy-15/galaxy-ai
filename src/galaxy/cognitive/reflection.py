"""Plan Reflection — critiques and validates the execution plan.

Stage 4 of the cognitive pipeline. Reviews the plan for completeness,
identifies missing components, and provides confidence scoring.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from galaxy.cognitive.types import (
    ExecutionPlan,
    ExpandedSpec,
    PipelineStage,
    ReflectionResult,
    RetrievedContext,
    StageResult,
)

logger = logging.getLogger(__name__)


class PlanReflection:
    """Critiques and validates execution plans.

    Checks for completeness, missing dependencies, architectural gaps,
    and provides a confidence score.
    """

    def reflect(
        self,
        spec: ExpandedSpec,
        plan: ExecutionPlan,
        context: RetrievedContext | None = None,
    ) -> ReflectionResult:
        """Reflect on the plan and provide critique.

        Args:
            spec: The original expanded spec.
            plan: The execution plan to critique.
            context: Retrieved context for additional validation.

        Returns:
            ReflectionResult with issues, suggestions, and confidence.
        """
        result = ReflectionResult()

        # Check feature coverage
        self._check_feature_coverage(spec, plan, result)

        # Check domain coverage
        self._check_domain_coverage(spec, plan, result)

        # Check dependency integrity
        self._check_dependencies(plan, result)

        # Check for common missing items
        self._check_common_gaps(spec, plan, result)

        # Calculate confidence
        result.confidence = self._calculate_confidence(result, plan)
        result.approved = result.confidence >= 0.7 and len(result.issues) == 0

        return result

    def reflect_to_stage_result(
        self,
        spec: ExpandedSpec,
        plan: ExecutionPlan,
        context: RetrievedContext | None = None,
    ) -> StageResult:
        """Reflect and wrap in a StageResult."""
        start = time.monotonic()
        reflection = self.reflect(spec, plan, context)
        duration = (time.monotonic() - start) * 1000

        result = StageResult(
            stage=PipelineStage.REFLECT,
            input_data=f"{len(plan.nodes)} nodes, {len(spec.features)} features",
            metadata=reflection.to_dict(),
        )

        output_parts = []
        if reflection.issues:
            output_parts.append("Issues: " + "; ".join(reflection.issues))
        if reflection.suggestions:
            output_parts.append("Suggestions: " + "; ".join(reflection.suggestions))
        output_parts.append(f"Confidence: {reflection.confidence:.2f}")
        output_parts.append(f"Approved: {reflection.approved}")

        result.complete("\n".join(output_parts), duration)
        return result

    def _check_feature_coverage(
        self,
        spec: ExpandedSpec,
        plan: ExecutionPlan,
        result: ReflectionResult,
    ) -> None:
        """Check if all features are covered by plan nodes."""
        plan_descriptions = " ".join(n.description.lower() for n in plan.nodes)

        for feature in spec.features:
            # Simple keyword matching
            feature_words = set(feature.lower().split())
            significant_words = {w for w in feature_words if len(w) > 3}

            if significant_words and not any(w in plan_descriptions for w in significant_words):
                result.missing_items.append(f"Feature not covered: {feature[:60]}")

    def _check_domain_coverage(
        self,
        spec: ExpandedSpec,
        plan: ExecutionPlan,
        result: ReflectionResult,
    ) -> None:
        """Check if all required domains have plan nodes."""
        plan_domains = set(n.domain for n in plan.nodes)
        for domain in spec.domains:
            if domain not in plan_domains:
                result.suggestions.append(f"Domain '{domain}' has no plan nodes")

    def _check_dependencies(
        self,
        plan: ExecutionPlan,
        result: ReflectionResult,
    ) -> None:
        """Check dependency integrity."""
        node_ids = {n.id for n in plan.nodes}
        for node in plan.nodes:
            for dep_id in node.dependencies:
                if dep_id not in node_ids:
                    result.issues.append(
                        f"Node '{node.name}' depends on missing node: {dep_id}"
                    )

        # Check for circular dependencies
        if self._has_cycle(plan):
            result.issues.append("Circular dependency detected in plan")

    def _check_common_gaps(
        self,
        spec: ExpandedSpec,
        plan: ExecutionPlan,
        result: ReflectionResult,
    ) -> None:
        """Check for commonly missing items."""
        plan_text = " ".join(n.description.lower() for n in plan.nodes)

        if "auth" in " ".join(spec.domains) and "error" not in plan_text:
            result.suggestions.append("Consider adding error handling for auth failures")

        if "database" in " ".join(spec.domains) and "migration" not in plan_text:
            result.suggestions.append("Consider adding database migration setup")

        if len(plan.nodes) > 0 and not any("test" in n.domain for n in plan.nodes):
            result.suggestions.append("No test nodes in plan — consider adding tests")

    def _calculate_confidence(
        self,
        result: ReflectionResult,
        plan: ExecutionPlan,
    ) -> float:
        """Calculate confidence score (0.0 to 1.0)."""
        score = 1.0

        # Deduct for issues
        score -= len(result.issues) * 0.2

        # Deduct for missing items
        score -= len(result.missing_items) * 0.1

        # Slight deduction for suggestions (not critical)
        score -= len(result.suggestions) * 0.02

        # Bonus for having diverse domains
        if len(plan.domains) >= 3:
            score += 0.05

        # Bonus for having a reasonable number of nodes
        if 3 <= len(plan.nodes) <= 20:
            score += 0.05

        return max(0.0, min(1.0, score))

    def _has_cycle(self, plan: ExecutionPlan) -> bool:
        """Check for circular dependencies using DFS."""
        node_map = {n.id: n for n in plan.nodes}
        visited: set[str] = set()
        in_stack: set[str] = set()

        def dfs(node_id: str) -> bool:
            if node_id in in_stack:
                return True
            if node_id in visited:
                return False
            visited.add(node_id)
            in_stack.add(node_id)
            node = node_map.get(node_id)
            if node:
                for dep_id in node.dependencies:
                    if dfs(dep_id):
                        return True
            in_stack.discard(node_id)
            return False

        return any(dfs(n.id) for n in plan.nodes)
