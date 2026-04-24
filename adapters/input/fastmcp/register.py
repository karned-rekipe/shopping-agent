"""MCP tools registration."""

import fastmcp
from adapters.input.fastmcp.tools import AdminMCP, AgentRunMCP
from arclith import Arclith
from infrastructure.containers.agent_run_container import build_agent_run_service
from infrastructure.purge_registry import purge_registry


def register_tools(mcp: fastmcp.FastMCP, arclith: Arclith) -> None:
    """Register all MCP tools."""
    service, logger = build_agent_run_service(arclith)
    purge_registry.register("agent_runs", service.purge)
    AgentRunMCP(service, logger, mcp)
    AdminMCP(purge_registry, logger, mcp)

