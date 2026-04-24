"""Universal entry point for the shopping agent.

    MODE=api          FastAPI REST  :8026
    MODE=mcp_http     MCP HTTP      :8024
    MODE=mcp_sse      MCP SSE       :8024
    MODE=all          API + MCP HTTP

Probe server starts on :9026.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import adapters.input.fastmcp.prompts as prompts_module
import adapters.input.fastmcp.register as tools_module
import adapters.input.fastmcp.resources as resources_module
from adapters.input.fastapi.register import register_routers
from arclith import Arclith
from infrastructure.logging_setup import setup_logging

SERVICE_NAME = "Rekipe - Shopping Agent"
_logger = setup_logging()
_CONFIG = Path(__file__).parent / "config"
_VALID_MODES = {"api", "mcp_http", "mcp_sse", "all"}

MODE = os.getenv("MODE", "all")

if MODE not in _VALID_MODES:
  _logger.error(f"MODE invalide: {MODE!r} — valeurs acceptées: {sorted(_VALID_MODES)}")
  sys.exit(1)

arclith = Arclith(_CONFIG)
app = arclith.fastapi()
register_routers(app, arclith)


def build_mcp_server(transport: str):
  mcp = arclith.fastmcp(f"{SERVICE_NAME} ({transport})")
  tools_module.register_tools(mcp, arclith)
  prompts_module.register_prompts(mcp, arclith)
  resources_module.register_resources(mcp, arclith)
  arclith.instrument_mcp(mcp)
  return mcp


def _make_api_runner():
  def _run() -> None:
    arclith.run_api("main:app")

  return _run


def _make_mcp_runner(transport: str):
  mcp = build_mcp_server(transport)

  match transport:
    case "mcp_http":
      def _run() -> None:
        arclith.run_mcp_http(mcp)
    case "mcp_sse":
      def _run() -> None:
        arclith.run_mcp_sse(mcp)
    case _:
      raise ValueError(f"Unknown MCP transport: {transport}")

  return _run


if __name__ == "__main__":
  _logger.info("🚀 Starting", service=SERVICE_NAME, mode=MODE)

  match MODE:
    case "api":
      arclith.run_with_probes(_make_api_runner(), transports=["api"])
    case "mcp_http" | "mcp_sse":
      arclith.run_with_probes(_make_mcp_runner(MODE), transports=[MODE])
    case "all":
      _logger.info("🧩 MODE=all — API :8026 + MCP HTTP :8024 + probes :9026")
      arclith.run_with_probes(
        _make_api_runner(),
        _make_mcp_runner("mcp_http"),
        transports=["api", "mcp_http"],
      )
