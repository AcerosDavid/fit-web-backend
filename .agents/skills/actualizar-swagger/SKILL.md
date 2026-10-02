---
name: actualizar-swagger
description: Use when creating, modifying or deleting anything that affects the REST API of this project — endpoints, routes, views, serializers, models, query params or permissions (files like */urls.py, */views.py, */serializers.py, */models.py, config/urls.py, config/settings.py) — to keep the Swagger/OpenAPI documentation (drf-spectacular, schema.yaml) updated and validated.
paths: "**/urls.py, **/views.py, **/serializers.py, **/models.py, config/settings.py, schema.yaml, requirements.txt"
---

# Actualizar Swagger (drf-spectacular)

Este proyecto documenta su API con **drf-spectacular** (OpenAPI 3). La documentación tiene dos formas de vida y **ambas deben actualizarse en cada cambio de API**:

1. **UI en vivo**: `GET /api/schema/` (esquema) y `GET /api/schema/swagger-ui/` (Swagger UI, assets locales vía `drf-spectacular-sidecar`). Se genera automáticamente desde el código.
2. **`schema.yaml` versionado en la raíz del repo**: fuente de verdad para frontend/móvil. **Debe regenerarse y commitearse junto con cualquier cambio de API.**

## Checklist obligatoria (en este orden)

1. **Anotar el cambio** con `@extend_schema` (de `drf_spectacular.utils`) en la vista afectada:
   - Siempre: `tags` (una de: `auth, users, members, plans, memberships, payments, attendance, dashboard, coaches, health`), `summary` (imperativo, corto) y `description` cuando el comportamiento no es obvio.
   - Request/response: usar `request=<Serializer>` y `responses={200/201/400/404: <Serializer>}`.
   - Query params manuales: `parameters=[OpenApiParameter(name='member', type=OpenApiTypes.INT, required=False, description='...')]`.
   - POST/PUT **sin cuerpo**: `request=None` (si no, la validación falla con "unable to guess serializer").
   - Endpoints públicos (sin token): `auth=[]`.
   - Los serializers de respuesta van en `responses`, nunca solo en `serializer_class` si el método usa `get_serializer_class()` distinto por verbo (DRF generics lo resuelve solo, pero las `APIView` puras hay que anotarlas a mano).
2. **Serializers nuevos**: crearlos en el `serializers.py` de la app (respuestas genéricas de error en `config/serializers.py`) y referenciarlos en `responses`. Los enums `status` repetidos entre apps se nombran en `SPECTACULAR_SETTINGS['ENUM_NAME_OVERRIDES']` (`config/settings.py`).
3. **Regenerar y validar** (0 warnings y 0 errors son obligatorios):
   ```bash
   docker compose exec web python manage.py spectacular --file schema.yaml --validate
   ```
   Con el override de desarrollo:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py spectacular --file schema.yaml --validate
   ```
   Sin Docker: `python manage.py spectacular --file schema.yaml --validate`. Si sale distinto de 0, arreglar los warnings (nunca dejarlos "para después") y repetir.
4. **Verificar la UI**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/schema/            # 200
   curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/schema/swagger-ui/ # 200
   ```
5. **Commitear `schema.yaml` en el mismo commit** que el cambio de código (nunca dejarlo desactualizado).

## Reglas del proyecto

- Rutas nuevas van en el `urls.py` de la app bajo el prefijo `api/` (`config/urls.py` monta las apps); registrar tags nuevos también en `SPECTACULAR_SETTINGS` (`config/settings.py`).
- Las **function views de Django puro** (ej. `def health(request)`) **no aparecen** en el Swagger: usar `rest_framework.views.APIView`.
- No renombrar `operationId` generados salvo conflicto (el frontend puede depender de ellos).
- La UI y el schema son públicos (`SERVE_PUBLIC=True`); no añadir auth a `/api/schema/`.
- Si se cambia `requirements.txt` (nuevas libs), reconstruir la imagen: `docker compose ... up -d --build`.

## Errores comunes

| Sintoma | Causa / arreglo |
|---|---|
| `unable to guess serializer` en un POST | Falta `request=<serializer>` o `request=None` si no hay cuerpo. |
| Warning de colisión de enum `status` | Falta entrada en `ENUM_NAME_OVERRIDES`. |
| Swagger UI no carga scripts | Falta `drf_spectacular_sidecar` en `INSTALLED_APPS` o `SWAGGER_UI_DIST='SIDECAR'`. |
| `schema.yaml` con diffs enormes no relacionados | Se generó con otra versión de drf-spectacular: regenerar siempre desde el contenedor. |
