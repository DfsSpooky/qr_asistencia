# Plan de Mejoras e Implementaciones - Sistema de Asistencia QR

A continuación se detalla una lista de mejoras clasificadas por área y prioridad, diseñadas para llevar el sistema de un MVP (Producto Viable Mínimo) a una solución de producción robusta, segura y escalable.

## 1. Seguridad (Prioridad Crítica)
Estas mejoras deben implementarse de inmediato para evitar vulnerabilidades graves.

*   [ ] **Eliminar Vista `create_superuser`:**
    *   **Acción:** Eliminar la función `create_superuser` en `asistencia/views.py` y su ruta en `urls.py`.
    *   **Razón:** Permite la creación de administradores vía web pública, lo cual es un riesgo de seguridad inaceptable.
    *   **Alternativa:** Usar `python manage.py createsuperuser` en la consola del servidor.

*   [ ] **Reforzar Seguridad en API `RegistrarAsistencia`:**
    *   **Acción:** Revisar el uso de `@method_decorator(csrf_exempt, ...)` en la clase `RegistrarAsistencia`.
    *   **Mejora:** Si el cliente es una app móvil, implementar autenticación por Token (JWT o Token Auth). Si es el navegador, mantener la protección CSRF estándar.
    *   **Rate Limiting:** Implementar `Throttling` de Django Rest Framework para evitar que un usuario envíe cientos de peticiones de asistencia por segundo.

*   [ ] **Protección de Variables de Entorno:**
    *   **Acción:** Asegurar que `DEBUG=False` en producción y que `SECRET_KEY` se cargue obligatoriamente desde el entorno (fallar si no existe), en lugar de tener un valor por defecto inseguro.

## 2. Backend y Calidad de Código (Prioridad Alta)
Mejoras para la mantenibilidad, rendimiento y estabilidad del sistema.

*   [ ] **Optimización de Importación Masiva:**
    *   **Acción:** Modificar `importar_usuarios` en `views.py`.
    *   **Mejora:** Utilizar `transaction.atomic()` para asegurar que si falla una fila, no se queden datos a medias. Usar `Usuario.objects.bulk_create()` para mejorar la velocidad si son miles de usuarios.

*   [ ] **Pruebas Unitarias (Testing):**
    *   **Acción:** Poblar el archivo `asistencia/tests.py`.
    *   **Alcance:**
        *   Probar modelos: Validar que no se pueda crear un DNI de 7 dígitos o con letras.
        *   Probar vistas: Verificar que `RegistrarAsistencia` rechaza peticiones sin autenticación.
        *   Probar lógica: Asegurar que no se puede registrar asistencia duplicada el mismo día.

*   [ ] **Manejo de Archivos Media (QR y Fotos):**
    *   **Acción:** Configurar `django-storages` con AWS S3, Google Cloud Storage o Azure.
    *   **Razón:** En servicios como Render/Heroku, el sistema de archivos es efímero. Si el servidor se reinicia, se pierden todas las fotos y QRs generados.

## 3. Experiencia de Usuario (Frontend y UX)
Mejoras visuales y de usabilidad para los usuarios finales y administradores.

*   [ ] **Feedback Visual y Sonoro al Escanear:**
    *   **Acción:** Modificar `escanear.html`.
    *   **Detalle:** Reproducir un sonido de "bip" exitoso o de "error" al procesar el QR. Mostrar un *overlay* verde (éxito) o rojo (error) grande en la pantalla, ya que el operador suele estar en movimiento.

*   [ ] **Dashboard de Estadísticas:**
    *   **Acción:** Crear una nueva vista en el panel de administrador.
    *   **Contenido:** Gráficos (usando Chart.js) que muestren:
        *   Porcentaje de asistencia por evento.
        *   Puntualidad (hora de llegada promedio).
        *   Usuarios con más inasistencias.

*   [ ] **Corrección de Diseño Móvil:**
    *   **Acción:** Revisar el `footer` en `base.html`. Actualmente tiene `position: fixed`, lo que puede tapar contenido en pantallas pequeñas. Cambiar a un diseño "Sticky footer" o añadir padding inferior al `body`.

## 4. Infraestructura y DevOps
Preparación para el despliegue profesional.

*   [ ] **Contenerización (Docker):**
    *   **Acción:** Crear un `Dockerfile` y `docker-compose.yml`.
    *   **Beneficio:** Facilita el despliegue en cualquier servidor y garantiza que el entorno de desarrollo sea idéntico al de producción.

*   [ ] **Base de Datos PostgreSQL:**
    *   **Acción:** Migrar de SQLite a PostgreSQL para producción (ya soportado por `dj_database_url` pero confirmar driver `psycopg2` en requisitos).
    *   **Razón:** SQLite no soporta bien alta concurrencia (múltiples lecturas/escrituras simultáneas al escanear rápido).

## Resumen de Prioridades

1.  **Inmediato:** Eliminar `create_superuser` y configurar persistencia de archivos (S3/Cloudinary).
2.  **Corto Plazo:** Tests unitarios y mejoras visuales en el escáner.
3.  **Medio Plazo:** Docker, Dashboard de estadísticas y optimización de importación.
