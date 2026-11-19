# AGENTS.md — `shopping-agent/`

Document d'entrée pour tout agent de codage qui intervient sur ce repo.
Lecture obligatoire avant toute modification.

Pour le contexte global du projet et les conventions transverses, voir `../AGENTS.md` à la racine du workspace.

---

## 1. Rôle

`shopping-agent/` est l'**agent IA** du domaine courses. Il assiste la génération et l'optimisation des listes de courses (regroupement, choix de fournisseur, suggestions). Il **ne possède aucune entité métier propre** — il délègue la persistance à `shopping/` via MCP.

Responsabilités :

- composer un contexte de courses à partir d'un plan ou d'un panier en cours ;
- appeler un LLM pour proposer regroupements, fournisseurs, ajustements ;
- exposer le résultat via REST, MCP, et CLI ;
- persister un `AgentRun` par exécution (traçabilité).

## 2. Stack et ports

| Élément | Valeur |
|---|---|
| Langage | Python 3.13 |
| Gestionnaire deps | `uv` |
| Framework de base | `arclith` |
| LLM | pydantic-ai (Anthropic / OpenAI / local via base_url) |
| Web | FastAPI |
| MCP | FastMCP |
| Stockage `AgentRun` | MongoDB (port `5971` en local) ; `memory` / `duckdb` pour les tests |
| API REST | `8026` |
| MCP HTTP | `8024` |
| Sources MCP consommées | `shopping/` (MCP `8021`), éventuellement `meal-planner/` (`8011`) et `recipe/` (`8001`) |

**Ne jamais changer ces ports** sans mettre à jour `start_services.sh` et `gwel/vite.config.ts`.

## 3. Architecture locale

Architecture hexagonale (mêmes principes que `agent-recipe-creator/` et `meal-planner-agent/`) :

```
domain/
  models/
    agent_run.py             # AgentRun — entité de traçabilité
  ports/
    output/
      agent_run_repository.py

application/                 # Services + use cases

adapters/
  input/
    fastapi/                 # REST :8026 — agent_run_router, admin
    fastmcp/                 # MCP :8024 — tools, prompts, resources
    schemas/
  output/
    mongodb/repositories/
    memory/repositories/
    duckdb/repositories/

infrastructure/              # DI, logging
config/
tests/units/

main.py                      # Entry point unique (MODE env var)
main_api.py
main_mcp_http.py
main_mcp_sse.py
main_mcp_stdio.py
main_cli.py
```

### Modes de lancement

Identiques aux autres agents (`api`, `mcp_http`, `mcp_sse`, `all` via `MODE`).

## 4. Règles de développement

### Règles transverses (rappel — voir `../AGENTS.md` §4)

- Architecture hexagonale stricte. `domain/` ne dépend que de `arclith` + `pydantic`.
- Toute interaction avec un autre service Rekipe passe par **MCP**.
- L'agent **ne persiste rien d'autre que `AgentRun`**. Les listes, projections et fournisseurs sont écrits dans `shopping/` via MCP.

### Règles spécifiques à ce repo

- **Toute exécution = un `AgentRun`** (status, input, output, métadonnées).
- **LLM configurable via `config.yaml`**.
- **Tests ≥ 80 %** : `make coverage`.
- **Pre-commit** : `make precommit`.
- **Aucun secret** dans `config/*.yaml`. Vault uniquement.

### Qualité

```bash
make lint typecheck security complexity
make test test-unit test-e2e
make coverage
make quality
make precommit
```

## 5. Commandes utiles

### Lancement local manuel

```bash
uv sync --group dev
uv run python main_api.py
uv run python main_mcp_http.py
uv run python main_cli.py "<prompt>"
```

(Préférer `./start_services.sh up shopping-agent` depuis la racine.)

### Consulter les runs

```bash
curl -fsS http://127.0.0.1:8026/agent-runs | jq '.[0:5]'
curl -fsS http://127.0.0.1:8026/agent-runs/<uuid> | jq

mongosh "mongodb://127.0.0.1:5971/shopping-agent" --eval \
  'db["agent_runs"].find({ status: "failed" }).sort({ created_at: -1 }).limit(5)'
```

## 6. Fichiers à lire en premier

1. `main.py` + `main_api.py` + `main_mcp_http.py`.
2. `domain/models/agent_run.py`.
3. `application/services/` — orchestration.
4. `adapters/input/fastapi/routers/agent_run_router.py`.
5. `adapters/input/fastmcp/tools/agent_run_tools.py`.
6. `adapters/input/fastmcp/register.py`.
7. `infrastructure/container.py`.
8. `config/`.

Pour ajouter une fonctionnalité, lire en plus :

- `docs/agent.md`
- `docs/new-entity.md`
- `docs/http-conventions.md`
- `docs/vault.md`

## 7. Règle du journal — rappel

Toute modification non triviale doit être consignée dans `journal/YYYY-MM-DD-slug.md` à la **racine du workspace**. Voir `../AGENTS.md` §6 et `../journal/README.md`.

Cas spécifiques à ce repo qui exigent une entrée journal :

- changement de modèle LLM par défaut ou de provider ;
- évolution de la logique d'optimisation (regroupement, fournisseur) ;
- ajout / retrait d'un tool MCP appelé par l'agent ;
- changement du contrat avec `shopping/`, `meal-planner/` ou `recipe/` côté MCP ;
- changement de port.

## 8. Hors scope

- La **persistance des listes de courses** : ce repo ne persiste rien d'autre que `AgentRun`.
- Les **plans de repas** restent la propriété de `meal-planner/`.
- Les **recettes** restent la propriété de `recipe/`.
- Le **paiement, les transactions, les API marchand** : aucune logique financière dans ce repo. L'agent peut suggérer un fournisseur, jamais commander.
