from application.use_cases import FindByNameUseCase
from domain.models.agent_run import AgentRun


async def test_find_by_name_returns_match(repo, logger):
    await repo.create(AgentRun(name="Farine de blé"))
    await repo.create(AgentRun(name="Sel fin"))
    result = await FindByNameUseCase(repo, logger).execute("farine")
    assert len(result) == 1
    assert result[0].name == "Farine de blé"


async def test_find_by_name_case_insensitive(repo, logger):
    await repo.create(AgentRun(name="Farine"))
    result = await FindByNameUseCase(repo, logger).execute("FARINE")
    assert len(result) == 1


async def test_find_by_name_partial_match(repo, logger):
    await repo.create(AgentRun(name="Farine de blé"))
    await repo.create(AgentRun(name="Farine complète"))
    result = await FindByNameUseCase(repo, logger).execute("farine")
    assert len(result) == 2


async def test_find_by_name_excludes_deleted(repo, logger):
    from datetime import datetime, timezone
    deleted = AgentRun(name="Farine", deleted_at=datetime.now(timezone.utc))
    await repo.create(deleted)
    result = await FindByNameUseCase(repo, logger).execute("farine")
    assert len(result) == 0


async def test_find_by_name_no_match(repo, logger):
    await repo.create(AgentRun(name="Sel"))
    result = await FindByNameUseCase(repo, logger).execute("farine")
    assert result == []

