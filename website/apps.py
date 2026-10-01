from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "website"

    def ready(self):
        # Importing the module registers the signal receivers.
        # The import looks unused to flake8, hence the noqa.
        import website.signals  # noqa: F401
