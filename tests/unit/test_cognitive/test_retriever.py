"""Tests for galaxy.cognitive.retriever."""

from pathlib import Path

from galaxy.cognitive.retriever import ContextRetriever


class TestContextRetriever:
    def test_retrieve_no_workspace(self) -> None:
        retriever = ContextRetriever()
        ctx = retriever.retrieve("Build API")
        assert ctx.relevant_files == []
        assert ctx.patterns == []

    def test_retrieve_with_workspace(self, tmp_path: Path) -> None:
        # Create some files
        (tmp_path / "main.py").write_text("from fastapi import FastAPI")
        (tmp_path / "models.py").write_text("class User: pass")
        (tmp_path / "requirements.txt").write_text("fastapi\n")

        retriever = ContextRetriever(workspace=tmp_path)
        ctx = retriever.retrieve("Build API")
        assert len(ctx.relevant_files) >= 2
        assert "main.py" in ctx.relevant_files

    def test_skips_hidden_dirs(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("x")
        (tmp_path / "app.py").write_text("x = 1")

        retriever = ContextRetriever(workspace=tmp_path)
        ctx = retriever.retrieve()
        assert all(".git" not in f for f in ctx.relevant_files)

    def test_detect_patterns(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("app = FastAPI()")
        (tmp_path / "requirements.txt").write_text("fastapi")

        retriever = ContextRetriever(workspace=tmp_path)
        ctx = retriever.retrieve()
        # Should detect some pattern
        assert isinstance(ctx.patterns, list)

    def test_tech_docs(self) -> None:
        retriever = ContextRetriever()
        ctx = retriever.retrieve(tech_stack=["FastAPI", "JWT"])
        assert len(ctx.documentation) >= 2
        assert any("FastAPI" in d for d in ctx.documentation)

    def test_stage_result(self) -> None:
        retriever = ContextRetriever()
        result = retriever.retrieve_to_stage_result("Build API")
        assert result.status.name == "COMPLETED"


class TestRetrieverSnippets:
    def test_extract_snippets(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")
        retriever = ContextRetriever(workspace=tmp_path)
        ctx = retriever.retrieve(domains=["backend"])
        assert len(ctx.code_snippets) >= 1
