from __future__ import annotations

import time
from typing import Optional


class Bucket:
    def __init__(self, rate_limit: float, bucket_size_in_seconds: float = 1) -> None:
        # Per-second rate limit
        self._rate_per_sec = rate_limit / 60

        # Capacity of the bucket
        self._capacity = rate_limit / 60 * bucket_size_in_seconds

        # The integration time of the bucket
        self._bucket_size_in_seconds = bucket_size_in_seconds

        # Last time the bucket capacity was checked
        self._last_checked = time.time()

    def get_capacity(self, current_time: Optional[float] = None) -> float:
        if current_time is None:
            current_time = time.time()

        assert self._last_checked is not None, "Capacity checked before set"
        time_passed = current_time - self._last_checked

        new_capacity = min(
            self._rate_per_sec * self._bucket_size_in_seconds,
            self._capacity + time_passed * self._rate_per_sec,
        )

        return new_capacity

    def set_capacity(
        self, new_capacity: float, current_time: Optional[float] = None
    ) -> None:
        self._last_checked = current_time
        self._capacity = new_capacity
