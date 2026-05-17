"""Tests for galaxy.brainstorm.decision_log."""

from pathlib import Path

from galaxy.brainstorm.decision_log import DecisionLog
from galaxy.brainstorm.types import DecisionRecord, DecisionType


class TestDecisionLogBasic:
    """Test basic DecisionLog operations."""

    def test_create_empty_log(self) -> None:
        log = DecisionLog()
        assert log.count == 0

    def test_record_decision(self) -> None:
        log = DecisionLog()
        record = log.record(
            DecisionType.IDEA_CREATED,
            idea_id="idea001",
            description="Created JWT auth idea",
            reason="User suggested it",
        )
        assert record.decision_type == DecisionType.IDEA_CREATED
        assert record.idea_id == "idea001"
        assert log.count == 1

    def test_record_multiple(self) -> None:
        log = DecisionLog()
        log.record(DecisionType.SESSION_STARTED, description="New session")
        log.record(DecisionType.IDEA_CREATED, idea_id="a")
        log.record(DecisionType.IDEA_APPROVED, idea_id="a")
        assert log.count == 3

    def test_record_with_context(self) -> None:
        log = DecisionLog()
        record = log.record(
            DecisionType.ARCHITECTURE_DECISION,
            description="Chose FastAPI",
            context={"alternatives": ["Flask", "Django"]},
        )
        assert record.context["alternatives"] == ["Flask", "Django"]


class TestDecisionLogQuery:
    """Test querying the decision log."""

    def setup_method(self) -> None:
        self.log = DecisionLog()
        self.log.record(DecisionType.SESSION_STARTED, description="Start")
        self.log.record(DecisionType.IDEA_CREATED, idea_id="idea1", description="Created A")
        self.log.record(DecisionType.IDEA_CREATED, idea_id="idea2", description="Created B")
        self.log.record(DecisionType.IDEA_APPROVED, idea_id="idea1", description="Approved A")
        self.log.record(DecisionType.IDEA_REJECTED, idea_id="idea2", description="Rejected B")

    def test_query_all(self) -> None:
        results = self.log.query()
        assert len(results) == 5

    def test_query_by_idea_id(self) -> None:
        results = self.log.query(idea_id="idea1")
        assert len(results) == 2  # Created + Approved

    def test_query_by_decision_type(self) -> None:
        results = self.log.query(decision_type=DecisionType.IDEA_CREATED)
        assert len(results) == 2

    def test_query_with_limit(self) -> None:
        results = self.log.query(limit=2)
        assert len(results) == 2

    def test_query_newest_first(self) -> None:
        results = self.log.query(decision_type=DecisionType.IDEA_CREATED)
        # Newest first
        assert results[0].description == "Created B"
        assert results[1].description == "Created A"

    def test_query_combined_filters(self) -> None:
        results = self.log.query(
            idea_id="idea1",
            decision_type=DecisionType.IDEA_APPROVED,
        )
        assert len(results) == 1
        assert results[0].description == "Approved A"


class TestDecisionLogHistory:
    """Test per-idea history tracking."""

    def test_get_idea_history(self) -> None:
        log = DecisionLog()
        log.record(DecisionType.IDEA_CREATED, idea_id="x", description="Created")
        log.record(DecisionType.IDEA_UPDATED, idea_id="x", description="Updated title")
        log.record(DecisionType.IDEA_APPROVED, idea_id="x", description="Approved")
        log.record(DecisionType.IDEA_CREATED, idea_id="y", description="Other idea")

        history = log.get_idea_history("x")
        assert len(history) == 3
        # Chronological order
        assert history[0].description == "Created"
        assert history[2].description == "Approved"

    def test_get_history_empty(self) -> None:
        log = DecisionLog()
        assert log.get_idea_history("nonexistent") == []

    def test_list_all_chronological(self) -> None:
        log = DecisionLog()
        log.record(DecisionType.SESSION_STARTED, description="Start")
        log.record(DecisionType.IDEA_CREATED, idea_id="a", description="A")
        all_records = log.list_all()
        assert len(all_records) == 2
        assert all_records[0].description == "Start"

    def test_clear(self) -> None:
        log = DecisionLog()
        log.record(DecisionType.IDEA_CREATED, idea_id="a")
        log.record(DecisionType.IDEA_CREATED, idea_id="b")
        count = log.clear()
        assert count == 2
        assert log.count == 0


class TestDecisionLogPersistence:
    """Test save/load to YAML."""

    def test_save_and_load(self, tmp_path: Path) -> None:
        log = DecisionLog(workspace=tmp_path)
        log.record(DecisionType.SESSION_STARTED, description="Start")
        log.record(DecisionType.IDEA_CREATED, idea_id="a", reason="User suggested")
        log.save()

        log2 = DecisionLog(workspace=tmp_path)
        count = log2.load()
        assert count == 2

    def test_roundtrip_preserves_fields(self, tmp_path: Path) -> None:
        log = DecisionLog(workspace=tmp_path)
        log.record(
            DecisionType.ARCHITECTURE_DECISION,
            idea_id="arch1",
            description="Use microservices",
            reason="Scalability",
            context={"pattern": "microservices"},
        )
        log.save()

        log2 = DecisionLog(workspace=tmp_path)
        log2.load()
        records = log2.list_all()
        assert len(records) == 1
        assert records[0].decision_type == DecisionType.ARCHITECTURE_DECISION
        assert records[0].reason == "Scalability"
        assert records[0].context["pattern"] == "microservices"

    def test_save_without_workspace(self) -> None:
        log = DecisionLog()
        assert log.save() is None

    def test_load_nonexistent(self, tmp_path: Path) -> None:
        log = DecisionLog(workspace=tmp_path)
        assert log.load() == 0
