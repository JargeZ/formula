from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DemoConfig(AppConfig):
    name = "demo"
    verbose_name = _("Demo")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Registers the demo tasks, so the Celery Beat admin lists them
        from demo import tasks  # noqa: F401
