"""Tests for galaxy.integrator types."""

from galaxy.integrator import (
    ConflictInfo,
    ConflictResolution,
    ConflictType,
    FileState,
    MergeResult,
    MergeStrategy,
)


class TestFileState:
    def test_default(self) -> None:
        fs = FileState()
        assert fs.path == ""
        assert fs.content == ""
        assert fs.symbols == []

    def test_has_symbol(self) -> None:
        fs = FileState(symbols=["foo", "bar"])
        assert fs.has_symbol("foo")
        assert not fs.has_symbol("baz")

    def test_add_symbol(self) -> None:
        fs = FileState()
        fs.add_symbol("foo")
        assert fs.has_symbol("foo")
        fs.add_symbol("foo")  # No duplicate
        assert len(fs.symbols) == 1

    def test_roundtrip(self) -> None:
        original = FileState(path="test.py", content="x = 1", symbols=["x"])
        restored = FileState.from_dict(original.to_dict())
        assert restored.path == original.path
        assert restored.content == original.content


class TestConflictInfo:
    def test_default(self) -> None:
        c = ConflictInfo()
        assert not c.is_resolved

    def test_resolve(self) -> None:
        c = ConflictInfo(symbol_name="foo")
        c.resolve(ConflictResolution.USE_NEW, "new content")
        assert c.is_resolved
        assert c.resolution == ConflictResolution.USE_NEW
        assert c.resolved_content == "new content"


class TestMergeResult:
    def test_default(self) -> None:
        r = MergeResult()
        assert r.success
        assert not r.has_conflicts

    def test_with_conflicts(self) -> None:
        r = MergeResult(conflicts=[ConflictInfo()])
        assert r.has_conflicts
