import os
from celery import Celery

# Define o módulo de configurações padrão do Django para o Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Lê as configurações do Django usando o prefixo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carrega automaticamente as tasks de todos os apps instalados (busca por tasks.py)  # noqa: E501
app.autodiscover_tasks()
