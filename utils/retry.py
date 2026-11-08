"""
Retry wrapper for litellm calls. Covers dropped connections and transient timeouts.
Used directly by tools that call litellm themselves (e.g. ViewImageTool).
Global litellm.num_retries covers CrewAI's managed LLM calls — set in token_logger.py.
"""

import asyncio
import logging
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
import litellm
from litellm.exceptions import APIConnectionError, ServiceUnavailableError, Timeout

logger = logging.getLogger(__name__)

_RETRYABLE = (APIConnectionError, ServiceUnavailableError, Timeout, OSError, ConnectionError)

_retry = retry(
    retry=retry_if_exception_type(_RETRYABLE),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


@_retry
def completion_with_retry(**kwargs):
    return litellm.completion(**kwargs)


@_retry
async def acompletion_with_retry(**kwargs):
    return await litellm.acompletion(**kwargs)
