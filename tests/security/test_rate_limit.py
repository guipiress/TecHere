from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from backend.app.rate_limit import (
    SlidingWindowLimiter,
    clear_login_limiters,
    login_account_limiter,
    login_ip_limiter,
    reserve_login_attempt,
)

class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make_limiter(max_attempts=3, window=60, max_keys=10_000):
    clock = FakeClock()
    limiter = SlidingWindowLimiter(
        max_attempts, window, max_keys=max_keys, clock=clock
    )
    return limiter, clock


def test_not_blocked_before_the_limit():
    limiter, _ = make_limiter(max_attempts=3)

    limiter.record("a")
    limiter.record("a")

    assert limiter.retry_after("a") == 0


def test_blocked_when_the_limit_is_reached():
    limiter, _ = make_limiter(max_attempts=3)

    for _ in range(3):
        limiter.record("a")

    assert limiter.retry_after("a") > 0


def test_retry_after_never_exceeds_the_window():
    limiter, _ = make_limiter(max_attempts=3, window=60)

    for _ in range(3):
        limiter.record("a")

    assert 1 <= limiter.retry_after("a") <= 61


def test_unblocked_after_the_window_passes():
    limiter, clock = make_limiter(max_attempts=3, window=60)

    for _ in range(3):
        limiter.record("a")

    clock.advance(61)

    assert limiter.retry_after("a") == 0


def test_window_slides_instead_of_resetting_all_at_once():
    limiter, clock = make_limiter(max_attempts=3, window=60)

    limiter.record("a")      # t = 0
    clock.advance(30)
    limiter.record("a")      # t = 30
    limiter.record("a")      # t = 30 -> blocked
    assert limiter.retry_after("a") > 0

    clock.advance(31)        # t = 61: the first event expired, two remain
    assert limiter.retry_after("a") == 0


def test_keys_are_independent():
    limiter, _ = make_limiter(max_attempts=2)

    limiter.record("victim")
    limiter.record("victim")

    assert limiter.retry_after("victim") > 0
    assert limiter.retry_after("someone-else") == 0


def test_reset_clears_only_that_key():
    limiter, _ = make_limiter(max_attempts=1)

    limiter.record("a")
    limiter.record("b")
    limiter.reset("a")

    assert limiter.retry_after("a") == 0
    assert limiter.retry_after("b") > 0


def test_clear_removes_everything():
    limiter, _ = make_limiter(max_attempts=1)

    limiter.record("a")
    limiter.record("b")
    limiter.clear()

    assert limiter.retry_after("a") == 0
    assert limiter.retry_after("b") == 0


def test_memory_is_bounded_under_many_distinct_keys():
    limiter, _ = make_limiter(max_attempts=3, max_keys=100)

    for i in range(1000):
        limiter.record(f"key-{i}")

    assert len(limiter._events) <= 100


def test_expired_keys_are_dropped():
    limiter, clock = make_limiter(max_attempts=3, window=60)

    limiter.record("a")
    clock.advance(61)
    limiter.retry_after("a")

    assert "a" not in limiter._events


def test_concurrent_login_reservations_do_not_exceed_account_limit():
    clear_login_limiters()

    workers = 20
    barrier = Barrier(workers)

    def attempt():
        barrier.wait()

        reservation, retry_after = reserve_login_attempt(
            "127.0.0.1",
            "127.0.0.1|teste@example.com",
        )

        if reservation is not None:
            reservation.keep()

        return reservation is not None, retry_after

    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(lambda _: attempt(), range(workers)))

        accepted = sum(1 for success, _ in results if success)
        blocked = sum(1 for success, _ in results if not success)

        assert accepted == 5
        assert blocked == 15

    finally:
        clear_login_limiters()


def test_success_does_not_remove_another_pending_reservation():
    clear_login_limiters()

    ip = "127.0.0.1"
    account_key = f"{ip}|teste@example.com"

    try:
        # Três falhas anteriores na conta.
        for _ in range(3):
            login_account_limiter.record(account_key)

        # Duas requisições conseguem reservar as duas vagas restantes.
        first, retry_after = reserve_login_attempt(ip, account_key)
        assert first is not None
        assert retry_after == 0

        second, retry_after = reserve_login_attempt(ip, account_key)
        assert second is not None
        assert retry_after == 0

        # A primeira autenticação tem sucesso.
        first.succeed()

        # A reserva da segunda requisição deve continuar existindo.
        events = login_account_limiter._events[account_key]

        assert len(events) == 1
        assert events[0].confirmed is False

        # A segunda autenticação falha.
        second.keep()

        events = login_account_limiter._events[account_key]

        assert len(events) == 1
        assert events[0].confirmed is True

    finally:
        clear_login_limiters()


def test_release_removes_only_its_own_reservations():
    clear_login_limiters()

    ip = "127.0.0.1"
    account_key = f"{ip}|teste@example.com"

    try:
        first, _ = reserve_login_attempt(ip, account_key)
        second, _ = reserve_login_attempt(ip, account_key)

        assert first is not None
        assert second is not None

        # Simula uma exceção durante o processamento da primeira requisição.
        first.release()

        ip_events = login_ip_limiter._events[ip]
        account_events = login_account_limiter._events[account_key]

        assert len(ip_events) == 1
        assert len(account_events) == 1

        # A segunda reserva continua válida.
        second.keep()

        assert login_ip_limiter.retry_after(ip) == 0
        assert login_account_limiter.retry_after(account_key) == 0

        assert login_ip_limiter._events[ip][0].confirmed is True
        assert login_account_limiter._events[account_key][0].confirmed is True

    finally:
        clear_login_limiters()


def test_concurrent_login_reservations_do_not_exceed_ip_limit():
    clear_login_limiters()

    workers = 30
    barrier = Barrier(workers)
    ip = "127.0.0.1"

    def attempt(index):
        barrier.wait()

        reservation, retry_after = reserve_login_attempt(
            ip,
            f"{ip}|user{index}@example.com",
        )

        if reservation is not None:
            reservation.keep()

        return reservation is not None, retry_after

    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(
                executor.map(attempt, range(workers))
            )

        accepted = sum(1 for success, _ in results if success)
        blocked = sum(1 for success, _ in results if not success)

        assert accepted == 20
        assert blocked == 10

    finally:
        clear_login_limiters()