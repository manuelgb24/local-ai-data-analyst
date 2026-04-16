"""Public exports for operational readiness and local product observability."""

from .errors import (
    ERROR_CATEGORY_CORE,
    ERROR_CATEGORY_DATASET,
    ERROR_CATEGORY_PROVIDER,
    ERROR_CATEGORY_REQUEST,
    build_api_error_details,
    classify_run_error,
    ensure_error_category,
)
from .logging import (
    JsonLogFormatter,
    bind_context,
    bound_context,
    clear_context,
    configure_structured_logging,
    current_context,
    generate_trace_id,
    get_logger,
    log_event,
    reset_context,
)
from .models import AppConfig, ApplicationHealth, HealthStatus, ProveedorHealth, ReadinessReport
from .service import (
    DEFAULT_PROVIDER_NAME,
    DEFAULT_PROVIDER_TIMEOUT_SECONDS,
    OperationalReadinessService,
    build_default_operational_readiness_service,
)

__all__ = [
    "AppConfig",
    "ApplicationHealth",
    "DEFAULT_PROVIDER_NAME",
    "DEFAULT_PROVIDER_TIMEOUT_SECONDS",
    "ERROR_CATEGORY_CORE",
    "ERROR_CATEGORY_DATASET",
    "ERROR_CATEGORY_PROVIDER",
    "ERROR_CATEGORY_REQUEST",
    "HealthStatus",
    "JsonLogFormatter",
    "OperationalReadinessService",
    "ProveedorHealth",
    "ReadinessReport",
    "bind_context",
    "bound_context",
    "build_api_error_details",
    "classify_run_error",
    "clear_context",
    "configure_structured_logging",
    "current_context",
    "ensure_error_category",
    "generate_trace_id",
    "get_logger",
    "log_event",
    "reset_context",
    "build_default_operational_readiness_service",
]
