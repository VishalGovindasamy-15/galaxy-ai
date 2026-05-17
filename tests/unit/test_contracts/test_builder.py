"""Tests for galaxy.contracts.builder."""

import pytest

from galaxy.contracts.builder import (
    ContractBuilder,
    ContractValidationError,
    build_contract_from_dict,
)
from galaxy.contracts.types import (
    ChunkOperation,
    ContractStatus,
)


class TestContractBuilderFluent:
    """Test fluent API for building contracts."""

    def test_basic_build(self) -> None:
        contract = (
            ContractBuilder("backend")
            .target("auth/service.py", "create_jwt")
            .description("Create a JWT token")
            .build()
        )
        assert contract.domain == "backend"
        assert contract.target_file == "auth/service.py"
        assert contract.function_name == "create_jwt"
        assert contract.status == ContractStatus.READY

    def test_full_build(self) -> None:
        contract = (
            ContractBuilder("backend")
            .target("auth/service.py", "create_jwt_token")
            .operation(ChunkOperation.CREATE_FUNCTION)
            .description("Create JWT token for user auth")
            .param("user_id", "int", description="User database ID")
            .param("secret", "str", description="JWT signing secret")
            .param("expiry_hours", "int", default="1", description="Token expiry")
            .returns("str", "Encoded JWT token")
            .depends_on("jwt", "datetime")
            .constraint("security", "high")
            .validate_with("returns valid JWT", "expires in 1h")
            .context("Part of the authentication system")
            .build()
        )
        assert contract.function_name == "create_jwt_token"
        assert len(contract.parameters) == 3
        assert contract.parameters[2].default == "1"
        assert contract.return_spec.type_hint == "str"
        assert "jwt" in contract.dependencies
        assert contract.constraints["security"] == "high"
        assert len(contract.validation) == 2
        assert "authentication" in contract.context

    def test_signature(self) -> None:
        contract = (
            ContractBuilder("backend")
            .target("utils.py", "add")
            .description("Add two numbers")
            .param("a", "int")
            .param("b", "int")
            .returns("int")
            .build()
        )
        assert contract.signature == "add(a: int, b: int) -> int"

    def test_builder_reset(self) -> None:
        builder = ContractBuilder("backend")
        builder.target("file1.py", "func1").description("Desc 1")
        c1 = builder.build()

        builder.reset()
        builder.target("file2.py", "func2").description("Desc 2")
        c2 = builder.build()

        assert c1.target_file == "file1.py"
        assert c2.target_file == "file2.py"
        assert c2.domain == "backend"  # Domain preserved after reset


class TestContractBuilderValidation:
    """Test contract validation."""

    def test_missing_target_file(self) -> None:
        with pytest.raises(ContractValidationError, match="target_file"):
            ContractBuilder("backend").description("Test").build()

    def test_missing_function_name(self) -> None:
        with pytest.raises(ContractValidationError, match="function_name"):
            (
                ContractBuilder("backend")
                .target("file.py")
                .description("Test")
                .build()
            )

    def test_missing_description(self) -> None:
        with pytest.raises(ContractValidationError, match="description"):
            (
                ContractBuilder("backend")
                .target("file.py", "func")
                .build()
            )

    def test_create_file_doesnt_need_function_name(self) -> None:
        """CREATE_FILE operation doesn't require function_name."""
        contract = (
            ContractBuilder("backend")
            .target("models.py")
            .operation(ChunkOperation.CREATE_FILE)
            .description("Create the models file")
            .build()
        )
        assert contract.operation == ChunkOperation.CREATE_FILE

    def test_skip_validation(self) -> None:
        contract = ContractBuilder("backend").build(validate=False)
        assert contract.target_file == ""  # No error raised


class TestBuildContractFromDict:
    """Test building contracts from dictionary (LLM output)."""

    def test_basic_dict(self) -> None:
        data = {
            "domain": "backend",
            "target_file": "auth/service.py",
            "function_name": "create_jwt",
            "description": "Create JWT token",
            "parameters": [
                {"name": "user_id", "type": "int", "description": "User ID"},
            ],
            "return_spec": {"type_hint": "str", "description": "JWT token"},
            "dependencies": ["jwt"],
        }
        contract = build_contract_from_dict(data)
        assert contract.domain == "backend"
        assert contract.function_name == "create_jwt"
        assert len(contract.parameters) == 1
        assert contract.parameters[0].type_hint == "int"
        assert contract.return_spec.type_hint == "str"

    def test_dict_with_function_alias(self) -> None:
        """Test 'function' as alias for 'function_name'."""
        data = {
            "target_file": "api.py",
            "function": "get_users",
            "description": "Get all users",
        }
        contract = build_contract_from_dict(data)
        assert contract.function_name == "get_users"

    def test_dict_with_string_returns(self) -> None:
        """Test 'returns' as string shorthand."""
        data = {
            "target_file": "api.py",
            "function_name": "count",
            "description": "Count items",
            "returns": "int",
        }
        contract = build_contract_from_dict(data)
        assert contract.return_spec.type_hint == "int"

    def test_dict_with_constraints(self) -> None:
        data = {
            "target_file": "auth.py",
            "function_name": "hash_password",
            "description": "Hash password",
            "constraints": {"security": "critical"},
            "validation": ["uses bcrypt", "returns hash string"],
        }
        contract = build_contract_from_dict(data)
        assert contract.constraints["security"] == "critical"
        assert len(contract.validation) == 2

    def test_empty_dict(self) -> None:
        contract = build_contract_from_dict({})
        assert contract.target_file == ""

    def test_dict_with_operation(self) -> None:
        data = {
            "target_file": "models.py",
            "function_name": "User",
            "description": "User model",
            "operation": "create_class",
        }
        contract = build_contract_from_dict(data)
        assert contract.operation == ChunkOperation.CREATE_CLASS

    def test_dict_with_invalid_operation(self) -> None:
        data = {
            "target_file": "x.py",
            "function_name": "f",
            "description": "Test",
            "operation": "invalid_op",
        }
        contract = build_contract_from_dict(data)
        assert contract.operation == ChunkOperation.CREATE_FUNCTION  # Falls back
