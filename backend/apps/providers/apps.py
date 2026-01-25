from django.apps import AppConfig


class ProvidersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.providers'
    label = 'providers'
    verbose_name = 'Gestion des Prestataires'
    
    def ready(self):
        """Charge les signals au démarrage de l'application."""
        import apps.providers.signals  # noqa: F401
