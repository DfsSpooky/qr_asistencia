from django import forms
from .models import Usuario, Asistencia, Evento
from django.core.exceptions import ValidationError

class FiltroAsistenciaForm(forms.Form):
    dni = forms.CharField(required=False, label='DNI', widget=forms.TextInput(attrs={'class': 'form-control'}))
    fecha = forms.DateField(required=False, label='Fecha', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    evento = forms.ModelChoiceField(queryset=Evento.objects.all(), required=False, label='Evento', widget=forms.Select(attrs={'class': 'form-select'}))
    estado = forms.ChoiceField(
        choices=[('', 'Todos'), ('asistieron', 'Asistieron'), ('faltaron', 'Faltaron')],
        required=False,
        label='Estado',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class ImportarUsuariosForm(forms.Form):
    archivo_csv = forms.FileField(label='Archivo CSV')

class BuscarUsuarioForm(forms.Form):
    query = forms.CharField(required=False, label='Buscar', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar por nombre, apellido o DNI'}))

class UsuarioRegistroForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Contraseña')
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Confirmar Contraseña')

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'dni', 'foto_perfil']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        foto_perfil = cleaned_data.get('foto_perfil')

        if password != password_confirm:
            raise ValidationError("Las contraseñas no coinciden.")

        # Validar la foto de perfil (si se proporciona)
        if foto_perfil:
            # Validar el tamaño (máximo 2 MB)
            max_size = 2 * 1024 * 1024  # 2 MB en bytes
            if foto_perfil.size > max_size:
                raise ValidationError({'foto_perfil': 'La imagen no debe exceder los 2 MB.'})

            # Validar el tipo de archivo (solo JPEG y PNG)
            if not foto_perfil.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValidationError({'foto_perfil': 'Solo se permiten archivos JPEG y PNG.'})

        return cleaned_data