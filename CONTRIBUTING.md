

# Contributing to CZOI Toolkit

First off—thanks for your interest in improving **CZOI (Constrained Zone‑Object Implementation)**. This project provides a modular Python toolkit for building, simulating, and maintaining Organizational Intelligent Information Systems (OIIS) based on the Constrained Zone‑Object Architecture (CZOA).

This guide explains how to propose changes, report issues, add new components (e.g., neural models, vector stores, daemons, integrations), write tests, and prepare pull requests.

> **Scope & Vision**
>
> CZOI aims to be:
>
> *   **Modular:** clearly separated subpackages (`core`, `permission`, `constraint`, `neural`, `embedding`, `daemon`, `simulation`, `integrations`, `cli`, `storage`, `utils`).
> *   **Extensible:** stable interfaces for adding engines, stores, daemons, and integrations.
> *   **Practical:** usable from small prototypes to enterprise deployments (in‑memory → SQLite → PostgreSQL with `pgvector`).
> *   **Secure by design:** explicit permissions, constraints, safe evaluation, and auditability.

**License:** MIT  
**Current version:** 0.1.0

***

## Table of Contents

1.  \#code-of-conduct
2.  \#how-to-get-help
3.  \#project-layout
4.  \#what-you-can-contribute
5.  \#development-setup
6.  \#coding-standards
7.  \#testing--coverage
8.  \#database--migrations
9.  \#documentation--examples
10. \#proposing-changes
11. \#pull-request-checklist
12. \#versioning--releases
13. \#security
14. \#module-specific-contribution-guides
15. \#contributor-tips

***

## Code of Conduct

Be respectful, inclusive, and constructive. We follow a standard, no‑surprises Code of Conduct. If the repository doesn’t yet include `CODE_OF_CONDUCT.md`, please assume the **Contributor Covenant v2.1**. Incidents can be reported privately (see #security).

***

## How to Get Help

*   **Usage questions** → Start a GitHub Discussion (preferred) or open a *question*‑labeled issue.
*   **Bug reports** → Open an issue with a minimal reproducible example (MRE).
*   **Security concerns** → See #security; do **not** open a public issue.
*   **Feature proposals** → Open an issue with the **proposal** template; larger features may need a lightweight RFC (see #proposing-changes).

***

## Project Layout

CZOI is organized into modules (as described in the technical specification):

*   **`czoi.core`**: zones, roles, users, applications, operations, gamma mappings, system container.
*   **`czoi.permission`**: `PermissionEngine` and `SimpleEngine` for effective permission calculus.
*   **`czoi.constraint`**: constraint types (`IDENTITY`, `TRIGGER`, `GOAL`, `ACCESS`), models, and manager; safe evaluation.
*   **`czoi.neural`**: `NeuralComponent` ABC; examples like `AnomalyDetector` and `RoleMiner`.
*   **`czoi.embedding`**: `VectorStore` ABC, `InMemoryVectorStore`, and `EmbeddingService`.
*   **`czoi.daemon`**: daemon base + examples (`SecurityDaemon`, `ComplianceDaemon`).
*   **`czoi.simulation`**: `SimulationEngine` base, logs & analysis helpers.
*   **`czoi.integrations`**: adapters for Django, Flask, and FastAPI (permission decorators/dependencies).
*   **`czoi.cli`**: Click‑based CLI (`czoi init`, `czoi check`, `czoi simulate`, etc.).
*   **`czoi.storage`**: SQLAlchemy models, persistence, and vector store adapters.
*   **`czoi.utils`**: `safe_eval`, logging, and helpers.
*   **`examples/`**: runnable examples covering core flows, permissions, gamma mappings, neural components, daemons, simulations, and web integrations.

***

## What You Can Contribute

*   **Bug fixes** (core logic, engines, utils, integrations).
*   **Documentation & examples** (tutorials, diagrams, walkthroughs).
*   **Tests** (unit, integration, DB, E2E CLI).
*   **New neural components** (extend `NeuralComponent`).
*   **New vector store adapters** (implement `VectorStore`).
*   **New daemons** (extend `Daemon`).
*   **New framework integrations** (follow existing FastAPI/Flask/Django patterns).
*   **Performance improvements** (e.g., permission computation, embedding search).
*   **Developer ergonomics** (tooling, pre-commit, CI, packaging).

***

## Development Setup

> **Python:** 3.10+ is recommended.

1.  **Fork & clone**
    ```bash
    git clone https://github.com/<your-username>/czoi_toolkit.git
    cd czoi_toolkit
    git remote add upstream https://github.com/hongxueharriswang/czoi_toolkit.git
    ```

2.  **Create a virtual environment**
    ```bash
    python -m venv .venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    ```

3.  **Editable install (pick extras as needed)**
    ```bash
    # Core only:
    pip install -e .

    # With optional extras from the spec:
    pip install -e ".[neural]"   # scikit-learn, PyTorch/transformers (as specified)
    pip install -e ".[api]"      # FastAPI, uvicorn
    pip install -e ".[django]"
    pip install -e ".[flask]"
    pip install -e ".[all]"      # everything
    ```

4.  **Developer tools** (if not provided by extras or `requirements-dev.txt`)
    ```bash
    pip install pytest pytest-cov black ruff mypy pre-commit
    pre-commit install
    ```

5.  **Quick smoke test**
    ```bash
    python -c "import czoi; print('CZOI OK')"
    czoi --help  # if CLI is exposed
    ```

***

## Coding Standards

*   **Style:** PEP 8, formatted with **Black**.
    ```bash
    black .
    ```

*   **Lint:** **Ruff** for linting & import sorting.
    ```bash
    ruff check .
    ruff format .   # if you prefer Ruff's formatter; otherwise Black
    ```

*   **Types:** Prefer **type hints**; keep `mypy --strict` clean in public modules.
    ```bash
    mypy czoi
    ```

*   **Docstrings:** Use **Google** or **NumPy** style consistently; include examples for public APIs.

*   **Logging:** Use the standard `logging` module; never print from libraries. Daemons and engines should use named loggers.

*   **Public API:** Anything not prefixed with `_` in the packages above is considered public and subject to semantic versioning.

***

## Testing & Coverage

*   **Framework:** `pytest` with `pytest-cov`.

*   **Targets:**
    *   Core access calculus (core/permission/constraint) → aim ≥ **90%** line coverage.
    *   Other modules → aim ≥ **80%**.
    *   Critical paths (e.g., `safe_eval`, `PermissionEngine.decide`) must have edge‑case tests.

*   **DB tests:** default to **in‑memory SQLite**; optionally run **PostgreSQL** tests by setting env vars:
    ```bash
    export CZOI_TEST_DB_URL=postgresql+psycopg2://user:pass@localhost:5432/czoi_test
    pytest -m "not slow"
    ```

*   **Markers:**
    *   `@pytest.mark.slow` for long‑running neural/embedding tests.
    *   `@pytest.mark.integration` for DB and framework integration tests.

*   **Examples as tests:** Keep example notebooks/scripts deterministic; wire at least one example per major module into CI (smoke run).

***

## Database & Migrations

*   **ORM:** SQLAlchemy models live under `czoi.storage`.
*   **Schema:** See the spec’s Appendix for canonical tables (zones, roles, users, applications, operations, role\_operations, user\_zone\_roles, gamma\_mappings, constraints, etc.).
*   **Migrations:** If the repo uses Alembic, include a migration in your PR; otherwise, update the schema documentation and `Storage.save_system` logic accordingly. Provide an **idempotent** upgrade path in PR notes.

***

## Documentation & Examples

*   **User docs:** Update or add Markdown docs under `docs/` (or the existing docs system). Every new public API should be discoverable from the docs landing page.
*   **API docs:** Ensure docstrings are complete (parameters, returns, raises, examples).
*   **Examples:** Place runnable examples in `examples/` with a short README and `requirements.txt` if needed. Keep outputs deterministic for CI.

***

## Proposing Changes

*   **Small fixes**: Open a PR directly with a clear description.
*   **Features / refactors**: Open an issue with the proposal template. For substantial changes, attach a short **RFC** that covers:
    *   Motivation & scope
    *   Public API changes (if any)
    *   Backwards compatibility & migration plan
    *   Security, performance, and testing impact
    *   Alternatives considered

We follow **Conventional Commits** for helpful history and automated versioning (e.g., `feat:`, `fix:`, `docs:`, `refactor:`, `perf:`, `test:`).

***

## Pull Request Checklist

*   [ ] Linked issue (or rationale provided).
*   [ ] **Tests added/updated** (unit + integration as appropriate).
*   [ ] **Docs updated** (README, module docs, examples).
*   [ ] **Changelog entry** (if the repo uses a `CHANGELOG.md`).
*   [ ] Lint & format clean:
    ```bash
    ruff check . && black --check .
    mypy czoi
    pytest -q
    ```
*   [ ] No API breakage without a migration guide.
*   [ ] For DB changes: migration included or schema docs updated.
*   [ ] For extras: keep base install light; put heavy deps under extras (`[neural]`, `[api]`, etc.).
*   [ ] For security‑sensitive areas (`safe_eval`, permission calculus): include adversarial tests.

***

## Versioning & Releases

*   **SemVer**: `MAJOR.MINOR.PATCH`.
*   **Public API surface**: all non‑private names in the modules listed above.
*   Changes that alter behavior or signatures of public APIs require a **minor/major** bump and release notes.
*   Keep version in the canonical place (e.g., `__version__` or `pyproject.toml`) in sync with tags (e.g., `v0.1.0`).

***

## Security

*   **Do not file public issues** for vulnerabilities.
*   Use GitHub’s **“Report a vulnerability”** (Security Advisories) if enabled, or email the maintainer privately.
*   PRs that touch `safe_eval`, access constraints, daemons that block/allow accesses, or audit flows **must** include:
    *   Threat model summary
    *   Negative tests (misuse, injection attempts, unsafe AST nodes)
    *   Performance considerations (no unbounded loops or blocking calls in daemons)

***

## Module‑Specific Contribution Guides

### 1) Permission Engine (`czoi.permission`)

*   **Goal:** Correct effective permission calculation across base role permissions, intra‑zone hierarchy (senior/junior), and inter‑zone **gamma mappings**.
*   **When adding logic:**
    *   Keep `SimpleEngine` in sync with `PermissionEngine` semantics.
    *   Add property‑based tests (e.g., Hypothesis) for inheritance composition.
    *   Validate conflict resolution (e.g., priority handling) with table‑driven tests.

### 2) Constraints (`czoi.constraint`)

*   Implement constraints with **clear targets** (roles/operations) and **priorities**.
*   **`safe_eval`**: Never allow arbitrary names; extend the whitelist intentionally. Include tests for rejected AST nodes and sandbox escapes.

### 3) Neural Components (`czoi.neural`)

*   **Implement** by subclassing `NeuralComponent` and providing `train/predict/save/load`.
*   For examples (`AnomalyDetector`, `RoleMiner`):
    *   Keep training deterministic where possible (fixed seeds).
    *   Treat heavy libraries as optional via `[neural]`.
    *   Save artifacts under a clearly documented path.

### 4) Embeddings & Vector Stores (`czoi.embedding`)

*   **Adapters** must implement `VectorStore` (`upsert`, `similarity_search`, `get`).
*   Provide a **round‑trip test** and a **top‑k precision sanity test**.
*   If adding external backends (e.g., `pgvector`, Chroma), gate under a new extra and integration tests behind env flags.

### 5) Daemons (`czoi.daemon`)

*   Subclass `Daemon`; implement `async check()` (return actions) and optionally override `execute`.
*   Ensure **non‑blocking** loops, proper **interval** handling, and **graceful stop**.
*   Provide tests with **simulated time** and mock storage/engines.

### 6) Simulation Engine (`czoi.simulation`)

*   Subclass `SimulationEngine` and implement `step`.
*   Ensure logs are **structured** (`Dict[str, Any]`) and redact PII.
*   Provide `analyze()` that yields stable metrics useful for tests.

### 7) Web Integrations (`czoi.integrations`)

*   Follow the existing decorator/dependency names:
    *   Django: `require_permission(operation: str, mode: str = 'i_rzbac')`
    *   Flask:  `permission_required(operation: str, mode: str = 'i_rzbac')`
    *   FastAPI: `require_permission(...)` dependency
*   Add small end‑to‑end tests per framework (skip unless env flag is set).

### 8) CLI (`czoi.cli`)

*   Commands are implemented with **Click**. Keep commands composable and script‑friendly.
*   For each command (`init`, `check`, `simulate`, `audit`, `migrate`, `train`, `daemon start`), provide:
    *   `--help` examples
    *   Non‑interactive defaults for CI
    *   Exit codes suitable for automation

### 9) Storage (`czoi.storage`)

*   Keep ORM models consistent with the spec tables.
*   Add batch methods where performance matters (e.g., bulk upsert for embeddings).
*   Document transaction boundaries and isolation assumptions.

### 10) Utils (`czoi.utils`)

*   `safe_eval(expr, context)` must remain **minimal and auditable**.
*   Any additions to allowed AST nodes need explicit justification and tests.

***

## Contributor Tips

*   Keep PRs **small and focused**; large PRs are harder to review.
*   Prefer **composition** over deep inheritance where possible.
*   Keep the **base install light**; push heavy deps into extras.
*   Align new API names with the domain language (zones, roles, gamma mappings, constraints).
*   Add an **example** whenever you add a new concept.

***

*Thank you for helping make CZOI robust, secure, and a pleasure to use.*

***

### Want me to open a PR or save the file?

If you’d like, I can save this as `CONTRIBUTING.md` and prepare a PR draft (and optionally add companion files like `CODE_OF_CONDUCT.md`, `SECURITY.md`, and issue/PR templates).
