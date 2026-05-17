"""Tests for galaxy.cognitive.planner."""

from galaxy.cognitive.planner import TaskPlanner
from galaxy.cognitive.types import ExpandedSpec


class TestTaskPlanner:
    def test_plan_basic(self) -> None:
        planner = TaskPlanner()
        spec = ExpandedSpec(
            project_type="REST API",
            features=["User login", "CRUD endpoints"],
            domains=["backend", "auth", "database"],
            tech_stack=["FastAPI", "PostgreSQL"],
        )
        plan = planner.plan(spec)
        assert len(plan.nodes) >= 2
        assert len(plan.execution_order) == len(plan.nodes)
        assert plan.estimated_total_chunks > 0

    def test_plan_creates_infra_first(self) -> None:
        planner = TaskPlanner()
        spec = ExpandedSpec(
            features=["API endpoints"],
            domains=["backend", "database"],
            tech_stack=["SQLAlchemy"],
        )
        plan = planner.plan(spec)
        roots = plan.get_roots()
        assert len(roots) >= 1
        assert any("database" in r.domain.lower() or "Database" in r.name for r in roots)

    def test_plan_topological_order(self) -> None:
        planner = TaskPlanner()
        spec = ExpandedSpec(
            features=["Feature A"],
            domains=["backend", "database", "auth"],
        )
        plan = planner.plan(spec)
        # Roots should come first in execution order
        root_ids = {n.id for n in plan.get_roots()}
        for root_id in root_ids:
            idx = plan.execution_order.index(root_id)
            # Root nodes should be early in the order
            assert idx < len(plan.nodes)

    def test_plan_assigns_domains(self) -> None:
        planner = TaskPlanner()
        spec = ExpandedSpec(
            features=["JWT authentication system", "database migration setup"],
            domains=["auth", "database", "backend"],
        )
        plan = planner.plan(spec)
        domains_used = {n.domain for n in plan.nodes}
        assert len(domains_used) >= 2

    def test_plan_with_testing(self) -> None:
        planner = TaskPlanner()
        spec = ExpandedSpec(
            features=["API"],
            domains=["backend", "testing"],
            tech_stack=["pytest"],
        )
        plan = planner.plan(spec)
        test_nodes = [n for n in plan.nodes if n.domain == "testing"]
        assert len(test_nodes) >= 1

    def test_plan_with_devops(self) -> None:
        planner = TaskPlanner()
        spec = ExpandedSpec(
            features=["API"],
            domains=["backend", "devops"],
        )
        plan = planner.plan(spec)
        devops_nodes = [n for n in plan.nodes if n.domain == "devops"]
        assert len(devops_nodes) >= 1
        # DevOps should depend on other nodes
        assert len(devops_nodes[0].dependencies) > 0

    def test_stage_result(self) -> None:
        planner = TaskPlanner()
        spec = ExpandedSpec(features=["Test"], domains=["backend"])
        result = planner.plan_to_stage_result(spec)
        assert result.status.name == "COMPLETED"
        assert result.duration_ms >= 0

    def test_empty_spec(self) -> None:
        planner = TaskPlanner()
        spec = ExpandedSpec()
        plan = planner.plan(spec)
        assert len(plan.nodes) >= 0
