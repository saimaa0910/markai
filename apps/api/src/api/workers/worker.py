from api.worker.celery_app import celery_app


def run_worker_daemon() -> None:
    """
    Initialize background worker process daemon.
    """
    celery_app.worker_main(argv=["worker", "--loglevel=info"])

