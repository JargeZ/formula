from django.apps import AppConfig


class FormulaAdminConfig(AppConfig):
    name = "formula"
    default = True

    def ready(self):
        import formula.signals  # NOQA

        from django.conf import settings

        if settings.DATABASE_READONLY:
            from django.contrib.auth.models import update_last_login
            from django.contrib.auth.signals import user_logged_in

            user_logged_in.disconnect(
                update_last_login, dispatch_uid="update_last_login"
            )
