from celery import Celery
from flask import current_app

celery_app = Celery("allocar")

def init_celery(app):
    celery_app.conf.broker_url = app.config["CELERY_BROKER_URL"]
    celery_app.conf.result_backend = app.config["CELERY_RESULT_BACKEND"]
    celery_app.conf.task_serializer = "json"
    celery_app.conf.result_serializer = "json"
    celery_app.conf.accept_content = ["json"]
    celery_app.conf.timezone = "UTC"
    celery_app.conf.enable_utc = True
    return celery_app
