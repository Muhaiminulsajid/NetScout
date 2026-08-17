from celery import Celery

from .config import settings

celery_app = Celery(
    "netscout",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.webgraph_tasks", "app.tasks.imagetrace_tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_max_tasks_per_child=25,  # Playwright hygiene
)
