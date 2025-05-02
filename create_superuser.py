import os
import django

# Configura el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qr_asistencia.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Define las credenciales del superuser
username = 'admin'
email = 'admin@example.com'
password = ',123456%'

# Crea el superuser si no existe
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser {username} creado exitosamente.')
else:
    print(f'El superuser {username} ya existe.')