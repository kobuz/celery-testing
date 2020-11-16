"""
Test canvas primitives for tasks defined as shared_task.
Not so practical because shared_task is intended for library authors but serves as a simple demonstration.

`celery_session_worker` starts a thread that will act as a worker shared between tests.
`celery_worker` can also be used but will spawn worker thread for each test
resulting in slower execution of the suite.

Shared tasks are way easier to test because they lack Celery app with specific configuration.
By default these settings are used by test app
    broker_url = 'memory://'
    result_backend = 'cache+memory://'
"""
from typing import List

import pytest
from celery import chain, chord, group, shared_task


@shared_task
def mul(x: int, y: int) -> int:
    return x * y


@shared_task
def halve_items(items: List[int]) -> List[int]:
    return [item // 2 for item in items]


@pytest.mark.usefixtures("celery_session_worker")
def test_canvas_single_delay():
    result = mul.delay(2, 3).get(timeout=3)
    assert result == 6


@pytest.mark.usefixtures("celery_session_worker")
def test_canvas_chain():
    """chain is a task with callback, e.g. (2 * 3) * 5"""
    canvas = chain(mul.s(2, 3), mul.s(5))
    result = canvas.delay().get(timeout=3)
    assert result == 30


@pytest.mark.usefixtures("celery_session_worker")
def test_canvas_group():
    """group is for parallel execution."""
    canvas = group([mul.s(2, 3), mul.s(4, 5)])
    result = canvas.delay().get(timeout=3)
    assert result == [6, 20]


@pytest.mark.usefixtures("celery_session_worker")
def test_canvas_chord():
    """chord is group with callback. Result from group becomes first argument of the callback task."""
    canvas = chord([mul.s(2, 3), mul.s(4, 5)], halve_items.s())
    result = canvas.delay().get(timeout=3)
    assert result == [3, 10]
