# Quickstart — shopping-agent

## Rôle

`shopping-agent` est l’agent associé au service `shopping`.

## Ports locaux

- API agent : `8026`
- MCP HTTP / SSE : `8024`
- Probes : `9026`

## Installation

```bash
cd /Users/killian/Karned/projets/Rekipe/shopping-agent
uv sync --group dev
```

## Lancement

```bash
uv run python main_api.py
uv run python main_mcp_http.py
uv run python main_mcp_sse.py
uv run python main_mcp_stdio.py
uv run python main_cli.py --help
```

## Configuration

- Keycloak : [config/adapters/input/keycloak.yaml](/Users/killian/Karned/projets/Rekipe/shopping-agent/config/adapters/input/keycloak.yaml)
- MongoDB : [config/adapters/output/mongodb.yaml](/Users/killian/Karned/projets/Rekipe/shopping-agent/config/adapters/output/mongodb.yaml)
- Tenant : [config/adapters/input/tenant.yaml](/Users/killian/Karned/projets/Rekipe/shopping-agent/config/adapters/input/tenant.yaml)

Par défaut, le repository reste en `memory` dans `config/adapters/adapters.yaml`. La configuration MongoDB multi-tenant est préparée pour la suite.
