Pinned Versions

    Python 3.13.0

    PySide6 6.8.1.1
    Pin both in CI, dev, staging, and prod.

Environment Setup

    # Create/discover & activate env:
    uv venv

    Afterwards, every uv command (uv add, uv sync, uv run) automatically uses that .venv.

Date-Aware Dependency Management

    Log today’s ISO date (YYYY-MM-DD) at the start of CI and install scripts.

    Discover the newest PySide6 release ≤ today on PyPI.

    Install the exact version:

uv add PySide6@6.8.1.1

Sync the lockfile into pyproject.toml:

    uv sync

    In pyproject.toml:

        Stable → ^6.8.1

        Prerelease → ==<exact-rc-version>

Async, Concurrency & Event-Driven Design

    Event-Loop Bridge

        Use qasync to integrate Qt’s event loop with asyncio.

    I/O Guidelines

        All external I/O (> 10 ms) must be async def + await.

        Wrap only truly long operations in async with timeout().

    Cancellation

        Never swallow asyncio.CancelledError in slots or background tasks.

Code Organisation & Style

    Separation

        Keep UI definitions (.ui/.qml/.qrc) separate from Python “glue” modules.

    Module Limits

        UI controllers: ≤ 150 LOC and ≤ 2 public symbols.

        Domain/business modules: follow your general soft/hard caps.

    Import Order

        Stdlib

        Third-party (PySide6 first)

        Internal

Security

    Secrets

        Read via os.getenv; do not commit .env.

        For packaged builds, load secrets at launch from an external file.

    Logging

        Never log tokens, secrets, or PII from UI events.

Testing

    Core

        pytest + pytest-asyncio with ≥ 70 % coverage on critical logic.

    GUI

        Add pytest-qt tests for widgets, signals/slots, and dialogs.

    Lint

        ruff --strict and mypy --strict per General Rules.

Logging & Observability

    Structured Logs

        Use structlog to emit JSON with event, module, elapsed_ms.

    Metrics

        Enable Prometheus on localhost:9000 only when launched with a --metrics flag.

Performance

    UI Responsiveness

        Keep the Qt UI thread under 10 ms per frame by offloading heavy work to QThreadPool or asyncio tasks.

    Profiling

        Only optimize hotspots identified via profiling (≥ 2 % CPU/time in a pure function).

Error Handling

    Global Hook

        Install a sys.excepthook to catch and log uncaught Qt exceptions.

    Fail-Fast

        Validate inputs early (raise ValueError/TypeError); catch broad exceptions only at the main() boundary.

General Engineering Principles

    Minimal Dependencies

        Only PySide6 + approved libraries installed via uv.

    Lean Codebase

        Delete obsolete UI screens/widgets—never hide them.

    Scope Discipline

        Implement exactly what’s scoped; track enhancements separately.

PySide (Qt) Integration & Deployment

    Resource Files

        Maintain one resources.qrc; compile in CI with:

    pyside6-rcc resources.qrc -o resources_rc.py

Translations

lupdate . -ts translations/app.ts
lrelease translations/app.ts

Ship the resulting .qm files.

Packaging

    Use PyInstaller (pinned version) with a minimal spec that includes Qt plugins (platforms/, styles/).

Signals & Slots

    Declare typed signals (e.g. Signal[int, str]); avoid anonymous callbacks.

Starter Template

    Include app.py, MainWindow.ui, and controller.py skeleton for new contributors.