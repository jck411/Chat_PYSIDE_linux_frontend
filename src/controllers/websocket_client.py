"""
Optimized WebSocket Client for Chat Frontend

Following WebSocket_Streaming_Optimizations.md:
- Persistent connection management with auto-reconnect
- Direct chunk processing (no batching delays)
- Dedicated background event loop
- Thread-safe PySide6 signal integration
- Optimal connection settings for speed
- Provider-specific optimizations (Anthropic, OpenAI, etc.)
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

from ..config import ProviderConfigManager, get_config_manager


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
    connection_status_changed = Signal(bool)
    error_occurred = Signal(str)
    provider_detected = Signal(str, str, str)  # provider, model, orchestrator
    session_cleared = Signal(str, str)  # new_conversation_id, old_conversation_id
    conversation_history_loaded = Signal(list)  # list of history messages

    def __init__(self, websocket_url: str | None = None):
        super().__init__()
        # Use configuration if no URL provided
        if websocket_url is None:
            config_manager = get_config_manager()
            self.websocket_url = config_manager.get_websocket_url()
        else:
            self.websocket_url = websocket_url

        self.logger = structlog.get_logger(__name__)

        # Provider configuration manager
        self.provider_config = ProviderConfigManager()

        # Connection state
        self._websocket: ClientConnection | None = None
        self._is_connected = False
        self._should_reconnect = True
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5

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
        # Reset reconnection attempts for manual connection
        self._reconnect_attempts = 0
        self._should_reconnect = True
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

    def clear_session(self) -> None:
        """Clear session and reset conversation (non-blocking)"""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._clear_session(), self._loop)

    async def _connect(self) -> None:
        """Establish WebSocket connection with provider-optimized settings"""
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

            # Get provider-optimized WebSocket configuration
            ws_config = self.provider_config.get_websocket_config()

            self.logger.info(
                "Using provider-optimized WebSocket configuration",
                connect_event="websocket_config",
                module=__name__,
                provider=self.provider_config.get_current_provider().value,
                config=ws_config,
            )

            # Establish connection with provider-optimized settings
            self._websocket = await websockets.connect(self.websocket_url, **ws_config)

            self._is_connected = True
            self._reconnect_attempts = 0

            # Emit connection status change
            self.connection_status_changed.emit(True)

            self.logger.info(
                "WebSocket connected successfully",
                connect_event="websocket_connected",
                module=__name__,
                provider_summary=self.provider_config.get_provider_summary(),
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
        self.connection_status_changed.emit(False)

        self.logger.info(
            "WebSocket disconnected",
            disconnect_event="websocket_disconnected",
            module=__name__,
        )

    async def _message_listener(self) -> None:
        """Listen for incoming messages with provider-specific optimizations"""
        if not self._websocket:
            return

        try:
            async for message in self._websocket:
                start_time = time.time()

                try:
                    data = json.loads(message)

                    # Defensive check to ensure data is not None
                    if data is None:
                        self.logger.warning(
                            "Received None data after JSON parsing",
                            parse_event="none_data_received",
                            module=__name__,
                        )
                        continue

                    # Handle backend response format
                    if "request_id" in data and "status" in data:
                        request_id = data.get("request_id")
                        status = data.get("status")

                        if status == "processing":
                            # Extract provider info and user message from processing message
                            chunk_data = data.get("chunk")
                            if chunk_data is not None:
                                metadata = chunk_data.get("metadata")
                                if metadata is not None:
                                    user_message = metadata.get("user_message", "")

                                    # Auto-detect and configure provider optimizations
                                    provider_info = metadata.get("provider_info")
                                    if provider_info:
                                        provider_changed = (
                                            self.provider_config.update_provider_info(
                                                provider_info
                                            )
                                        )

                                        if provider_changed:
                                            # Emit provider detection signal
                                            self.provider_detected.emit(
                                                provider_info.get("provider", ""),
                                                provider_info.get("model", ""),
                                                provider_info.get(
                                                    "orchestrator_type", ""
                                                ),
                                            )

                                            # Log provider-specific optimization applied
                                            self.logger.info(
                                                "Provider-specific optimizations applied",
                                                provider_event="optimizations_applied",
                                                module=__name__,
                                                provider_summary=self.provider_config.get_provider_summary(),
                                            )
                                else:
                                    user_message = ""
                            else:
                                user_message = ""

                            self.message_started.emit(request_id, user_message)
                            self.logger.info(
                                "Message processing started",
                                stream_event="processing_started",
                                module=__name__,
                                request_id=request_id,
                                user_message=user_message,
                                provider=self.provider_config.get_current_provider().value,
                            )

                        elif status == "chunk":
                            chunk = data.get("chunk")
                            if chunk is not None and chunk.get("type") == "text":
                                chunk_content = chunk.get("data", "")

                                # Extract provider info from chunk metadata if available
                                metadata = chunk.get("metadata")
                                if metadata and "provider_info" in metadata:
                                    provider_info = metadata["provider_info"]
                                    self.provider_config.update_provider_info(
                                        provider_info
                                    )

                                # Apply provider-specific chunk processing
                                optimizations = self.provider_config.get_optimizations()

                                if optimizations.immediate_processing:
                                    # CRITICAL: Direct chunk processing - no batching delays!
                                    self.chunk_received.emit(chunk_content)
                                else:
                                    # Future: Could implement buffering for providers that benefit from it
                                    self.chunk_received.emit(chunk_content)

                                # Performance monitoring
                                self._track_chunk_performance(start_time)

                        elif status == "completed":
                            # Check if this is a clear session response
                            chunk = data.get("chunk", {})
                            if chunk.get("type") == "session_cleared":
                                # Handle clear session completion
                                metadata = chunk.get("metadata", {})
                                new_conversation_id = metadata.get("new_conversation_id", "")
                                old_conversation_id = metadata.get("old_conversation_id", "")

                                self.session_cleared.emit(new_conversation_id, old_conversation_id)
                                self.logger.info(
                                    "Session cleared successfully",
                                    clear_event="session_cleared",
                                    module=__name__,
                                    request_id=request_id,
                                    new_conversation_id=new_conversation_id,
                                    old_conversation_id=old_conversation_id,
                                )
                            else:
                                # Regular message completion
                                self.message_completed.emit(request_id, "")
                                self.logger.info(
                                    "Response completed",
                                    stream_event="response_complete",
                                    module=__name__,
                                    request_id=request_id,
                                    provider=self.provider_config.get_current_provider().value,
                                )

                        elif status == "init":
                            # Handle conversation history loading
                            chunk = data.get("chunk", {})
                            if chunk.get("type") == "conversation_history":
                                history_data = chunk.get("data", [])
                                self.conversation_history_loaded.emit(history_data)
                                self.logger.info(
                                    "Conversation history loaded",
                                    history_event="conversation_history_loaded",
                                    module=__name__,
                                    message_count=len(history_data),
                                )

                        elif status == "error":
                            await self._handle_error_message(data, request_id)

                        elif status == "success":
                            # Handle successful action responses (legacy support)
                            action = data.get("action")
                            if action == "clear_session":
                                session_data = data.get("data", {})
                                new_conversation_id = session_data.get("new_conversation_id", "")
                                old_conversation_id = session_data.get("old_conversation_id", "")

                                self.session_cleared.emit(new_conversation_id, old_conversation_id)
                                self.logger.info(
                                    "Session cleared successfully (legacy)",
                                    clear_event="session_cleared_legacy",
                                    module=__name__,
                                    request_id=request_id,
                                    new_conversation_id=new_conversation_id,
                                    old_conversation_id=old_conversation_id,
                                )

                    else:
                        self.logger.warning(
                            "Unknown message format received",
                            parse_event="unknown_message_format",
                            module=__name__,
                            message_keys=list(data.keys()) if data else [],
                        )

                except json.JSONDecodeError as e:
                    self.logger.warning(
                        "Invalid JSON received",
                        parse_event="invalid_json",
                        module=__name__,
                        error=str(e),
                    )

        except websockets.exceptions.ConnectionClosed:
            self.logger.info(
                "WebSocket connection closed",
                close_event="websocket_closed",
                module=__name__,
            )
            await self._handle_connection_lost()

        except websockets.exceptions.InvalidURI as e:
            self.logger.error(
                "Invalid WebSocket URI",
                connect_event="websocket_invalid_uri",
                module=__name__,
                error=str(e),
            )
            self.error_occurred.emit(f"Invalid WebSocket URI: {e!s}")

        except websockets.exceptions.InvalidHandshake as e:
            self.logger.error(
                "WebSocket handshake failed",
                connect_event="websocket_handshake_failed",
                module=__name__,
                error=str(e),
            )
            self.error_occurred.emit(f"WebSocket handshake failed: {e!s}")
            await self._schedule_reconnect()

        except TimeoutError:
            self.logger.error(
                "WebSocket connection timeout",
                connect_event="websocket_timeout",
                module=__name__,
            )
            self.error_occurred.emit("Connection timeout")
            await self._schedule_reconnect()

        except (OSError, ConnectionRefusedError) as e:
            self.logger.error(
                "Network connection error",
                connect_event="websocket_network_error",
                module=__name__,
                error=str(e),
            )
            self.error_occurred.emit(f"Network error: {e!s}")
            await self._schedule_reconnect()

        except json.JSONDecodeError as e:
            self.logger.error(
                "Invalid JSON in WebSocket message",
                parse_event="websocket_json_error",
                module=__name__,
                error=str(e),
            )
            # Continue listening for more messages

        except Exception as e:
            self.logger.error(
                "Unexpected message listener error",
                listener_event="message_listener_unexpected_error",
                module=__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
            await self._handle_connection_lost()

    async def _handle_error_message(self, data: dict, request_id: str) -> None:
        """Handle error messages with provider-specific error recovery"""
        chunk = data.get("chunk", {})
        error_msg = chunk.get("error", data.get("error", "Unknown error"))

        # Extract provider info and recoverable flag from error metadata
        metadata = chunk.get("metadata", {})
        provider_info = metadata.get("provider_info")
        is_recoverable = metadata.get("recoverable", False)

        # Update provider info if available
        if provider_info:
            self.provider_config.update_provider_info(provider_info)

        # Apply provider-specific error handling
        if self.provider_config.should_use_recoverable_errors() and is_recoverable:
            # For Anthropic and other providers that support recoverable errors
            if self.provider_config.should_retry_on_recoverable():
                self.logger.warning(
                    "Recoverable error received - will retry",
                    error_event="recoverable_error",
                    module=__name__,
                    error=error_msg,
                    request_id=request_id,
                    provider=self.provider_config.get_current_provider().value,
                )

                # Could implement automatic retry logic here
                # For now, just emit as a warning rather than error
                # self.error_occurred.emit(f"Warning: {error_msg} (retrying...)")
                return
            else:
                self.logger.warning(
                    "Recoverable error received",
                    error_event="recoverable_error_no_retry",
                    module=__name__,
                    error=error_msg,
                    request_id=request_id,
                    provider=self.provider_config.get_current_provider().value,
                )

        # Handle as regular error
        self.error_occurred.emit(error_msg)
        self.logger.error(
            "Backend error received",
            error_event="backend_error",
            module=__name__,
            error=error_msg,
            request_id=request_id,
            provider=self.provider_config.get_current_provider().value,
            recoverable=is_recoverable,
        )

    async def _send_message(self, message: str) -> None:
        """Send message to WebSocket server using correct protocol"""
        if not self._websocket or not self._is_connected:
            self.logger.warning(
                "Cannot send message - not connected",
                send_event="send_message_not_connected",
                module=__name__,
            )
            return

        try:
            message_data = {
                "action": "chat",
                "payload": {"text": message},
                "request_id": str(uuid.uuid4()),
            }

            await self._websocket.send(json.dumps(message_data))

            self.logger.info(
                "Message sent",
                send_event="message_sent",
                module=__name__,
                message_length=len(message),
                request_id=message_data["request_id"],
            )

        except Exception as e:
            self.logger.error(
                "Failed to send message",
                send_event="send_message_error",
                module=__name__,
                error=str(e),
            )
            self.error_occurred.emit(f"Send failed: {e!s}")

    async def _clear_session(self) -> None:
        """Send clear session request to WebSocket server"""
        if not self._websocket or not self._is_connected:
            self.logger.warning(
                "Cannot clear session - not connected",
                send_event="clear_session_not_connected",
                module=__name__,
            )
            return

        try:
            clear_data = {
                "action": "clear_session",
                "request_id": str(uuid.uuid4()),
            }

            await self._websocket.send(json.dumps(clear_data))

            self.logger.info(
                "Clear session request sent",
                send_event="clear_session_sent",
                module=__name__,
                request_id=clear_data["request_id"],
            )

        except Exception as e:
            self.logger.error(
                "Failed to send clear session request",
                send_event="clear_session_error",
                module=__name__,
                error=str(e),
            )
            self.error_occurred.emit(f"Clear session failed: {e!s}")

    async def _handle_connection_lost(self) -> None:
        """Handle lost connection with reconnection logic"""
        self._is_connected = False
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

    def get_provider_info(self) -> dict[str, str]:
        """Get current provider information"""
        return {
            "provider": self.provider_config.get_current_provider().value,
            "model": self.provider_config.get_current_model() or "",
            "orchestrator": self.provider_config.get_current_orchestrator() or "",
        }

    def get_provider_summary(self) -> dict:
        """Get detailed provider configuration summary"""
        return self.provider_config.get_provider_summary()

    def cleanup(self) -> None:
        """Clean shutdown of WebSocket client with comprehensive resource cleanup"""
        try:
            self._should_reconnect = False

            # Disconnect from backend
            try:
                self.disconnect_from_backend()
            except Exception as e:
                self.logger.warning(
                    "Error during WebSocket disconnect",
                    cleanup_event="websocket_disconnect_error",
                    module=__name__,
                    error=str(e),
                )

            # Stop and close event loop
            if self._loop and not self._loop.is_closed():
                try:
                    self._loop.call_soon_threadsafe(self._loop.stop)
                    # Wait briefly for loop to stop
                    time.sleep(0.1)
                except RuntimeError as e:
                    self.logger.warning(
                        "Error stopping event loop",
                        cleanup_event="event_loop_stop_error",
                        module=__name__,
                        error=str(e),
                    )

            # Clean up thread
            if self._thread and self._thread.is_alive():
                try:
                    self._thread.join(timeout=5.0)
                    if self._thread.is_alive():
                        self.logger.warning(
                            "WebSocket thread did not terminate within timeout",
                            cleanup_event="thread_timeout",
                            module=__name__,
                        )
                except Exception as e:
                    self.logger.warning(
                        "Error joining WebSocket thread",
                        cleanup_event="thread_join_error",
                        module=__name__,
                        error=str(e),
                    )

            # Clear references to prevent memory leaks
            self._websocket = None
            self._thread = None
            # Note: Don't close the loop here as it might be shared

            self.logger.info(
                "WebSocket client cleaned up successfully",
                cleanup_event="websocket_cleanup_complete",
                module=__name__,
            )

        except Exception as e:
            self.logger.error(
                "Unexpected error during WebSocket cleanup",
                cleanup_event="websocket_cleanup_error",
                module=__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
