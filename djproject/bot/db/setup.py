import os
import sys
import django

# Настройка окружения Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(BASE_DIR))
sys.path.append(os.path.join(os.path.dirname(BASE_DIR), 'djproject'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djproject.djproject.settings')
django.setup()