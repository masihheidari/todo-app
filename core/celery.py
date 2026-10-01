import os

from celery import Celery

# Tell Celery which Django settings module to use (when not already set)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
# Read every setting that starts with CELERY_ from Django settings
# (e.g. CELERY_BROKER_URL -> broker_url)
app.config_from_object("django.conf:settings", namespace="CELERY")
# Find tasks.py in each installed app (e.g. users/tasks.py) automatically
app.autodiscover_tasks()
