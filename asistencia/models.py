from django.db import models
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
import qrcode
from io import BytesIO
import base64
import re
from django.contrib.auth.models import User
from PIL import Image

class Ubicacion(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

class Evento(models.Model):
    nombre = models.CharField(max_length=100)
    fecha = models.DateField()
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.fecha})"

class Usuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    foto_perfil = models.ImageField(upload_to='perfil_fotos/', blank=True, null=True)

    def clean(self):
        if not self.dni.isdigit() or len(self.dni) != 8:
            raise ValidationError({'dni': 'El DNI debe tener exactamente 8 dígitos numéricos.'})
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', self.nombre):
            raise ValidationError({'nombre': 'El nombre solo puede contener letras y espacios.'})
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', self.apellido):
            raise ValidationError({'apellido': 'El apellido solo puede contener letras y espacios.'})

    def save(self, *args, **kwargs):
        self.full_clean()

        # Procesar la foto de perfil si se proporciona
        if self.foto_perfil:
            try:
                # Abrir la imagen con Pillow
                img = Image.open(self.foto_perfil)
                img = img.convert('RGB')  # Convertir a RGB para manejar imágenes PNG/JPEG

                # Reescalar la imagen a 200x200 píxeles
                img = img.resize((200, 200), Image.Resampling.LANCZOS)

                # Guardar la imagen comprimida en un buffer
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=70)  # Comprimir con calidad 70
                buffer.seek(0)

                # Actualizar el campo foto_perfil con la imagen comprimida
                self.foto_perfil.save(
                    f'perfil_{self.dni}.jpg',
                    ContentFile(buffer.getvalue()),
                    save=False
                )
            except Exception as e:
                # Si hay un error al procesar la imagen, usar la imagen por defecto
                self.foto_perfil = 'images/default_avatar.png'

        # Si no se proporciona foto, usar la imagen por defecto
        if not self.foto_perfil:
            self.foto_perfil = 'images/default_avatar.png'

        # Generar el código QR
        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        encoded_dni = base64.b64encode(self.dni.encode()).decode()
        qr.add_data(encoded_dni)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG', quality=70)
        self.qr_code.save(f'qr_{self.dni}.png', ContentFile(buffer.getvalue()), save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.dni})"

    class Meta:
        permissions = [
            ("can_manage_users", "Can manage users"),
            ("can_scan_qr", "Can scan QR codes"),
        ]
        indexes = [
            models.Index(fields=['dni']),
        ]

class Asistencia(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True)
    evento = models.ForeignKey(Evento, on_delete=models.SET_NULL, null=True, blank=True)
    confirmada = models.BooleanField(default=False)

    def __str__(self):
        return f"Asistencia de {self.usuario} el {self.fecha} {'(Confirmada)' if self.confirmada else ''}"

    class Meta:
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['usuario']),
            models.Index(fields=['evento']),
        ]

class LogAccion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.accion} por {self.usuario} el {self.fecha}"

    class Meta:
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['usuario']),
        ]