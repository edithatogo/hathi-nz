"""Shared retry helpers for HTTP-bound pipeline operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import requests
from huggingface_hub.errors import HfHubHTTPError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

RetryableFunc = TypeVar("RetryableFunc", bound=Callable[..., Any])

_TRANSIENT_STATUS_CODES = {408, 425, 429}


def _is_transient_http_error(exc: BaseException) -> bool:
    if isinstance(exc, requests.RequestException):
        return True

    if not isinstance(exc, HfHubHTTPError):
        return False

    response = exc.response
    status_code = getattr(response, "status_code", None)
    if not isinstance(status_code, int):
        return False
    return status_code in _TRANSIENT_STATUS_CODES or status_code >= 500


def retry_on_transient_http_errors(func: RetryableFunc) -> RetryableFunc:
    """Retry transient network and hub errors with exponential backoff."""
    return retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=1.0),
        retry=retry_if_exception(_is_transient_http_error),
    )(func)
