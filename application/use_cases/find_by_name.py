from arclith.domain.ports.logger import Logger
from domain.models.agent_run import AgentRun
from domain.ports.output.agent_run_repository import AgentRunRepository


class FindByNameUseCase:
    def __init__(self, repository: AgentRunRepository, logger: Logger) -> None:
        self._repository = repository
        self._logger = logger

    async def execute(self, name: str) -> list[AgentRun]:
        self._logger.info("🔍 Finding agent_runs by name", name=name)
        result = [i for i in await self._repository.find_by_name(name) if not i.is_deleted]
        self._logger.info("✅ AgentRuns found", name=name, count=len(result))
        return result

