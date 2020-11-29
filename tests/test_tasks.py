"""
This module demonstrates how to test tasks decorated with project's Celery instance which is most often the case.
For some reason it doesn't work well with external broker and backend but fortunately it does
with in memory counterparts which are also faster and let run tests in more isolation.

There are tricky parts here.
1) Celery app is initialized before tests are loaded and it's hard (or impossible?) to reconfigure it
to use in memory equivalents of broker and result backend.
So before running integration tests we need to set these envvars like:

export CELERY_RESULT_BACKEND=cache+memory://
export CELERY_BROKER_URL=memory://

There are many ways pytest can handle that: skipif marker, custom marker, calling this module explicitely
with `pytest path/to/test_module`.

2) You can use `mock.patch` for the duration of the test. However worker which executes tasks in another thread
is very susceptible to this kind of code manipulation and tends to crash with unrelated error messages.
That's because it waits only for the first task to finish and ignores the rest (no thread join or whatsoever).
In case this task calls some children tasks then they are no longer under the charm of patch.
The easiest workaround I found is to use time.sleep (lol) for expected duration of the tasks + some empirically
found value.

3) celery_session_worker is a lot faster than celery_worker but keep in mind it's reused by tests from different
modules.
"""
import time
from unittest import mock

import pytest
import responses

from project import tasks
from project.celery_app import app


@pytest.fixture(scope="session")
def celery_worker_parameters():
    return {
        "loglevel": "info",
        "perform_ping_check": False,
    }


@pytest.fixture(scope="session")
def celery_session_app():
    # this app is already configured and doesn't allow to be changed, look at docstring point 1)
    return app


def test_simple_one(celery_session_worker):
    task = tasks.simple_one.delay(5)

    assert task.get(timeout=3) == 5


def test_manually_retrying_task(celery_session_worker):
    assert tasks.manual_retry_counter == 0
    task = tasks.manually_retrying_task.delay(1)

    with pytest.raises(tasks.AppError):
        task.get(timeout=10)

    assert tasks.manual_retry_counter == 4


def test_auto_retrying_task(celery_session_worker):
    assert tasks.auto_retry_counter == 0
    task = tasks.auto_retrying_task.delay(1)

    with pytest.raises(tasks.AppError):
        task.get(timeout=10)

    assert tasks.auto_retry_counter == 4


@pytest.fixture
def mock_requests():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mock_db():
    """The implementation in tasks.py would end with an error."""
    db = mock.Mock(spec=tasks.DB)
    with mock.patch("project.tasks.DB", return_value=db):
        yield db


def test_run_both(celery_session_worker, mock_requests, mock_db):
    mock_requests.add(
        responses.GET,
        "http://example.com",
        match_querystring=False,
        json={"data": "something interesting"},
    )
    task = tasks.run_both.delay("http://example.com")
    # now with shorter sleep period it fails and the longer `task.get timeout` doesn't help
    # check module docstring point 2) to see why
    time.sleep(3)
    task.get(timeout=3)
    mock_db.write.assert_called_once_with("something interesting")
