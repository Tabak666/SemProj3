from django.apps import AppConfig
# from django_celery_beat.models import PeriodicTask, IntervalSchedule


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"


try:
    from core.tasks import thread  
    print("Background updater thread started")
except Exception as e:
    print("Failed to start background thread:", e)