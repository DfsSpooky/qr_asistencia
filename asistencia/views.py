from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from .models import Usuario, Asistencia, Ubicacion, Evento, LogAccion
from .forms import FiltroAsistenciaForm, ImportarUsuariosForm, BuscarUsuarioForm, UsuarioRegistroForm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from datetime import date
import base64
from weasyprint import HTML
import csv
from io import TextIOWrapper
from django.db import models
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_protect

def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('lista_usuarios')
    return redirect('perfil_usuario')

class CustomLoginView(LoginView):
    template_name = 'asistencia/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['can_scan_qr'] = user.is_authenticated and user.has_perm('asistencia.can_scan_qr')
        return context

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return '/lista_usuarios/'
            else:
                return '/perfil/'
        return '/login/'

def custom_login(request):
    return CustomLoginView.as_view()(request)

@require_GET
@csrf_protect
def custom_logout(request):
    logout(request)
    return redirect('login')

@login_required
@permission_required('asistencia.can_manage_users', raise_exception=True)
def lista_usuarios(request):
    form = BuscarUsuarioForm(request.GET or None)
    usuarios = Usuario.objects.all().order_by('dni')
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        if query:
            usuarios = usuarios.filter(
                models.Q(nombre__icontains=query) |
                models.Q(apellido__icontains=query) |
                models.Q(dni__icontains=query)
            )
    
    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'can_scan_qr': request.user.has_perm('asistencia.can_scan_qr')
    }
    return render(request, 'asistencia/lista_usuarios.html', context)

@login_required
@permission_required('asistencia.can_manage_users', raise_exception=True)
def detalle_usuario(request, dni):
    usuario = get_object_or_404(Usuario, dni=dni)
    context = {
        'usuario': usuario,
        'can_scan_qr': request.user.has_perm('asistencia.can_scan_qr')
    }
    return render(request, 'asistencia/detalle_usuario.html', context)

@login_required
@permission_required('asistencia.can_scan_qr', raise_exception=True)
def escanear_qr(request):
    ubicaciones = Ubicacion.objects.all()
    eventos = Evento.objects.filter(activo=True)
    context = {
        'ubicaciones': ubicaciones,
        'eventos': eventos,
        'can_scan_qr': request.user.has_perm('asistencia.can_scan_qr')
    }
    return render(request, 'asistencia/escanear.html', context)

@method_decorator(csrf_exempt, name='dispatch')
@permission_classes([IsAuthenticated])
class RegistrarAsistencia(APIView):
    def post(self, request):
        print("Usuario autenticado:", request.user)
        print("¿Está autenticado?:", request.user.is_authenticated)
        if not request.user.is_authenticated:
            print("Error: El usuario no está autenticado.")
            return Response({'error': 'No estás autenticado. Por favor, inicia sesión.'}, status=status.HTTP_403_FORBIDDEN)
        
        print("Solicitud POST recibida:", request.data)
        encoded_dni = request.data.get('dni')
        ubicacion_id = request.data.get('ubicacion_id')
        evento_id = request.data.get('evento_id')
        try:
            dni = base64.b64decode(encoded_dni).decode()
            print("DNI decodificado:", dni)
            usuario = Usuario.objects.get(dni=dni)
            today = date.today()
            evento = Evento.objects.get(id=evento_id, activo=True) if evento_id else None
            if evento and evento.fecha != today:
                return Response({
                    'error': f'El evento {evento.nombre} no está programado para hoy.'
                }, status=status.HTTP_400_BAD_REQUEST)
            existing_asistencia = Asistencia.objects.filter(
                usuario=usuario,
                fecha__date=today,
                evento=evento
            ).first()
            if existing_asistencia:
                return Response({
                    'error': f'{usuario.nombre} {usuario.apellido} ya registró su asistencia para el evento {evento.nombre} hoy a las {existing_asistencia.fecha}.'
                }, status=status.HTTP_400_BAD_REQUEST)
            ubicacion = Ubicacion.objects.get(id=ubicacion_id) if ubicacion_id else None
            asistencia = Asistencia.objects.create(usuario=usuario, ubicacion=ubicacion, evento=evento)

            LogAccion.objects.create(
                usuario=request.user,
                accion="Registrar asistencia",
                descripcion=f"{request.user.username} registró asistencia para {usuario.nombre} {usuario.apellido} en el evento {(evento.nombre if evento else 'sin evento')}."
            )

            return Response({
                'message': f'Asistencia registrada para {usuario.nombre} {usuario.apellido} en el evento {evento.nombre if evento else 'sin evento'} con éxito.',
                'fecha': asistencia.fecha
            }, status=status.HTTP_201_CREATED)
        except Usuario.DoesNotExist:
            print("Error: Usuario no encontrado")
            return Response({'error': 'El DNI escaneado no corresponde a ningún usuario registrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Evento.DoesNotExist:
            print("Error: Evento no encontrado o no activo")
            return Response({'error': 'El evento seleccionado no es válido o no está activo.'}, status=status.HTTP_400_BAD_REQUEST)
        except Ubicacion.DoesNotExist:
            print("Error: Ubicación no encontrada")
            return Response({'error': 'La ubicación seleccionada no es válida.'}, status=status.HTTP_400_BAD_REQUEST)
        except base64.binascii.Error:
            print("Error: QR inválido")
            return Response({'error': 'El código QR escaneado es inválido.'}, status=status.HTTP_400_BAD_REQUEST)

@login_required
@cache_page(60 * 5)
def historial_asistencias(request):
    form = FiltroAsistenciaForm(request.GET or None)
    asistencias = Asistencia.objects.all().order_by('-fecha')
    usuarios_no_asistentes = None
    
    if form.is_valid():
        dni = form.cleaned_data.get('dni')
        fecha = form.cleaned_data.get('fecha')
        evento = form.cleaned_data.get('evento')
        estado = form.cleaned_data.get('estado')
        print("Filtro aplicado - DNI:", dni, "Fecha:", fecha, "Evento ID:", form.cleaned_data.get('evento'), "Estado:", estado)
        
        if dni:
            asistencias = asistencias.filter(usuario__dni__contains=dni)
        if fecha:
            asistencias = asistencias.filter(fecha__date=fecha)
        if evento:
            asistencias = asistencias.filter(evento=evento)
            if estado == 'asistieron':
                asistencias = asistencias.filter(evento=evento)
            elif estado == 'faltaron':
                asistencias = asistencias.none()
                todos_usuarios = Usuario.objects.all()
                asistentes_ids = Asistencia.objects.filter(evento=evento).values_list('usuario__id', flat=True)
                usuarios_no_asistentes = todos_usuarios.exclude(id__in=asistentes_ids).order_by('nombre')
    
    paginator = Paginator(asistencias, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'usuarios_no_asistentes': usuarios_no_asistentes,
        'can_scan_qr': request.user.has_perm('asistencia.can_scan_qr')
    }
    return render(request, 'asistencia/historial_asistencias.html', context)

@login_required
@permission_required('asistencia.can_manage_users', raise_exception=True)
def confirmar_asistencia(request, asistencia_id):
    asistencia = get_object_or_404(Asistencia, id=asistencia_id)
    if not asistencia.confirmada:
        asistencia.confirmada = True
        asistencia.save()
        messages.success(request, f"Asistencia de {asistencia.usuario} confirmada exitosamente.")
        LogAccion.objects.create(
            usuario=request.user,
            accion="Confirmar asistencia",
            descripcion=f"{request.user.username} confirmó la asistencia de {asistencia.usuario.nombre} {asistencia.usuario.apellido} para el evento {asistencia.evento.nombre if asistencia.evento else 'sin evento'}."
        )
    else:
        messages.warning(request, f"La asistencia de {asistencia.usuario} ya estaba confirmada.")
    return redirect('historial_asistencias')

@login_required
@permission_required('asistencia.can_manage_users', raise_exception=True)
def descargar_reporte_pdf(request):
    asistencias = Asistencia.objects.all().order_by('-fecha')
    html = render(request, 'asistencia/reporte_asistencias.html', {'asistencias': asistencias}).content.decode('utf-8')
    pdf_file = HTML(string=html).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_asistencias.pdf"'
    
    LogAccion.objects.create(
        usuario=request.user,
        accion="Descargar reporte PDF",
        descripcion=f"{request.user.username} descargó el reporte general de asistencias."
    )
    
    context = {
        'can_scan_qr': request.user.has_perm('asistencia.can_scan_qr')
    }
    return response

@login_required
@permission_required('asistencia.can_manage_users', raise_exception=True)
def importar_usuarios(request):
    form = ImportarUsuariosForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        csv_file = TextIOWrapper(request.FILES['archivo_csv'].file, encoding='utf-8')
        reader = csv.DictReader(csv_file)
        errores = []
        usuarios_importados = 0
        for row in reader:
            try:
                usuario = Usuario.objects.create(
                    nombre=row['nombre'],
                    apellido=row['apellido'],
                    dni=row['dni']
                )
                LogAccion.objects.create(
                    usuario=request.user,
                    accion="Importar usuario",
                    descripcion=f"{request.user.username} importó al usuario {usuario.nombre} {usuario.apellido} (DNI: {usuario.dni})."
                )
                usuarios_importados += 1
            except Exception as e:
                errores.append(f"Fila con DNI {row['dni']}: {str(e)}")
                continue
        context = {
            'form': form,
            'success': True,
            'usuarios_importados': usuarios_importados,
            'errores': errores,
            'can_scan_qr': request.user.has_perm('asistencia.can_scan_qr')
        }
        return render(request, 'asistencia/importar_usuarios.html', context)
    context = {
        'form': form,
        'can_scan_qr': request.user.has_perm('asistencia.can_scan_qr')
    }
    return render(request, 'asistencia/importar_usuarios.html', context)

@login_required
@permission_required('asistencia.can_manage_users', raise_exception=True)
def registrar_usuario(request):
    if request.method == 'POST':
        form = UsuarioRegistroForm(request.POST, request.FILES)
        if form.is_valid():
            usuario = form.save(commit=False)
            user = User.objects.create_user(
                username=usuario.dni,
                password=form.cleaned_data['password']
            )
            usuario.user = user
            usuario.save()
            LogAccion.objects.create(
                usuario=request.user,
                accion="Registrar usuario",
                descripcion=f"{request.user.username} registró al usuario {usuario.nombre} {usuario.apellido} (DNI: {usuario.dni})."
            )
            return redirect('lista_usuarios')
    else:
        form = UsuarioRegistroForm()
    context = {
        'form': form,
        'can_scan_qr': request.user.has_perm('asistencia.can_scan_qr')
    }
    return render(request, 'asistencia/registrar_usuario.html', context)

@login_required
def perfil_usuario(request):
    try:
        usuario = Usuario.objects.get(user=request.user)
        asistencias = Asistencia.objects.filter(usuario=usuario).order_by('-fecha')
        context = {
            'usuario': usuario,
            'asistencias': asistencias,
            'can_scan_qr': request.user.has_perm('asistencia.can_scan_qr')
        }
        return render(request, 'asistencia/perfil_usuario.html', context)
    except Usuario.DoesNotExist:
        context = {
            'error': 'No se encontró un usuario asociado a tu cuenta.',
            'can_scan_qr': request.user.has_perm('asistencia.can_scan_qr')
        }
        return render(request, 'asistencia/perfil_usuario.html', context)

@login_required
@permission_required('asistencia.can_manage_users', raise_exception=True)
def descargar_reporte_evento_pdf(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    asistencias = Asistencia.objects.filter(evento=evento).order_by('usuario__nombre')
    todos_usuarios = Usuario.objects.all()
    asistentes_ids = asistencias.values_list('usuario__id', flat=True)
    no_asistentes = todos_usuarios.exclude(id__in=asistentes_ids).order_by('nombre')
    total_usuarios = todos_usuarios.count()
    porcentaje_asistencia = (asistencias.count() / total_usuarios * 100) if total_usuarios > 0 else 0
    
    html = render(request, 'asistencia/reporte_evento.html', {
        'evento': evento,
        'asistencias': asistencias,
        'no_asistentes': no_asistentes,
        'total_usuarios': total_usuarios,
        'porcentaje_asistencia': porcentaje_asistencia
    }).content.decode('utf-8')
    
    pdf_file = HTML(string=html).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_{evento.nombre}.pdf"'
    
    LogAccion.objects.create(
        usuario=request.user,
        accion="Descargar reporte PDF",
        descripcion=f"{request.user.username} descargó el reporte PDF del evento {evento.nombre}."
    )
    
    context = {
        'can_scan_qr': request.user.has_perm('asistencia.can_scan_qr')
    }
    return response

def create_test_user(request):
    if User.objects.filter(username='testadmin').exists():
        return HttpResponse("El usuario 'testadmin' ya existe.")
    # Crear un User (superusuario)
    user = User.objects.create_superuser(
        username='testadmin',
        email='testadmin@example.com',
        password='testpassword123'
    )
    # Crear un Usuario vinculado
    Usuario.objects.create(
        user=user,
        dni='99999999',  # DNI único, ajusta si es necesario
        nombre='Admin',
        apellido='Test'
    )
    return HttpResponse("Usuario creado: testadmin / testpassword123")