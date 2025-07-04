"""
Optimized WebSocket Client for Chat Frontend

Following WebSocket_Streaming_Optimizations.md:
- Persistent connection management with auto-reconnect
- Direct chunk processing (no batching delays)
- Dedicated background event loop
- Thread-safe PySide6 signal integration
- Optimal connection settings for speed
"""

import asyncio
import json
import threading
import time
import uuid

import structlog
import websockets
from PySide6.QtCore import QObject, Signal
from websockets.asyncio.client import ClientConnection

from ..config import get_config_manager


class OptimizedWebSocketClient(QObject):
    """
    Ultra-fast WebSocket client optimized for real-time text streaming.

    Key optimizations:
    - Single persistent connection per session
    - Immediate chunk processing (no artificial delays)
    - Dedicated asyncio event loop in background thread
    - Exponential backoff reconnection strategy
    - Compression enabled for bandwidth efficiency
    """

    # Thread-safe signals for UI updates
    chunk_received = Signal(str)  # For text_chunk content
    message_started = Signal(str, str)  # message_id, user_message
    message_completed = Signal(str, str)  # message_id, full_content
    connection_established = Signal(str)  # client_id
    connection_status_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self, websocket_url: str | None = None):
        super().__init__()
        # Use configuration if no URL provided
        if websocket_url is None:
            config_manager = get_config_manager()
            self.websocket_url = config_manager.get_websocket_url()
        else:
            self.websocket_url = websocket_url

        self.logger = structlog.get_logger(__name__)

        # Connection state
        self._websocket: ClientConnection | None = None
        self._is_connected = False
        self._should_reconnect = True
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._client_id: str | None = None

        # Background event loop
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

        # Performance monitoring
        self._chunk_times: list[float] = []
        self._last_chunk_time: float | None = None

        # Start the background event loop
        self._start_background_loop()

    def _start_background_loop(self) -> None:
        """Start dedicated background thread with asyncio event loop"""

        def run_loop() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self.logger.info(
                "WebSocket background loop started",
                ws_event="websocket_loop_start",
                module=__name__,
            )
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()

        # Wait for loop to be ready
        while self._loop is None:
            time.sleep(0.001)

    def connect_to_backend(self) -> None:
        """Initiate WebSocket connection (non-blocking)"""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._connect(), self._loop)

    def disconnect_from_backend(self) -> None:
        """Cleanly disconnect WebSocket"""
        self._should_reconnect = False
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop)

    def update_backend_url(self, new_url: str | None = None) -> None:
        """Update WebSocket URL and reconnect"""
        if new_url is None:
            # Get current URL from config manager
            config_manager = get_config_manager()
            new_url = config_manager.get_websocket_url()

        if new_url != self.websocket_url:
            self.logger.info(
                "Updating WebSocket URL",
                ws_event="url_update",
                module=__name__,
                old_url=self.websocket_url,
                new_url=new_url,
            )

            self.websocket_url = new_url

            # Disconnect and reconnect with new URL
            self.disconnect_from_backend()
            # Small delay to ensure clean disconnect
            if self._loop and not self._loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self._reconnect_with_delay(), self._loop
                )

    async def _reconnect_with_delay(self) -> None:
        """Reconnect after a short delay"""
        await asyncio.sleep(1)  # Wait for clean disconnect
        self._should_reconnect = True
        self._reconnect_attempts = 0  # Reset reconnect attempts
        await self._connect()

    def send_message(self, message: str) -> None:
        """Send message to WebSocket server (non-blocking)"""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._send_message(message), self._loop)

    async def _connect(self) -> None:
        """Establish WebSocket connection with optimal settings"""
        try:
            if not self.websocket_url:
                self.error_occurred.emit("No WebSocket URL configured")
                return

            self.logger.info(
                "Attempting WebSocket connection",
                connect_event="websocket_connect_start",
                module=__name__,
                url=self.websocket_url,
            )

            # Optimal WebSocket configuration per optimization guide
            self._websocket = await websockets.connect(
                self.websocket_url,
                ping_interval=20,  # Keep connection alive
                ping_timeout=10,  # Quick failure detection
                max_size=2**20,  # 1MB max message size
                compression="deflate",  # Reduce bandwidth
            )

            self._is_connected = True
            self._reconnect_attempts = 0

            # Emit connection status change
            self.connection_status_changed.emit(True)

            self.logger.info(
                "WebSocket connected successfully",
                connect_event="websocket_connected",
                module=__name__,
            )

            # Start message listener
            await self._message_listener()

        except Exception as e:
            self.logger.error(
                "WebSocket connection failed",
                connect_event="websocket_connect_error",
                module=__name__,
                error=str(e),
            )
            self.error_occurred.emit(f"Connection failed: {e!s}")
            await self._schedule_reconnect()

    async def _disconnect(self) -> None:
        """Clean disconnect from WebSocket"""
        if self._websocket:
            await self._websocket.close()
            self._websocket = None

        self._is_connected = False
        self._client_id = None
        self.connection_status_changed.emit(False)

        self.logger.info(
            "WebSocket disconnected",
            disconnect_event="websocket_disconnected",
            module=__name__,
        )

    async def _message_listener(self) -> None:
        """Listen for incoming messages with new protocol format only - no backward compatibility"""
        if not self._websocket:
            return

        try:
            async for message in self._websocket:
                start_time = time.time()

                try:
                    data = json.loads(message)

                    # Handle new protocol format
                    if "request_id" in data and "status" in data:
                        request_id = data.get("request_id")
                        status = data.get("status")

                        if status == "processing":
                            # Message started processing
                            self.message_started.emit(request_id, "")
                            self.logger.info(
                                "Message processing started",
                                stream_event="message_processing_start",
                                module=__name__,
                                request_id=request_id,
                            )

                        elif status == "chunk":
                            # Handle chunk data - fail fast if chunk is missing
                            if "chunk" not in data:
                                error_msg = f"Chunk status missing chunk data. Request ID: {request_id}"
                                self.logger.error(
                                    "Chunk status missing chunk data - failing fast",
                                    parse_event="missing_chunk_data",
                                    module=__name__,
                                    request_id=request_id,
                                    error=error_msg,
                                )
                                self.error_occurred.emit(error_msg)
                                continue

                            chunk = data["chunk"]
                            chunk_type = chunk.get("type")
                            chunk_data = chunk.get("data", "")

                            if chunk_type == "text":
                                # CRITICAL: Direct chunk processing - no batching delays!
                                self.chunk_received.emit(chunk_data)

                                # Performance monitoring
                                self._track_chunk_performance(start_time)

                            elif chunk_type == "metadata":
                                # Handle metadata chunks (status updates, etc.)
                                self.logger.info(
                                    "Metadata chunk received",
                                    stream_event="metadata_chunk",
                                    module=__name__,
                                    request_id=request_id,
                                    metadata=chunk_data,
                                )

                            elif chunk_type == "error":
                                # Handle error chunks
                                self.error_occurred.emit(chunk_data)
                                self.logger.error(
                                    "Error chunk received",
                                    error_event="error_chunk",
                                    module=__name__,
                                    request_id=request_id,
                                    error=chunk_data,
                                )

                            # Handle other chunk types (image, audio, binary) when needed
                            elif chunk_type in ["image", "audio", "binary"]:
                                # For now, just log these - will be implemented later
                                self.logger.info(
                                    "Non-text chunk received",
                                    stream_event="non_text_chunk",
                                    module=__name__,
                                    request_id=request_id,
                                    chunk_type=chunk_type,
                                )

                            else:
                                # Fail fast on unknown chunk types
                                error_msg = f"Unknown chunk type: {chunk_type}. Request ID: {request_id}"
                                self.logger.error(
                                    "Unknown chunk type received - failing fast",
                                    parse_event="unknown_chunk_type",
                                    module=__name__,
                                    request_id=request_id,
                                    chunk_type=chunk_type,
                                    error=error_msg,
                                )
                                self.error_occurred.emit(error_msg)

                        elif status == "complete":
                            # Message completed
                            self.message_completed.emit(request_id, "")
                            self.logger.info(
                                "Message completed",
                                stream_event="message_complete",
                                module=__name__,
                                request_id=request_id,
                            )

                        elif status == "error":
                            # Handle error status
                            error_msg = data.get("error", "Unknown error")
                            self.error_occurred.emit(error_msg)
                            self.logger.error(
                                "Error status received",
                                error_event="error_status",
                                module=__name__,
                                request_id=request_id,
                                error=error_msg,
                            )

                        else:
                            # Fail fast on unknown status types
                            error_msg = f"Unknown status type: {status}. Request ID: {request_id}"
                            self.logger.error(
                                "Unknown status type received - failing fast",
                                parse_event="unknown_status_type",
                                module=__name__,
                                request_id=request_id,
                                status=status,
                                error=error_msg,
                            )
                            self.error_occurred.emit(error_msg)

                    # No backward compatibility - fail fast on unexpected message format
                    else:
                        error_msg = f"Invalid message format: missing required fields (request_id, status). Got: {list(data.keys())}"
                        self.logger.error(
                            "Invalid message format received - failing fast",
                            parse_event="invalid_message_format",
                            module=__name__,
                            error=error_msg,
                            message_keys=list(data.keys()),
                        )
                        self.error_occurred.emit(error_msg)
                        # Fail fast - don't process invalid messages

                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON received - failing fast: {e}"
                    self.logger.error(
                        "Invalid JSON received - failing fast",
                        parse_event="invalid_json",
                        module=__name__,
                        error=error_msg,
                    )
                    self.error_occurred.emit(error_msg)

        except websockets.exceptions.ConnectionClosed:
            self.logger.info(
                "WebSocket connection closed",
                close_event="websocket_closed",
                module=__name__,
            )
            await self._handle_connection_lost()

        except Exception as e:
            self.logger.error(
                "Message listener error",
                listener_event="message_listener_error",
                module=__name__,
                error=str(e),
            )
            await self._handle_connection_lost()

    async def _send_message(self, message: str) -> None:
        """Send message to WebSocket server using new protocol format"""
        if not self._websocket or not self._is_connected:
            self.logger.warning(
                "Cannot send message - not connected",
                send_event="send_message_not_connected",
                module=__name__,
            )
            return

        try:
            # Use the new protocol format
            message_data = {
                "action": "chat",
                "payload": {"text": message},
                "request_id": str(uuid.uuid4()),
                "user_id": None,  # Optional, can be added later
            }

            await self._websocket.send(json.dumps(message_data))

            self.logger.info(
                "Message sent",
                send_event="message_sent",
                module=__name__,
                message_length=len(message),
                request_id=message_data["request_id"],
                action=message_data["action"],
            )

        except Exception as e:
            self.logger.error(
                "Failed to send message",
                send_event="send_message_error",
                module=__name__,
                error=str(e),
            )
            self.error_occurred.emit(f"Send failed: {e!s}")

    def send_ping(self) -> None:
        """Send ping to check connection health"""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._send_ping(), self._loop)

    async def _send_ping(self) -> None:
        """Send ping message using new protocol format"""
        if not self._websocket or not self._is_connected:
            return

        try:
            # Use new protocol format for ping
            ping_data = {
                "action": "frontend_command",
                "payload": {"command": "ping"},
                "request_id": str(uuid.uuid4()),
                "user_id": None,
            }
            await self._websocket.send(json.dumps(ping_data))
        except Exception as e:
            self.logger.error(
                "Failed to send ping",
                ping_event="ping_error",
                module=__name__,
                error=str(e),
            )

    def get_history(self) -> None:
        """Request chat history from backend"""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._get_history(), self._loop)

    async def _get_history(self) -> None:
        """Send get_history request using new protocol format"""
        if not self._websocket or not self._is_connected:
            return

        try:
            history_data = {
                "action": "frontend_command",
                "payload": {"command": "get_history"},
                "request_id": str(uuid.uuid4()),
                "user_id": None,
            }
            await self._websocket.send(json.dumps(history_data))
        except Exception as e:
            self.logger.error(
                "Failed to get history",
                history_event="get_history_error",
                module=__name__,
                error=str(e),
            )

    def clear_history(self) -> None:
        """Request to clear chat history"""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._clear_history(), self._loop)

    async def _clear_history(self) -> None:
        """Send clear_history request using new protocol format"""
        if not self._websocket or not self._is_connected:
            return

        try:
            clear_data = {
                "action": "frontend_command",
                "payload": {"command": "clear_history"},
                "request_id": str(uuid.uuid4()),
                "user_id": None,
            }
            await self._websocket.send(json.dumps(clear_data))
        except Exception as e:
            self.logger.error(
                "Failed to clear history",
                history_event="clear_history_error",
                module=__name__,
                error=str(e),
            )

    def get_config(self) -> None:
        """Request backend configuration"""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._get_config(), self._loop)

    async def _get_config(self) -> None:
        """Send get_config request using new protocol format"""
        if not self._websocket or not self._is_connected:
            return

        try:
            config_data = {
                "action": "frontend_command",
                "payload": {"command": "get_config"},
                "request_id": str(uuid.uuid4()),
                "user_id": None,
            }
            await self._websocket.send(json.dumps(config_data))
        except Exception as e:
            self.logger.error(
                "Failed to get config",
                config_event="get_config_error",
                module=__name__,
                error=str(e),
            )

    async def _handle_connection_lost(self) -> None:
        """Handle lost connection with reconnection logic"""
        self._is_connected = False
        self._client_id = None
        self.connection_status_changed.emit(False)

        if self._should_reconnect:
            await self._schedule_reconnect()

    async def _schedule_reconnect(self) -> None:
        """Schedule reconnection with exponential backoff"""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            self.logger.error(
                "Max reconnection attempts reached",
                reconnect_event="max_reconnect_attempts",
                module=__name__,
                attempts=self._reconnect_attempts,
            )
            self.error_occurred.emit("Connection failed - max retries exceeded")
            return

        # Exponential backoff with cap at 60 seconds
        delay = min(2**self._reconnect_attempts, 60)
        self._reconnect_attempts += 1

        self.logger.info(
            "Scheduling reconnection",
            reconnect_event="schedule_reconnect",
            module=__name__,
            delay=delay,
            attempt=self._reconnect_attempts,
        )

        await asyncio.sleep(delay)
        await self._connect()

    def _track_chunk_performance(self, start_time: float) -> None:
        """Track chunk processing performance for optimization"""
        now = time.time()
        processing_time = now - start_time

        if self._last_chunk_time:
            inter_chunk_latency = start_time - self._last_chunk_time
            self._chunk_times.append(inter_chunk_latency)

            # Log performance every 100 chunks
            if len(self._chunk_times) % 100 == 0:
                avg_latency = sum(self._chunk_times[-100:]) / 100
                self.logger.info(
                    "Chunk performance metrics",
                    perf_event="chunk_performance",
                    module=__name__,
                    avg_latency_ms=avg_latency * 1000,
                    processing_time_ms=processing_time * 1000,
                    chunks_processed=len(self._chunk_times),
                )

        self._last_chunk_time = now

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected"""
        return self._is_connected

    @property
    def client_id(self) -> str | None:
        """Get the client ID assigned by the backend"""
        return self._client_id

    def cleanup(self) -> None:
        """Clean shutdown of WebSocket client"""
        self._should_reconnect = False
        self.disconnect_from_backend()

        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

        self.logger.info(
            "WebSocket client cleaned up",
            cleanup_event="websocket_cleanup",
            module=__name__,
        )
