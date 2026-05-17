"""Integration tests for the brainstorming engine.

Tests the complete flow: session → ideas → approve/reject → spec → persistence.
"""

from pathlib import Path

from galaxy.brainstorm.engine import BrainstormEngine
from galaxy.brainstorm.interviewer import BrainstormInterviewer
from galaxy.brainstorm.types import (
    BrainstormMode,
    BrainstormPhase,
    DecisionType,
    IdeaCategory,
    IdeaStatus,
)


class TestBrainstormToPermantentFlow:
    """Test complete flow from brainstorming to permanent ideas."""

    def test_full_brainstorm_to_permanent(self, tmp_path: Path) -> None:
        """Full lifecycle: brainstorm → approve → permanent → spec."""
        engine = BrainstormEngine(workspace=tmp_path)

        # Start session
        session = engine.start_session(
            "Build a REST API with authentication",
            project_name="my-api",
            mode=BrainstormMode.STRUCTURED,
        )
        assert session.phase == BrainstormPhase.IDEATION

        # Add ideas (simulating user input)
        jwt = engine.add_idea(
            "JWT Authentication",
            "Token-based auth with refresh tokens",
            IdeaCategory.SECURITY,
            priority=1,
        )
        crud = engine.add_idea(
            "CRUD Endpoints",
            "RESTful endpoints for all entities",
            IdeaCategory.FEATURE,
            priority=1,
        )
        postgres = engine.add_idea(
            "PostgreSQL Database",
            "Use PostgreSQL for data storage",
            IdeaCategory.CONSTRAINT,
        )
        graphql = engine.add_idea(
            "GraphQL Gateway",
            "Add GraphQL alongside REST",
            IdeaCategory.ARCHITECTURE,
        )
        docker = engine.add_idea(
            "Docker Deployment",
            "Containerize with Docker",
            IdeaCategory.DEVOPS,
        )

        assert engine.temp_store.count == 5
        assert engine.permanent_store.count == 0

        # Approve core features
        engine.approve_idea(jwt.id, reason="Required for security")
        engine.approve_idea(crud.id, reason="Core functionality")
        engine.approve_idea(postgres.id, reason="Client requirement")
        engine.approve_idea(docker.id, reason="Standard deployment")

        # Reject non-essential
        engine.reject_idea(graphql.id, reason="Too complex for MVP")

        assert engine.permanent_store.count == 4
        assert engine.temp_store.count == 1  # rejected stays in temp

        # Verify spec
        spec = engine.get_project_spec()
        assert len(spec["security"]) == 1
        assert spec["security"][0]["title"] == "JWT Authentication"
        assert len(spec["features"]) == 1
        assert len(spec["constraints"]) == 1

        # Verify decision log
        jwt_history = engine.decision_log.get_idea_history(jwt.id)
        assert len(jwt_history) == 2  # created + approved
        assert jwt_history[0].decision_type == DecisionType.IDEA_CREATED
        assert jwt_history[1].decision_type == DecisionType.IDEA_APPROVED

        # Save and verify persistence
        engine.save()
        engine2 = BrainstormEngine(workspace=tmp_path)
        counts = engine2.load()
        assert counts["permanent_ideas"] == 4
        assert counts["temp_ideas"] == 1

    def test_brainstorm_with_runtime_updates(self, tmp_path: Path) -> None:
        """Test updating permanent ideas during project creation."""
        engine = BrainstormEngine(workspace=tmp_path)
        engine.start_session("Build API")

        # Add and approve
        idea = engine.add_idea("REST API", "Basic REST endpoints")
        engine.approve_idea(idea.id)
        assert engine.permanent_store.count == 1

        # Simulate runtime update via chat
        engine.update_permanent_idea(
            idea.id,
            description="REST + WebSocket real-time endpoints",
        )

        # Verify update
        updated = engine.permanent_store.get(idea.id)
        assert "WebSocket" in updated.description

        # Verify decision log records the update
        update_records = engine.decision_log.query(
            idea_id=idea.id,
            decision_type=DecisionType.IDEA_UPDATED,
        )
        assert len(update_records) == 1


class TestPermanentIdeasFeedIntoPlanning:
    """Test that permanent ideas correctly feed into project planning."""

    def test_spec_structure_for_master_agent(self, tmp_path: Path) -> None:
        """Verify spec output is structured for Master agent consumption."""
        engine = BrainstormEngine(workspace=tmp_path)
        engine.start_session("Full-stack app")

        # Add diverse ideas
        ideas = [
            ("Login System", IdeaCategory.FEATURE, 1),
            ("FastAPI Backend", IdeaCategory.ARCHITECTURE, 1),
            ("Must use SQLite", IdeaCategory.CONSTRAINT, 2),
            ("Bcrypt hashing", IdeaCategory.SECURITY, 1),
            ("API → Frontend", IdeaCategory.WORKFLOW, 3),
            ("Use React", IdeaCategory.DEPENDENCY, 2),
        ]
        for title, cat, pri in ideas:
            idea = engine.add_idea(title, category=cat, priority=pri)
            engine.approve_idea(idea.id)

        spec = engine.get_project_spec()

        # Verify all categories populated
        assert len(spec["features"]) == 1
        assert len(spec["architecture"]) == 1
        assert len(spec["constraints"]) == 1
        assert len(spec["security"]) == 1
        assert len(spec["workflows"]) == 1
        assert len(spec["dependencies"]) == 1

        # Verify priority sorting (priority 1 items first)
        assert spec["features"][0]["priority"] == 1

        # Verify spec items have required fields
        for category_items in spec.values():
            for item in category_items:
                assert "id" in item
                assert "title" in item
                assert "description" in item
                assert "priority" in item

    def test_interviewer_detects_gaps_in_plan(self) -> None:
        """Verify interviewer identifies missing categories."""
        engine = BrainstormEngine()
        engine.start_session("Build API")
        interviewer = BrainstormInterviewer()

        # Only add a feature — lots of gaps
        engine.add_idea("User login", category=IdeaCategory.FEATURE)

        analysis = interviewer.generate_gap_analysis(
            "Build API",
            engine.temp_store.list_all(),
        )

        # Should have many missing categories
        assert len(analysis["missing_categories"]) > 3
        assert "deployment" in analysis["missing_categories"]
        assert len(analysis["suggestions"]) > 0

    def test_multiple_sessions_accumulate(self, tmp_path: Path) -> None:
        """Test that ideas persist across multiple sessions."""
        # Session 1
        engine = BrainstormEngine(workspace=tmp_path)
        engine.start_session("API v1")
        idea = engine.add_idea("Auth system")
        engine.approve_idea(idea.id)
        engine.save()

        # Session 2
        engine2 = BrainstormEngine(workspace=tmp_path)
        engine2.load()
        assert engine2.permanent_store.count == 1

        engine2.start_session("API v2")
        idea2 = engine2.add_idea("Rate limiting")
        engine2.approve_idea(idea2.id)
        engine2.save()

        # Session 3: verify all ideas persisted
        engine3 = BrainstormEngine(workspace=tmp_path)
        engine3.load()
        assert engine3.permanent_store.count == 2

    def test_phase_progression(self) -> None:
        """Test full phase progression through brainstorming."""
        engine = BrainstormEngine()
        session = engine.start_session("Test")

        phases = [BrainstormPhase.IDEATION]
        while not session.is_complete:
            engine.advance_phase()
            phases.append(session.phase)

        assert phases == [
            BrainstormPhase.IDEATION,
            BrainstormPhase.REFINEMENT,
            BrainstormPhase.EVALUATION,
            BrainstormPhase.APPROVAL,
            BrainstormPhase.COMPLETE,
        ]

        # Decision log should have phase changes
        phase_records = engine.decision_log.query(
            decision_type=DecisionType.PHASE_CHANGED,
        )
        assert len(phase_records) == 4  # 4 phase transitions
