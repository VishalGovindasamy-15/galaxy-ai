"""Tests for galaxy.brainstorm.permanent_store."""

from pathlib import Path

from galaxy.brainstorm.permanent_store import PermanentIdeaStore
from galaxy.brainstorm.types import Idea, IdeaCategory, IdeaStatus


class TestPermanentIdeaStoreBasic:
    """Test basic PermanentIdeaStore operations."""

    def test_create_empty_store(self) -> None:
        store = PermanentIdeaStore()
        assert store.count == 0

    def test_promote_idea(self) -> None:
        store = PermanentIdeaStore()
        idea = Idea(title="JWT Auth", category=IdeaCategory.SECURITY)
        promoted = store.promote(idea)
        assert promoted.status == IdeaStatus.APPROVED
        assert store.count == 1

    def test_promote_sets_approved(self) -> None:
        store = PermanentIdeaStore()
        idea = Idea(title="Test", status=IdeaStatus.DRAFT)
        store.promote(idea)
        assert idea.status == IdeaStatus.APPROVED

    def test_add_already_approved(self) -> None:
        store = PermanentIdeaStore()
        idea = Idea(title="Pre-approved")
        idea.approve()
        store.add(idea)
        assert store.count == 1

    def test_get_idea(self) -> None:
        store = PermanentIdeaStore()
        idea = Idea(title="Find me")
        store.promote(idea)
        found = store.get(idea.id)
        assert found is not None
        assert found.title == "Find me"

    def test_get_nonexistent(self) -> None:
        store = PermanentIdeaStore()
        assert store.get("nope") is None

    def test_remove_idea(self) -> None:
        store = PermanentIdeaStore()
        idea = Idea(title="Remove me")
        store.promote(idea)
        removed = store.remove(idea.id)
        assert removed is not None
        assert store.count == 0

    def test_remove_nonexistent(self) -> None:
        store = PermanentIdeaStore()
        assert store.remove("nope") is None


class TestPermanentIdeaStoreFiltering:
    """Test filtering and sorting."""

    def setup_method(self) -> None:
        self.store = PermanentIdeaStore()
        self.store.promote(Idea(title="Feature A", category=IdeaCategory.FEATURE, priority=2))
        self.store.promote(Idea(title="Security B", category=IdeaCategory.SECURITY, priority=1))
        self.store.promote(Idea(title="Feature C", category=IdeaCategory.FEATURE, priority=0))

    def test_list_all(self) -> None:
        assert len(self.store.list_all()) == 3

    def test_list_by_category(self) -> None:
        features = self.store.list_by_category(IdeaCategory.FEATURE)
        assert len(features) == 2
        security = self.store.list_by_category(IdeaCategory.SECURITY)
        assert len(security) == 1

    def test_list_by_priority(self) -> None:
        prioritized = self.store.list_by_priority()
        # Priority 1 first, then 2, then 0 (unset) last
        assert prioritized[0].priority == 1
        assert prioritized[1].priority == 2
        assert prioritized[2].priority == 0

    def test_search(self) -> None:
        results = self.store.search("Security")
        assert len(results) == 1
        assert results[0].title == "Security B"

    def test_search_case_insensitive(self) -> None:
        results = self.store.search("feature")
        assert len(results) == 2


class TestPermanentIdeaStoreUpdate:
    """Test runtime mutation of permanent ideas."""

    def test_update_title(self) -> None:
        store = PermanentIdeaStore()
        idea = Idea(title="Old")
        store.promote(idea)
        updated = store.update(idea.id, title="New")
        assert updated is not None
        assert updated.title == "New"

    def test_update_nonexistent(self) -> None:
        store = PermanentIdeaStore()
        assert store.update("nope", title="X") is None

    def test_update_during_runtime(self) -> None:
        """Simulate updating spec during project creation via chat."""
        store = PermanentIdeaStore()
        idea = Idea(title="REST API", description="Basic REST")
        store.promote(idea)
        # User updates during project creation
        store.update(idea.id, description="REST API with GraphQL gateway")
        assert store.get(idea.id).description == "REST API with GraphQL gateway"


class TestPermanentIdeaStoreSpec:
    """Test to_spec() for feeding into Master agent."""

    def test_empty_spec(self) -> None:
        store = PermanentIdeaStore()
        spec = store.to_spec()
        assert spec["features"] == []
        assert spec["constraints"] == []

    def test_spec_categorizes_ideas(self) -> None:
        store = PermanentIdeaStore()
        store.promote(Idea(title="Login", category=IdeaCategory.FEATURE))
        store.promote(Idea(title="Use PostgreSQL", category=IdeaCategory.CONSTRAINT))
        store.promote(Idea(title="Encrypt passwords", category=IdeaCategory.SECURITY))

        spec = store.to_spec()
        assert len(spec["features"]) == 1
        assert len(spec["constraints"]) == 1
        assert len(spec["security"]) == 1

    def test_spec_contains_idea_details(self) -> None:
        store = PermanentIdeaStore()
        store.promote(Idea(
            title="JWT Auth",
            description="Implement JWT tokens",
            priority=1,
            tags=["auth"],
            category=IdeaCategory.FEATURE,
        ))
        spec = store.to_spec()
        feature = spec["features"][0]
        assert feature["title"] == "JWT Auth"
        assert feature["description"] == "Implement JWT tokens"
        assert feature["priority"] == 1
        assert feature["tags"] == ["auth"]

    def test_spec_sorted_by_priority(self) -> None:
        store = PermanentIdeaStore()
        store.promote(Idea(title="Low", category=IdeaCategory.FEATURE, priority=3))
        store.promote(Idea(title="High", category=IdeaCategory.FEATURE, priority=1))
        spec = store.to_spec()
        assert spec["features"][0]["title"] == "High"
        assert spec["features"][1]["title"] == "Low"


class TestPermanentIdeaStorePersistence:
    """Test save/load to YAML."""

    def test_save_and_load(self, tmp_path: Path) -> None:
        store = PermanentIdeaStore(workspace=tmp_path)
        store.promote(Idea(title="Idea A", category=IdeaCategory.ARCHITECTURE))
        store.promote(Idea(title="Idea B", category=IdeaCategory.SECURITY))
        store.save()

        store2 = PermanentIdeaStore(workspace=tmp_path)
        count = store2.load()
        assert count == 2

    def test_roundtrip_preserves_status(self, tmp_path: Path) -> None:
        store = PermanentIdeaStore(workspace=tmp_path)
        store.promote(Idea(title="Test"))
        store.save()

        store2 = PermanentIdeaStore(workspace=tmp_path)
        store2.load()
        assert store2.list_all()[0].status == IdeaStatus.APPROVED

    def test_save_without_workspace(self) -> None:
        store = PermanentIdeaStore()
        assert store.save() is None

    def test_load_nonexistent(self, tmp_path: Path) -> None:
        store = PermanentIdeaStore(workspace=tmp_path)
        assert store.load() == 0
