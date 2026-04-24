"""MCP resources."""

import fastmcp

from arclith import Arclith
from adapters.input.fastmcp.resources.agent_run_resources import AgentRunResources
from infrastructure.containers.agent_run_container import build_agent_run_service

__all__ = ["AgentRunResources"]


def register_resources(mcp: fastmcp.FastMCP, arclith: Arclith) -> None:
    service, logger = build_agent_run_service(arclith)
    AgentRunResources(service, logger, mcp)
