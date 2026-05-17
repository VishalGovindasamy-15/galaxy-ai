"""Tests for galaxy.integrator.merger."""

from galaxy.contracts.types import ChunkOperation, ChunkStatus, CodeChunk
from galaxy.integrator import FileState
from galaxy.integrator.merger import ChunkMerger


class TestChunkMergerBasic:
    def test_merge_single_function(self) -> None:
        merger = ChunkMerger()
        chunk = CodeChunk(
            target_file="utils.py",
            target_symbol="add",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def add(a: int, b: int) -> int:\n    return a + b",
        )
        result = merger.merge_chunk(chunk)
        assert result.success
        assert "def add" in result.content
        assert result.chunks_merged == 1
        assert "add" in result.symbols_added

    def test_merge_function_with_imports(self) -> None:
        merger = ChunkMerger()
        chunk = CodeChunk(
            target_file="utils.py",
            target_symbol="now",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="from datetime import datetime\n\ndef now() -> str:\n    return datetime.now().isoformat()",
        )
        result = merger.merge_chunk(chunk)
        assert "from datetime import datetime" in result.content
        assert "def now" in result.content
        assert result.imports_added == ["from datetime import datetime"]

    def test_merge_with_dependencies(self) -> None:
        merger = ChunkMerger()
        chunk = CodeChunk(
            target_file="auth.py",
            target_symbol="hash_pw",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def hash_pw(pw: str) -> str:\n    return bcrypt.hashpw(pw)",
            dependencies=["bcrypt"],
        )
        result = merger.merge_chunk(chunk)
        assert "import bcrypt" in result.content

    def test_merge_class(self) -> None:
        merger = ChunkMerger()
        chunk = CodeChunk(
            target_file="models.py",
            target_symbol="User",
            operation=ChunkOperation.CREATE_CLASS,
            content="class User:\n    def __init__(self, name: str):\n        self.name = name",
        )
        result = merger.merge_chunk(chunk)
        assert "class User" in result.content
        assert "User" in result.symbols_added

    def test_chunk_status_updated(self) -> None:
        merger = ChunkMerger()
        chunk = CodeChunk(
            target_file="x.py",
            target_symbol="f",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def f(): pass",
        )
        assert chunk.status == ChunkStatus.PENDING
        merger.merge_chunk(chunk)
        assert chunk.status == ChunkStatus.MERGED


class TestChunkMergerMultiple:
    def test_merge_two_functions(self) -> None:
        merger = ChunkMerger()
        fs = FileState(path="math.py")

        chunk1 = CodeChunk(
            target_file="math.py",
            target_symbol="add",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def add(a, b):\n    return a + b",
        )
        chunk2 = CodeChunk(
            target_file="math.py",
            target_symbol="sub",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def sub(a, b):\n    return a - b",
        )

        merger.merge_chunk(chunk1, fs)
        result = merger.merge_chunk(chunk2, fs)

        assert "def add" in result.content
        assert "def sub" in result.content
        assert len(fs.symbols) == 2

    def test_merge_chunks_batch(self) -> None:
        merger = ChunkMerger()
        chunks = [
            CodeChunk(
                target_file="api.py",
                target_symbol="get_users",
                operation=ChunkOperation.CREATE_FUNCTION,
                content="def get_users():\n    return []",
            ),
            CodeChunk(
                target_file="api.py",
                target_symbol="get_user",
                operation=ChunkOperation.CREATE_FUNCTION,
                content="def get_user(id: int):\n    return {}",
            ),
        ]
        result = merger.merge_chunks(chunks)
        assert result.chunks_merged == 2
        assert "def get_users" in result.content
        assert "def get_user" in result.content

    def test_import_deduplication(self) -> None:
        merger = ChunkMerger()
        fs = FileState(path="test.py")

        chunk1 = CodeChunk(
            target_file="test.py",
            target_symbol="f1",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="import os\n\ndef f1():\n    return os.getcwd()",
        )
        chunk2 = CodeChunk(
            target_file="test.py",
            target_symbol="f2",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="import os\nimport json\n\ndef f2():\n    return json.dumps({})",
        )

        merger.merge_chunk(chunk1, fs)
        merger.merge_chunk(chunk2, fs)

        assembled = merger.assemble_file(fs)
        assert assembled.count("import os") == 1
        assert "import json" in assembled


class TestChunkMergerOperations:
    def test_create_file(self) -> None:
        merger = ChunkMerger()
        chunk = CodeChunk(
            target_file="new.py",
            operation=ChunkOperation.CREATE_FILE,
            content='"""New module."""\n\nx = 1\ny = 2',
        )
        result = merger.merge_chunk(chunk)
        assert '"""New module."""' in result.content

    def test_append_code(self) -> None:
        merger = ChunkMerger()
        fs = FileState(path="config.py", content="DEBUG = True")
        chunk = CodeChunk(
            target_file="config.py",
            operation=ChunkOperation.APPEND_CODE,
            content="PORT = 8080",
        )
        result = merger.merge_chunk(chunk, fs)
        assert "DEBUG = True" in result.content
        assert "PORT = 8080" in result.content

    def test_add_import(self) -> None:
        merger = ChunkMerger()
        fs = FileState(path="test.py", content="x = 1")
        chunk = CodeChunk(
            target_file="test.py",
            operation=ChunkOperation.ADD_IMPORT,
            content="import json",
        )
        result = merger.merge_chunk(chunk, fs)
        assert "import json" in result.content


class TestAssembleFile:
    def test_import_ordering(self) -> None:
        merger = ChunkMerger()
        fs = FileState(
            path="test.py",
            imports=[
                "from galaxy.core import types",
                "import os",
                "import fastapi",
            ],
            content="x = 1",
        )
        assembled = merger.assemble_file(fs)
        lines = assembled.split("\n")

        # stdlib before third-party before local
        os_idx = next(i for i, l in enumerate(lines) if "import os" in l)
        fastapi_idx = next(i for i, l in enumerate(lines) if "import fastapi" in l)
        galaxy_idx = next(i for i, l in enumerate(lines) if "galaxy" in l)

        assert os_idx < fastapi_idx
        assert fastapi_idx < galaxy_idx

    def test_empty_file_state(self) -> None:
        merger = ChunkMerger()
        fs = FileState(path="empty.py")
        assert merger.assemble_file(fs) == ""
