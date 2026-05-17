"""Tests for galaxy.integrator.conflict."""

from galaxy.contracts.types import ChunkOperation, CodeChunk
from galaxy.integrator import (
    ConflictInfo,
    ConflictResolution,
    ConflictType,
    FileState,
)
from galaxy.integrator.conflict import ConflictDetector, ConflictResolver


class TestConflictDetector:
    def test_detect_duplicate_symbol(self) -> None:
        detector = ConflictDetector()
        fs = FileState(
            path="test.py",
            content="def foo():\n    pass",
            symbols=["foo"],
        )
        chunk = CodeChunk(
            target_file="test.py",
            target_symbol="foo",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def foo():\n    return 42",
        )
        conflicts = detector.detect(chunk, fs)
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.DUPLICATE_SYMBOL
        assert conflicts[0].symbol_name == "foo"

    def test_no_conflict_new_symbol(self) -> None:
        detector = ConflictDetector()
        fs = FileState(path="test.py", content="def foo(): pass", symbols=["foo"])
        chunk = CodeChunk(
            target_file="test.py",
            target_symbol="bar",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def bar(): pass",
        )
        conflicts = detector.detect(chunk, fs)
        assert len(conflicts) == 0

    def test_detect_import_conflict(self) -> None:
        detector = ConflictDetector()
        fs = FileState(
            path="test.py",
            imports=["from os import path"],
        )
        chunk = CodeChunk(
            target_file="test.py",
            target_symbol="f",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="from os import getcwd\n\ndef f(): pass",
        )
        conflicts = detector.detect(chunk, fs)
        import_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.IMPORT_CONFLICT]
        assert len(import_conflicts) == 1

    def test_detect_batch_inter_chunk(self) -> None:
        detector = ConflictDetector()
        fs = FileState(path="test.py")
        chunks = [
            CodeChunk(target_file="test.py", target_symbol="foo", content="def foo(): pass"),
            CodeChunk(target_file="test.py", target_symbol="foo", content="def foo(): return 1"),
        ]
        conflicts = detector.detect_batch(chunks, fs)
        assert len(conflicts) >= 1


class TestConflictResolver:
    def test_resolve_use_new(self) -> None:
        resolver = ConflictResolver()
        conflict = ConflictInfo(
            existing_content="def foo(): pass",
            new_content="def foo(): return 42",
        )
        result = resolver.resolve(conflict, ConflictResolution.USE_NEW)
        assert result == "def foo(): return 42"
        assert conflict.is_resolved

    def test_resolve_keep_existing(self) -> None:
        resolver = ConflictResolver()
        conflict = ConflictInfo(
            existing_content="def foo(): pass",
            new_content="def foo(): return 42",
        )
        result = resolver.resolve(conflict, ConflictResolution.KEEP_EXISTING)
        assert result == "def foo(): pass"

    def test_auto_resolve_duplicate(self) -> None:
        resolver = ConflictResolver()
        conflict = ConflictInfo(
            conflict_type=ConflictType.DUPLICATE_SYMBOL,
            existing_content="old",
            new_content="new",
        )
        result = resolver.auto_resolve(conflict)
        assert result == "new"

    def test_auto_resolve_import_merges(self) -> None:
        resolver = ConflictResolver()
        conflict = ConflictInfo(
            conflict_type=ConflictType.IMPORT_CONFLICT,
            existing_content="from os import path",
            new_content="from os import getcwd",
        )
        result = resolver.auto_resolve(conflict)
        assert "path" in result
        assert "getcwd" in result
        assert result.startswith("from os import")

    def test_merge_imports_dedup(self) -> None:
        resolver = ConflictResolver()
        conflict = ConflictInfo(
            conflict_type=ConflictType.IMPORT_CONFLICT,
            existing_content="from os import path, getcwd",
            new_content="from os import path, listdir",
        )
        result = resolver.auto_resolve(conflict)
        assert "path" in result
        assert "getcwd" in result
        assert "listdir" in result
