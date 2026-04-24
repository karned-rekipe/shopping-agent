from unittest.mock import AsyncMock, patch

import fastmcp
import pytest

from adapters.input.fastmcp.prompts import AgentRunPrompts
from application.services.agent_run_service import AgentRunService
from domain.models.agent_run import AgentRun


@pytest.fixture
def mcp_app():
    return fastmcp.FastMCP("test")


@pytest.fixture
def service(repo, logger):
    return AgentRunService(repo, logger)


@pytest.fixture
async def client(service, logger, mcp_app):
    with patch("adapters.input.fastmcp.prompts.agent_run_prompts.inject_tenant_uri", new=AsyncMock()):
        AgentRunPrompts(service, logger, mcp_app)
        async with fastmcp.Client(mcp_app) as c:
            yield c


def _text(result) -> str:
    return result.messages[0].content.text


# --- check_duplicate ---

async def test_check_duplicate_contains_name(client):
    result = await client.get_prompt("check_duplicate", {"agent_run_name": "Farine"})
    assert "Farine" in _text(result)


async def test_check_duplicate_mentions_list_tool(client):
    result = await client.get_prompt("check_duplicate", {"agent_run_name": "Sel"})
    assert "list_agent_runs" in _text(result)


# --- explore_agent_runs ---

async def test_explore_empty_catalog(client):
    result = await client.get_prompt("explore_agent_runs", {})
    assert "No agent_runs available" in _text(result)


async def test_explore_lists_agent_run_names(client, service):
    await service.create(AgentRun(name="Farine"))
    await service.create(AgentRun(name="Sel"))
    result = await client.get_prompt("explore_agent_runs", {})
    text = _text(result)
    assert "Farine" in text
    assert "Sel" in text


async def test_explore_shows_total_count(client, service):
    for i in range(3):
        await service.create(AgentRun(name=f"Item {i}"))
    result = await client.get_prompt("explore_agent_runs", {})
    assert "3" in _text(result)


# --- mcp_help ---

async def test_mcp_help_lists_tools(client):
    text = _text(await client.get_prompt("mcp_help", {}))
    assert "create_agent_run" in text
    assert "list_agent_runs" in text
    assert "purge_agent_runs" in text


async def test_mcp_help_lists_prompts(client):
    text = _text(await client.get_prompt("mcp_help", {}))
    assert "check_duplicate" in text
    assert "explore_agent_runs" in text
    assert "mcp_help" in text


async def test_mcp_help_lists_resources(client):
    text = _text(await client.get_prompt("mcp_help", {}))
    assert "resource://agent-runs/sample" in text
    assert "resource://agent-runs/recent" in text
    assert "resource://agent-run/{uuid}" in text
