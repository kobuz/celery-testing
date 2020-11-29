"""
This module demonstrates how to test tasks decorated with app's Celery instance which is most often the case.
For some reason it doesn't work external broker and backend but fortunately it does with in memory counterparts.

There are tricky parts here.
1) Celery app is initialized before tests are loaded and it's hard (or impossible?) to reconfigure it
to use in memory equivalents. So we need to set these envvars like:
export CELERY_RESULT_BACKEND=cache+memory://
export CELERY_BROKER_URL=memory://
2) You can use mock.patch for the duration of the test but worker which executes tasks in another thread
is very susceptible to this kind of code manipulation and tends to crash with unrelated error messages.
The easiest workaround I found is to use time.sleep (lol)

"""
import pytest

from project import tasks
from project.celery_app import app


@pytest.fixture(scope="session")
def celery_worker_parameters():
    return {
        "loglevel": "info",
        "perform_ping_check": False,
    }


@pytest.fixture(scope="session")
def celery_app():
    return app


def test_simple_one(celery_worker):
    task = tasks.simple_one.delay(5)

    assert task.get(timeout=3) == 5


def test_manually_retrying_task(celery_worker):
    assert tasks.manual_retry_counter == 0
    task = tasks.manually_retrying_task.delay(1)

    with pytest.raises(tasks.AppError):
        task.get(timeout=10)

    assert tasks.manual_retry_counter == 4


def test_auto_retrying_task(celery_worker):
    assert tasks.auto_retry_counter == 0
    task = tasks.auto_retrying_task.delay(1)

    with pytest.raises(tasks.AppError):
        task.get(timeout=10)

    assert tasks.auto_retry_counter == 4
