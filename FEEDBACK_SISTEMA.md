# Reporte de Análisis y Feedback del Sistema de Asistencia QR

## 1. Resumen Ejecutivo
El sistema es una aplicación web robusta construida con **Django** diseñada para gestionar la asistencia a eventos o ubicaciones físicas mediante el escaneo de códigos QR. Está orientado a organizaciones que necesitan un control ágil y digitalizado de la presencia de sus miembros (empleados, estudiantes, asistentes).

El sistema cuenta con una arquitectura sólida, buenas prácticas de desarrollo (uso de Class-Based Views, validaciones de modelos, generación de reportes PDF) pero presenta **riesgos de seguridad críticos** y desafíos de infraestructura que deben ser atendidos antes de un despliegue en producción masivo.

---

## 2. Análisis Funcional (¿A quién va dirigido y cómo funciona?)

### Público Objetivo
*   **Administradores de RRHH / Profesores / Organizadores:** Que necesitan registrar quién asiste, cuándo y dónde.
*   **Usuarios Finales:** Que necesitan un método rápido de identificación (QR) y acceso a su historial.

### Flujo de Trabajo
1.  **Registro y Gestión de Usuarios:**
    *   Los usuarios pueden registrarse o ser importados masivamente (CSV) por un administrador.
    *   Al crearse un usuario, el sistema **genera automáticamente un código QR** único basado en su DNI y procesa su foto de perfil.
2.  **Configuración de Eventos:**
    *   Los administradores crean "Ubicaciones" y "Eventos" (con fecha y estado activo/inactivo).
3.  **Toma de Asistencia (Escaneo):**
    *   El personal autorizado accede a la vista de escaneo.
    *   Utilizando la cámara del dispositivo, escanean el QR del usuario.
    *   El sistema valida:
        *   Que el usuario exista.
        *   Que el evento sea hoy.
        *   Que no se haya registrado ya la asistencia.
    *   Se registra la asistencia con fecha y hora.
4.  **Reportes y Monitoreo:**
    *   Se pueden visualizar historiales filtrados por fecha, evento o estado (asistió/faltó).
    *   Generación de PDFs profesionales para respaldo físico.

---

## 3. Análisis Técnico

### Arquitectura y Tecnologías
*   **Backend:** Django (Python). Framework maduro y seguro por defecto.
*   **API:** Django Rest Framework (DRF) para el endpoint de registro de asistencia, permitiendo desacoplar la lógica de escaneo si se quisiera crear una App móvil nativa en el futuro.
*   **Base de Datos:** SQLite (configuración actual), abstraída con `dj_database_url` para facilitar el cambio a PostgreSQL en producción.
*   **Archivos:** `Pillow` para procesamiento de imágenes y `WeasyPrint` para reportes PDF.

### Puntos Fuertes
*   **Validaciones de Datos:** El modelo `Usuario` tiene validaciones explícitas para el DNI (8 dígitos) y nombres (regex), lo que garantiza la integridad de los datos.
*   **Manejo de Permisos:** Uso correcto de permisos personalizados (`can_scan_qr`, `can_manage_users`) en lugar de depender solo de `is_staff`.
*   **Feedback al Usuario:** Uso de mensajes flash (Django Messages) y logs de acción (`LogAccion`) para auditoría interna.

---

## 4. Auditoría de Seguridad y Riesgos (Crítico)

### 🔴 1. Vulnerabilidad en Creación de Superusuario
**Archivo:** `asistencia/views.py` -> `create_superuser`
**Riesgo:** Crítico.
**Descripción:** Existe una vista accesible vía web (`/create-superuser/`) que intenta crear un administrador. Aunque depende de variables de entorno, si estas no están configuradas (o se usan las por defecto hardcodeadas en el código: `,123456%`), cualquier persona que visite esa URL podría comprometer el sistema.
**Solución Recomendada:** Eliminar esta vista inmediatamente. Los superusuarios deben crearse únicamente mediante consola (`python manage.py createsuperuser`) o scripts de despliegue seguros, nunca vía web pública.

### 🟠 2. Persistencia de Archivos Media (QR y Fotos)
**Riesgo:** Medio/Alto (Dependiendo del hosting).
**Descripción:** El sistema guarda los códigos QR y fotos en el sistema de archivos local (`media/`).
**Impacto:** En plataformas como Render, Heroku o Railway (sin volúmenes persistentes), cada vez que la aplicación se reinicia o se hace un despliegue, **todos los códigos QR e imágenes de perfil se borrarán**, rompiendo la funcionalidad.
**Solución Recomendada:** Configurar almacenamiento en la nube (AWS S3, Google Cloud Storage, Cloudinary) usando `django-storages`.

### 🟡 3. Exposición de Secretos
**Riesgo:** Medio.
**Descripción:** En `settings.py`, la `SECRET_KEY` tiene un valor por defecto inseguro si falla la variable de entorno.
**Solución:** Asegurar que en producción la aplicación falle si no existe la variable de entorno, en lugar de usar un valor inseguro conocido.

---

## 5. Recomendaciones de Mejora

### Inmediatas
1.  **Eliminar la vista `create_superuser`:** Es un vector de ataque innecesario.
2.  **Configurar Almacenamiento Externo:** Para evitar la pérdida de imágenes.
3.  **Proteger Endpoint API:** Agregar "Throttling" (límite de peticiones) al endpoint de escaneo para evitar fuerza bruta de códigos QR.

### A Futuro
1.  **Tests Unitarios:** El archivo `tests.py` está vacío actualmente. Es imperativo implementar pruebas unitarias para los modelos (especialmente validaciones de DNI) y las vistas críticas (API de registro).
2.  **Interfaz Móvil:** Mejorar la UI de escaneo para que sea "Responsive" y funcione nativamente mejor en móviles (PWA).
3.  **Confirmación Visual:** Agregar un sonido o feedback visual más notorio al escanear correctamente un QR (verde) o fallar (rojo).

---

**Conclusión:** El sistema tiene una base sólida y funcional para un MVP (Producto Viable Mínimo). Con las correcciones de seguridad mencionadas, es apto para uso en entornos controlados.
