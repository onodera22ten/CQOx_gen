"""
Input Validation and Sanitization

Features:
- Pydantic strict validation
- SQL injection prevention
- XSS protection
- Rate limiting (100 req/min per IP)
- Input sanitization
- Path traversal prevention
- Command injection prevention
"""
from typing import Any, Optional, Callable
from pydantic import BaseModel, validator, Field
from fastapi import Request, HTTPException, status
from functools import wraps
import re
import html
from loguru import logger

from cqox.storage.redis_cache import get_redis_client


class StrictString(str):
    """
    Strict string validator

    - No SQL injection patterns
    - No XSS patterns
    - No path traversal
    - No command injection
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("Must be a string")

        # Check for SQL injection patterns
        sql_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bUPDATE\b.*\bSET\b)",
            r"(\bDELETE\b.*\bFROM\b)",
            r"(--\s*$)",  # SQL comments
            r"(/\*.*\*/)",  # SQL block comments
            r"(\bEXEC\b|\bEXECUTE\b)",
            r"(;\s*DROP\b)",
            r"('\s*OR\s*'1'\s*=\s*'1)",
        ]

        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Potential SQL injection detected: {pattern}")

        # Check for XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",  # Event handlers like onclick=
            r"<iframe",
            r"<object",
            r"<embed",
            r"<applet",
        ]

        for pattern in xss_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Potential XSS detected: {pattern}")

        # Check for path traversal
        if ".." in v or "~/" in v:
            raise ValueError("Path traversal pattern detected")

        # Check for command injection
        cmd_patterns = [
            r"[;&|`$]",  # Shell metacharacters
            r"\$\(",  # Command substitution
            r"\n",  # Newlines in commands
        ]

        for pattern in cmd_patterns:
            if re.search(pattern, v):
                raise ValueError(f"Potential command injection detected: {pattern}")

        return v


class SafeEmail(str):
    """Email validator with strict RFC 5322 compliance"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("Must be a string")

        # RFC 5322 simplified email regex
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")

        if len(v) > 254:  # RFC 5321
            raise ValueError("Email too long (max 254 characters)")

        return v.lower()


class SafeURL(str):
    """URL validator with whitelist of allowed schemes"""

    ALLOWED_SCHEMES = ["http", "https"]

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("Must be a string")

        # Simple URL validation
        url_pattern = r"^(https?://)([a-zA-Z0-9.-]+)(:[0-9]+)?(/.*)?$"

        if not re.match(url_pattern, v):
            raise ValueError("Invalid URL format")

        # Check scheme
        scheme = v.split("://")[0]
        if scheme not in cls.ALLOWED_SCHEMES:
            raise ValueError(f"URL scheme must be one of {cls.ALLOWED_SCHEMES}")

        return v


class SafeFilename(str):
    """Safe filename validator (no path traversal, no special chars)"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("Must be a string")

        # Only allow alphanumeric, dash, underscore, dot
        if not re.match(r"^[a-zA-Z0-9._-]+$", v):
            raise ValueError(
                "Filename can only contain alphanumeric, dash, underscore, dot"
            )

        # No path traversal
        if ".." in v or v.startswith("."):
            raise ValueError("Invalid filename")

        # Limit length
        if len(v) > 255:
            raise ValueError("Filename too long (max 255 characters)")

        return v


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML input

    Escapes all HTML entities to prevent XSS

    Args:
        text: Input text

    Returns:
        HTML-escaped text
    """
    return html.escape(text)


def sanitize_sql_identifier(identifier: str) -> str:
    """
    Sanitize SQL identifier (table/column name)

    Only allows alphanumeric and underscore

    Args:
        identifier: SQL identifier

    Returns:
        Sanitized identifier

    Raises:
        ValueError: If identifier contains invalid characters
    """
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier):
        raise ValueError(
            f"Invalid SQL identifier: {identifier}. "
            "Only alphanumeric and underscore allowed."
        )

    # Check against SQL reserved words
    sql_reserved = {
        "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
        "ALTER", "TABLE", "FROM", "WHERE", "JOIN", "UNION"
    }

    if identifier.upper() in sql_reserved:
        raise ValueError(f"SQL reserved word cannot be used: {identifier}")

    return identifier


async def rate_limit_by_ip(
    request: Request,
    max_requests: int = 100,
    window_seconds: int = 60
) -> bool:
    """
    Rate limit by IP address

    Uses Redis sliding window algorithm

    Args:
        request: FastAPI request object
        max_requests: Maximum requests allowed (default: 100)
        window_seconds: Time window in seconds (default: 60 = 1 minute)

    Returns:
        True if within limit

    Raises:
        HTTPException: If rate limit exceeded
    """
    # Get client IP
    client_ip = request.client.host

    # Check X-Forwarded-For header (for proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    redis = await get_redis_client()

    # Use sliding window rate limiting
    allowed = await redis.sliding_window_rate_limit(
        f"ratelimit:ip:{client_ip}",
        max_requests=max_requests,
        window_seconds=window_seconds
    )

    if not allowed:
        logger.warning(
            f"Rate limit exceeded: {client_ip} "
            f"({max_requests} req/{window_seconds}s)"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {max_requests} requests per "
                   f"{window_seconds} seconds."
        )

    return True


def validate_pagination(
    page: int = 1,
    page_size: int = 50,
    max_page_size: int = 1000
) -> tuple[int, int]:
    """
    Validate pagination parameters

    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        max_page_size: Maximum allowed page size

    Returns:
        (validated_page, validated_page_size)

    Raises:
        ValueError: If parameters are invalid
    """
    if page < 1:
        raise ValueError("Page must be >= 1")

    if page_size < 1:
        raise ValueError("Page size must be >= 1")

    if page_size > max_page_size:
        raise ValueError(f"Page size must be <= {max_page_size}")

    return page, page_size


class PaginationParams(BaseModel):
    """Pagination parameters with validation"""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=1000, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate SQL offset"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """SQL limit (alias for page_size)"""
        return self.page_size


class SortParams(BaseModel):
    """Sorting parameters with validation"""

    sort_by: Optional[str] = Field(
        default=None,
        description="Field to sort by"
    )
    sort_order: Optional[str] = Field(
        default="desc",
        description="Sort order (asc or desc)"
    )

    @validator("sort_order")
    def validate_sort_order(cls, v):
        if v and v.lower() not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower() if v else "desc"

    @validator("sort_by")
    def validate_sort_by(cls, v):
        """Validate sort field is safe SQL identifier"""
        if v:
            return sanitize_sql_identifier(v)
        return v


def require_rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Decorator to enforce rate limiting on endpoints

    Usage:
        @app.get("/api/data")
        @require_rate_limit(max_requests=100, window_seconds=60)
        async def get_data(request: Request):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs or args
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise ValueError("Request object not found in arguments")

            # Check rate limit
            await rate_limit_by_ip(request, max_requests, window_seconds)

            # Call original function
            return await func(*args, **kwargs)

        return wrapper
    return decorator


class SecureInput(BaseModel):
    """
    Base model with strict validation for all inputs

    Usage:
        class UserInput(SecureInput):
            name: StrictString
            email: SafeEmail
    """

    class Config:
        # Strict mode: reject extra fields
        extra = "forbid"

        # Validate on assignment
        validate_assignment = True

        # Use enum values instead of names
        use_enum_values = True

        # Don't allow mutation after creation
        frozen = False

        # Strict types (no coercion)
        strict = True


# Example usage models
class SecureUserInput(SecureInput):
    """Example: Secure user input model"""
    name: StrictString = Field(..., min_length=1, max_length=100)
    email: SafeEmail
    website: Optional[SafeURL] = None


class SecureFileUpload(SecureInput):
    """Example: Secure file upload model"""
    filename: SafeFilename
    content_type: StrictString = Field(..., max_length=100)

    @validator("content_type")
    def validate_content_type(cls, v):
        """Whitelist allowed content types"""
        allowed_types = [
            "text/plain",
            "text/csv",
            "application/json",
            "image/png",
            "image/jpeg",
            "application/pdf"
        ]

        if v not in allowed_types:
            raise ValueError(f"Content type not allowed: {v}")

        return v


class SecureSearchQuery(SecureInput):
    """Example: Secure search query"""
    query: StrictString = Field(..., min_length=1, max_length=500)
    filters: Optional[dict] = Field(default_factory=dict)

    @validator("filters")
    def validate_filters(cls, v):
        """Validate filter keys are safe"""
        if v:
            for key in v.keys():
                sanitize_sql_identifier(key)
        return v
