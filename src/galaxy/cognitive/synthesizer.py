"""Plan Synthesizer — merges all pipeline outputs into a final plan.

Stage 5 of the cognitive pipeline. Takes all previous stage outputs
and synthesizes them into a coherent, actionable execution plan.
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


class PlanSynthesizer:
    """Synthesizes all pipeline stage outputs into a final plan.

    Merges the expanded spec, execution plan, retrieved context,
    and reflection results into a comprehensive, actionable plan.
    """

    def synthesize(
        self,
        spec: ExpandedSpec,
        plan: ExecutionPlan,
        context: RetrievedContext,
        reflection: ReflectionResult,
    ) -> str:
        """Synthesize all outputs into a final plan document.

        Args:
            spec: Expanded specification.
            plan: Execution plan DAG.
            context: Retrieved workspace context.
            reflection: Plan critique and validation.

        Returns:
            Formatted plan document string.
        """
        sections: list[str] = []

        # Header
        sections.append(self._build_header(spec))

        # Tech stack
        sections.append(self._build_tech_section(spec))

        # Execution plan
        sections.append(self._build_plan_section(plan))

        # Context awareness
        if context.patterns or context.documentation:
            sections.append(self._build_context_section(context))

        # Reflection notes
        if reflection.suggestions or reflection.issues:
            sections.append(self._build_reflection_section(reflection))

        # Summary
        sections.append(self._build_summary(plan, reflection))

        return "\n\n".join(sections)

    def synthesize_to_stage_result(
        self,
        spec: ExpandedSpec,
        plan: ExecutionPlan,
        context: RetrievedContext,
        reflection: ReflectionResult,
    ) -> StageResult:
        """Synthesize and wrap in a StageResult."""
        start = time.monotonic()
        final_plan = self.synthesize(spec, plan, context, reflection)
        duration = (time.monotonic() - start) * 1000

        result = StageResult(
            stage=PipelineStage.SYNTHESIZE,
            input_data=f"spec + {len(plan.nodes)} nodes + context + reflection",
            metadata={
                "plan_length": len(final_plan),
                "confidence": reflection.confidence,
                "domains": plan.domains,
            },
        )
        result.complete(final_plan, duration)
        return result

    def _build_header(self, spec: ExpandedSpec) -> str:
        lines = [
            f"# Project Plan: {spec.project_type}",
            "",
            f"**Original Request:** {spec.original_prompt}",
        ]
        if spec.ambiguities:
            lines.append("")
            lines.append("**Ambiguities to resolve:**")
            for a in spec.ambiguities:
                lines.append(f"  - {a}")
        return "\n".join(lines)

    def _build_tech_section(self, spec: ExpandedSpec) -> str:
        lines = [
            "## Technology Stack",
            ", ".join(spec.tech_stack),
        ]
        if spec.constraints:
            lines.append("")
            lines.append("**Constraints:**")
            for c in spec.constraints:
                lines.append(f"  - {c}")
        if spec.non_functional:
            lines.append("")
            lines.append("**Non-Functional Requirements:**")
            for nf in spec.non_functional:
                lines.append(f"  - {nf}")
        return "\n".join(lines)

    def _build_plan_section(self, plan: ExecutionPlan) -> str:
        lines = [
            "## Execution Plan",
            f"**Domains:** {', '.join(plan.domains)}",
            f"**Estimated Chunks:** {plan.estimated_total_chunks}",
            "",
        ]

        # Group by domain
        by_domain: dict[str, list[Any]] = {}
        for node in plan.nodes:
            by_domain.setdefault(node.domain, []).append(node)

        for domain, nodes in by_domain.items():
            lines.append(f"### Domain: {domain}")
            for node in nodes:
                deps = f" (depends on: {len(node.dependencies)} nodes)" if node.dependencies else ""
                lines.append(f"  - [{node.priority}] {node.name}{deps} — ~{node.estimated_chunks} chunks")
            lines.append("")

        # Execution order
        lines.append("### Execution Order")
        for i, node_id in enumerate(plan.execution_order, 1):
            node = plan.get_node(node_id)
            if node:
                lines.append(f"  {i}. [{node.domain}] {node.name}")

        return "\n".join(lines)

    def _build_context_section(self, context: RetrievedContext) -> str:
        lines = ["## Context"]
        if context.patterns:
            lines.append(f"**Detected Patterns:** {', '.join(context.patterns)}")
        if context.documentation:
            lines.append("")
            lines.append("**Tech Notes:**")
            for doc in context.documentation[:5]:
                lines.append(f"  - {doc}")
        if context.relevant_files:
            lines.append(f"\n**Existing Files:** {len(context.relevant_files)} found")
        return "\n".join(lines)

    def _build_reflection_section(self, reflection: ReflectionResult) -> str:
        lines = ["## Review Notes"]
        if reflection.issues:
            lines.append("**Issues:**")
            for issue in reflection.issues:
                lines.append(f"  ⚠ {issue}")
        if reflection.suggestions:
            lines.append("**Suggestions:**")
            for s in reflection.suggestions:
                lines.append(f"  → {s}")
        if reflection.missing_items:
            lines.append("**Missing:**")
            for m in reflection.missing_items:
                lines.append(f"  ✗ {m}")
        return "\n".join(lines)

    def _build_summary(self, plan: ExecutionPlan, reflection: ReflectionResult) -> str:
        status = "✓ APPROVED" if reflection.approved else "⚠ NEEDS REVIEW"
        return (
            f"## Summary\n"
            f"**Status:** {status}\n"
            f"**Confidence:** {reflection.confidence:.0%}\n"
            f"**Total Nodes:** {len(plan.nodes)}\n"
            f"**Total Domains:** {len(plan.domains)}\n"
            f"**Estimated Chunks:** {plan.estimated_total_chunks}"
        )
