"""Tests for galaxy.brainstorm.temp_store."""

from pathlib import Path

import pytest

from galaxy.brainstorm.temp_store import TempIdeaStore
from galaxy.brainstorm.types import Idea, IdeaCategory, IdeaStatus


class TestTempIdeaStoreBasic:
    """Test basic TempIdeaStore operations."""

    def test_create_empty_store(self) -> None:
        store = TempIdeaStore()
        assert store.count == 0
        assert store.list_all() == []

    def test_add_idea(self) -> None:
        store = TempIdeaStore()
        idea = store.add("Add JWT auth", "Implement JWT authentication")
        assert idea.title == "Add JWT auth"
        assert idea.status == IdeaStatus.DRAFT
        assert store.count == 1

    def test_add_idea_with_category(self) -> None:
        store = TempIdeaStore()
        idea = store.add("Encrypt passwords", category=IdeaCategory.SECURITY)
        assert idea.category == IdeaCategory.SECURITY

    def test_add_idea_with_tags(self) -> None:
        store = TempIdeaStore()
        idea = store.add("Feature X", tags=["important", "v1"])
        assert idea.tags == ["important", "v1"]

    def test_add_idea_with_priority(self) -> None:
        store = TempIdeaStore()
        idea = store.add("Critical feature", priority=1)
        assert idea.priority == 1

    def test_add_multiple_ideas(self) -> None:
        store = TempIdeaStore()
        store.add("Idea 1")
        store.add("Idea 2")
        store.add("Idea 3")
        assert store.count == 3

    def test_get_idea(self) -> None:
        store = TempIdeaStore()
        idea = store.add("Test idea")
        retrieved = store.get(idea.id)
        assert retrieved is not None
        assert retrieved.title == "Test idea"

    def test_get_nonexistent_idea(self) -> None:
        store = TempIdeaStore()
        assert store.get("nonexistent") is None

    def test_remove_idea(self) -> None:
        store = TempIdeaStore()
        idea = store.add("To remove")
        removed = store.remove(idea.id)
        assert removed is not None
        assert removed.title == "To remove"
        assert store.count == 0

    def test_remove_nonexistent_idea(self) -> None:
        store = TempIdeaStore()
        assert store.remove("nonexistent") is None

    def test_clear(self) -> None:
        store = TempIdeaStore()
        store.add("Idea 1")
        store.add("Idea 2")
        count = store.clear()
        assert count == 2
        assert store.count == 0


class TestTempIdeaStoreFiltering:
    """Test filtering and search capabilities."""

    def setup_method(self) -> None:
        self.store = TempIdeaStore()
        self.store.add("JWT Auth", category=IdeaCategory.SECURITY)
        self.store.add("React Frontend", category=IdeaCategory.FEATURE)
        idea = self.store.add("Old idea", category=IdeaCategory.FEATURE)
        idea.reject()

    def test_list_all(self) -> None:
        assert len(self.store.list_all()) == 3

    def test_list_by_category(self) -> None:
        features = self.store.list_by_category(IdeaCategory.FEATURE)
        assert len(features) == 2
        security = self.store.list_by_category(IdeaCategory.SECURITY)
        assert len(security) == 1

    def test_list_by_status(self) -> None:
        drafts = self.store.list_by_status(IdeaStatus.DRAFT)
        assert len(drafts) == 2
        rejected = self.store.list_by_status(IdeaStatus.REJECTED)
        assert len(rejected) == 1

    def test_list_active(self) -> None:
        active = self.store.list_active()
        assert len(active) == 2  # Only DRAFT/EXPLORING

    def test_search_by_title(self) -> None:
        results = self.store.search("JWT")
        assert len(results) == 1
        assert results[0].title == "JWT Auth"

    def test_search_case_insensitive(self) -> None:
        results = self.store.search("jwt")
        assert len(results) == 1

    def test_search_no_results(self) -> None:
        results = self.store.search("GraphQL")
        assert len(results) == 0


class TestTempIdeaStoreUpdate:
    """Test updating ideas in the store."""

    def test_update_title(self) -> None:
        store = TempIdeaStore()
        idea = store.add("Old title")
        updated = store.update(idea.id, title="New title")
        assert updated is not None
        assert updated.title == "New title"

    def test_update_category(self) -> None:
        store = TempIdeaStore()
        idea = store.add("Feature", category=IdeaCategory.FEATURE)
        updated = store.update(idea.id, category=IdeaCategory.ARCHITECTURE)
        assert updated is not None
        assert updated.category == IdeaCategory.ARCHITECTURE

    def test_update_nonexistent(self) -> None:
        store = TempIdeaStore()
        assert store.update("nonexistent", title="X") is None

    def test_update_changes_updated_at(self) -> None:
        store = TempIdeaStore()
        idea = store.add("Test")
        before = idea.updated_at
        store.update(idea.id, title="Updated")
        assert idea.updated_at >= before


class TestTempIdeaStorePersistence:
    """Test save/load to YAML files."""

    def test_save_and_load(self, tmp_path: Path) -> None:
        # Save
        store = TempIdeaStore(workspace=tmp_path)
        store.add("Idea A", description="Description A", category=IdeaCategory.SECURITY)
        store.add("Idea B", tags=["tag1"])
        path = store.save()
        assert path is not None
        assert path.exists()

        # Load into new store
        store2 = TempIdeaStore(workspace=tmp_path)
        count = store2.load()
        assert count == 2
        ideas = store2.list_all()
        titles = {i.title for i in ideas}
        assert "Idea A" in titles
        assert "Idea B" in titles

    def test_save_creates_directories(self, tmp_path: Path) -> None:
        store = TempIdeaStore(workspace=tmp_path)
        store.add("Test")
        path = store.save()
        assert path is not None
        assert (tmp_path / ".galaxy" / "brainstorm").is_dir()

    def test_load_empty_file(self, tmp_path: Path) -> None:
        store = TempIdeaStore(workspace=tmp_path)
        count = store.load()  # No file exists
        assert count == 0

    def test_save_without_workspace(self) -> None:
        store = TempIdeaStore()  # No workspace
        assert store.save() is None

    def test_load_preserves_status(self, tmp_path: Path) -> None:
        store = TempIdeaStore(workspace=tmp_path)
        idea = store.add("Test")
        idea.approve()
        store.save()

        store2 = TempIdeaStore(workspace=tmp_path)
        store2.load()
        loaded = store2.list_all()[0]
        assert loaded.status == IdeaStatus.APPROVED

    def test_roundtrip_preserves_all_fields(self, tmp_path: Path) -> None:
        store = TempIdeaStore(workspace=tmp_path)
        original = store.add(
            "Full test",
            description="All fields",
            category=IdeaCategory.ARCHITECTURE,
            tags=["important", "v2"],
            priority=2,
            metadata={"source": "chat"},
        )
        original_id = original.id
        store.save()

        store2 = TempIdeaStore(workspace=tmp_path)
        store2.load()
        loaded = store2.get(original_id)
        assert loaded is not None
        assert loaded.title == "Full test"
        assert loaded.description == "All fields"
        assert loaded.category == IdeaCategory.ARCHITECTURE
        assert loaded.tags == ["important", "v2"]
        assert loaded.priority == 2
        assert loaded.metadata == {"source": "chat"}
