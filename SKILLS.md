# SKILLS.md — `shopping-agent/`

Recettes paramétriques pour les tâches récurrentes sur l'agent `shopping-agent`.
Pour les tâches cross-repo, voir `../SKILLS.md` à la racine du workspace.

Format : chaque skill est identifiée `SK-SHA##` (SHA = Shopping Agent).

---

## SK-SHA01 — Ajouter un tool MCP exposé par l'agent

**Contexte :** exposer une nouvelle capacité (regroupement avancé, suggestion de fournisseur, ajustement de quantités).

### Étapes

1. `adapters/input/fastmcp/tools/<sujet>_tools.py` — méthode `@mcp.tool()` avec docstring orientée agent.
2. Schéma I/O dans `adapters/input/schemas/` si nécessaire.
3. Enregistrement dans `adapters/input/fastmcp/register.py` → `register_tools()`.
4. Logique métier dans `application/services/`, jamais dans le tool.
5. Test : `tests/units/adapters/input/fastmcp/test_<sujet>_tools.py`.

### Validation

```bash
make test-unit
uv run python main_mcp_http.py
```

---

## SK-SHA02 — Étendre le contrat MCP avec `shopping/`, `meal-planner/` ou `recipe/`

**Contexte :** appeler un nouveau tool MCP côté backend.

### Étapes

1. Vérifier que le tool est exposé côté backend (cf. `../recipe/SKILLS.md` SK-R07 et équivalents).
2. Ajouter la méthode encapsulant l'appel MCP côté agent (typiquement dans `adapters/output/` ou `infrastructure/`).
3. Nom du tool **exactement identique** au nom exposé côté backend.
4. Tests avec mock MCP ou faux serveur.

### Validation

```bash
./start_services.sh up shopping shopping-agent
uv run python main_cli.py "<prompt qui exerce le nouveau tool>"
```

Vérifier le `AgentRun` correspondant (status `success`).

---

## SK-SHA03 — Changer le modèle LLM (cloud / local)

**Contexte :** identique à `../meal-planner-agent/SKILLS.md` SK-MPA03.

### Étapes

1. Éditer `config.yaml` section `lm`.
2. Pour un LLM local : vérifier que le serveur tourne sur le port configuré.
3. Pour Anthropic / OpenAI cloud : token via Vault (`docs/vault.md`).

### Validation

```bash
uv run python main_cli.py "<prompt simple>"
```

---

## SK-SHA04 — Ajuster la logique d'optimisation

**Contexte :** modifier comment l'agent regroupe les ingrédients, choisit un fournisseur, ou applique des contraintes (budget, distance, préférence bio).

### Étapes

1. Identifier le composant concerné dans `application/services/` ou `domain/`.

2. Garder la logique **déterministe et testable** côté domain (pas de LLM dans le scoring déterministe). Le LLM intervient pour les cas que les règles ne tranchent pas.

3. Tests : couvrir cas limites, conflits de contraintes, exclusions.

4. Documenter le changement dans une entrée journal — la logique d'optimisation est de la sémantique métier qui dépasse le simple bug fix.

### Validation

```bash
make test-unit
make coverage
uv run python main_cli.py "<prompt>"
```

---

## SK-SHA05 — Consulter et trier les `AgentRun`

**Contexte :** diagnostiquer un échec ou comprendre une suggestion passée.

Identique à `../meal-planner-agent/SKILLS.md` SK-MPA05, en remplaçant le port (`8026`) et la base (`shopping-agent`).

```bash
curl -fsS http://127.0.0.1:8026/agent-runs | jq '.[0:5]'
mongosh "mongodb://127.0.0.1:5971/shopping-agent" --eval \
  'db["agent_runs"].find({ status: "failed" }).sort({ created_at: -1 }).limit(10)'
```

---

## SK-SHA06 — Diagnostiquer un agent qui échoue

**Contexte :** `AgentRun` en `status=failed` ou résultat vide.

### Étapes

1. Lire `error` et la stack.

2. Vérifier les services consommés en MCP :

   ```bash
   ./start_services.sh status
   curl -fsS http://127.0.0.1:8021/mcp     # shopping MCP
   curl -fsS http://127.0.0.1:8011/mcp     # meal-planner MCP (si consommé)
   curl -fsS http://127.0.0.1:8001/mcp     # recipe MCP (si consommé)
   ```

3. Vérifier la config LLM (token, base_url, modèle).

4. Logs `shopping-agent` :

   ```bash
   ./start_services.sh logs shopping-agent | tail -100
   ```

### Validation

Un nouveau `AgentRun` en `status=success`.

---

## SK-SHA07 — Restaurer ou exporter la base MongoDB locale

**Contexte :** repartir d'un état connu pour les `AgentRun`.

Voir `../SKILLS.md` SK-W03. Base par défaut : `shopping-agent` (cf. `config/adapters/output/mongodb.yaml`).
