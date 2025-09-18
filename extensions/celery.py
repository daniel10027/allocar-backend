from celery import Celery
from flask import Flask

celery_app = Celery("allocar")

def init_celery(app: Flask):
    # Broker / backend / sérialisation
    celery_app.conf.broker_url = app.config["CELERY_BROKER_URL"]
    celery_app.conf.result_backend = app.config["CELERY_RESULT_BACKEND"]
    celery_app.conf.task_serializer = "json"
    celery_app.conf.result_serializer = "json"
    celery_app.conf.accept_content = ["json"]
    celery_app.conf.timezone = "UTC"
    celery_app.conf.enable_utc = True


    class AppContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = AppContextTask
    return celery_app
