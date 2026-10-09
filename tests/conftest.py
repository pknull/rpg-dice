"""Per-test wall-clock guard.

e179458 looped forever on expressions such as ``1d6r<=6``; a regression of that
kind must fail one test, not hang the suite.  Unix only (SIGALRM).
"""
import os
import signal

import pytest

TEST_TIMEOUT_SECONDS = int(os.environ.get("RPG_DICE_TEST_TIMEOUT", "120"))


@pytest.fixture(autouse=True)
def _wall_clock_guard():
    if not hasattr(signal, 'SIGALRM'):
        yield
        return

    def expire(signum, frame):
        raise TimeoutError(f'test exceeded {TEST_TIMEOUT_SECONDS} s')

    previous = signal.signal(signal.SIGALRM, expire)
    signal.alarm(TEST_TIMEOUT_SECONDS)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
