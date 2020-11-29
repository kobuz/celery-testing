set -xe
pytest -s tests/test_shared_task.py
export CELERY_RESULT_BACKEND=cache+memory://
export CELERY_BROKER_URL=memory://
pytest -s tests/test_tasks.py
set +xe
