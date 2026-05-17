"""Tests for WorkerAgent chunk generation."""

from unittest.mock import AsyncMock, MagicMock
import pytest

from galaxy.agents.worker import WorkerAgent
from galaxy.contracts.builder import ContractBuilder
from galaxy.contracts.types import ChunkOperation
from galaxy.events.bus import EventBus


@pytest.fixture
def worker_agent():
    router = MagicMock()
    bus = EventBus()
    return WorkerAgent(
        name="test-worker",
        model_router=router,
        event_bus=bus,
        domain="backend",
    )


class TestWorkerContractExecution:
    @pytest.mark.asyncio
    async def test_execute_contract(self, worker_agent: WorkerAgent) -> None:
        contract = (
            ContractBuilder("backend")
            .target("auth.py", "create_token")
            .operation(ChunkOperation.CREATE_FUNCTION)
            .description("Create JWT token")
            .param("user_id", "int")
            .returns("str")
            .build()
        )

        response = MagicMock()
        response.content = "def create_token(user_id: int) -> str:\n    return 'token'"
        response.total_tokens = 50
        worker_agent.invoke_llm = AsyncMock(return_value=response)

        chunk = await worker_agent.execute_contract(contract)
        assert chunk.contract_id == contract.id
        assert chunk.target_file == "auth.py"
        assert chunk.target_symbol == "create_token"
        assert chunk.operation == ChunkOperation.CREATE_FUNCTION
        assert "def create_token" in chunk.content
        assert chunk.worker_id == worker_agent.id

    @pytest.mark.asyncio
    async def test_execute_contract_with_context(self, worker_agent: WorkerAgent) -> None:
        contract = (
            ContractBuilder("backend")
            .target("main.py", "main")
            .description("Entry point")
            .build()
        )

        response = MagicMock()
        response.content = "def main(): pass"
        response.total_tokens = 20
        worker_agent.invoke_llm = AsyncMock(return_value=response)

        chunk = await worker_agent.execute_contract(contract, context="FastAPI project")
        assert chunk.content == "def main(): pass"

    @pytest.mark.asyncio
    async def test_execute_contract_failure(self, worker_agent: WorkerAgent) -> None:
        contract = (
            ContractBuilder("backend")
            .target("fail.py", "fail")
            .description("Will fail")
            .build()
        )

        worker_agent.invoke_llm = AsyncMock(side_effect=RuntimeError("LLM error"))

        with pytest.raises(RuntimeError, match="LLM error"):
            await worker_agent.execute_contract(contract)

        assert worker_agent.tasks_failed == 1

    @pytest.mark.asyncio
    async def test_contract_uses_structured_prompt(self, worker_agent: WorkerAgent) -> None:
        contract = (
            ContractBuilder("backend")
            .target("service.py", "process")
            .operation(ChunkOperation.CREATE_FUNCTION)
            .description("Process data")
            .param("data", "dict")
            .returns("bool")
            .build()
        )

        response = MagicMock()
        response.content = "def process(data: dict) -> bool: return True"
        response.total_tokens = 30
        worker_agent.invoke_llm = AsyncMock(return_value=response)

        await worker_agent.execute_contract(contract)

        # Check that the prompt used was the contract's structured prompt
        call_args = worker_agent.invoke_llm.call_args
        prompt = call_args.kwargs.get("user_message", "")
        assert "process" in prompt
        assert "No explanations" in prompt
