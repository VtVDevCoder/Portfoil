# conftest.py
import pytest
from core.celery import app as celery_app


@pytest.fixture(autouse=True)
def celery_eager(settings):
    """Force Celery to run tasks synchronously in every test."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    yield

    # Restore after test
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False
