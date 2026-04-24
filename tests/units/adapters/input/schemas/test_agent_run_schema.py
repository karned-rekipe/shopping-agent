import pytest
from datetime import datetime, timezone

from adapters.input.schemas.agent_run_schema import (
    AgentRunCreateSchema,
    AgentRunPatchSchema,
    AgentRunSchema,
    AgentRunUpdateSchema,
)
from domain.models.agent_run import AgentRun


# --- AgentRunCreateSchema ---

def test_create_schema_valid():
    s = AgentRunCreateSchema(name="Farine")
    assert s.name == "Farine"


def test_create_schema_empty_name_raises():
    with pytest.raises(Exception):
        AgentRunCreateSchema(name="")


# --- AgentRunPatchSchema ---

def test_patch_schema_all_none():
    s = AgentRunPatchSchema()
    assert s.name is None


def test_patch_schema_partial():
    s = AgentRunPatchSchema(name="Farine complète")
    assert s.name == "Farine complète"


def test_patch_schema_empty_name_raises():
    with pytest.raises(Exception):
        AgentRunPatchSchema(name="")


# --- AgentRunUpdateSchema ---

def test_update_schema_valid():
    s = AgentRunUpdateSchema(name="Sel fin")
    assert s.name == "Sel fin"


def test_update_schema_empty_name_raises():
    with pytest.raises(Exception):
        AgentRunUpdateSchema(name="")


# --- AgentRunSchema (response) ---

def test_agent_run_schema_from_entity():
    entity = AgentRun(name="Farine")
    schema = AgentRunSchema.model_validate(entity)
    assert schema.name == "Farine"
    assert schema.is_deleted is False
    assert schema.version == 1


def test_agent_run_schema_deleted_entity():
    entity = AgentRun(name="Sel", deleted_at=datetime.now(timezone.utc))
    schema = AgentRunSchema.model_validate(entity)
    assert schema.is_deleted is True


def test_agent_run_schema_uuid_serialized():
    entity = AgentRun(name="Farine")
    schema = AgentRunSchema.model_validate(entity)
    assert str(schema.uuid) == str(entity.uuid)

