from arclith.adapters.output.memory.repository import InMemoryRepository
from domain.models.agent_run import AgentRun
from domain.ports.output.agent_run_repository import AgentRunRepository


class InMemoryAgentRunRepository(InMemoryRepository[AgentRun], AgentRunRepository):
    async def find_by_name(self, name: str) -> list[AgentRun]:
        return [i for i in self._store.values() if name.lower() in i.name.lower() and not i.is_deleted]

    async def find_page_by_name(self, name: str, offset: int = 0, limit: int | None = None) -> tuple[list[AgentRun], int]:
        filtered = [i for i in self._store.values() if name.lower() in i.name.lower() and not i.is_deleted]
        total = len(filtered)
        page = filtered[offset: offset + limit] if limit is not None else filtered[offset:]
        return page, total
