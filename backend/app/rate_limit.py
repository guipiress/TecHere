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
from dataclasses import dataclass


@dataclass
class LoginEvent:
    timestamp: float
    event_id: object
    confirmed: bool


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

        while events and events[0].timestamp <= cutoff:
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

            return max(
                1,
                int(events[0].timestamp + self.window_seconds - now) + 1,
            )

    def _add_event(self, key: str, confirmed: bool) -> object:
        now = self._clock()
        events = self._prune(key, now)

        if events is None:
            events = deque()
            self._events[key] = events

        event_id = object()

        events.append(
            LoginEvent(
                timestamp=now,
                event_id=event_id,
                confirmed=confirmed,
            )
        )

        self._events.move_to_end(key)

        while len(self._events) > self.max_keys:
            self._events.popitem(last=False)

        return event_id

    def record(self, key: str) -> object:
        """Record a confirmed failed attempt."""
        with self._lock:
            return self._add_event(key, confirmed=True)

    def reserve_event(self, key: str) -> object:
        """Create a provisional event for an ongoing login."""
        with self._lock:
            return self._add_event(key, confirmed=False)

    def confirm_event(self, key: str, event_id: object) -> None:
        """Turn a provisional event into a confirmed failure."""
        with self._lock:
            events = self._events.get(key)

            if events is None:
                return

            for event in events:
                if event.event_id is event_id:
                    event.confirmed = True
                    return

    def remove_event(self, key: str, event_id: object) -> None:
        """Remove exactly one event, identified by its unique ID."""
        with self._lock:
            events = self._events.get(key)

            if events is None:
                return

            remaining = deque(
                event for event in events
                if event.event_id is not event_id
            )

            if remaining:
                self._events[key] = remaining
            else:
                del self._events[key]

    def reset_confirmed(self, key: str) -> None:
        """Remove failed attempts without removing pending reservations."""
        with self._lock:
            events = self._events.get(key)

            if events is None:
                return

            remaining = deque(
                event for event in events
                if not event.confirmed
            )

            if remaining:
                self._events[key] = remaining
            else:
                del self._events[key]

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


_login_reservation_lock = threading.Lock()


class LoginReservation:
    def __init__(
        self,
        ip: str,
        account_key: str,
        ip_event_id: object,
        account_event_id: object,
    ):
        self.ip = ip
        self.account_key = account_key
        self.ip_event_id = ip_event_id
        self.account_event_id = account_event_id
        self._finished = False

    def keep(self) -> None:
        """Keep both events after an authentication failure."""
        with _login_reservation_lock:
            if self._finished:
                return

            login_ip_limiter.confirm_event(
                self.ip,
                self.ip_event_id,
            )
            login_account_limiter.confirm_event(
                self.account_key,
                self.account_event_id,
            )

            self._finished = True

    def succeed(self) -> None:
        """Release reservations after successful authentication."""
        with _login_reservation_lock:
            if self._finished:
                return

            login_ip_limiter.remove_event(
                self.ip,
                self.ip_event_id,
            )
            login_account_limiter.remove_event(
                self.account_key,
                self.account_event_id,
            )

            login_account_limiter.reset_confirmed(self.account_key)

            self._finished = True

    def release(self) -> None:
        """Release both reservations if processing fails."""
        with _login_reservation_lock:
            if self._finished:
                return

            login_ip_limiter.remove_event(
                self.ip,
                self.ip_event_id,
            )
            login_account_limiter.remove_event(
                self.account_key,
                self.account_event_id,
            )

            self._finished = True


def reserve_login_attempt(
    ip: str,
    account_key: str,
) -> tuple[LoginReservation | None, int]:
    """Atomically check and reserve capacity in both login limiters."""
    with _login_reservation_lock:
        retry_after = max(
            login_ip_limiter.retry_after(ip),
            login_account_limiter.retry_after(account_key),
        )

        if retry_after:
            return None, retry_after

        ip_event_id = login_ip_limiter.reserve_event(ip)
        account_event_id = login_account_limiter.reserve_event(account_key)

        return (
            LoginReservation(
                ip,
                account_key,
                ip_event_id,
                account_event_id,
            ),
            0,
        )