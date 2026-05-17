"""Tests for galaxy.integrator.engine."""

from pathlib import Path

from galaxy.contracts.types import ChunkOperation, CodeChunk
from galaxy.integrator.engine import IntegratorEngine


class TestIntegratorEngineBasic:
    def test_create_engine(self) -> None:
        engine = IntegratorEngine()
        assert engine.file_count == 0
        assert engine.total_chunks_merged == 0

    def test_integrate_single_chunk(self) -> None:
        engine = IntegratorEngine()
        chunk = CodeChunk(
            target_file="utils.py",
            target_symbol="add",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def add(a, b):\n    return a + b",
        )
        result = engine.integrate(chunk)
        assert result.success
        assert engine.file_count == 1
        assert engine.total_chunks_merged == 1

    def test_integrate_multiple_to_same_file(self) -> None:
        engine = IntegratorEngine()
        engine.integrate(CodeChunk(
            target_file="math.py",
            target_symbol="add",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def add(a, b):\n    return a + b",
        ))
        engine.integrate(CodeChunk(
            target_file="math.py",
            target_symbol="sub",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def sub(a, b):\n    return a - b",
        ))
        assert engine.file_count == 1
        assert engine.total_chunks_merged == 2

        files = engine.get_all_files()
        assert "def add" in files["math.py"]
        assert "def sub" in files["math.py"]

    def test_integrate_to_different_files(self) -> None:
        engine = IntegratorEngine()
        engine.integrate(CodeChunk(
            target_file="models.py",
            target_symbol="User",
            operation=ChunkOperation.CREATE_CLASS,
            content="class User:\n    pass",
        ))
        engine.integrate(CodeChunk(
            target_file="routes.py",
            target_symbol="get_users",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def get_users():\n    return []",
        ))
        assert engine.file_count == 2

    def test_get_file_state(self) -> None:
        engine = IntegratorEngine()
        engine.integrate(CodeChunk(
            target_file="test.py",
            target_symbol="foo",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def foo(): pass",
        ))
        state = engine.get_file_state("test.py")
        assert state is not None
        assert "foo" in state.symbols

    def test_get_nonexistent_file_state(self) -> None:
        engine = IntegratorEngine()
        assert engine.get_file_state("nope.py") is None


class TestIntegratorEngineBatch:
    def test_integrate_batch(self) -> None:
        engine = IntegratorEngine()
        chunks = [
            CodeChunk(
                target_file="api.py",
                target_symbol="list_items",
                operation=ChunkOperation.CREATE_FUNCTION,
                content="def list_items():\n    return []",
            ),
            CodeChunk(
                target_file="api.py",
                target_symbol="get_item",
                operation=ChunkOperation.CREATE_FUNCTION,
                content="def get_item(id):\n    return {}",
            ),
            CodeChunk(
                target_file="models.py",
                target_symbol="Item",
                operation=ChunkOperation.CREATE_CLASS,
                content="class Item:\n    pass",
            ),
        ]
        results = engine.integrate_batch(chunks)
        assert len(results) == 2  # 2 files
        assert engine.file_count == 2


class TestIntegratorEngineWrite:
    def test_write_all(self, tmp_path: Path) -> None:
        engine = IntegratorEngine()
        engine.integrate(CodeChunk(
            target_file="src/utils.py",
            target_symbol="helper",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def helper():\n    return True",
        ))
        engine.integrate(CodeChunk(
            target_file="src/models.py",
            target_symbol="User",
            operation=ChunkOperation.CREATE_CLASS,
            content="class User:\n    pass",
        ))
        written = engine.write_all(tmp_path)
        assert len(written) == 2
        assert (tmp_path / "src" / "utils.py").exists()
        assert (tmp_path / "src" / "models.py").exists()
        assert "def helper" in (tmp_path / "src" / "utils.py").read_text()

    def test_write_creates_subdirs(self, tmp_path: Path) -> None:
        engine = IntegratorEngine()
        engine.integrate(CodeChunk(
            target_file="deep/nested/dir/file.py",
            target_symbol="func",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def func(): pass",
        ))
        engine.write_all(tmp_path)
        assert (tmp_path / "deep" / "nested" / "dir" / "file.py").exists()


class TestIntegratorEngineSummary:
    def test_summary(self) -> None:
        engine = IntegratorEngine()
        engine.integrate(CodeChunk(
            target_file="a.py",
            target_symbol="f1",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def f1(): pass",
        ))
        engine.integrate(CodeChunk(
            target_file="a.py",
            target_symbol="f2",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def f2(): pass",
        ))
        summary = engine.get_summary()
        assert summary["files"] == 1
        assert summary["chunks_merged"] == 2
        assert "f1" in summary["symbols"]["a.py"]
        assert "f2" in summary["symbols"]["a.py"]

    def test_reset(self) -> None:
        engine = IntegratorEngine()
        engine.integrate(CodeChunk(
            target_file="x.py",
            target_symbol="f",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def f(): pass",
        ))
        engine.reset()
        assert engine.file_count == 0
        assert engine.total_chunks_merged == 0
