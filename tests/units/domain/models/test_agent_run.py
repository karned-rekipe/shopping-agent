import pytest
from domain.models.agent_run import AgentRun


def test_valid_agent_run():
    i = AgentRun(name="Farine")
    assert i.name == "Farine"


def test_name_stripped():
    i = AgentRun(name="  Sel fin  ")
    assert i.name == "Sel fin"


def test_empty_name_raises():
    with pytest.raises(Exception):
        AgentRun(name="")


def test_blank_name_raises():
    with pytest.raises(Exception):
        AgentRun(name="   ")



def test_inherits_entity_fields():
    from uuid6 import UUID
    i = AgentRun(name="Sel")
    assert isinstance(i.uuid, UUID)
    assert i.version == 1
    assert not i.is_deleted


def test_model_copy_update():
    i = AgentRun(name="Farine")
    copy = i.model_copy(update={"name": "Farine complète"})
    assert copy.name == "Farine complète"
    assert copy.uuid == i.uuid

