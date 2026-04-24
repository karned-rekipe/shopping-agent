import pytest
from application.services.agent_run_service import AgentRunService
from arclith.infrastructure.config import (
    AppConfig,
    AdaptersSettings,
    MongoDBSettings,
    DuckDBSettings,
)
from infrastructure.containers.agent_run_container import build_agent_run_service
from unittest.mock import MagicMock


def _arclith(config: AppConfig, logger):
    mock = MagicMock()
    mock.config = config
    mock.logger = logger
    return mock


def test_memory_creates_service(logger):
    arclith = _arclith(AppConfig(adapters = AdaptersSettings(repository = "memory")), logger)
    service, log = build_agent_run_service(arclith)
    assert isinstance(service, AgentRunService)
    assert log is logger


def test_mongodb_creates_service(logger):
    config = AppConfig(adapters = AdaptersSettings(
        repository = "mongodb",
        mongodb = MongoDBSettings(uri = "mongodb://localhost:27017", db_name = "test"),
    ))
    service, log = build_agent_run_service(_arclith(config, logger))
    assert isinstance(service, AgentRunService)


def test_duckdb_creates_service(logger, tmp_path):
    config = AppConfig(adapters = AdaptersSettings(
        repository = "duckdb",
        duckdb = DuckDBSettings(path = str(tmp_path) + "/"),
    ))
    service, log = build_agent_run_service(_arclith(config, logger))
    assert isinstance(service, AgentRunService)


def test_mongodb_missing_config_raises(logger):
    mock = MagicMock()
    mock.config.adapters.repository = "mongodb"
    mock.config.adapters.mongodb = None
    mock.logger = logger
    with pytest.raises(RuntimeError, match = "MongoDB"):
        build_agent_run_service(mock)


def test_duckdb_missing_config_raises(logger):
    mock = MagicMock()
    mock.config.adapters.repository = "duckdb"
    mock.config.adapters.duckdb = None
    mock.logger = logger
    with pytest.raises(RuntimeError, match = "DuckDB"):
        build_agent_run_service(mock)
