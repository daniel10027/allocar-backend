from app import create_app
from extensions.celery import init_celery, celery_app


flask_app = create_app()
init_celery(flask_app)

import domain.users.tasks  # noqa: F401
