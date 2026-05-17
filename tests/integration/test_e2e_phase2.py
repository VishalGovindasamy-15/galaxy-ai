"""End-to-end Phase 2 test: Full pipeline from prompt to project files.

PHASE GATE: Tests the complete flow:
  Prompt → Brainstorm → Cognitive Pipeline → Contracts → Chunks → Integrator → Files

This validates that all Phase 2 subsystems work together.
"""

from pathlib import Path

from galaxy.brainstorm.engine import BrainstormEngine
from galaxy.cognitive.pipeline import CognitivePipeline
from galaxy.cognitive.types import CognitiveMode
from galaxy.contracts.builder import ContractBuilder
from galaxy.contracts.types import ChunkOperation, CodeChunk
from galaxy.integrator.engine import IntegratorEngine
from galaxy.project.loader import ProjectLoader
from galaxy.project.spec import DomainSpec, FileSpec, FileStatus, ProjectSpec, ProjectStatus
from galaxy.scaling.cost_estimator import CostEstimator
from galaxy.scaling.limiter import RateLimiter, ResourceLimit


class TestEndToEndPhase2:
    """Full Phase 2 pipeline: prompt → brainstorm → plan → contracts → files."""

    def test_full_pipeline(self, tmp_path: Path) -> None:
        """Complete E2E test simulating a real Galaxy run."""

        # ─── Step 1: Brainstorm ──────────────────────────────────────────
        brainstorm = BrainstormEngine(workspace=tmp_path)
        brainstorm.start_session("Build a REST API with JWT auth and CRUD")
        brainstorm.add_idea("JWT Authentication")
        brainstorm.add_idea("User CRUD endpoints")
        brainstorm.add_idea("PostgreSQL database models")

        for idea in brainstorm.temp_store.list_all():
            brainstorm.approve_idea(idea.id)

        project_spec_dict = brainstorm.get_project_spec()
        assert len(project_spec_dict) > 0

        # ─── Step 2: Cognitive Pipeline ─────────────────────────────────
        pipeline = CognitivePipeline(workspace=tmp_path)
        state = pipeline.run(
            "Build a REST API with JWT auth and user CRUD",
            mode=CognitiveMode.REASONING,
        )
        assert state.success
        assert state.final_plan
        assert len(state.stage_results) == 5

        # ─── Step 3: Cost Estimation ────────────────────────────────────
        estimator = CostEstimator(vram_gb=6.0)
        estimate = estimator.estimate_from_chunks(10, num_domains=2)
        assert estimate.total_chunks == 10
        assert estimate.estimated_time_minutes > 0

        # ─── Step 4: Rate Limiting ──────────────────────────────────────
        limiter = RateLimiter(ResourceLimit.for_gpu(6.0))
        assert limiter.can_proceed()
        assert limiter.acquire(estimated_tokens=500)

        # ─── Step 5: Contracts ──────────────────────────────────────────
        builder = ContractBuilder("backend")
        contracts = []

        c1 = (
            builder.reset()
            .target("auth/service.py", "create_jwt_token")
            .operation(ChunkOperation.CREATE_FUNCTION)
            .description("Create JWT token for user authentication")
            .param("user_id", "int", description="User database ID")
            .param("secret", "str", description="JWT signing secret")
            .returns("str", "Encoded JWT token")
            .depends_on("jwt", "datetime")
            .build()
        )
        contracts.append(c1)

        c2 = (
            builder.reset()
            .target("models/user.py", "User")
            .operation(ChunkOperation.CREATE_CLASS)
            .description("User data model")
            .param("name", "str")
            .param("email", "str")
            .build()
        )
        contracts.append(c2)

        c3 = (
            builder.reset()
            .target("routes/users.py", "get_users")
            .operation(ChunkOperation.CREATE_FUNCTION)
            .description("List all users endpoint")
            .returns("list[dict]")
            .depends_on("fastapi")
            .build()
        )
        contracts.append(c3)

        # ─── Step 6: Worker chunks (simulated) ─────────────────────────
        chunks = [
            CodeChunk(
                contract_id=c1.id,
                target_file="auth/service.py",
                target_symbol="create_jwt_token",
                operation=ChunkOperation.CREATE_FUNCTION,
                content=(
                    "import jwt\nfrom datetime import datetime, timedelta\n\n"
                    "def create_jwt_token(user_id: int, secret: str) -> str:\n"
                    '    payload = {"user_id": user_id, "exp": datetime.utcnow() + timedelta(hours=1)}\n'
                    '    return jwt.encode(payload, secret, algorithm="HS256")\n'
                ),
                dependencies=["jwt", "datetime"],
                worker_id="worker-001",
            ),
            CodeChunk(
                contract_id=c2.id,
                target_file="models/user.py",
                target_symbol="User",
                operation=ChunkOperation.CREATE_CLASS,
                content=(
                    "from dataclasses import dataclass\n\n"
                    "@dataclass\nclass User:\n    name: str\n    email: str\n"
                ),
                worker_id="worker-002",
            ),
            CodeChunk(
                contract_id=c3.id,
                target_file="routes/users.py",
                target_symbol="get_users",
                operation=ChunkOperation.CREATE_FUNCTION,
                content=(
                    "from fastapi import APIRouter\n\n"
                    "router = APIRouter()\n\n"
                    "@router.get('/users')\n"
                    "def get_users() -> list[dict]:\n    return []\n"
                ),
                dependencies=["fastapi"],
                worker_id="worker-003",
            ),
        ]

        # ─── Step 7: Integrator merges chunks → files ──────────────────
        integrator = IntegratorEngine()
        for chunk in chunks:
            result = integrator.integrate(chunk)
            assert result.success

        assert integrator.file_count == 3

        # Write to disk
        output_dir = tmp_path / "output"
        written = integrator.write_all(output_dir)
        assert len(written) == 3
        assert (output_dir / "auth" / "service.py").exists()
        assert (output_dir / "models" / "user.py").exists()
        assert (output_dir / "routes" / "users.py").exists()

        # Verify file contents
        auth_content = (output_dir / "auth" / "service.py").read_text()
        assert "def create_jwt_token" in auth_content
        assert "import jwt" in auth_content

        model_content = (output_dir / "models" / "user.py").read_text()
        assert "class User" in model_content

        # ─── Step 8: Project Spec ──────────────────────────────────────
        project = ProjectSpec(
            name="my-api",
            description="REST API with auth and CRUD",
            project_type="REST API",
            tech_stack=["FastAPI", "PostgreSQL", "JWT"],
            status=ProjectStatus.BUILDING,
            master_model="qwen2.5-coder:3b",
        )

        for chunk in chunks:
            project.add_file(FileSpec(
                path=chunk.target_file,
                domain="backend",
                status=FileStatus.INTEGRATED,
                symbols=[chunk.target_symbol] if chunk.target_symbol else [],
            ))

        project.add_domain(DomainSpec(
            name="backend",
            description="Backend API domain",
            files=[c.target_file for c in contracts],
        ))

        project.calculate_progress()
        assert project.progress == 1.0  # All files integrated

        # Save and reload
        loader = ProjectLoader(workspace=tmp_path)
        loader.save(project)
        reloaded = loader.load()
        assert reloaded is not None
        assert reloaded.name == "my-api"
        assert reloaded.file_count == 3
        assert reloaded.domain_count == 1

        # Release rate limiter
        limiter.release()
        assert limiter.active_agents == 0

        # ─── Summary ───────────────────────────────────────────────────
        summary = integrator.get_summary()
        assert summary["files"] == 3
        assert summary["chunks_merged"] == 3

    def test_project_analysis_and_spec(self, tmp_path: Path) -> None:
        """Analyze an existing project and create a spec."""
        from galaxy.project.analyzer import ProjectAnalyzer

        # Create a fake project
        (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")
        (tmp_path / "models.py").write_text("class User:\n    pass\n\nclass Item:\n    pass")
        (tmp_path / "requirements.txt").write_text("fastapi\nsqlalchemy\n")
        (tmp_path / "auth").mkdir()
        (tmp_path / "auth" / "service.py").write_text("def login(): pass")
        (tmp_path / "test_main.py").write_text("def test_app(): assert True")

        # Analyze
        analyzer = ProjectAnalyzer(workspace=tmp_path)
        spec = analyzer.analyze(name="analyzed-project")

        assert spec.name == "analyzed-project"
        assert spec.file_count >= 4
        assert "FastAPI" in spec.tech_stack or "Python" in spec.tech_stack

        # Save
        loader = ProjectLoader(workspace=tmp_path)
        loader.save(spec)
        assert loader.exists

        # Reload and verify
        reloaded = loader.load()
        assert reloaded.name == "analyzed-project"
        assert reloaded.file_count == spec.file_count
