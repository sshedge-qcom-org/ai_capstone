import time
from collections import OrderedDict, deque
from threading import Lock


class LoginLimiter:
    """Bounded single-instance IP throttle; deploy proxy limits as a second layer."""

    def __init__(self):
        self.buckets: OrderedDict[str, deque[float]] = OrderedDict()
        self.lock = Lock()

    def allow(self, key: str, limit: int) -> bool:
        now = time.monotonic()
        with self.lock:
            bucket = self.buckets.setdefault(key, deque())
            self.buckets.move_to_end(key)
            while bucket and bucket[0] <= now - 60:
                bucket.popleft()
            if len(self.buckets) > 10000:
                self.buckets.popitem(last=False)
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True


login_limiter = LoginLimiter()
