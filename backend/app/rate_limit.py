"""Small in-memory sliding-window limiter for failed login attempts.

Limitations (by design, to keep it dependency-free):
  * State lives in one process. With several workers each has its own
    counters, and a restart clears them. For a real deployment move this to a
    shared store such as Redis.
  * The client address is taken from the TCP peer. Behind a reverse proxy
    that is the proxy's address; configure the proxy / uvicorn
    (--proxy-headers with a trusted --forwarded-allow-ips) before relying on it.
"""

import threading
import time
from collections import OrderedDict, deque


class SlidingWindowLimiter:
    def __init__(
        self,
        max_attempts: int,
        window_seconds: float,
        max_keys: int = 10_000,
        clock=time.monotonic,
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._clock = clock
        self._lock = threading.Lock()
        self._events: "OrderedDict[str, deque]" = OrderedDict()

    def _prune(self, key: str, now: float):
        events = self._events.get(key)

        if events is None:
            return None

        cutoff = now - self.window_seconds

        while events and events[0] <= cutoff:
            events.popleft()

        if not events:
            del self._events[key]
            return None

        return events

    def retry_after(self, key: str) -> int:
        """Seconds until the key may try again; 0 when it is not blocked."""
        with self._lock:
            now = self._clock()
            events = self._prune(key, now)

            if events is None or len(events) < self.max_attempts:
                return 0

            return max(1, int(events[0] + self.window_seconds - now) + 1)

    def record(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            events = self._prune(key, now)

            if events is None:
                events = deque()
                self._events[key] = events

            events.append(now)
            self._events.move_to_end(key)

            # Bound memory under a flood of distinct keys: drop the least
            # recently used ones.
            while len(self._events) > self.max_keys:
                self._events.popitem(last=False)

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


# 5 wrong passwords per account+address, and 20 failures per address, in 15 min.
# The account limit is keyed together with the address so that a stranger
# cannot lock a victim out just by failing against the victim's e-mail.
LOGIN_WINDOW_SECONDS = 15 * 60
login_account_limiter = SlidingWindowLimiter(5, LOGIN_WINDOW_SECONDS)
login_ip_limiter = SlidingWindowLimiter(20, LOGIN_WINDOW_SECONDS)


# Public sign-up runs a memory-hard Argon2 hash per request, so an unbounded
# stream of registrations is a cheap way to exhaust CPU and memory.
register_ip_limiter = SlidingWindowLimiter(10, 60 * 60)


def clear_login_limiters() -> None:
    login_account_limiter.clear()
    login_ip_limiter.clear()
    register_ip_limiter.clear()
