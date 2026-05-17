"""Tests for galaxy.cognitive.expander."""

from galaxy.cognitive.expander import PromptExpander


class TestPromptExpander:
    def test_detect_rest_api(self) -> None:
        expander = PromptExpander()
        spec = expander.expand("Build a REST API with authentication")
        assert spec.project_type == "REST API"
        assert "auth" in spec.domains

    def test_detect_web_app(self) -> None:
        expander = PromptExpander()
        spec = expander.expand("Create a web app with React frontend")
        assert spec.project_type == "Web Application"
        assert "React" in spec.tech_stack

    def test_detect_cli_tool(self) -> None:
        expander = PromptExpander()
        spec = expander.expand("Build a CLI tool for file management")
        assert spec.project_type == "CLI Tool"

    def test_tech_stack_detection(self) -> None:
        expander = PromptExpander()
        spec = expander.expand("API with PostgreSQL database and JWT auth")
        assert any("PostgreSQL" in t or "SQLAlchemy" in t for t in spec.tech_stack)
        assert any("JWT" in t for t in spec.tech_stack)

    def test_domain_suggestion(self) -> None:
        expander = PromptExpander()
        spec = expander.expand("REST API with user login, database models, and Docker deployment")
        assert "auth" in spec.domains
        assert "database" in spec.domains
        assert "devops" in spec.domains

    def test_feature_extraction(self) -> None:
        expander = PromptExpander()
        spec = expander.expand("Build user authentication, CRUD endpoints, and tests")
        assert len(spec.features) >= 2

    def test_ambiguity_detection(self) -> None:
        expander = PromptExpander()
        spec = expander.expand("Build something")
        assert len(spec.ambiguities) > 0

    def test_nonfunctional_detection(self) -> None:
        expander = PromptExpander()
        spec = expander.expand("Build a production-grade secure API with high performance")
        assert len(spec.non_functional) >= 2

    def test_preserves_original_prompt(self) -> None:
        expander = PromptExpander()
        spec = expander.expand("My custom prompt")
        assert spec.original_prompt == "My custom prompt"

    def test_stage_result(self) -> None:
        expander = PromptExpander()
        result = expander.expand_to_stage_result("Build an API")
        assert result.status.name == "COMPLETED"
        assert result.duration_ms >= 0
        assert result.output_data
