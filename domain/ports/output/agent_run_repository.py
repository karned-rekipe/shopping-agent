from abc import abstractmethod

from arclith.domain.ports.repository import Repository
from domain.models.agent_run import AgentRun


class AgentRunRepository(Repository[AgentRun]):
    @abstractmethod
    async def find_by_name(self, name: str) -> list[AgentRun]:
        pass

    @abstractmethod
    async def find_page_by_name(self, name: str, offset: int = 0, limit: int | None = None) -> tuple[list[AgentRun], int]:
        """Return a page of agent_runs matching name filter and the total count."""
        pass

