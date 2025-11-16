"""
Configuration Celery pour PRESSO
"""
import os
from celery import Celery
from celery.schedules import crontab

# Définir le module de settings Django par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Créer l'application Celery
app = Celery('presso')

# Charger la configuration depuis Django settings avec le namespace CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-découverte des tâches dans TOUTES les apps Django
# Celery cherchera un fichier tasks.py dans chacune de ces apps
app.autodiscover_tasks(lambda: [
    'apps.core',
    'apps.api',
    'apps.users',
    'apps.providers',
    'apps.services',
    'apps.tariffs',
    'apps.orders',
    'apps.order_items',
    'apps.payments',
    'apps.reviews',
])

# Configuration des tâches planifiées (Celery Beat)
app.conf.beat_schedule = {
    # Nettoyer les OTP expirés toutes les 30 minutes
    'clean-expired-otp': {
        'task': 'apps.core.tasks.clean_expired_otp',
        'schedule': crontab(minute='*/30'),
    },
    # Nettoyer les tokens JWT blacklistés expirés (1x par jour à 3h du matin)
    'clean-expired-tokens': {
        'task': 'apps.core.tasks.clean_expired_tokens',
        'schedule': crontab(hour=3, minute=0),
    },
    # Générer des rapports quotidiens (1x par jour à 6h du matin)
    'generate-daily-reports': {
        'task': 'apps.core.tasks.generate_daily_reports',
        'schedule': crontab(hour=6, minute=0),
    },
}

# Configuration supplémentaire
app.conf.update(
    # Fuseau horaire
    timezone='Africa/Abidjan',
    enable_utc=True,
    
    # Sérialisation
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Résultats
    result_extended=True,
    result_expires=3600,  # 1 heure
    
    # Contrôle des tâches
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max par tâche
    task_soft_time_limit=240,  # Warning à 4 minutes
    
    # Retry
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker
    worker_prefetch_multiplier=2,
    worker_max_tasks_per_child=1000,  # Redémarrer worker après 1000 tâches
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tâche de debug pour tester Celery"""
    print(f'Request: {self.request!r}')

