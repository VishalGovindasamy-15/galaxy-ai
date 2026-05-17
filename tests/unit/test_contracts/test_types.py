"""Tests for galaxy.contracts.types."""

from galaxy.contracts.types import (
    ChunkOperation,
    ChunkStatus,
    CodeChunk,
    ContractStatus,
    ExecutionContract,
    ParameterSpec,
    ReturnSpec,
)


class TestEnums:
    """Test contract enums."""

    def test_chunk_operations(self) -> None:
        assert len(ChunkOperation) == 10
        assert ChunkOperation.CREATE_FUNCTION.value == "create_function"

    def test_contract_status_terminal(self) -> None:
        assert ContractStatus.COMPLETED.is_terminal()
        assert ContractStatus.FAILED.is_terminal()
        assert not ContractStatus.DRAFT.is_terminal()
        assert not ContractStatus.IN_PROGRESS.is_terminal()

    def test_chunk_status_terminal(self) -> None:
        assert ChunkStatus.MERGED.is_terminal()
        assert ChunkStatus.FAILED.is_terminal()
        assert not ChunkStatus.PENDING.is_terminal()


class TestParameterSpec:
    """Test ParameterSpec dataclass."""

    def test_default(self) -> None:
        p = ParameterSpec()
        assert p.name == ""
        assert p.type_hint == "Any"
        assert p.default is None

    def test_with_values(self) -> None:
        p = ParameterSpec(name="user_id", type_hint="int", description="User ID")
        assert p.name == "user_id"
        assert p.type_hint == "int"

    def test_roundtrip(self) -> None:
        original = ParameterSpec(name="x", type_hint="str", default="''", description="Name")
        restored = ParameterSpec.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.type_hint == original.type_hint
        assert restored.default == original.default


class TestReturnSpec:
    """Test ReturnSpec dataclass."""

    def test_default(self) -> None:
        r = ReturnSpec()
        assert r.type_hint == "None"

    def test_roundtrip(self) -> None:
        original = ReturnSpec(type_hint="dict[str, Any]", description="User data")
        restored = ReturnSpec.from_dict(original.to_dict())
        assert restored.type_hint == original.type_hint


class TestExecutionContract:
    """Test ExecutionContract dataclass."""

    def test_default(self) -> None:
        c = ExecutionContract()
        assert c.id
        assert c.status == ContractStatus.DRAFT
        assert c.operation == ChunkOperation.CREATE_FUNCTION

    def test_signature_generation(self) -> None:
        c = ExecutionContract(
            function_name="create_jwt",
            parameters=[
                ParameterSpec(name="user_id", type_hint="int"),
                ParameterSpec(name="secret", type_hint="str"),
            ],
            return_spec=ReturnSpec(type_hint="str"),
        )
        assert c.signature == "create_jwt(user_id: int, secret: str) -> str"

    def test_signature_with_defaults(self) -> None:
        c = ExecutionContract(
            function_name="greet",
            parameters=[
                ParameterSpec(name="name", type_hint="str"),
                ParameterSpec(name="greeting", type_hint="str", default="'Hello'"),
            ],
            return_spec=ReturnSpec(type_hint="str"),
        )
        assert "greeting: str = 'Hello'" in c.signature

    def test_assign_worker(self) -> None:
        c = ExecutionContract()
        c.assign("worker-001")
        assert c.worker_id == "worker-001"
        assert c.status == ContractStatus.ASSIGNED

    def test_complete(self) -> None:
        c = ExecutionContract()
        c.complete()
        assert c.status == ContractStatus.COMPLETED

    def test_fail(self) -> None:
        c = ExecutionContract()
        c.fail()
        assert c.status == ContractStatus.FAILED

    def test_to_worker_prompt(self) -> None:
        c = ExecutionContract(
            function_name="validate_email",
            target_file="utils/validators.py",
            operation=ChunkOperation.CREATE_FUNCTION,
            description="Validate an email address format",
            parameters=[
                ParameterSpec(name="email", type_hint="str", description="Email to validate"),
            ],
            return_spec=ReturnSpec(type_hint="bool", description="True if valid"),
            dependencies=["re"],
            constraints={"security": "high"},
            validation=["returns True for valid emails", "returns False for invalid"],
        )
        prompt = c.to_worker_prompt()
        assert "validate_email" in prompt
        assert "utils/validators.py" in prompt
        assert "email" in prompt
        assert "bool" in prompt
        assert "re" in prompt
        assert "security: high" in prompt
        assert "No explanations" in prompt

    def test_roundtrip(self) -> None:
        original = ExecutionContract(
            domain="backend",
            target_file="auth/service.py",
            function_name="create_jwt",
            description="Create JWT token",
            parameters=[ParameterSpec(name="user_id", type_hint="int")],
            return_spec=ReturnSpec(type_hint="str"),
            dependencies=["jwt"],
            constraints={"security": "high"},
            validation=["returns valid JWT"],
        )
        restored = ExecutionContract.from_dict(original.to_dict())
        assert restored.domain == original.domain
        assert restored.target_file == original.target_file
        assert restored.function_name == original.function_name
        assert len(restored.parameters) == 1
        assert restored.dependencies == ["jwt"]


class TestCodeChunk:
    """Test CodeChunk dataclass."""

    def test_default(self) -> None:
        chunk = CodeChunk()
        assert chunk.id
        assert chunk.status == ChunkStatus.PENDING

    def test_with_values(self) -> None:
        chunk = CodeChunk(
            contract_id="c001",
            target_file="auth/service.py",
            target_symbol="create_jwt",
            operation=ChunkOperation.CREATE_FUNCTION,
            content="def create_jwt(user_id: int) -> str:\n    ...",
            dependencies=["jwt"],
        )
        assert chunk.target_symbol == "create_jwt"
        assert "def create_jwt" in chunk.content

    def test_roundtrip(self) -> None:
        original = CodeChunk(
            contract_id="c002",
            target_file="models.py",
            target_symbol="User",
            operation=ChunkOperation.CREATE_CLASS,
            content="class User:\n    pass",
            worker_id="w001",
        )
        restored = CodeChunk.from_dict(original.to_dict())
        assert restored.contract_id == original.contract_id
        assert restored.target_symbol == original.target_symbol
        assert restored.content == original.content
