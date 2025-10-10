from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    label = 'users'  # Label sans point pour les références
    verbose_name = 'Gestion des Utilisateurs'
