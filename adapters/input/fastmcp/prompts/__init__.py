"""MCP prompts."""

import fastmcp

from arclith import Arclith
from adapters.input.fastmcp.prompts.agent_run_prompts import AgentRunPrompts
from infrastructure.containers.agent_run_container import build_agent_run_service

__all__ = ["AgentRunPrompts"]


def register_prompts(mcp: fastmcp.FastMCP, arclith: Arclith) -> None:
    service, logger = build_agent_run_service(arclith)
    AgentRunPrompts(service, logger, mcp)
