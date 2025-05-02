from django.urls import path
from .views import (
    index, lista_usuarios, detalle_usuario, RegistrarAsistencia,
    escanear_qr, historial_asistencias, descargar_reporte_pdf,
    importar_usuarios, perfil_usuario, descargar_reporte_evento_pdf,
    registrar_usuario, confirmar_asistencia, create_superuser  # Agrega create_superuser aquí
)

urlpatterns = [
    path('', index, name='index'),
    path('lista_usuarios/', lista_usuarios, name='lista_usuarios'),
    path('usuario/<str:dni>/', detalle_usuario, name='detalle_usuario'),
    path('api/registrar-asistencia/', RegistrarAsistencia.as_view(), name='registrar_asistencia'),
    path('escanear/', escanear_qr, name='escanear_qr'),
    path('historial/', historial_asistencias, name='historial_asistencias'),
    path('descargar-reporte/', descargar_reporte_pdf, name='descargar_reporte_pdf'),
    path('importar-usuarios/', importar_usuarios, name='importar_usuarios'),
    path('perfil/', perfil_usuario, name='perfil_usuario'),
    path('descargar-reporte-evento/<int:evento_id>/', descargar_reporte_evento_pdf, name='descargar_reporte_evento_pdf'),
    path('registrar-usuario/', registrar_usuario, name='registrar_usuario'),
    path('confirmar-asistencia/<int:asistencia_id>/', confirmar_asistencia, name='confirmar_asistencia'),
    path('create-superuser/', create_superuser, name='create_superuser'),  # Ahora puedes usar create_superuser directamente
]