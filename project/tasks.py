import requests

from project.celery_app import app


class AppError(Exception):
    pass


@app.task()
def simple_one(x):
    return x


@app.task(
    autoretry_for=(AppError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=2,
)
def retrying_task():
    raise AppError


@app.task()
def first_part(url: str):
    """Fetch some data"""
    response = requests.get(url)
    return response.json()["data"]


@app.task()
def second_part(data: str):
    """Do something with the result like additional processing and saving into db."""
