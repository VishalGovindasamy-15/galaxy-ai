"""Cognitive Pipeline — orchestrates the 5-stage reasoning engine.

Runs: Expand → Plan → Retrieve → Reflect → Synthesize
Produces a comprehensive, validated execution plan from a raw prompt.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from galaxy.cognitive.expander import PromptExpander
from galaxy.cognitive.planner import TaskPlanner
from galaxy.cognitive.reflection import PlanReflection
from galaxy.cognitive.retriever import ContextRetriever
from galaxy.cognitive.synthesizer import PlanSynthesizer
from galaxy.cognitive.types import (
    CognitiveMode,
    ExpandedSpec,
    ExecutionPlan,
    PipelineStage,
    PipelineState,
    ReflectionResult,
    RetrievedContext,
    StageResult,
    StageStatus,
)

logger = logging.getLogger(__name__)


class CognitivePipeline:
    """Orchestrates the full cognitive reasoning pipeline.

    Usage:
        pipeline = CognitivePipeline(workspace=Path("."))
        state = pipeline.run("Build a REST API with auth and CRUD")
        print(state.final_plan)
    """

    def __init__(self, workspace: Path | None = None) -> None:
        self._workspace = workspace
        self._expander = PromptExpander()
        self._planner = TaskPlanner()
        self._retriever = ContextRetriever(workspace)
        self._reflection = PlanReflection()
        self._synthesizer = PlanSynthesizer()

    def run(
        self,
        prompt: str,
        mode: CognitiveMode = CognitiveMode.REASONING,
        context: str = "",
    ) -> PipelineState:
        """Run the cognitive pipeline on a prompt.

        Args:
            prompt: Raw user prompt.
            mode: Pipeline mode (NORMAL=fast, REASONING=deep).
            context: Additional context (e.g., from brainstorm spec).

        Returns:
            PipelineState with all stage results and final plan.
        """
        state = PipelineState(
            mode=mode,
            original_prompt=prompt,
        )
        start = time.monotonic()

        if mode == CognitiveMode.NORMAL:
            self._run_normal(prompt, context, state)
        else:
            self._run_reasoning(prompt, context, state)

        state.total_duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "Pipeline complete: %s mode, %d stages, %.0fms",
            mode.value,
            len(state.stage_results),
            state.total_duration_ms,
        )
        return state

    def _run_normal(self, prompt: str, context: str, state: PipelineState) -> None:
        """Fast mode — expand and plan only."""
        # Stage 1: Expand
        expand_result = self._expander.expand_to_stage_result(prompt, context)
        state.stage_results.append(expand_result)

        if expand_result.status == StageStatus.FAILED:
            return

        spec = ExpandedSpec.from_dict(expand_result.metadata)

        # Stage 2: Plan
        plan_result = self._planner.plan_to_stage_result(spec)
        state.stage_results.append(plan_result)

        plan = ExecutionPlan(**{
            k: v for k, v in plan_result.metadata.items()
            if k != "nodes"
        })
        # Reconstruct nodes
        if "nodes" in plan_result.metadata:
            from galaxy.cognitive.types import PlanNode
            plan.nodes = [PlanNode.from_dict(n) for n in plan_result.metadata["nodes"]]

        # Simple synthesis for normal mode
        state.final_plan = (
            f"Project: {spec.project_type}\n"
            f"Tech: {', '.join(spec.tech_stack)}\n"
            f"Tasks: {len(plan.nodes)}\n\n"
            + plan_result.output_data
        )

    def _run_reasoning(self, prompt: str, context: str, state: PipelineState) -> None:
        """Deep mode — full 5-stage pipeline."""

        # Stage 1: Expand
        expand_result = self._expander.expand_to_stage_result(prompt, context)
        state.stage_results.append(expand_result)
        if expand_result.status == StageStatus.FAILED:
            return
        spec = ExpandedSpec.from_dict(expand_result.metadata)

        # Stage 2: Plan
        plan_result = self._planner.plan_to_stage_result(spec)
        state.stage_results.append(plan_result)
        if plan_result.status == StageStatus.FAILED:
            return

        # Reconstruct plan from metadata
        plan = self._reconstruct_plan(plan_result.metadata)

        # Stage 3: Retrieve
        retrieve_result = self._retriever.retrieve_to_stage_result(
            prompt=prompt,
            domains=spec.domains,
            tech_stack=spec.tech_stack,
        )
        state.stage_results.append(retrieve_result)
        retrieved_context = RetrievedContext(
            patterns=retrieve_result.metadata.get("patterns", []),
            documentation=self._retriever.retrieve(
                prompt=prompt, domains=spec.domains, tech_stack=spec.tech_stack
            ).documentation,
        )

        # Stage 4: Reflect
        reflect_result = self._reflection.reflect_to_stage_result(spec, plan, retrieved_context)
        state.stage_results.append(reflect_result)
        reflection = ReflectionResult(**reflect_result.metadata)

        # Stage 5: Synthesize
        synth_result = self._synthesizer.synthesize_to_stage_result(
            spec, plan, retrieved_context, reflection,
        )
        state.stage_results.append(synth_result)

        state.final_plan = synth_result.output_data

    def _reconstruct_plan(self, metadata: dict[str, Any]) -> ExecutionPlan:
        """Reconstruct an ExecutionPlan from stage metadata."""
        from galaxy.cognitive.types import PlanNode
        nodes = [PlanNode.from_dict(n) for n in metadata.get("nodes", [])]
        return ExecutionPlan(
            nodes=nodes,
            execution_order=metadata.get("execution_order", []),
            domains=metadata.get("domains", []),
            estimated_total_chunks=metadata.get("estimated_total_chunks", 0),
        )

    @property
    def expander(self) -> PromptExpander:
        return self._expander

    @property
    def planner(self) -> TaskPlanner:
        return self._planner

    @property
    def retriever(self) -> ContextRetriever:
        return self._retriever

    @property
    def reflection(self) -> PlanReflection:
        return self._reflection

    @property
    def synthesizer(self) -> PlanSynthesizer:
        return self._synthesizer
