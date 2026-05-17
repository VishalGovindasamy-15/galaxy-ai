"""Tests for galaxy.cli.confirm."""

from galaxy.cli.confirm import (
    ConfirmationItem,
    ConfirmationRequest,
    build_project_confirmation,
    confirm_action,
)


class TestConfirmationItem:
    def test_default(self) -> None:
        item = ConfirmationItem()
        assert item.label == ""
        assert item.category == "general"

    def test_to_dict(self) -> None:
        item = ConfirmationItem(label="Test", detail="Detail", category="feature")
        d = item.to_dict()
        assert d["label"] == "Test"
        assert d["category"] == "feature"


class TestConfirmationRequest:
    def test_add_items(self) -> None:
        req = ConfirmationRequest(title="Test")
        req.add("Feature 1", "Detail 1")
        req.add("Feature 2", "Detail 2", category="feature")
        assert len(req.items) == 2

    def test_add_warning(self) -> None:
        req = ConfirmationRequest()
        req.add_warning("This will overwrite files")
        assert len(req.warnings) == 1


class TestConfirmAction:
    def test_auto_approve(self) -> None:
        req = ConfirmationRequest(title="Test")
        assert confirm_action(req, auto_approve=True) is True


class TestBuildProjectConfirmation:
    def test_basic(self) -> None:
        req = build_project_confirmation(
            project_name="my-api",
            features=["Auth", "CRUD"],
            domains=["backend", "auth"],
            tech_stack=["FastAPI", "PostgreSQL"],
            estimated_chunks=10,
        )
        assert req.title == "Create Project: my-api"
        assert req.estimated_chunks == 10
        assert len(req.items) >= 4  # project + tech + domains + 2 features

    def test_many_features_capped(self) -> None:
        features = [f"Feature {i}" for i in range(15)]
        req = build_project_confirmation(
            project_name="big",
            features=features,
            domains=["backend"],
            tech_stack=["Python"],
        )
        # Should have capped features + "... and N more" item
        assert any("more" in item.label for item in req.items)
