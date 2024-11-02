from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast, overload

from typing_extensions import ParamSpec

if TYPE_CHECKING:
    from openlimit.rate_limiters import RateLimiter
    from openlimit.redis_rate_limiters import RateLimiterWithRedis

    R = TypeVar("R")
    P = ParamSpec("P")


class FunctionDecorator:
    """Converts rate limiter into a function decorator."""

    def __init__(self, rate_limiter: Union[RateLimiter, RateLimiterWithRedis]):
        self.rate_limiter = rate_limiter

    @overload
    def __call__(
        self, func: Callable[P, Awaitable[R]]
    ) -> Callable[P, Awaitable[R]]: ...

    @overload
    def __call__(self, func: Callable[P, R]) -> Callable[P, R]: ...

    def __call__(
        self, func: Union[Callable[P, Awaitable[R]], Callable[P, R]]
    ) -> Union[Callable[P, Awaitable[R]], Callable[P, R]]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with self.rate_limiter.limit(**kwargs):
                return cast(Callable[P, R], func)(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            async with self.rate_limiter.limit(**kwargs):
                return await cast(Callable[P, Awaitable[R]], func)(*args, **kwargs)

        return async_wrapper if iscoroutinefunction(func) else wrapper


class ContextManager:
    """Converts rate limiter into context manager."""

    def __init__(
        self, num_tokens: int, rate_limiter: Union[RateLimiter, RateLimiterWithRedis]
    ):
        self.num_tokens = num_tokens
        self.rate_limiter = rate_limiter

    def __enter__(self):
        self.rate_limiter.wait_for_capacity_sync(self.num_tokens)

    def __exit__(self, *exc: Any):
        return False

    async def __aenter__(self):
        await self.rate_limiter.wait_for_capacity(self.num_tokens)

    async def __aexit__(self, *exc: Any):
        return False
