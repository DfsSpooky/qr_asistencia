#!/bin/bash
echo "Iniciando script de despliegue..."
echo "Aplicando migraciones..."
python manage.py migrate --noinput
if [ $? -eq 0 ]; then
    echo "Migraciones aplicadas exitosamente"
else
    echo "Error al aplicar migraciones"
    exit 1
fi
echo "Creando superusuario..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('miguel', 'admin@example.com', '123456') if not User.objects.filter(username='admin').exists() else None"
if [ $? -eq 0 ]; then
    echo "Superusuario creado exitosamente"
else
    echo "Error al crear superusuario"
    exit 1
fi
echo "Iniciando Gunicorn..."
exec gunicorn qr_asistencia.wsgi:application --log-file -