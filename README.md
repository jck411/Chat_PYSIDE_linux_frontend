# Chat PySide Frontend

PySide6 chat frontend for smart home WebSocket streaming.

## Requirements

- Python 3.13.0
- PySide6 6.8.1.1
- Linux

## Setup

```bash
# Create virtual environment
uv venv

# Install dependencies
uv sync

# Run application
uv run python src/app.py
```

## Configuration

### Backend Profiles

Configure multiple backend connections via the settings dialog or environment variables:

```bash
export CHAT_BACKEND_HOST=192.168.1.223
export CHAT_BACKEND_PORT=8000
export CHAT_BACKEND_SSL=false
```

### Command Line

```bash
# Custom backend
uv run python src/app.py --host localhost --port 3000

# With SSL
uv run python src/app.py --host server.com --port 443 --ssl
```

## Features

- Real-time WebSocket streaming
- Light/dark theme switching
- Backend profile management
- Auto-reconnection
- Window state persistence

## Project Structure

```
src/
├── app.py                    # Main application
├── config/                   # Configuration management
├── controllers/              # UI controllers and WebSocket client
├── themes/                   # Theme system
└── ui/                       # UI components

resources/                    # Qt resources (icons, themes)
tests/                        # Test suite
```

## Development

```bash
# Run tests
uv run pytest

# Lint code
uv run ruff check .
uv run mypy src/

# Build resources
uv run python scripts/build_resources.py
```

## Rules

- [GENERAL_RULES.md](./GENERAL_RULES.md) - Language-agnostic engineering rules
- [PROJECT_RULES.md](./PROJECT_RULES.md) - PySide6-specific project rules
