"""Integration test: Domain contract → Worker chunk → Integrator → File.

MODULE GATE for Week 13-14: Structured Contracts + Chunk-Based Workers.
Tests the complete flow from contract creation to file output.
"""

from pathlib import Path

from galaxy.contracts.builder import ContractBuilder, build_contract_from_dict
from galaxy.contracts.types import ChunkOperation, CodeChunk, ContractStatus
from galaxy.integrator.engine import IntegratorEngine


class TestDomainContractToWorkerChunkToFile:
    """Test the full contract → chunk → file pipeline."""

    def test_full_pipeline(self, tmp_path: Path) -> None:
        """Domain creates contract → Worker generates chunk → Integrator merges → File written."""

        # Step 1: Domain creates contracts
        jwt_contract = (
            ContractBuilder("backend")
            .target("auth/service.py", "create_jwt_token")
            .operation(ChunkOperation.CREATE_FUNCTION)
            .description("Create a JWT token for authenticated users")
            .param("user_id", "int", description="User database ID")
            .param("secret", "str", description="JWT signing secret")
            .param("expiry_hours", "int", default="1", description="Token expiry in hours")
            .returns("str", "Encoded JWT token string")
            .depends_on("jwt", "datetime")
            .constraint("security", "high")
            .validate_with("returns valid JWT", "expires correctly")
            .build()
        )

        verify_contract = (
            ContractBuilder("backend")
            .target("auth/service.py", "verify_jwt_token")
            .operation(ChunkOperation.CREATE_FUNCTION)
            .description("Verify and decode a JWT token")
            .param("token", "str", description="JWT token to verify")
            .param("secret", "str", description="JWT signing secret")
            .returns("dict", "Decoded token payload")
            .depends_on("jwt")
            .constraint("security", "high")
            .validate_with("returns payload for valid token", "raises for expired token")
            .build()
        )

        # Verify contracts are well-formed
        assert jwt_contract.status == ContractStatus.READY
        assert jwt_contract.signature == "create_jwt_token(user_id: int, secret: str, expiry_hours: int = 1) -> str"
        assert "jwt" in jwt_contract.dependencies
        assert jwt_contract.constraints["security"] == "high"

        # Step 2: Worker generates chunks from contracts
        # (In production, the worker LLM generates this. Here we simulate.)
        jwt_chunk = CodeChunk(
            contract_id=jwt_contract.id,
            target_file=jwt_contract.target_file,
            target_symbol=jwt_contract.function_name,
            operation=jwt_contract.operation,
            content=(
                "import jwt\nfrom datetime import datetime, timedelta\n\n"
                "def create_jwt_token(user_id: int, secret: str, expiry_hours: int = 1) -> str:\n"
                '    payload = {\n'
                '        "user_id": user_id,\n'
                '        "exp": datetime.utcnow() + timedelta(hours=expiry_hours),\n'
                '    }\n'
                '    return jwt.encode(payload, secret, algorithm="HS256")\n'
            ),
            dependencies=["jwt", "datetime"],
            worker_id="worker-001",
        )

        verify_chunk = CodeChunk(
            contract_id=verify_contract.id,
            target_file=verify_contract.target_file,
            target_symbol=verify_contract.function_name,
            operation=verify_contract.operation,
            content=(
                "import jwt\n\n"
                "def verify_jwt_token(token: str, secret: str) -> dict:\n"
                '    return jwt.decode(token, secret, algorithms=["HS256"])\n'
            ),
            dependencies=["jwt"],
            worker_id="worker-002",
        )

        # Step 3: Integrator merges chunks into files
        engine = IntegratorEngine()
        result1 = engine.integrate(jwt_chunk)
        result2 = engine.integrate(verify_chunk)

        assert result1.success
        assert result2.success

        # Step 4: Verify assembled file
        files = engine.get_all_files()
        assert "auth/service.py" in files

        content = files["auth/service.py"]
        assert "import jwt" in content
        assert "from datetime import" in content
        assert "def create_jwt_token" in content
        assert "def verify_jwt_token" in content

        # Import dedup: jwt should appear only once
        assert content.count("import jwt") == 1

        # Step 5: Write to disk and verify
        written = engine.write_all(tmp_path)
        assert len(written) == 1

        output_file = tmp_path / "auth" / "service.py"
        assert output_file.exists()
        file_content = output_file.read_text()
        assert "def create_jwt_token" in file_content
        assert "def verify_jwt_token" in file_content

    def test_multi_file_pipeline(self, tmp_path: Path) -> None:
        """Test contract pipeline across multiple files."""

        # Domain creates contracts for different files
        model_contract_data = {
            "domain": "backend",
            "target_file": "models/user.py",
            "function_name": "User",
            "operation": "create_class",
            "description": "User data model",
            "parameters": [
                {"name": "name", "type": "str"},
                {"name": "email", "type": "str"},
            ],
        }
        route_contract_data = {
            "domain": "backend",
            "target_file": "routes/users.py",
            "function_name": "get_users",
            "operation": "create_function",
            "description": "Get all users endpoint",
            "return_spec": {"type_hint": "list[dict]"},
            "dependencies": ["fastapi"],
        }

        # Build from dict (simulating LLM output)
        model_contract = build_contract_from_dict(model_contract_data)
        route_contract = build_contract_from_dict(route_contract_data)

        assert model_contract.function_name == "User"
        assert model_contract.operation == ChunkOperation.CREATE_CLASS
        assert route_contract.return_spec.type_hint == "list[dict]"

        # Simulate worker output
        model_chunk = CodeChunk(
            contract_id=model_contract.id,
            target_file="models/user.py",
            target_symbol="User",
            operation=ChunkOperation.CREATE_CLASS,
            content=(
                "from dataclasses import dataclass\n\n"
                "@dataclass\n"
                "class User:\n"
                "    name: str\n"
                "    email: str\n"
            ),
        )
        route_chunk = CodeChunk(
            contract_id=route_contract.id,
            target_file="routes/users.py",
            target_symbol="get_users",
            operation=ChunkOperation.CREATE_FUNCTION,
            content=(
                "from fastapi import APIRouter\n\n"
                "router = APIRouter()\n\n"
                "@router.get('/users')\n"
                "def get_users() -> list[dict]:\n"
                "    return []\n"
            ),
        )

        # Integrate
        engine = IntegratorEngine()
        engine.integrate(model_chunk)
        engine.integrate(route_chunk)

        assert engine.file_count == 2

        # Write
        engine.write_all(tmp_path)
        assert (tmp_path / "models" / "user.py").exists()
        assert (tmp_path / "routes" / "users.py").exists()

        model_content = (tmp_path / "models" / "user.py").read_text()
        assert "class User" in model_content
        assert "dataclass" in model_content

    def test_contract_worker_prompt_quality(self) -> None:
        """Verify contract generates a high-quality worker prompt."""
        contract = (
            ContractBuilder("backend")
            .target("auth/middleware.py", "require_auth")
            .operation(ChunkOperation.CREATE_FUNCTION)
            .description("Middleware that requires JWT authentication")
            .param("request", "Request", description="FastAPI request")
            .returns("dict", "Decoded token payload")
            .depends_on("jwt", "fastapi")
            .constraint("security", "critical")
            .validate_with("rejects invalid tokens", "passes valid tokens")
            .context("Used as FastAPI dependency injection")
            .build()
        )

        prompt = contract.to_worker_prompt()

        # The prompt should contain all key information
        assert "require_auth" in prompt
        assert "auth/middleware.py" in prompt
        assert "Request" in prompt
        assert "dict" in prompt
        assert "jwt" in prompt
        assert "security: critical" in prompt
        assert "rejects invalid tokens" in prompt
        assert "FastAPI dependency injection" in prompt
        assert "No explanations" in prompt

    def test_summary_stats(self) -> None:
        """Test integration summary is accurate."""
        engine = IntegratorEngine()

        for i in range(5):
            engine.integrate(CodeChunk(
                target_file=f"file_{i % 2}.py",
                target_symbol=f"func_{i}",
                operation=ChunkOperation.CREATE_FUNCTION,
                content=f"def func_{i}(): pass",
            ))

        summary = engine.get_summary()
        assert summary["files"] == 2
        assert summary["chunks_merged"] == 5
