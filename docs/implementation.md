# Implémenter une entité avec arclith

Ce dossier est le projet de référence. Il montre comment brancher `arclith` pour une entité concrète : **AgentRun**.

Chaque section correspond à un fichier à créer, dans l'ordre des couches (de l'intérieur vers l'extérieur).

---

## 1. `domain/models/` — L'entité

Hérite de `Entity`. Contient uniquement les champs métier et leur validation.

```python
# domain/models/agent_run.py
from dataclasses import dataclass
from arclith.domain.models.entity import Entity


@dataclass
class AgentRun(Entity):
    name: str = ""
    unit: str | None = None

    def __post_init__(self) -> None:
        # validation métier ici
        if not self.name.strip():
            raise ValueError("AgentRun name cannot be empty")
```

> `Entity` apporte automatiquement : `uuid`, `created_at`, `updated_at`, `deleted_at`, `is_deleted`, `version`.

---

## 2. `domain/ports/` — Le port spécifique

Si ton entité a des requêtes au-delà du CRUD générique, déclare-les ici sous forme d'interface abstraite.

```python
# domain/ports/agent_run_repository.py
from abc import abstractmethod
from arclith.domain.ports.repository import Repository
from domain.models.agent_run import AgentRun


class AgentRunRepository(Repository[AgentRun]):
    @abstractmethod
    async def find_by_name(self, name: str) -> list[AgentRun]: ...
```

> Si ton entité n'a pas de requêtes spécifiques, utilise directement `Repository[T]` — pas besoin de ce fichier.

---

## 3. `application/use_cases/` — Les cas d'usage spécifiques

Les use cases génériques (create, read, update…) sont fournis par `arclith`.  
Ajoute ici uniquement ce qui est propre à ton entité.

```python
# application/use_cases/find_by_name.py
from arclith.domain.ports.logger import Logger
from domain.models.agent_run import AgentRun
from domain.ports.agent_run_repository import AgentRunRepository


class FindByNameUseCase:
    def __init__(self, repository: AgentRunRepository, logger: Logger) -> None:
        self._repository = repository
        self._logger = logger

    async def execute(self, name: str) -> list[AgentRun]:
        self._logger.info("🔍 Finding agent_runs by name", name=name)
        result = [i for i in await self._repository.find_by_name(name) if not i.is_deleted]
        self._logger.info("✅ AgentRuns found", name=name, count=len(result))
        return result
```

---

## 4. `application/services/` — La façade de service

Étend `BaseService` pour exposer les méthodes aux adapters. Ne contient pas de logique — délègue aux use cases.

```python
# application/services/agent_run_service.py
from arclith.application.services.base_service import BaseService
from arclith.domain.ports.logger import Logger
from domain.models.agent_run import AgentRun
from domain.ports.agent_run_repository import AgentRunRepository
from application.use_cases import FindByNameUseCase


class AgentRunService(BaseService[AgentRun]):
    def __init__(self, repository: AgentRunRepository, logger: Logger, retention_days: float | None = None) -> None:
        super().__init__(repository, logger, retention_days)
        self._find_by_name_uc = FindByNameUseCase(repository, logger)

    async def find_by_name(self, name: str) -> list[AgentRun]:
        return await self._find_by_name_uc.execute(name)
```

> `BaseService` expose déjà : `create`, `read`, `update`, `delete`, `find_all`, `duplicate`, `purge`.

---

## 5. `adapters/input/schemas/` — Les schémas Pydantic

Séparent le modèle HTTP du modèle domaine. Un schéma par intention (création, mise à jour, réponse).

```python
# adapters/input/schemas/agent_run_schema.py
from arclith.adapters.input.schemas.base_schema import BaseSchema


class AgentRunCreateSchema(BaseModel):
    name: str
    unit: str | None = None


class AgentRunSchema(BaseSchema):  # réponse — hérite de BaseSchema (uuid, timestamps…)
    name: str
    unit: str | None = None
```

> `BaseSchema` inclut automatiquement les champs de `Entity` dans la réponse.

---

## 6. `adapters/output/` — Les repositories concrets

Implémente le port en héritant du repository `arclith` correspondant **et** du port spécifique.

```python
# adapters/output/memory/repository.py
from arclith.adapters.output.memory.repository import InMemoryRepository
from domain.models.agent_run import AgentRun
from domain.ports.agent_run_repository import AgentRunRepository


class InMemoryAgentRunRepository(InMemoryRepository[AgentRun], AgentRunRepository):
    async def find_by_name(self, name: str) -> list[AgentRun]:
        return [i for i in self._store.values() if name.lower() in i.name.lower()]
```

Même pattern pour MongoDB :

```python
# adapters/output/mongodb/repository.py
from arclith.adapters.output.mongodb.repository import MongoDBRepository


class MongoDBAgentRunRepository(MongoDBRepository[AgentRun], AgentRunRepository):
    def __init__(self, config: MongoDBConfig, logger: Logger) -> None:
        super().__init__(config, AgentRun, logger)

    async def find_by_name(self, name: str) -> list[AgentRun]:
        return [self._from_doc(doc) async for doc in self._collection.find({"name": {"$regex": name, "$options": "i"}})]
```

---

## 7. `infrastructure/container.py` — L'injection de dépendances

Lit la config via l'instance `Arclith` et instancie les dépendances. C'est le seul endroit où tout se branche.

```python
from arclith import Arclith, MongoDBConfig
from domain.ports.agent_run_repository import AgentRunRepository
from application.services.agent_run_service import AgentRunService


def build_agent_run_service(arclith: Arclith) -> tuple[AgentRunService, ...]:
    logger = arclith.logger
    config = arclith.config
    match config.adapters.repository:
        case "mongodb":
            from adapters.output.mongodb.repository import MongoDBAgentRunRepository
            mongo = config.adapters.mongodb
            repo: AgentRunRepository = MongoDBAgentRunRepository(
                MongoDBConfig(uri=mongo.uri, db_name=mongo.db_name, collection_name=mongo.collection_name),
                logger,
            )
        case "duckdb":
            from adapters.output.duckdb.repository import DuckDBAgentRunRepository
            repo = DuckDBAgentRunRepository(config.adapters.duckdb.path)
        case _:
            from adapters.output.memory.repository import InMemoryAgentRunRepository
            repo = InMemoryAgentRunRepository()
    return AgentRunService(repo, logger, config.soft_delete.retention_days), logger
```

---

## 8. `adapters/input/fastapi/dependencies.py` — Multitenancy FastAPI

Crée le `inject_tenant_uri` qui sera injecté sur toutes les routes.

```python
from pathlib import Path
from arclith.adapters.input.fastapi.dependencies import make_inject_tenant_uri
from arclith.infrastructure.config import load_config

inject_tenant_uri = make_inject_tenant_uri(
    load_config(Path(__file__).parent.parent.parent.parent / "config.yaml")
)
```

Puis dans le router :

```python
from fastapi import APIRouter, Depends
from adapters.input.fastapi.dependencies import inject_tenant_uri

self.router = APIRouter(
    prefix="/agent_run/v1",
    tags=["agent_runs"],
    dependencies=[Depends(inject_tenant_uri)],
)
```

---

## 9. `config.yaml` — La configuration

Choisit le repository actif, configure les connexions et le mode multitenancy.

```yaml
adapters:
  repository: memory    # memory | mongodb | duckdb
  multitenant: false    # true = URI résolue par requête (vault via JWT)

  mongodb:
    uri: mongodb://localhost:27017  # ignoré si multitenant: true
    db_name: mydb
    collection_name: agent_runs

  duckdb:
    path: data/agent_runs.csv   # .csv | .parquet | .json | .arrow

soft_delete:
  retention_days: 30    # null = jamais supprimé physiquement
```

---

## Checklist pour une nouvelle entité

```
✅ domain/models/              →  MaClasse(Entity)
✅ domain/ports/               →  MaClasseRepository(Repository[MaClasse])   ← si requêtes spécifiques
✅ application/use_cases/      →  MonUseCaseSpécifique                        ← si logique spécifique
✅ application/services/       →  MaClasseService(BaseService[MaClasse])
✅ adapters/input/schemas/     →  schémas Pydantic (Create, Update, Patch, Response)
✅ adapters/output/            →  MaClasseRepository(InMemoryRepository / MongoDBRepository / DuckDBRepository)
✅ adapters/input/fastapi/dependencies.py  →  inject_tenant_uri (multitenancy)
✅ infrastructure/container.py →  brancher le repository et le service via Arclith
```

