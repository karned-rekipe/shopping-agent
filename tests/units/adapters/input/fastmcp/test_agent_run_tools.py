import fastmcp
import json
import pytest
from unittest.mock import AsyncMock, patch

from adapters.input.fastmcp.tools import AdminMCP, AgentRunMCP
from application.services.agent_run_service import AgentRunService


@pytest.fixture
def mcp_app():
    return fastmcp.FastMCP("test")


@pytest.fixture
def service(repo, logger):
    return AgentRunService(repo, logger)


@pytest.fixture
async def client(service, logger, mcp_app):
    with patch("adapters.input.fastmcp.tools.agent_run_tools.inject_tenant_uri", new=AsyncMock()):
        with patch("adapters.input.fastmcp.tools.agent_run_tools.require_auth_mcp", new=AsyncMock(return_value={"sub": "test-user"})):
            with patch("adapters.input.fastmcp.tools.admin_tools.require_auth_mcp", new=AsyncMock(return_value={"sub": "test-user"})):
                from infrastructure.purge_registry import PurgeRegistry
                registry = PurgeRegistry()
                registry.register("agent_runs", service.purge)
                AgentRunMCP(service, logger, mcp_app)
                AdminMCP(registry, logger, mcp_app)
                async with fastmcp.Client(mcp_app) as c:
                    yield c


def _data(result) -> dict | list | None:
    if not result.content:
        return result.data
    return json.loads(result.content[0].text)


@pytest.fixture
async def created_uuid(client) -> str:
    result = await client.call_tool("create_agent_run", {"name": "Farine"})
    data = _data(result)
    assert isinstance(data, dict)
    return data["uuid"]


# --- create_agent_run ---

async def test_create_returns_uuid(client):
    result = await client.call_tool("create_agent_run", {"name": "Farine"})
    assert "uuid" in _data(result)



# --- get_agent_run ---

async def test_get_found(client, created_uuid):
    result = await client.call_tool("get_agent_run", {"uuid": created_uuid})
    assert _data(result)["name"] == "Farine"


async def test_get_not_found_returns_none(client):
    result = await client.call_tool("get_agent_run", {"uuid": "01951234-5678-7abc-def0-000000000000"})
    assert _data(result) is None


# --- update_agent_run ---

async def test_update_changes_name(client, created_uuid):
    await client.call_tool("update_agent_run", {"uuid": created_uuid, "name": "Farine T55"})
    result = await client.call_tool("get_agent_run", {"uuid": created_uuid})
    assert _data(result)["name"] == "Farine T55"


# --- delete_agent_run ---

async def test_delete_hides_agent_run(client, created_uuid):
    await client.call_tool("delete_agent_run", {"uuid": created_uuid})
    result = await client.call_tool("get_agent_run", {"uuid": created_uuid})
    assert _data(result) is None


# --- list_agent_runs ---

async def test_list_all(client):
    await client.call_tool("create_agent_run", {"name": "Farine"})
    await client.call_tool("create_agent_run", {"name": "Sel"})
    result = await client.call_tool("list_agent_runs", {})
    assert len(_data(result)) == 2


async def test_list_filtered(client):
    await client.call_tool("create_agent_run", {"name": "Farine de blé"})
    await client.call_tool("create_agent_run", {"name": "Sel fin"})
    result = await client.call_tool("list_agent_runs", {"name": "farine"})
    items = _data(result)
    assert len(items) == 1
    assert items[0]["name"] == "Farine de blé"


# --- duplicate_agent_run ---

async def test_duplicate_returns_new_uuid(client, created_uuid):
    result = await client.call_tool("duplicate_agent_run", {"uuid": created_uuid})
    assert _data(result)["uuid"] != created_uuid


# --- purge_all ---

async def test_purge_returns_count(client):
    result = await client.call_tool("purge_all", {})
    data = _data(result)
    assert "purged" in data
    assert "total" in data
