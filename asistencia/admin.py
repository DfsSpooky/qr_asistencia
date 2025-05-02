from django.contrib import admin
from .models import Usuario, Asistencia, Ubicacion, Evento, LogAccion

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'dni')
    search_fields = ('nombre', 'apellido', 'dni')
    readonly_fields = ('qr_code',)

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha', 'ubicacion', 'evento', 'confirmada')
    search_fields = ('usuario__nombre', 'usuario__apellido', 'usuario__dni')
    list_filter = ('confirmada', 'ubicacion', 'evento')
    actions = ['confirmar_asistencias']

    def confirmar_asistencias(self, request, queryset):
        queryset.update(confirmada=True)
        self.message_user(request, "Asistencias confirmadas exitosamente.")
    confirmar_asistencias.short_description = "Confirmar asistencias seleccionadas"

@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha', 'activo')
    search_fields = ('nombre',)
    list_filter = ('activo', 'fecha')
    actions = ['finalizar_eventos']

    def finalizar_eventos(self, request, queryset):
        queryset.update(activo=False)
        self.message_user(request, "Eventos finalizados exitosamente.")
    finalizar_eventos.short_description = "Finalizar eventos seleccionados"

@admin.register(LogAccion)
class LogAccionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'fecha')
    search_fields = ('usuario__username', 'accion', 'descripcion')
    list_filter = ('accion', 'fecha')
    readonly_fields = ('usuario', 'accion', 'descripcion', 'fecha')