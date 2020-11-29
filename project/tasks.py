import time

import requests
from celery import chain
from celery.utils.log import get_task_logger

from project.celery_app import app

logger = get_task_logger(__name__)


class AppError(Exception):
    pass


class DB:
    def write(self, data):
        raise NotImplemented


manual_retry_counter = 0
auto_retry_counter = 0


@app.task()
def simple_one(x):
    return x


@app.task(bind=True)
def manually_retrying_task(self, x: int):
    logger.info(f"Attempting to run with {x}")
    global manual_retry_counter
    manual_retry_counter += 1
    try:
        raise AppError
    except AppError as exc:
        raise self.retry(exc=exc, max_retries=3, countdown=1)


@app.task(
    autoretry_for=(AppError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=1,
)
def auto_retrying_task(x: int):
    logger.info(f"Attempting to run with {x}")
    global auto_retry_counter
    auto_retry_counter += 1
    raise AppError


@app.task()
def first_part(url: str):
    """Fetch some data"""
    response = requests.get(url)
    time.sleep(1)  # pretend something is happening
    return response.json()["data"]


@app.task()
def second_part(data: str):
    """Do something with the result like additional processing and saving into db."""
    logger.info(f"Doing something with {data}")
    db = DB()
    time.sleep(1)  # pretend something is happening
    db.write(data)


@app.task()
def run_both(url: str):
    """A task that calls other tasks."""
    url += f"?t={int(time.time())}"
    chain(first_part.s(url), second_part.s()).delay()
