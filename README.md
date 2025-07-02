# Chat PySide Frontend - Lightning Fast Streaming

Ultra-fast PySide6 chat frontend optimized for real-time WebSocket text streaming.

## Features

- **Lightning-fast streaming**: Sub-10ms chunk latency from server to UI
- **Persistent WebSocket connections**: No connection overhead
- **Optimized for LLM streaming**: Direct chunk processing without batching delays
- **Auto-reconnection**: Exponential backoff strategy for robust connections
- **Structured logging**: JSON logs with performance metrics
- **Linux optimized**: Built specifically for Ubuntu/Raspberry Pi

## Requirements

- Python 3.13.0
- PySide6 6.8.1.1
- Linux (Ubuntu/Raspberry Pi)

## Setup

```bash
# Clone and navigate to project
cd Chat_PYSIDE_linux_frontend

# Create virtual environment (uv automatically uses .venv)
uv venv

# Install dependencies
uv sync

# Run the application (connects to 192.168.1.223:8000 by default)
uv run python src/app.py

# Or with custom backend
uv run python src/app.py --host localhost --port 3000

# With SSL
uv run python src/app.py --host your-server.com --port 443 --ssl

# Show help
uv run python src/app.py --help
```

## Architecture

```
Backend (LLM + WebSocket) ←→ PySide6 Frontend (streaming display)
```

### Key Optimizations

- **Direct chunk processing**: No artificial batching delays
- **Dedicated event loop**: Background thread for WebSocket operations
- **Persistent connections**: Single connection per session
- **Immediate UI updates**: Thread-safe Qt signals for sub-10ms latency

## Configuration

### Backend Connection

The frontend automatically connects to your backend. Default configuration:
- **Host**: `192.168.1.223`
- **Port**: `8000`
- **WebSocket URL**: `ws://192.168.1.223:8000/ws/chat`
- **Health Check**: `http://192.168.1.223:8000/health`

### Command Line Arguments

Quick backend configuration via command line:

```bash
# Connect to different backend
uv run python src/app.py --host localhost --port 3000

# Use SSL/TLS
uv run python src/app.py --host secure-server.com --port 443 --ssl

# Show all options
uv run python src/app.py --help
```

### Environment Variables

Override defaults using environment variables:

```bash
# Backend configuration
export CHAT_BACKEND_HOST=192.168.1.223
export CHAT_BACKEND_PORT=8000
export CHAT_BACKEND_SSL=false  # Set to 'true' for wss:// and https://

# Run with custom backend
CHAT_BACKEND_HOST=localhost CHAT_BACKEND_PORT=3000 uv run python src/app.py
```

### Programmatic Configuration

```python
from src.config import set_backend_config

# Override configuration in code
set_backend_config(host="your-server.com", port=8080, use_ssl=True)
```

## WebSocket Protocol

Expected message format:
```json
{
  "type": "chunk",
  "content": "text chunk"
}
```

## Performance

- **Target latency**: Sub-10ms chunk processing
- **UI responsiveness**: <10ms per frame on Qt UI thread
- **Memory efficient**: Optimized for long chat sessions
- **Auto-scroll**: Smooth scrolling without performance impact

Built following strict PROJECT_RULES.md for optimal performance and maintainability.
