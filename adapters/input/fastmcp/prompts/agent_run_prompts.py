import fastmcp

from adapters.input.fastmcp.dependencies import inject_tenant_uri
from application.services.agent_run_service import AgentRunService
from arclith.domain.ports.logger import Logger

_EXPLORE_PREVIEW_LIMIT = 20


class AgentRunPrompts:
    def __init__(self, service: AgentRunService, logger: Logger, mcp: fastmcp.FastMCP) -> None:
        self._service = service
        self._logger = logger
        self._mcp = mcp
        self._register_prompts()

    def _register_prompts(self) -> None:
        service = self._service

        @self._mcp.prompt
        def check_duplicate(agent_run_name: str) -> str:
            """Check for duplicates before creating a new agent_run.

            Use this prompt before calling create_agent_run.
            The LLM will guide you to call list_agent_runs with a partial
            name filter to surface any existing match.
            """
            return (
                f"Before creating the agent_run '{agent_run_name}', "
                "call list_agent_runs with a partial name filter to check for existing similar entries. "
                "If a match is found, suggest using the existing one instead of creating a duplicate."
            )

        @self._mcp.prompt
        async def explore_agent_runs(ctx: fastmcp.Context) -> str:
            """Explore and discover available agent_runs.

            Loads the current catalog and guides the LLM to help the user
            search by name or identify what is available.
            """
            await inject_tenant_uri(ctx)
            items = await service.find_all()
            if not items:
                snapshot = "No agent_runs available yet. Use create_agent_run to add the first one."
            else:
                names = ", ".join(i.name for i in items[:_EXPLORE_PREVIEW_LIMIT])
                total = len(items)
                snapshot = f"{total} agent_run(s) available: {names}{'...' if total > _EXPLORE_PREVIEW_LIMIT else '.'}"
            return (
                f"{snapshot}\n\n"
                "Help me explore these agent_runs: search by name, "
                "or suggest which ones to use for a given dish."
            )

        @self._mcp.prompt
        def mcp_help() -> str:
            """Overview of all MCP capabilities exposed by this server.

            Lists every tool, prompt, and resource with a short description.
            Use this as a starting point when discovering what this server can do.
            """
            return (
                "Here are all the capabilities exposed by this MCP server:\n\n"
                "**Tools** (actions):\n"
                "- create_agent_run(name) — create a new agent_run\n"
                "- get_agent_run(uuid) — retrieve by UUID\n"
                "- update_agent_run(uuid, name) — full replacement (PUT semantics)\n"
                "- delete_agent_run(uuid) — soft-delete\n"
                "- list_agent_runs(name?) — list all active, optional partial name filter\n"
                "- duplicate_agent_run(uuid) — clone with a new UUID\n"
                "- purge_agent_runs() — permanently remove expired soft-deleted entries\n\n"
                "**Prompts** (LLM guidance):\n"
                "- check_duplicate(agent_run_name) — avoid duplicates before creating\n"
                "- explore_agent_runs — discover and filter available agent_runs\n"
                "- mcp_help — this overview\n\n"
                "**Resources** (read-only data):\n"
                "- resource://agent-runs/sample — first 5 agent_runs (quick dataset preview)\n"
                "- resource://agent-runs/recent — last 10 agent_runs by creation date, newest first\n"
                "- resource://agent-run/{uuid} — single agent_run by UUID\n"
            )
