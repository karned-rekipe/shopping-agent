from application.use_cases import FindByNameUseCase
from arclith import BaseService, Logger
from domain.models.agent_run import AgentRun
from domain.ports.output.agent_run_repository import AgentRunRepository


class AgentRunService(BaseService[AgentRun]):
    def __init__(self, repository: AgentRunRepository, logger: Logger, retention_days: float | None = None) -> None:
        super().__init__(repository, logger, retention_days)
        self._agent_run_repo = repository
        self._find_by_name_uc = FindByNameUseCase(repository, logger)

    async def find_by_name(self, name: str) -> list[AgentRun]:
        return await self._find_by_name_uc.execute(name)

    async def find_page_filtered(self, name: str | None = None, offset: int = 0, limit: int | None = None) -> tuple[list[AgentRun], int]:
        """Return a page of agent_runs (optionally filtered by name) and total count."""
        if name:
            return await self._agent_run_repo.find_page_by_name(name, offset, limit)
        return await self._agent_run_repo.find_page(offset, limit)

