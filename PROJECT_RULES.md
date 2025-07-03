# Project Rules - PySide6 Smart Home Chat Frontend

> This document extends [GENERAL_RULES.md](./GENERAL_RULES.md) with PySide6-specific requirements.

## Python & PySide6 Versions

- **Python 3.13.0**
- **PySide6 6.8.1.1**

Pin both in CI, dev, staging, and prod.

## Environment Setup

```bash
# Create/discover & activate env:
uv venv
```

Afterwards, every uv command (uv add, uv sync, uv run) automatically uses that .venv.

## Python-Specific Dependency Management

Install with exact versions:

```bash
uv add PySide6@6.8.1.1
```

Sync the lockfile into pyproject.toml:

```bash
uv sync
```

In pyproject.toml:
- Stable → `^6.8.1`
- Prerelease → `==<exact-rc-version>`

Never invoke `pip`, `poetry`, or `conda` directly.

## Qt + Asyncio Integration

- Use **qasync** to integrate Qt's event loop with asyncio
- All external I/O (> 10 ms) must be `async def` + `await`
- Wrap only truly long operations in `async with timeout()`
- Never swallow `asyncio.CancelledError` in slots or background tasks

## WebSocket Streaming Performance

### Real-Time Chat Requirements
- Target sub-10ms chunk processing for smooth streaming
- Direct UI updates without batching delays
- Auto-scroll optimization for chat display
- Connection status monitoring with auto-reconnect

### Qt UI Thread Performance
- Keep Qt UI thread under 10ms per frame
- Offload heavy work to QThreadPool or asyncio tasks
- Profile hotspots (≥ 2% CPU/time) before optimizing

## PySide6 Code Organization

### UI Architecture
- Keep UI definitions (.qrc) separate from Python "glue" modules
- Use programmatic UI creation for dynamic interfaces
- UI controllers: ≤ 200 LOC and ≤ 3 public symbols (relaxed for hobby projects)

### Import Order (Python-specific)
1. Standard library
2. Third-party (PySide6 first)
3. Internal modules

## Theme System & Material Design

### Theme Management
- Support light/dark theme switching
- Use consistent icon theming across components
- Maintain theme state persistence
- Resource compilation via pyside6-rcc

### Configuration Management
- Backend profile system for smart home connections
- Window geometry persistence
- User preference storage
- Environment-based configuration loading

## Python Testing & Quality

### Testing Stack
- pytest + pytest-asyncio with ≥ 40% coverage on critical logic
- pytest-qt tests for widgets, signals/slots, and dialogs

### Code Quality
- ruff --strict and mypy --strict must pass
- Target Python 3.13 features in ruff configuration
- Ignore missing imports during development (`--ignore-missing-imports`)

## Python Logging

### Structured Logging
- Use **structlog** to emit JSON with event, module, elapsed_ms
- Include performance metrics for streaming operations
- Never log tokens, secrets, or PII from UI events

## Python Error Handling

### Qt Exception Handling
- Install a `sys.excepthook` to catch and log uncaught Qt exceptions
- Validate inputs early (raise `ValueError`/`TypeError`)
- Catch broad exceptions only at the `main()` boundary

## PySide6 Resource Management

### Resource Files
- Maintain one `resources.qrc`; compile in CI with:

```bash
pyside6-rcc resources.qrc -o resources_rc.py
```

### Packaging (Optional for Hobby Projects)
- Use PyInstaller (pinned version) for standalone deployment
- Useful for running on dedicated smart home devices (Raspberry Pi, etc.)
- Include Qt plugins (platforms/, styles/) in spec

### Signals & Slots
- Declare typed signals (e.g. `Signal[int, str]`)
- Avoid anonymous callbacks for better debugging

## Smart Home Integration

### Backend Communication
- WebSocket-first for real-time chat streaming
- Support multiple backend profiles/endpoints
- Graceful connection handling and reconnection
- Status indicators for connection health

### Personal Project Considerations
- Focus on functionality over enterprise features
- Prioritize user experience for single-user scenarios
- Keep deployment simple for home network usage

## Dependencies

### Core Dependencies
- PySide6 (UI framework)
- qasync (Qt + asyncio integration)
- structlog (structured logging)
- websockets (WebSocket client)

### Development Dependencies
- pytest + pytest-asyncio + pytest-qt (testing)
- ruff (linting and formatting)
- mypy (type checking)
- pre-commit (git hooks)

## Project Structure

```
src/
├── app.py                    # Main application entry point
├── resources_rc.py          # Compiled Qt resources
├── config/                  # Configuration management
├── controllers/             # UI controllers and WebSocket client
├── themes/                  # Theme system and Material Design
└── ui/                      # UI components and dialogs

resources/
├── resources.qrc           # Qt resource definition
├── icons/                  # Material Design icons
└── themes/                 # QSS theme files

tests/                      # Test suite
scripts/                    # Build and utility scripts
```

## Removed Enterprise Features

The following are explicitly not implemented for this hobby project:
- ❌ Prometheus metrics endpoints
- ❌ Translation/internationalization support
- ❌ Starter templates for new contributors
- ❌ High coverage requirements (keeping realistic 40%)
