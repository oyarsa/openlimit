import time
import typing

import redis.asyncio.client
import redis.asyncio.lock


class RedisBucket:
    def __init__(
        self,
        rate_limit: int,
        bucket_key: str,
        redis: redis.asyncio.Redis,
        bucket_size_in_seconds: float = 1,
    ):
        # Per-second rate limit
        self._rate_per_sec = rate_limit / 60

        # The integration time of the bucket
        self._bucket_size_in_seconds = bucket_size_in_seconds

        # Redis
        self._redis = redis
        self._bucket_key = bucket_key

    def lock(self, **kwargs: typing.Any) -> redis.asyncio.lock.Lock:
        return redis.asyncio.lock.Lock(
            self._redis, f"{self._bucket_key}:lock", **kwargs
        )

    async def get_capacity(
        self,
        pipeline: typing.Optional[redis.asyncio.client.Pipeline] = None,
        current_time: typing.Optional[float] = None,
    ) -> float:
        if pipeline is None:
            pipeline = self._redis.pipeline()

        pipeline.get(f"{self._bucket_key}:last_checked")
        pipeline.get(f"{self._bucket_key}:capacity")

        if current_time is None:
            current_time = time.time()

        last_checked, capacity = await pipeline.execute()  # type: ignore
        assert isinstance(last_checked, float)
        assert isinstance(capacity, float)

        if not last_checked or not capacity:
            last_checked = current_time
            capacity = self._rate_per_sec * self._bucket_size_in_seconds

        time_passed = current_time - float(last_checked)
        new_capacity = min(
            self._rate_per_sec * self._bucket_size_in_seconds,
            float(capacity) + time_passed * self._rate_per_sec,
        )

        return new_capacity

    async def set_capacity(
        self,
        new_capacity: float,
        pipeline: typing.Optional[redis.asyncio.client.Pipeline] = None,
        current_time: typing.Optional[float] = None,
        execute: bool = True,
    ) -> None:
        if pipeline is None:
            pipeline = self._redis.pipeline()

        if current_time is None:
            current_time = time.time()

        pipeline.set(f"{self._bucket_key}:last_checked", current_time)
        pipeline.set(f"{self._bucket_key}:capacity", new_capacity)

        if execute:
            await pipeline.execute()
