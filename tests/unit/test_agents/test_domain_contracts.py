"""Tests for DomainAgent contract support."""

from unittest.mock import AsyncMock, MagicMock
import json
import pytest

from galaxy.agents.domain import DomainAgent
from galaxy.events.bus import EventBus


@pytest.fixture
def domain_agent():
    router = MagicMock()
    bus = EventBus()
    return DomainAgent(
        name="test-backend",
        model_router=router,
        event_bus=bus,
        domain="backend",
    )


class TestDomainContractBuilder:
    def test_build_contract(self, domain_agent: DomainAgent) -> None:
        builder = domain_agent.build_contract()
        contract = (
            builder
            .target("auth.py", "login")
            .description("Login function")
            .build(validate=False)
        )
        assert contract.domain == "backend"
        assert contract.function_name == "login"


class TestDomainContractParsing:
    def test_parse_valid_contracts(self, domain_agent: DomainAgent) -> None:
        raw = json.dumps([{
            "target_file": "auth.py",
            "function_name": "login",
            "operation": "create_function",
            "description": "Login function",
        }])
        contracts = domain_agent._parse_contracts(raw)
        assert len(contracts) == 1
        assert contracts[0].function_name == "login"
        assert contracts[0].domain == "backend"

    def test_parse_invalid_json(self, domain_agent: DomainAgent) -> None:
        contracts = domain_agent._parse_contracts("not json")
        assert len(contracts) == 1  # Fallback contract

    def test_parse_markdown_wrapped(self, domain_agent: DomainAgent) -> None:
        raw = '```json\n' + json.dumps([{
            "target_file": "main.py",
            "function_name": "main",
            "operation": "create_function",
            "description": "Entry point",
        }]) + '\n```'
        contracts = domain_agent._parse_contracts(raw)
        assert len(contracts) == 1
        assert contracts[0].function_name == "main"


class TestDomainContractPlanning:
    @pytest.mark.asyncio
    async def test_plan_contracts(self, domain_agent: DomainAgent) -> None:
        response = MagicMock()
        response.content = json.dumps([{
            "target_file": "routes.py",
            "function_name": "get_users",
            "operation": "create_function",
            "description": "List users",
        }])
        domain_agent.invoke_llm = AsyncMock(return_value=response)

        contracts = await domain_agent.plan_contracts("Build user CRUD")
        assert len(contracts) == 1
        assert contracts[0].function_name == "get_users"
