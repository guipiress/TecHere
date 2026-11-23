from backend.app.rate_limit import SlidingWindowLimiter


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
