"""Tests for galaxy.scaling.cost_estimator."""

from galaxy.cognitive.types import ExecutionPlan, PlanNode
from galaxy.scaling.cost_estimator import CostEstimate, CostEstimator


class TestCostEstimate:
    def test_default(self) -> None:
        e = CostEstimate()
        assert e.total_chunks == 0

    def test_time_display_seconds(self) -> None:
        e = CostEstimate(estimated_time_minutes=0.5)
        assert "seconds" in e.estimated_time_display

    def test_time_display_minutes(self) -> None:
        e = CostEstimate(estimated_time_minutes=15)
        assert "minutes" in e.estimated_time_display

    def test_time_display_hours(self) -> None:
        e = CostEstimate(estimated_time_minutes=90)
        assert "hours" in e.estimated_time_display


class TestCostEstimator:
    def test_estimate_from_plan(self) -> None:
        estimator = CostEstimator(vram_gb=6.0)
        plan = ExecutionPlan(
            nodes=[
                PlanNode(name="Auth", domain="auth", estimated_chunks=4),
                PlanNode(name="API", domain="backend", estimated_chunks=6),
            ],
            domains=["auth", "backend"],
            estimated_total_chunks=10,
        )
        estimate = estimator.estimate_from_plan(plan)
        assert estimate.total_chunks == 10
        assert estimate.total_domains == 2
        assert estimate.estimated_tokens > 0
        assert estimate.estimated_time_minutes > 0

    def test_estimate_parallelism(self) -> None:
        estimator = CostEstimator(vram_gb=12.0)
        plan = ExecutionPlan(
            nodes=[PlanNode(name=f"N{i}", domain=f"d{i}") for i in range(3)],
            domains=["d0", "d1", "d2"],
            estimated_total_chunks=30,
        )
        estimate = estimator.estimate_from_plan(plan)
        # With 3 domains and 12GB, should have parallelism
        assert estimate.max_concurrent_agents >= 3

    def test_estimate_from_chunks(self) -> None:
        estimator = CostEstimator(vram_gb=6.0)
        estimate = estimator.estimate_from_chunks(20, num_domains=2)
        assert estimate.total_chunks == 20
        assert estimate.estimated_tokens == 20 * 800

    def test_vram_warning(self) -> None:
        estimator = CostEstimator(vram_gb=1.0)  # Very small GPU
        plan = ExecutionPlan(
            nodes=[PlanNode(name=f"N{i}", domain=f"d{i}") for i in range(5)],
            domains=[f"d{i}" for i in range(5)],
            estimated_total_chunks=50,
        )
        estimate = estimator.estimate_from_plan(plan)
        # With 1GB GPU, even 1 agent at 1500MB exceeds 1024MB
        assert any("VRAM" in w for w in estimate.warnings)

    def test_time_warning(self) -> None:
        estimator = CostEstimator(vram_gb=6.0)
        plan = ExecutionPlan(
            nodes=[PlanNode(name="Big", domain="backend", estimated_chunks=200)],
            domains=["backend"],
            estimated_total_chunks=200,
        )
        estimate = estimator.estimate_from_plan(plan)
        if estimate.estimated_time_minutes > 30:
            assert any("time" in w.lower() for w in estimate.warnings)

    def test_small_project_no_warnings(self) -> None:
        estimator = CostEstimator(vram_gb=6.0)
        estimate = estimator.estimate_from_chunks(5, num_domains=1)
        assert len(estimate.warnings) == 0
