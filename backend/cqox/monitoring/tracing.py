"""
OpenTelemetry distributed tracing

Jaeger integration for:
- Request tracing across services
- Performance profiling
- Dependency visualization
- Error tracking with context
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.trace import Status, StatusCode
from functools import wraps
from typing import Callable
from loguru import logger


class TracingConfig:
    """Tracing configuration"""
    def __init__(
        self,
        service_name: str = "cqox-engine",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831,
        sample_rate: float = 1.0
    ):
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.sample_rate = sample_rate


def setup_tracing(
    app=None,
    service_name: str = "cqox-api",
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831
):
    """
    Initialize OpenTelemetry tracing

    Sets up:
    - Jaeger exporter
    - Service resource
    - Auto-instrumentation for FastAPI, AsyncPG, Redis
    
    Args:
        app: FastAPI app instance (optional, for auto-instrumentation)
        service_name: Service name for tracing
        jaeger_host: Jaeger agent host
        jaeger_port: Jaeger agent port
    """
    # Create resource
    resource = Resource(attributes={
        SERVICE_NAME: service_name
    })

    # Create Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add span processor
    processor = BatchSpanProcessor(jaeger_exporter)
    provider.add_span_processor(processor)

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI if app is provided
    if app is not None:
        instrument_app(app)
    
    logger.info(f"OpenTelemetry tracing initialized: {jaeger_host}:{jaeger_port}")


def instrument_app(app):
    """Auto-instrument FastAPI application"""
    FastAPIInstrumentor.instrument_app(app)
    AsyncPGInstrumentor().instrument()
    RedisInstrumentor().instrument()


def get_tracer(name: str = "cqox"):
    """Get tracer instance"""
    return trace.get_tracer(name)


# Decorators for manual tracing
def trace_function(span_name: str = None):
    """Decorator to trace function execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            name = span_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(name) as span:
                try:
                    # Add function arguments as attributes
                    span.set_attribute("function.args", str(args))
                    span.set_attribute("function.kwargs", str(kwargs))

                    result = await func(*args, **kwargs)

                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            name = span_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(name) as span:
                try:
                    span.set_attribute("function.args", str(args))
                    span.set_attribute("function.kwargs", str(kwargs))

                    result = func(*args, **kwargs)

                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR))
                    span.record_exception(e)
                    raise

        # Check if function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def add_span_attributes(**attributes):
    """Add attributes to current span"""
    span = trace.get_current_span()
    for key, value in attributes.items():
        span.set_attribute(key, str(value))


def add_span_event(name: str, **attributes):
    """Add event to current span"""
    span = trace.get_current_span()
    span.add_event(name, attributes={k: str(v) for k, v in attributes.items()})
