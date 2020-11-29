from celery import Celery

app = Celery(
    "cabbage",
    broker="redis://redis/0",  # both broker and backend are mentioned but not used
    backend="redis://redis/1",
)

app.conf.update(dict(imports=["project.tasks"]))
