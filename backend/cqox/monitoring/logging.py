"""
Structured logging with correlation IDs

Features:
- JSON-formatted logs
- Request correlation IDs
- Trace ID correlation with OpenTelemetry
- Log aggregation (Loki)
"""
import sys
import logging
from loguru import logger
from contextvars import ContextVar
from typing import Dict, Any
import json
from datetime import datetime

# Context variables for correlation
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')


class StructuredLogger:
    """
    Structured logger with JSON output

    Includes:
    - Correlation IDs
    - Trace IDs (OpenTelemetry)
    - Timestamps
    - Severity levels
    - Contextual metadata
    """

    def __init__(
        self,
        service_name: str = "cqox-engine",
        level: str = "INFO",
        json_output: bool = True
    ):
        self.service_name = service_name
        self.level = level
        self.json_output = json_output

        self._configure_logger()

    def _configure_logger(self):
        """Configure loguru logger"""
        # Remove default handler
        logger.remove()

        # Add structured JSON handler
        if self.json_output:
            logger.add(
                self._json_sink,
                level=self.level,
            )
        else:
            logger.add(
                sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
                level=self.level
            )

        # Add file handler for errors
        import os
        os.makedirs("logs", exist_ok=True)
        logger.add(
            self._file_json_sink,
            level="ERROR",
        )

    def _json_sink(self, message):
        """Custom sink for JSON-formatted logs"""
        record = message.record
        
        # Get OpenTelemetry trace context
        try:
            from opentelemetry import trace
            span = trace.get_current_span()
            span_context = span.get_span_context()
        except Exception:
            span_context = None

        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "service": self.service_name,
            "logger": record["name"],
            "function": record["function"],
            "line": record["line"],
            "correlation_id": correlation_id_var.get(),
            "trace_id": format(span_context.trace_id, '032x') if span_context and span_context.is_valid else trace_id_var.get(),
            "span_id": format(span_context.span_id, '016x') if span_context and span_context.is_valid else None
        }

        # Add exception info if present
        if record["exception"]:
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": str(record["exception"].traceback) if record["exception"].traceback else None
            }

        # Add extra fields
        if "extra" in record:
            log_entry["extra"] = record["extra"]

        # Write to stdout
        sys.stdout.write(json.dumps(log_entry) + "\n")
        sys.stdout.flush()

    def _file_json_sink(self, message):
        """Custom sink for JSON-formatted file logs"""
        record = message.record
        
        # Get OpenTelemetry trace context
        try:
            from opentelemetry import trace
            span = trace.get_current_span()
            span_context = span.get_span_context()
        except Exception:
            span_context = None

        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "service": self.service_name,
            "logger": record["name"],
            "function": record["function"],
            "line": record["line"],
            "correlation_id": correlation_id_var.get(),
            "trace_id": format(span_context.trace_id, '032x') if span_context and span_context.is_valid else trace_id_var.get(),
            "span_id": format(span_context.span_id, '016x') if span_context and span_context.is_valid else None
        }

        # Add exception info if present
        if record["exception"]:
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": str(record["exception"].traceback) if record["exception"].traceback else None
            }

        # Add extra fields
        if "extra" in record:
            log_entry["extra"] = record["extra"]

        # Write to file
        with open("logs/error.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")


def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context"""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str:
    """Get correlation ID from current context"""
    return correlation_id_var.get()


def log_with_context(level: str, message: str, **kwargs):
    """Log message with additional context"""
    logger_func = getattr(logger, level.lower())
    logger_func(message, **kwargs)


# Middleware to inject correlation IDs
class CorrelationIdMiddleware:
    """FastAPI middleware to inject correlation IDs"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Get or generate correlation ID
        headers = dict(scope["headers"])
        correlation_id = headers.get(b"x-correlation-id", b"").decode()

        if not correlation_id:
            import uuid
            correlation_id = str(uuid.uuid4())

        set_correlation_id(correlation_id)

        # Add correlation ID to response headers
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                headers.append((b"x-correlation-id", correlation_id.encode()))
                message["headers"] = headers

            await send(message)

        return await self.app(scope, receive, send_wrapper)


# Global setup function
_logger_instance: StructuredLogger = None


def setup_logging(
    service_name: str = "cqox-api",
    level: str = "INFO",
    json_output: bool = True
):
    """
    Setup structured logging globally
    
    Args:
        service_name: Service name for logs
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_output: Whether to output logs as JSON
    """
    global _logger_instance
    _logger_instance = StructuredLogger(
        service_name=service_name,
        level=level,
        json_output=json_output
    )
    logger.info(f"Structured logging initialized: service={service_name}, level={level}")
    return _logger_instance


def get_logger() -> StructuredLogger:
    """Get the global logger instance"""
    if _logger_instance is None:
        setup_logging()
    return _logger_instance
