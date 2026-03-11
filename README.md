
# CZOI — Constrained Zoned‑Object Implementation Toolkit

**CZOI** is a Python toolkit for analysis, design, modeling, implementation, simulation, maintenance, and **access control** of **organizational intelligent information systems** at any scale—grounded in the **Constrained Zoned‑Object Architecture (CZOA)**. It unifies hierarchical zoning, role/permission control, constraints, embeddings, neural components, continuous monitoring daemons, and simulation—so you can move from theory to robust implementations quickly.

![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg) ![License MIT](https://img.shields.io/badge/license-MIT-green.svg) ![Build passing](https://img.shields.io/badge/build-passing-brightgreen.svg) ![Status alpha](https://img.shields.io/badge/status-alpha-orange.svg)

***

## Contents

*   key-capabilities
*   when-to-use-czoi
*   installation
*   quick-start
*   architecture-at-a-glance
*   core-concepts
    *   zones
    *   roles--inheritance
    *   operations--applications
    *   gamma-mappings-interzone-role-projection
    *   constraints
    *   permission-engine
    *   neural-components
    *   embedding-service--vector-store
    *   daemons-security--compliance
    *   simulation-engine
    *   storage
*   cli
*   examples
*   testing
*   project-layout
*   roadmap
*   contributing
*   security-notes
*   license
*   citation
*   faq
*   troubleshooting

***

## Key Capabilities

*   **CZOA core modeling**: Zones, roles, users, applications, and operations with hierarchical semantics.
*   **Policy computation**: Intra‑zone role inheritance + inter‑zone γ‑mappings for cross‑zone privilege projection.
*   **Constraint system**: Identity / Trigger / Goal / Access constraints with a **safe evaluator**.
*   **Neural components**: Role mining (cluster patterns) and anomaly detection for adaptive governance.
*   **Embeddings & similarity**: Deterministic hash fallback + pluggable vector stores for entity similarity.
*   **Daemons**: Security & compliance monitors for continuous enforcement and alerting.
*   **Simulation**: Generate synthetic access logs; analyze allow/deny rates under policy & constraints.
*   **CLI**: Bootstrap systems from YAML, run checks, launch simulations.
*   **Framework integration**: Stubs for Django, Flask, FastAPI middleware/decorators.

***

## When to Use CZOI

Use CZOI when you need:

*   **Multi‑zone**, multi‑tenant, or federated systems with **hierarchical** governance.
*   **Fine‑grained access control** with **computable constraints** and explainable decisions.
*   **Adaptive** policy evolution informed by usage **signals** (anomalies, clusters).
*   **Repeatable simulation and analysis** to validate policy designs before production.

***

## Installation

> Python **3.9+** is recommended.

**Development install (editable):**

```bash
git clone https://github.com/<YOUR_ORG>/czoi.git
cd czoi
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install -e .
```

**Optional extras** (APIs, deep learning, etc.):

```bash
# If you’ll build APIs or use transformers later:
pip install "fastapi uvicorn torch transformers"
```

> Note: The sample tests do not require a database; the SQLAlchemy storage layer is present but not mandatory for the quick start.

***

## Quick Start

A minimal end‑to‑end example using in‑memory objects and a fake storage (no DB required):

```python
from czoi.core.models import Zone, Role, User, Application
from czoi.permission.engine import PermissionEngine

# Minimal storage stub for examples & tests
class FakeStorage:
    def get_gamma_mappings(self, **kwargs): return []
    def get_role(self, role_id): return None
    def get_constraints(self, **kwargs): return []

# Build a small hierarchy
root = Zone("Root")
hr = Zone("HR", parent=root)

manager = Role("Manager", hr)
assistant = Role("Assistant", hr)
assistant.add_senior(manager)  # Assistant inherits from Manager downward in the hierarchy

app = Application("HR App")
view_op = app.add_operation("view_employee")
edit_op = app.add_operation("edit_employee")

assistant.grant_permission(view_op)
manager.grant_permission(edit_op)

alice = User("alice")
alice.assign_role(hr, assistant)

engine = PermissionEngine(FakeStorage())
print("View allowed:", engine.decide(alice, view_op, hr))  # True
print("Edit allowed:", engine.decide(alice, edit_op, hr))  # False
```

Run it:

```bash
python examples/quickstart.py
```

***

## Architecture at a Glance

    czoi/
      core/         → Zones, Roles, Users, Applications, Operations, System
      permission/   → PermissionEngine (intra-zone inheritance + γ-mappings + constraints)
      constraint/   → Constraint model & manager; safe expression evaluation
      neural/       → AnomalyDetector, RoleMiner (placeholders for adaptive governance)
      embedding/    → Vector store abstraction + EmbeddingService
      daemon/       → SecurityDaemon, ComplianceDaemon
      simulation/   → SimulationEngine (traffic, logs, metrics)
      storage/      → SQLAlchemy models & storage stub
      integrations/ → Django / Flask / FastAPI stubs
      cli/          → Console entrypoints
      utils/        → Logging & safe_eval

***

## Core Concepts

### Zones

Zones define hierarchical, **composable contexts** (e.g., Root → Dept → Team). Child zones inherit lineage; policies can traverse up/down as needed.

### Roles & Inheritance

Roles live **within a zone**. A role can declare **senior/junior** relations (intra‑zone). CZOI computes effective permissions by **accumulating junior permissions** when evaluating a senior role—this is deliberate to enable bottom‑up accumulation of capabilities.

### Operations & Applications

Applications define named operations (e.g., `view_employee`, `edit_employee`, HTTP verbs, or custom actions). Roles grant permissions to operations.

### Gamma Mappings (Inter‑Zone Role Projection)

**Γ‑mappings** project a role in a child zone to a role in a **parent** zone (or across zones via ancestry). This lets organizations centralize some privileges while empowering local autonomy.

### Constraints

Four types are supported out‑of‑the‑box:

*   **Identity**: who/what is acting
*   **Trigger**: event‑driven activation
*   **Goal**: target states to achieve
*   **Access**: guard conditions for authorization checks

CZOI includes a **safe expression evaluator** to execute boolean conditions with a **restricted AST** and disabled builtins.

### Permission Engine

`PermissionEngine.decide(user, operation, zone, context)` evaluates:

1.  User’s **assigned roles** in the current zone (with weights),
2.  **Intra‑zone** inheritance (accumulate junior role permissions),
3.  **Inter‑zone γ‑mappings** up the ancestry to add parent‑role permissions, and
4.  **Access constraints** for final admission control.

### Neural Components

*   **AnomalyDetector**: Isolation Forest for unusual usage patterns.
*   **RoleMiner**: clustering‑based role discovery (placeholder to help suggest refinements).

> You can wire real telemetry and retrain periodically to evolve policies.

### Embedding Service & Vector Store

A pluggable abstraction for vector similarity (e.g., nearest neighbor of entities: users, resources, operations). The default is an **in‑memory store** with a **deterministic hash fallback embedding** (no external models required).

### Daemons (Security & Compliance)

*   **SecurityDaemon**: receives signals (e.g., alerts, high risk scores) and can trigger protective actions (e.g., temporary constraints).
*   **ComplianceDaemon**: scans recent events/violations and raises alerts.

### Simulation Engine

Generates randomized traffic over a configured duration to **exercise policy**, then produces allow/deny metrics and optional JSON logs. Use it before deploying a new policy.

### Storage

SQLAlchemy ORM models are provided. The example `Storage.save_system` is a stub—extend it to persist your in‑memory graph to your database of choice.

***

## CLI

The package provides a `czoi` command with subcommands:

```bash
czoi --help
```

*   **Initialize from YAML**
    ```bash
    czoi init -c path/to/system.yaml
    ```
    Parses zones/roles/apps/users from a config and prepares persistence hooks.

*   **Check a permission**
    ```bash
    czoi check --user alice --operation edit_employee --zone HR --db sqlite:///czoa.db
    ```

*   **Run a simulation**
    ```bash
    czoi simulate --db sqlite:///czoa.db --duration 120 --output simulation_logs.json
    ```

> The CLI commands include placeholders where you can connect to real storage and lookup logic.

***

## Examples

*   `examples/quickstart.py`: Minimal in‑memory scenario (no DB).
*   Add your own scenario files under `examples/` to test organizational topologies, workflows, or migration plans.

***

## Testing

This repository includes **pytest** tests:

```bash
pytest -q
```

The sample test (`tests/test_basic.py`) verifies that:

*   a junior role with `view` is **allowed** to view; and
*   the same user is **denied** `edit` unless that permission is present via inheritance/γ‑mapping/constraints.

***

## Project Layout

    czoi/
    ├── czoi/
    │   ├── core/           # models.py, system.py
    │   ├── permission/     # engine.py
    │   ├── constraint/     # models.py, manager.py
    │   ├── neural/         # base.py, components.py
    │   ├── embedding/      # vector_store.py, service.py
    │   ├── daemon/         # base.py, builtins.py
    │   ├── simulation/     # engine.py
    │   ├── integrations/   # django.py, flask.py, fastapi.py (placeholders)
    │   ├── cli/            # main.py (console entrypoint)
    │   ├── storage/        # sqlalchemy.py, vector.py
    │   └── utils/          # logging.py, eval.py
    ├── tests/
    │   └── test_basic.py
    ├── examples/
    │   └── quickstart.py
    ├── requirements.txt
    ├── setup.py
    ├── README.md
    ├── LICENSE
    └── .gitignore

***

## Roadmap

*   **Storage adapters**: Implement `save_system` + loaders (Postgres, SQLite), graph serializers.
*   **Vector DB support**: pgvector, Chroma, Milvus adapters.
*   **Policy explanations**: richer decision traces for audit & explainability.
*   **Daemons**: plug in real telemetry, rules, and automated remediation.
*   **RoleMiner** improvements\*\*: production‑ready clustering & delta recommendations.
*   **API server kit**: FastAPI example with middleware and JWT/session integration.
*   **Docs site**: Tutorials, COU diagrams, API references, and larger examples.

If you have preferred priorities, I can tailor the backlog and open issues accordingly.

***

## Contributing

Contributions are welcome!  
Please open an issue describing:

*   the problem/use case,
*   your proposed change, and
*   any new dependencies or migration impacts.

Then submit a PR with:

*   tests for new behavior,
*   docs/examples updates, and
*   clean commit history.

***

## Security Notes

*   The constraint **safe evaluator** blocks dangerous Python builtins and allows only a restricted AST. Still, treat all expressions as **untrusted input** and enforce **strict reviews** of constraint sources.
*   Keep **telemetry** and **PII** handling aligned with your institutional policy and applicable regulations.
*   For **production deployments**, enable proper logging, rotation, and SIEM forwarding.

***

## License

This project is licensed under the **MIT License**. See LICENSE for details.

***

## Citation

If you use CZOI in academic work, please cite:

    Wang, H. (2026). CZOI: A Python Toolkit for the Constrained Zoned-Object Architecture (CZOA).

*(Update the reference with any DOI, venue, or preprint link you prefer.)*

***

## FAQ

**Q: Do I need a database to start?**  
A: No. You can use in‑memory structures and the sample `FakeStorage`. Add a DB only when you need persistence and multi‑process coordination.

**Q: How do γ‑mappings interact with constraints?**  
A: The engine accumulates permissions from intra‑zone inheritance and γ‑mappings first, then evaluates **access constraints**; a failing constraint denies the request.

**Q: Can I integrate with my existing IAM/IdP?**  
A: Yes—map IdP attributes to `User.attributes`, resolve roles at login, and call `PermissionEngine.decide()` in your middleware before protected operations.

**Q: Can I explain “why” a decision happened?**  
A: The current engine is straightforward to trace. We plan to add a **decision trace API** that returns the path (assignments → inheritance → γ‑mappings → constraints).

***

## Troubleshooting

*   **ImportError / hdbscan**: If you want to use HDBSCAN for role mining, install `hdbscan`:
    ```bash
    pip install hdbscan
    ```
    Or adjust `neural/components.py` to fallback to `DBSCAN`.

*   **`Permission: ALLOWED` hard‑coded in CLI check**: The CLI’s `check` command ships with placeholder lookups. Implement user/zone/operation retrieval or wire a loader in `storage/sqlalchemy.py`.

*   **No logs from Daemons**: They are stubs by default. Point them at your telemetry, implement actions (e.g., create constraints on alerts), and configure logging (`utils/logging.py`).

*   **Simulation shows all denials**: Ensure your users have roles in the **same zone** as the evaluated operation context, and verify that at least one granted permission path exists.

