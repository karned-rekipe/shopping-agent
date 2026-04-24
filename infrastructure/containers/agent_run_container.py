from __future__ import annotations

from typing import cast

from application.services.agent_run_service import AgentRunService
from arclith import Arclith, AdapterRegistry
from arclith.adapters.output.mongodb.config import MongoDBConfig
from arclith.domain.ports.logger import Logger
from arclith.domain.ports.repository import Repository
from arclith.infrastructure.config import AppConfig
from domain.models.agent_run import AgentRun
from domain.ports.output.agent_run_repository import AgentRunRepository


def _build_memory(cfg: AppConfig, log: Logger) -> Repository[AgentRun]:
    from adapters.output.memory.repository import InMemoryAgentRunRepository
    return InMemoryAgentRunRepository()


def _build_mongodb(cfg: AppConfig, log: Logger) -> Repository[AgentRun]:
    from adapters.output.mongodb.repository import MongoDBAgentRunRepository
    mongo = cfg.adapters.mongodb
    if mongo is None:
        raise RuntimeError("MongoDB settings are required when repository=mongodb")
    return MongoDBAgentRunRepository(
        MongoDBConfig(uri=mongo.uri, db_name=mongo.db_name),
        log,
    )


def _build_duckdb(cfg: AppConfig, log: Logger) -> Repository[AgentRun]:
    from adapters.output.duckdb.repository import DuckDBAgentRunRepository
    duckdb = cfg.adapters.duckdb
    if duckdb is None:
        raise RuntimeError("DuckDB settings are required when repository=duckdb")
    return DuckDBAgentRunRepository(duckdb.path)


_registry = cast(
    AdapterRegistry[AgentRun],
    AdapterRegistry[AgentRun]()
    .register("memory", _build_memory)  # type: ignore[arg-type]
    .register("mongodb", _build_mongodb)  # type: ignore[arg-type]
    .register("duckdb", _build_duckdb)  # type: ignore[arg-type]
)


def build_agent_run_service(arclith: Arclith) -> tuple[AgentRunService, Logger]:
    arclith.logger.info("🗄️ Repository adapter selected", adapter=arclith.config.adapters.repository)
    repo: AgentRunRepository = cast(AgentRunRepository, _registry.build(arclith.config, arclith.logger))
    return AgentRunService(repo, arclith.logger, arclith.config.soft_delete.retention_days), arclith.logger
