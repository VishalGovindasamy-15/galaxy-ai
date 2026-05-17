"""Tests for galaxy.brainstorm.types."""

from datetime import datetime, timezone

from galaxy.brainstorm.types import (
    BrainstormMode,
    BrainstormPhase,
    BrainstormSession,
    BrainstormSummary,
    DecisionRecord,
    DecisionType,
    Idea,
    IdeaCategory,
    IdeaStatus,
)


# ─── IdeaStatus Tests ────────────────────────────────────────────────────────


class TestIdeaStatus:
    """Test IdeaStatus enum."""

    def test_all_statuses_exist(self) -> None:
        assert len(IdeaStatus) == 6

    def test_terminal_statuses(self) -> None:
        assert IdeaStatus.APPROVED.is_terminal()
        assert IdeaStatus.REJECTED.is_terminal()
        assert IdeaStatus.MERGED.is_terminal()

    def test_non_terminal_statuses(self) -> None:
        assert not IdeaStatus.DRAFT.is_terminal()
        assert not IdeaStatus.EXPLORING.is_terminal()
        assert not IdeaStatus.DEFERRED.is_terminal()

    def test_active_statuses(self) -> None:
        assert IdeaStatus.DRAFT.is_active()
        assert IdeaStatus.EXPLORING.is_active()

    def test_inactive_statuses(self) -> None:
        assert not IdeaStatus.APPROVED.is_active()
        assert not IdeaStatus.REJECTED.is_active()
        assert not IdeaStatus.DEFERRED.is_active()

    def test_string_values(self) -> None:
        assert IdeaStatus.DRAFT.value == "draft"
        assert IdeaStatus.APPROVED.value == "approved"


# ─── IdeaCategory Tests ──────────────────────────────────────────────────────


class TestIdeaCategory:
    """Test IdeaCategory enum."""

    def test_all_categories(self) -> None:
        assert len(IdeaCategory) == 12

    def test_key_categories_exist(self) -> None:
        assert IdeaCategory.FEATURE.value == "feature"
        assert IdeaCategory.ARCHITECTURE.value == "architecture"
        assert IdeaCategory.SECURITY.value == "security"

    def test_string_enum(self) -> None:
        assert isinstance(IdeaCategory.FEATURE, str)


# ─── BrainstormMode Tests ────────────────────────────────────────────────────


class TestBrainstormMode:
    """Test BrainstormMode enum."""

    def test_all_modes(self) -> None:
        assert len(BrainstormMode) == 3

    def test_descriptions(self) -> None:
        assert "Open-ended" in BrainstormMode.FREE_FORM.description
        assert "Guided" in BrainstormMode.STRUCTURED.description
        assert "Master" in BrainstormMode.GUIDED.description


# ─── BrainstormPhase Tests ───────────────────────────────────────────────────


class TestBrainstormPhase:
    """Test BrainstormPhase enum."""

    def test_all_phases(self) -> None:
        assert len(BrainstormPhase) == 5

    def test_phase_order(self) -> None:
        phases = list(BrainstormPhase)
        assert phases[0] == BrainstormPhase.IDEATION
        assert phases[-1] == BrainstormPhase.COMPLETE


# ─── DecisionType Tests ──────────────────────────────────────────────────────


class TestDecisionType:
    """Test DecisionType enum."""

    def test_all_types(self) -> None:
        assert len(DecisionType) == 11

    def test_idea_lifecycle_types(self) -> None:
        assert DecisionType.IDEA_CREATED.value == "idea_created"
        assert DecisionType.IDEA_APPROVED.value == "idea_approved"
        assert DecisionType.IDEA_REJECTED.value == "idea_rejected"


# ─── Idea Tests ──────────────────────────────────────────────────────────────


class TestIdea:
    """Test Idea dataclass."""

    def test_default_creation(self) -> None:
        idea = Idea()
        assert idea.id  # auto-generated
        assert idea.status == IdeaStatus.DRAFT
        assert idea.category == IdeaCategory.FEATURE
        assert idea.priority == 0
        assert idea.tags == []
        assert idea.dependencies == []
        assert idea.parent_id is None

    def test_creation_with_values(self) -> None:
        idea = Idea(
            title="Add JWT auth",
            description="Implement JWT-based authentication",
            category=IdeaCategory.SECURITY,
            priority=1,
            tags=["auth", "security"],
        )
        assert idea.title == "Add JWT auth"
        assert idea.category == IdeaCategory.SECURITY
        assert idea.priority == 1
        assert "auth" in idea.tags

    def test_approve(self) -> None:
        idea = Idea(title="Test")
        idea.approve()
        assert idea.status == IdeaStatus.APPROVED
        assert idea.status.is_terminal()

    def test_reject(self) -> None:
        idea = Idea(title="Test")
        idea.reject()
        assert idea.status == IdeaStatus.REJECTED

    def test_defer(self) -> None:
        idea = Idea(title="Test")
        idea.defer()
        assert idea.status == IdeaStatus.DEFERRED

    def test_merge_into(self) -> None:
        idea = Idea(title="Small idea")
        idea.merge_into("parent123")
        assert idea.status == IdeaStatus.MERGED
        assert idea.parent_id == "parent123"

    def test_to_dict(self) -> None:
        idea = Idea(id="abc123", title="Test idea", category=IdeaCategory.ARCHITECTURE)
        d = idea.to_dict()
        assert d["id"] == "abc123"
        assert d["title"] == "Test idea"
        assert d["category"] == "architecture"
        assert d["status"] == "draft"
        assert "created_at" in d
        assert "updated_at" in d

    def test_from_dict(self) -> None:
        data = {
            "id": "xyz789",
            "title": "Restored idea",
            "description": "From disk",
            "category": "security",
            "status": "approved",
            "priority": 2,
            "tags": ["important"],
            "dependencies": [],
            "parent_id": None,
            "metadata": {"source": "brainstorm"},
        }
        idea = Idea.from_dict(data)
        assert idea.id == "xyz789"
        assert idea.title == "Restored idea"
        assert idea.category == IdeaCategory.SECURITY
        assert idea.status == IdeaStatus.APPROVED
        assert idea.priority == 2

    def test_roundtrip(self) -> None:
        original = Idea(
            title="Roundtrip test",
            category=IdeaCategory.WORKFLOW,
            tags=["test"],
            priority=3,
        )
        restored = Idea.from_dict(original.to_dict())
        assert restored.title == original.title
        assert restored.category == original.category
        assert restored.tags == original.tags
        assert restored.priority == original.priority

    def test_updated_at_changes_on_actions(self) -> None:
        idea = Idea(title="Test")
        before = idea.updated_at
        idea.approve()
        assert idea.updated_at >= before


# ─── DecisionRecord Tests ────────────────────────────────────────────────────


class TestDecisionRecord:
    """Test DecisionRecord dataclass."""

    def test_default_creation(self) -> None:
        record = DecisionRecord()
        assert record.id
        assert record.decision_type == DecisionType.IDEA_CREATED
        assert record.idea_id is None
        assert record.description == ""

    def test_creation_with_values(self) -> None:
        record = DecisionRecord(
            decision_type=DecisionType.IDEA_APPROVED,
            idea_id="idea123",
            description="User approved JWT feature",
            reason="Critical for security",
        )
        assert record.decision_type == DecisionType.IDEA_APPROVED
        assert record.idea_id == "idea123"
        assert "JWT" in record.description

    def test_to_dict(self) -> None:
        record = DecisionRecord(
            id="dec001",
            decision_type=DecisionType.ARCHITECTURE_DECISION,
            description="Chose FastAPI over Flask",
        )
        d = record.to_dict()
        assert d["id"] == "dec001"
        assert d["decision_type"] == "architecture_decision"

    def test_from_dict(self) -> None:
        data = {
            "id": "dec002",
            "decision_type": "idea_rejected",
            "idea_id": "idea456",
            "description": "Too complex",
            "reason": "MVP scope",
            "context": {"phase": "evaluation"},
        }
        record = DecisionRecord.from_dict(data)
        assert record.decision_type == DecisionType.IDEA_REJECTED
        assert record.idea_id == "idea456"
        assert record.context["phase"] == "evaluation"

    def test_roundtrip(self) -> None:
        original = DecisionRecord(
            decision_type=DecisionType.CONSTRAINT_ADDED,
            description="Must use PostgreSQL",
            reason="Client requirement",
        )
        restored = DecisionRecord.from_dict(original.to_dict())
        assert restored.decision_type == original.decision_type
        assert restored.description == original.description


# ─── BrainstormSession Tests ─────────────────────────────────────────────────


class TestBrainstormSession:
    """Test BrainstormSession dataclass."""

    def test_default_creation(self) -> None:
        session = BrainstormSession()
        assert session.id
        assert session.mode == BrainstormMode.STRUCTURED
        assert session.phase == BrainstormPhase.IDEATION
        assert not session.is_complete

    def test_advance_phase(self) -> None:
        session = BrainstormSession()
        assert session.phase == BrainstormPhase.IDEATION

        new_phase = session.advance_phase()
        assert new_phase == BrainstormPhase.REFINEMENT
        assert session.phase == BrainstormPhase.REFINEMENT

    def test_advance_through_all_phases(self) -> None:
        session = BrainstormSession()
        phases_seen = [session.phase]
        while not session.is_complete:
            session.advance_phase()
            phases_seen.append(session.phase)
        assert len(phases_seen) == 5  # All 5 phases
        assert phases_seen[-1] == BrainstormPhase.COMPLETE

    def test_advance_past_complete_stays_complete(self) -> None:
        session = BrainstormSession(phase=BrainstormPhase.COMPLETE)
        session.advance_phase()
        assert session.phase == BrainstormPhase.COMPLETE

    def test_is_complete(self) -> None:
        session = BrainstormSession(phase=BrainstormPhase.COMPLETE)
        assert session.is_complete

    def test_to_dict(self) -> None:
        session = BrainstormSession(
            id="ses001",
            project_name="my-api",
            prompt="Build a REST API",
            mode=BrainstormMode.GUIDED,
        )
        d = session.to_dict()
        assert d["id"] == "ses001"
        assert d["project_name"] == "my-api"
        assert d["mode"] == "guided"

    def test_from_dict(self) -> None:
        data = {
            "id": "ses002",
            "project_name": "test-project",
            "prompt": "Build something",
            "mode": "free_form",
            "phase": "refinement",
            "idea_ids": ["a", "b", "c"],
            "decision_ids": ["d1"],
            "config": {"max_ideas": 20},
        }
        session = BrainstormSession.from_dict(data)
        assert session.mode == BrainstormMode.FREE_FORM
        assert session.phase == BrainstormPhase.REFINEMENT
        assert len(session.idea_ids) == 3

    def test_roundtrip(self) -> None:
        original = BrainstormSession(
            project_name="roundtrip",
            mode=BrainstormMode.GUIDED,
            idea_ids=["i1", "i2"],
        )
        restored = BrainstormSession.from_dict(original.to_dict())
        assert restored.project_name == original.project_name
        assert restored.mode == original.mode
        assert restored.idea_ids == original.idea_ids


# ─── BrainstormSummary Tests ─────────────────────────────────────────────────


class TestBrainstormSummary:
    """Test BrainstormSummary dataclass."""

    def test_default_creation(self) -> None:
        summary = BrainstormSummary()
        assert summary.total_ideas == 0
        assert summary.approved_ideas == 0
        assert summary.categories == {}

    def test_with_values(self) -> None:
        summary = BrainstormSummary(
            session_id="ses001",
            total_ideas=10,
            approved_ideas=7,
            rejected_ideas=2,
            deferred_ideas=1,
            categories={"feature": 5, "security": 3, "architecture": 2},
        )
        assert summary.total_ideas == 10
        assert summary.approved_ideas == 7
        assert len(summary.categories) == 3
