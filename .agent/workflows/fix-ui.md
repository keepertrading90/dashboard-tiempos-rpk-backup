---
description: Proceso para corregir y validar la visualización (UI/UX) del Dashboard.
---

# Skill: Fix UI/UX Alignment

Este workflow se utiliza cuando la interfaz web no carga correctamente los estilos (CSS), imágenes o scripts.

## Pasos de Corrección

1. **Consolidación de Montajes Estáticos**:
   - Preferir un único montaje `app.mount("/static", ...)` de la carpeta raíz `frontend/`.
   - Esto evita problemas de resolución de rutas en subdirectorios bajo Windows.
   - Usar el prefijo `/static/` en el HTML: `/static/ui/styles.css`, `/static/assets/logo.png`.

2. **Validación de Rutas en el Backend**:
   - Asegurar que `BASE_DIR` apunta a la raíz del proyecto.
   - Verificar que `app.mount` utiliza rutas absolutas (`.resolve().absolute()`).
   - Comprobar que los nombres de las carpetas (`frontend`, `ui`, `assets`) coinciden exactamente (case-sensitive).

2. **Validación de Enlaces en el HTML**:
   - Usar rutas absolutas comenzando con `/`. Ejemplo: `<link href="/ui/styles.css">`.
   - Verificar que no haya conflictos entre rutas montadas.

3. **Verificación de MIME Types**:
   - Asegurarse de que el servidor FastAPI está sirviendo los archivos con el `Content-Type` correcto (especialmente `text/css`).

4. **Reinicio de Procesos**:
   - Matar cualquier proceso colgante en el puerto 8000.
   - Reiniciar el servidor desde la raíz del proyecto.

## Comandos de Verificación
// turbo
```powershell
# Verificar estructura
ls -R frontend/
# Probar endpoint de estado
Invoke-WebRequest -Uri "http://localhost:8000/api/status"
```
