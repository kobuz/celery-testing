from celery import Celery

app = Celery(
    "cabbage",
    broker="redis://redis/0",
    backend="redis://redis/1",
)

app.conf.update(dict(imports=["project.tasks"]))
