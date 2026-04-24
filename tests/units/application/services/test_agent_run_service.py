import pytest
from uuid6 import uuid7

from application.services.agent_run_service import AgentRunService
from domain.models.agent_run import AgentRun


@pytest.fixture
def service(repo, logger):
    return AgentRunService(repo, logger)


async def test_create_and_read(service):
    agent_run = await service.create(AgentRun(name="Farine"))
    found = await service.read(agent_run.uuid)
    assert found is not None
    assert found.name == "Farine"


async def test_update(service):
    agent_run = await service.create(AgentRun(name="Farine"))
    updated = await service.update(agent_run.model_copy(update={"name": "Farine complète"}))
    assert updated.name == "Farine complète"
    assert updated.version == 2


async def test_delete_hides_from_read(service):
    agent_run = await service.create(AgentRun(name="Sel"))
    await service.delete(agent_run.uuid)
    assert await service.read(agent_run.uuid) is None


async def test_find_all(service):
    await service.create(AgentRun(name="Farine"))
    await service.create(AgentRun(name="Sel"))
    result = await service.find_all()
    assert len(result) == 2


async def test_find_by_name(service):
    await service.create(AgentRun(name="Farine de blé"))
    await service.create(AgentRun(name="Sel fin"))
    result = await service.find_by_name("farine")
    assert len(result) == 1
    assert result[0].name == "Farine de blé"


async def test_duplicate(service):
    agent_run = await service.create(AgentRun(name="Farine"))
    clone = await service.duplicate(agent_run.uuid)
    assert clone.uuid != agent_run.uuid
    assert clone.name == "Farine"


async def test_read_unknown_returns_none(service):
    assert await service.read(uuid7()) is None


async def test_find_by_name_no_results(service):
    await service.create(AgentRun(name="Sel"))
    result = await service.find_by_name("farine")
    assert result == []

