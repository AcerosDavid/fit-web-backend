# Documentación Técnica — FitWeb Backend (API REST)

> **Idiomas / Languages:** este documento está redactado en **español (Parte I)** e **inglés (Parte II)**.
> *This document is written in **Spanish (Part I)** and **English (Part II)**.*
>
> | | |
> |---|---|
> | **Proyecto / Project** | FitWeb — API de gestión administrativa de gimnasios (SaaS) |
> | **Módulo / Module** | Backend (Django REST Framework) |
> | **Asignatura / Course** | Diseño Funcional / Ingeniería de Software — Desarrollo de backend |
> | **Autores / Authors** | Carlos José Mantilla Cote · David Arturo Aceros Ortiz |
> | **Última actualización / Last update** | 26-11-2026 |
> | **Versión de la API / API version** | 1.0.0 (`schema.yaml`, `config/settings.py → SPECTACULAR_SETTINGS`) |

---

# PARTE I — DOCUMENTACIÓN TÉCNICA (ESPAÑOL)

## 1. Información general

**FitWeb Backend** es una API RESTful que centraliza la gestión administrativa de gimnasios: personal del
gimnasio (administradores, recepcionistas y entrenadores), clientes, planes de suscripción, membresías,
pagos, control de acceso físico (check-in / check-out) y métricas del tablero de administración.

- **Tecnologías:** Python 3.12 · Django 6.1 · Django REST Framework 3.18 · SimpleJWT · drf-spectacular
  (OpenAPI 3) · PostgreSQL 17 (o SQLite en local) · Docker / Docker Compose.
- **Arquitectura:** proyecto Django con **9 aplicaciones** (`users`, `members`, `plans`, `memberships`,
  `payments`, `attendance`, `dashboard`, `coaches`, `history`) más el paquete de configuración `config`.
  Cada aplicación sigue la separación *modelo → serializer → vista → url → test*.
- **Autenticación:** JSON Web Tokens (`Authorization: Bearer <access>`), con rotación de *refresh*.
- **Documentación viva de la API:** Swagger UI en `/api/schema/swagger-ui/` y esquema OpenAPI en
  `/api/schema/` (archivo versionado `schema.yaml` en la raíz).

### 1.1 Inventario de archivos Python

| Aplicación | Archivos Python (sin migraciones) | Responsabilidad |
|---|---|---|
| `config/` | `settings.py`, `urls.py`, `views.py`, `serializers.py`, `wsgi.py`, `asgi.py` | Configuración, enrutado raíz, healthcheck y serializers comunes |
| `users/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed.py`, `management/commands/seed_all.py` | Autenticación JWT y gestión del *staff* |
| `members/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed_members.py` | Clientes del gimnasio con *soft-delete* |
| `plans/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed_plans.py` | Catálogo de planes de suscripción |
| `memberships/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed_memberships.py` | Suscripciones cliente ↔ plan |
| `payments/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed_payments.py` | Registro financiero de cobros |
| `attendance/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `services.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed_attendance.py`, `management/commands/close_stale_attendances.py` | Control de acceso físico y escaneo de QR |
| `dashboard/` | `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `models.py` | Métricas agregadas del tablero |
| `coaches/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py` | Entrenadores y su asistencia |
| `history/` | `serializers.py`, `views.py`, `urls.py`, `apps.py`, `tests.py` | Historial agregado de clientes y línea de tiempo global |
| `scripts/` | `generar_diccionario_datos.py`, `generar_datos_prueba.py` | Utilidades para producir los archivos complementarios |
| raíz | `manage.py` | Utilidad de línea de comandos de Django |

**Totales:** 122 archivos `.py` (101 del proyecto + 21 archivos en `migrations/`, de los cuales 13 son migraciones de esquema y 8 son `__init__.py`).

### 1.2 Endpoints públicos del proyecto

| Método | Ruta | Vista / clase | Módulo |
|---|---|---|---|
| GET | `/api/health/` | `config.views.HealthView.get` | config |
| POST | `/api/auth/login/` | `users.views.LoginView.post` | users |
| POST | `/api/auth/refresh/` | `users.views.RefreshView.post` | users |
| GET/PUT/PATCH | `/api/auth/me/` | `users.views.MeView` | users |
| GET/POST | `/api/users/` | `users.views.UserListCreateView` | users |
| GET/PUT/PATCH/DELETE | `/api/users/{id}/` | `users.views.UserDetailView` | users |
| GET/POST | `/api/members/` | `members.views.MemberListCreateView` | members |
| GET/PUT/PATCH | `/api/members/{id}/` | `members.views.MemberDetailView` | members |
| DELETE | `/api/members/{id}/delete/` | `members.views.MemberDeleteView.delete` | members |
| POST | `/api/members/{id}/restore/` | `members.views.MemberRestoreView.post` | members |
| GET/POST | `/api/plans/` | `plans.views.PlanListCreateView` | plans |
| GET/PUT/PATCH/DELETE | `/api/plans/{id}/` | `plans.views.PlanDetailView` | plans |
| GET/POST | `/api/memberships/` | `memberships.views.MembershipListCreateView` | memberships |
| GET/PUT/PATCH | `/api/memberships/{id}/` | `memberships.views.MembershipDetailView` | memberships |
| GET/POST | `/api/payments/` | `payments.views.PaymentListCreateView` | payments |
| GET/PUT/PATCH | `/api/payments/{id}/` | `payments.views.PaymentDetailView` | payments |
| GET | `/api/attendance/` | `attendance.views.AttendanceListView` | attendance |
| POST | `/api/attendance/check-in/` | `attendance.views.CheckInView.post` | attendance |
| POST | `/api/attendance/scan/` | `attendance.views.ScanQrView.post` | attendance |
| POST | `/api/attendance/{id}/check-out/` | `attendance.views.CheckOutView.post` | attendance |
| GET | `/api/dashboard/` | `dashboard.views.DashboardStatsView.get` | dashboard |
| GET/POST | `/api/coaches/` | `coaches.views.CoachListCreateView` | coaches |
| GET/PUT/PATCH/DELETE | `/api/coaches/{id}/` | `coaches.views.CoachDetailView` | coaches |
| GET | `/api/coaches/{id}/history/` | `coaches.views.CoachHistoryView.get` | coaches |
| POST | `/api/coaches/{id}/check-in/` | `coaches.views.CoachCheckInView.post` | coaches |
| POST | `/api/coaches/{id}/check-out/` | `coaches.views.CoachCheckOutView.post` | coaches |
| GET | `/api/members/{id}/history/` | `history.views.MemberHistoryView.get` | history |
| GET | `/api/history/` | `history.views.GlobalHistoryView.get` | history |
| GET | `/api/schema/`, `/api/schema/swagger-ui/` | drf-spectacular | config |

---

## 2. Mapa de los temas estudiados durante la asignatura

La numeración (`1`–`40`) corresponde a los ítems de la *Lista de chequeo – Validación del código fuente*.
Cada fila indica **archivo**, **clase / función / método** y **qué se implementa**.

### A. Fundamentos de programación y Python (ítems 1–8)

| N.º | Tema | Archivo(s) | Clase / función / método | Implementación |
|---|---|---|---|---|
| 1 | Problema o necesidad identificada | `README.md`, `attendance/services.py`, `members/models.py`, `memberships/models.py` | docstrings de negocio | Gestión de gimnasios: `attendance/services.py` documenta el control de acceso; `members/models.py` conserva el historial contable con *soft-delete*; `memberships/models.py` calcula la fecha de fin |
| 2 | Requerimientos funcionales identificables | `users/views.py`, `attendance/views.py`, `memberships/views.py`, `payments/views.py`, `dashboard/views.py`, `history/views.py` | `LoginView`, `RefreshView`, `MeView`, `CheckInView`, `CheckOutView`, `ScanQrView`, `MembershipListCreateView`, `PaymentListCreateView`, `DashboardStatsView`, `MemberHistoryView`, `GlobalHistoryView` | 11 requerimientos implementados y documentados en `schema.yaml` |
| 3 | Variables con nombres descriptivos | `dashboard/views.py`, `attendance/services.py`, `members/management/commands/seed_members.py` | variables `active_members_count`, `monthly_revenue`, `next_week`, `expiring_memberships`, `start_of_today`, `closed`, `created_count`, `skipped_count` | Nombres autoexplicativos en todo el proyecto |
| 4 | Tipos `int`, `float`, `str`, `bool` | `plans/models.py`, `dashboard/serializers.py`, `attendance/serializers.py`, `members/serializers.py`, `users/management/commands/seed_all.py` | `DecimalField`, `PositiveIntegerField`, `BooleanField`, `IntegerField`, `FloatField`, `ChoiceField`, `type=int` | Tipos usados en modelos, serializadores y argumentos de CLI |
| 5 | Operadores aritméticos | `memberships/models.py`, `dashboard/views.py`, `coaches/models.py`, `history/views.py` | `Membership.save`, `DashboardStatsView.get`, `CoachAttendance.duration_minutes`, `MemberHistoryView.get` | `start_date + timedelta(days=plan.duration_days)`, `today + timedelta(days=7)`, `total_seconds() // 60`, `Sum('amount')` |
| 6 | Operadores de comparación y lógicos | `memberships/models.py`, `history/views.py`, `coaches/views.py`, `users/serializers.py`, `config/settings.py`, `attendance/models.py` | `Membership.is_valid`, `_parse_date_range`, `IsAdminOrReceptionist.has_permission`, `UserUpdateSerializer.update`, `UserSerializer` | `==`, `>=`, `and`, `or`, `not`; condiciones `Q(...)` en restricciones de base de datos |
| 7 | Entrada de información y salida de resultados | `attendance/views.py`, `history/views.py`, `users/management/commands/seed_all.py`, `dashboard/views.py`, seeders | `CheckInView.post`, `_parse_date_param`, `Command.add_arguments`, `self.stdout.write` | Entrada HTTP (`request.data`, query params) y CLI; salida JSON (`Response`) y consola de Django |
| 8 | Conversiones de tipos de datos | `attendance/views.py`, `history/views.py`, `dashboard/views.py`, `history/serializers.py` | `_resolve_qr_code`, `_parse_int_param`, `DashboardStatsView.get`, `HistorySummarySerializer` | `int(value)` sobre `isdigit()`, `float(monthly_revenue)`, `Decimal(...).quantize(Decimal('0.01'))` |

### B. Estructuras condicionales y repetitivas (ítems 9–15)

| N.º | Tema | Archivo(s) | Clase / función / método | Implementación |
|---|---|---|---|---|
| 9 | `if`, `elif`, `else` | `members/management/commands/seed_members.py`, `users/management/commands/seed.py`, `attendance/views.py` | `Command.handle`, `_scan_member` | Ramificaciones según género/estado y según presencia de asistencia abierta |
| 10 | Condiciones compuestas o anidadas | `history/views.py`, `coaches/views.py`, `attendance/views.py`, `memberships/management/commands/seed_memberships.py` | `_parse_date_range`, `CoachHistoryView.get`, `_resolve_qr_code`, `Command.handle` | Tres operandos con `and`, bucles `for` → `if` → `if` anidados |
| 11 | Ciclo `while` | `entrypoint.sh` (heredoc Python) | bucle `for attempt in range(30)` con `else: raise SystemExit` | Espera de disponibilidad de la base de datos con control de terminación |
| 12 | Ciclos `for` | `attendance/management/commands/seed_attendance.py`, `members/management/commands/seed_members.py`, `attendance/services.py`, `users/management/commands/seed_all.py` | `Command.handle`, `close_stale_attendances`, `Command.handle` | `for i in range(7)`, `for _ in range(count)`, recorrido de querysets, `enumerate(steps, start=1)` |
| 13 | Ciclos anidados | `attendance/management/commands/seed_attendance.py`, `history/views.py` | `Command.handle`, `_parse_types` | `for i in range(7)` → `for member in daily_visitors`; comprensión interna de `split/strip` |
| 14 | `break` y `continue` | `entrypoint.sh`, `attendance/migrations/0002_close_duplicate_open_attendances.py`, `coaches/migrations/0003_close_duplicate_open_coach_attendances.py` | bucle de espera de BD; `RunPython` de migraciones | `break` al conectar; `continue` para saltar duplicados en migraciones |
| 15 | Control de condiciones de terminación | `members/management/commands/seed_members.py`, `history/views.py`, `attendance/views.py`, `entrypoint.sh` | `Command.add_arguments`, `GlobalHistoryView.get`, `_resolve_qr_code` | `range(count)`, paginación acotada `max(1, min(limit, MAX_EVENT_LIMIT))`, `return` temprano |

### C. Cadenas y estructuras de datos (ítems 16–23)

| N.º | Tema | Archivo(s) | Clase / función / método | Implementación |
|---|---|---|---|---|
| 16 | Manipulación de cadenas | `attendance/views.py`, `history/views.py`, `users/management/commands/seed.py`, `plans/management/commands/seed_plans.py`, `attendance/models.py` | `_resolve_qr_code`, `_parse_types`, `Command.handle`, `Attendance.__str__` | `.strip().upper()`, `.startswith()`, `.isdigit()`, `.split(',')`, `', '.join(...)`, f-strings, `strftime` |
| 17 | Índices para consultar elementos | `attendance/views.py`, `history/views.py`, `members/management/commands/seed_members.py` | `_resolve_qr_code`, `GlobalHistoryView.get`, `Command.handle` | Slice de cadena `code[len(prefix):]`, slice de lista `events[offset:offset + limit]`, `choice[0]` |
| 18 | Listas para almacenar elementos | `members/models.py`, `payments/models.py`, `users/models.py`, `config/settings.py`, `attendance/serializers.py` | `TextChoices` `Status`/`Gender`, `Method`, `Role`, `INSTALLED_APPS`, `ChoiceField` | Listas de opciones y de configuración del proyecto |
| 19 | Agregar, consultar y modificar elementos de una lista | `config/settings.py`, `history/views.py`, `users/management/commands/seed.py` | `ALLOWED_HOSTS.append`, `CSRF_TRUSTED_ORIGINS.append`, `GlobalHistoryView.get`, `users_data` | `events = []`, `events.extend(...)`, `dict.fromkeys(...)` |
| 20 | `append()`, `remove()` o `len()` | `config/settings.py`, `history/views.py`, `users/management/commands/seed_all.py`, `attendance/management/commands/seed_attendance.py` | dos `append()` en settings, `len(events)`, `len(steps)`, `min(len(members), ...)` | Nota: no se usa `remove()`; el borrado lógico es `deleted_at` |
| 21 | Tuplas para valores inmutables | `history/serializers.py`, `attendance/views.py`, `config/settings.py` | `HistoryEventType.CHOICES`, `return kind, int(value)`, `permission_classes = (IsAdminOrReceptionist,)`, `AUTH_HEADER_TYPES` | Tuplas de opciones, retornos múltiples y clases de permiso |
| 22 | Diccionarios como registros | `dashboard/views.py`, `history/views.py`, `users/management/commands/seed.py`, `config/settings.py` | payload de `DashboardStatsView.get`, `summary`/`data`/`metadata`, `users_data`, `DATABASES` | Diccionarios para respuestas JSON y configuraciones |
| 23 | Consultar y actualizar diccionarios | `attendance/views.py`, `payments/views.py`, `users/serializers.py`, `history/views.py`, `payments/serializers.py` | `.get()` en query params, `data["user"] = ...`, `metadata['duration_minutes'] = ...`, `validated_data['received_by'] = ...` | Lectura y actualización de claves |

### D. Vectores, matrices y agregaciones (ítems 24–30)

| N.º | Tema | Archivo(s) | Clase / función / método | Implementación |
|---|---|---|---|---|
| 24 | Estructura unidimensional | `history/views.py`, `users/management/commands/seed_all.py`, `plans/management/commands/seed_plans.py`, `attendance/management/commands/seed_attendance.py` | `events = []`, `steps`, `plans_data`, `members = list(...)` | Listas de trabajo de cada comando y vista |
| 25 | Recorridos mediante índices o ciclos | `plans/management/commands/seed_plans.py`, `attendance/management/commands/seed_attendance.py`, `users/management/commands/seed_all.py`, `history/views.py` | `for data in plans_data`, `for i in range(7)`, `enumerate(steps, start=1)`, acceso por `offset` | Recorridos con índice explícito |
| 26 | Ordenamiento ascendente o descendente | `history/views.py`, `memberships/models.py`, `plans/models.py`, `payments/models.py` | `events.sort(key=lambda event: event['date'], reverse=True)`, `Meta.ordering` | Descendente por fecha; `price` ascendente en planes |
| 27 | Búsqueda dentro de una colección | `dashboard/views.py`, `payments/views.py`, `memberships/views.py`, `members/views.py`, `attendance/services.py` | `.filter()`, `.get()`, `.exists()`, `.first()` | Búsqueda secuencial mediante el ORM |
| 28 | Matriz / estructura bidimensional | `attendance/views.py`, `users/management/commands/seed_all.py`, `config/settings.py` | `for prefix, kind in ((MEMBER_QR_PREFIX, 'member'), ...)`, `steps = [(nombre, [args]), ...]`, `TEMPLATES`, `SPECTACULAR_SETTINGS['TAGS']` | Tablas de tuplas y diccionarios anidados en lugar de matrices literales |
| 29 | Acceder y recorrer filas y columnas | `attendance/views.py`, `users/management/commands/seed_all.py`, `plans/management/commands/seed_plans.py`, `config/settings.py` | desempaquetado de filas, `data["name"]`, `DATABASES['default']['ENGINE']` | Acceso por posición y por clave |
| 30 | Sumas, totales o promedios sobre datos | `dashboard/views.py`, `history/views.py`, `coaches/views.py`, `history/serializers.py` | `aggregate(total=Sum('amount'))`, `Coalesce(Sum(...))`, `sum(... duration_minutes ...)`, `get_total_paid` | Totales y conteos con funciones de agregación del ORM |

### E. Funciones, procedimientos y modularización (ítems 31–36)

| N.º | Tema | Archivo(s) | Clase / función / método | Implementación |
|---|---|---|---|---|
| 31 | Funciones con `def` | `attendance/services.py`, `history/views.py`, `members/views.py`, `manage.py` | 5 funciones de `services.py`, 6 helpers en `history/views.py`, `IsAdminOrReceptionist.has_permission`, `main` | Unidad de reutilización principal del proyecto |
| 32 | Funciones con parámetros y argumentos | `attendance/services.py`, `history/views.py`, `attendance/tests.py` | `check_out_time(attendance, now=None)`, `create_attendance(model, **fields)`, `_parse_date_param(request, name)`, `_filter_by_date(queryset, field, date_from, date_to)`, `local_datetime(day, hour, ...)` | Funciones parametrizadas y con argumentos por defecto |
| 33 | Funciones con `return` | `attendance/services.py`, `config/views.py`, `members/views.py`, `history/views.py` | las 5 funciones de `services.py`, `HealthView.get`, `has_permission`, retornos múltiples | Retorno explícito en todas las funciones de servicio |
| 34 | Procedimientos sin valor de retorno | `*/management/commands/seed*.py`, `attendance/management/commands/close_stale_attendances.py`, `members/models.py` | `handle()`, `flush_related()`, `Member.delete()` | Procedimientos de efecto: siembra, limpieza y borrado lógico |
| 35 | Función `lambda` | `history/views.py` | `events.sort(key=lambda event: event['date'], reverse=True)` | Ordenamiento con clave de ordenamiento |
| 36 | Funciones reutilizables y buen alcance de variables | `attendance/services.py`, `members/models.py`, `members/views.py`, `history/views.py` | `SoftDeleteManager`, `AllObjectsManager`, `IsAdminOrReceptionist` (usada por 8 apps), `_parse_date_param` | Núcleo de lógica reutilizado por varias aplicaciones |

### F. Programación orientada a objetos (clases, herencia, encapsulamiento)

| Tema | Archivo(s) | Clase / método | Implementación |
|---|---|---|---|
| Modelo de dominio | `users/models.py`, `members/models.py`, `plans/models.py`, `memberships/models.py`, `payments/models.py`, `attendance/models.py`, `coaches/models.py` | `User`, `Member`, `Plan`, `Membership`, `Payment`, `Attendance`, `Coach`, `CoachAttendance` | 8 modelos con campos, opciones (`TextChoices`) y `Meta.ordering` |
| Herencia | `users/models.py`, `members/models.py` | `User(AbstractUser)`, `SoftDeleteManager(models.Manager)`, `AllObjectsManager(models.Manager)` | Especialización del usuario de Django y managers propios |
| Encapsulamiento y propiedades | `members/models.py`, `memberships/models.py`, `coaches/models.py` | `full_name`, `qr_code`, `is_deleted`, `is_valid`, `duration_minutes` | `@property` de solo lectura sobre datos derivados |
| Comportamiento en el modelo | `members/models.py`, `memberships/models.py` | `Member.delete()`, `Member.restore()`, `Member.hard_delete()`, `Membership.save()` | Reglas de negocio dentro del modelo (cálculo automático de `end_date`) |
| Polimorfismo / reutilización de vistas | `members/views.py`, `plans/views.py`, `memberships/views.py`, `payments/views.py`, `attendance/views.py` | `ListCreateAPIView`, `RetrieveUpdateAPIView`, `ListAPIView` de DRF | Clases genéricas reutilizadas por los 9 módulos |
| Composición de servicios | `attendance/services.py`, `attendance/views.py`, `coaches/views.py` | `create_attendance(model, **fields)` | Un mismo servicio atiende `Attendance` y `CoachAttendance` |

### G. Documentación, calidad y funcionamiento (ítems 37–40)

| N.º | Tema | Archivo(s) | Clase / función / método | Implementación |
|---|---|---|---|---|
| 37 | Código documentado con comentarios | `attendance/services.py`, `dashboard/views.py`, `attendance/views.py`, `history/views.py`, seeders | docstrings y comentarios numerados (`# 1. Total de miembros activos` …) | Documentación en línea de la lógica de negocio |
| 38 | Ejecución correcta sin errores | `*/tests.py`, `config/views.py`, `entrypoint.sh`, `Dockerfile`, `docker-compose.yml` | 53 pruebas, `HealthView.get`, `manage.py migrate`, `collectstatic` | Ver sección **6. Evidencias de funcionamiento** |
| 39 | Validación de datos y control de errores | `users/serializers.py`, `attendance/serializers.py`, `attendance/views.py`, `members/views.py`, `history/views.py`, `attendance/models.py` | `min_length=8`, `IntegerField`, `ChoiceField`, `ValidationError`, `try/except` → 404, `_parse_int_param`, `UniqueConstraint` | Validación en serializers, vistas y base de datos |
| 40 | Funcionalidades integradas y demostrables | `config/urls.py`, `users/management/commands/seed_all.py`, `schema.yaml`, `README.md` | `urlpatterns`, `Command.handle`, `flush_related` | 28 endpoints integrados bajo `/api/` + Swagger + seeders en cascada |

---

## 3. Archivos complementarios

| Archivo | Descripción |
|---|---|
| `complementos/diccionario_datos.xlsx` | Diccionario de datos de las 8 tablas del modelo. Hojas: **Modelos** (tabla, clase y número de registros), **Campos** (tipo, detalle, restricciones y relación de cada campo) y **Relaciones** (FK / OneToOne con su `on_delete`) |
| `complementos/datos_prueba.xlsx` | Exportación de los datos generados por los seeders. Hojas: **Resumen**, **Usuarios**, **Clientes**, **Planes**, **Membresías**, **Pagos**, **Asistencias**, **Entrenadores**, **Asistencias entrenadores** |
| `scripts/generar_diccionario_datos.py` | Script que produce el diccionario de datos (recorre `apps.get_models()` y `model._meta.get_fields()`) |
| `scripts/generar_datos_prueba.py` | Script que exporta los registros de la base de datos a Excel |
| `requirements.txt` | Dependencias de ejecución del API |
| `requirements-dev.txt` | Dependencias adicionales para regenerar los Excel (`openpyxl`) |
| `.env.example` | Plantilla de variables de entorno (copiar a `.env`) |
| `schema.yaml` | Esquema OpenAPI 3 versionado (fuente de verdad para el frontend) |
| `seed.sh` | Ejecución encadenada de los 6 seeders individuales |
| `Dockerfile`, `docker-compose.yml`, `docker-compose.dev.yml`, `entrypoint.sh`, `render.yaml` | Despliegue reproducible (contenedores, desarrollo, producción) |
| `logo.png` | Logotipo oficial usado en README y Swagger |

> Regenerar los Excel:
> ```bash
> pip install -r requirements-dev.txt
> python scripts/generar_diccionario_datos.py
> python scripts/generar_datos_prueba.py
> ```

---

## 4. Dependencias e instrucciones de ejecución

### 4.1 Dependencias

| Librería | Versión | Uso en el proyecto |
|---|---|---|
| `Django` | 6.1.1 | Framework web, ORM, migraciones, admin |
| `djangorestframework` | 3.18.1 | Serializers, vistas genéricas, permisos |
| `djangorestframework_simplejwt` | 5.5.1 | Emisión y rotación de tokens JWT |
| `PyJWT` | 2.15.1 | Firma/verificación de tokens |
| `drf-spectacular` (+ `sidecar`) | 0.30.0 / 2026.10.1 | Generación del esquema OpenAPI y Swagger UI local |
| `django-cors-headers` | 4.9.0 | Consumption de la API desde el frontend React |
| `dj-database-url` | 3.1.2 | Conexión por `DATABASE_URL` (Render / Neon / Supabase) |
| `python-decouple` | 3.8 | Lectura tipada de variables de entorno |
| `psycopg[binary]` | 3.3.6 | Driver PostgreSQL |
| `whitenoise` | 6.12.0 | Serving de archivos estáticos sin Nginx |
| `gunicorn` | 26.2.0 | Servidor WSGI de producción |
| `Faker` | 40.40.0 | Datos ficticios en los seeders |
| `openpyxl` (*dev*) | 3.1.5 | Generación de los archivos Excel complementarios |

### 4.2 Ejecución local (sin Docker)

```bash
# 1. Entorno virtual
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Dependencias
pip install -r requirements.txt

# 3. Variables de entorno
cp .env.example .env               # en .env: SECRET_KEY, DEBUG=True y bloque SQLite

# 4. Base de datos
python manage.py migrate

# 5. Datos de prueba (opcional)
python manage.py seed_all --count=100

# 6. Servidor
python manage.py runserver          # http://127.0.0.1:8000/
```

### 4.3 Ejecución con Docker

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build   # desarrollo
docker compose up --build -d                                              # producción (gunicorn)
docker compose exec web python manage.py seed_all                          # datos de prueba
```

### 4.4 Comandos de gestión propios

| Comando | Función |
|---|---|
| `python manage.py seed` | Administrador por defecto (`admin` / `admin1234`) y roles |
| `python manage.py seed_members [--count=N]` | Clientes ficticios |
| `python manage.py seed_plans` | Catálogo de planes |
| `python manage.py seed_memberships` | Asigna membresías a clientes |
| `python manage.py seed_payments` | Genera los cobros de las membresías |
| `python manage.py seed_attendance` | Simula accesos de los últimos 7 días |
| `python manage.py seed_all [--count=N] [--flush]` | Ejecuta los 6 seeders en orden |
| `python manage.py close_stale_attendances` | Cierra asistencias abiertas de días anteriores |
| `python manage.py spectacular --file schema.yaml --validate` | Regenera y valida el esquema OpenAPI |
| `python manage.py test` | Ejecuta las 53 pruebas |

### 4.5 Autenticación de prueba

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin1234"}'
# → {"access":"<JWT>","refresh":"<JWT>","user":{...}}

curl http://127.0.0.1:8000/api/dashboard/ -H "Authorization: Bearer <JWT>"
```

---

## 5. Evidencias de funcionamiento

| Evidencia | Ubicación | Contenido |
|---|---|---|
| Salida de la suite de pruebas | `evidencias/pruebas_integracion.txt` | Ejecución completa de `python manage.py test -v 2`: **53 pruebas, 0 fallos, código de salida 0** |

**Cobertura por aplicación** (53 pruebas de integración y unitarias):

| Aplicación | Pruebas | Tipo | Qué verifica |
|---|---|---|---|
| `attendance` | 14 | Unitarias / API | Check-in, check-out, escaneo de QR, cierres de asistencias antiguas, restricción de una asistencia abierta por persona, filtros por fecha y cliente |
| `history` | 8 | API | Historial por cliente (secciones y totales), filtros por rango de fechas, errores 400, línea de tiempo global ordenada, filtros por tipo, paginación |
| `users` | 9 | API | Login JWT, refresh con rotación, `/auth/me/`, listar usuarios solo como admin, hash de contraseñas, longitud mínima, sincronización de `is_staff` con el rol |
| `members` | 6 | API | Permisos por rol, alta de clientes, email duplicado, *soft-delete* que conserva el registro, restauración solo por admin |
| `coaches` | 4 | API | Alta y listado, flujo check-in/check-out, historial agregado, borrado lógico |
| `dashboard` | 3 | API | Métricas calculadas sobre datos reales, dashboard vacío, restricción por rol |
| `memberships` | 3 | API | Cálculo automático de `end_date`, filtro por cliente, cancelación de membresía |
| `payments` | 3 | API | Registro del cobrador, filtros por membresía y cliente, acceso anónimo rechazado |
| `plans` | 3 | API | Recepción lista pero no crea, administración crea y actualiza, anónimo rechazado |

**Reproducir la evidencia:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # usar bloque SQLite
python manage.py test -v 2
```

**Defectos detectados y corregidos por las pruebas durante esta entrega:**

1. `members/views.py → IsAdminOrReceptionist.has_permission`: un usuario anónimo provocaba
   `AttributeError: 'AnonymousUser' object has no attribute 'role'` (HTTP 500). Ahora se valida
   `is_authenticated` y responde 401.
2. `dashboard/views.py → DashboardStatsView.get`: el filtro del mes generaba el aviso
   `RuntimeWarning: DateTimeField Payment.payment_date received a naive datetime`. Se cambió a
   `payment_date__date__gte=first_day_of_month`.

---

# PART II — TECHNICAL DOCUMENTATION (ENGLISH)

## 1. General information

**FitWeb Backend** is a RESTful API that centralizes the administrative management of gyms: staff
members (administrators, receptionists and coaches), customers, subscription plans, memberships,
payments, physical access control (check-in / check-out) and the metrics shown on the
administration dashboard.

- **Stack:** Python 3.12 · Django 6.1 · Django REST Framework 3.18 · SimpleJWT · drf-spectacular
  (OpenAPI 3) · PostgreSQL 17 (or SQLite locally) · Docker / Docker Compose.
- **Architecture:** a Django project with **9 applications** (`users`, `members`, `plans`,
  `memberships`, `payments`, `attendance`, `dashboard`, `coaches`, `history`) plus the `config`
  project package. Every application follows the *model → serializer → view → url → test* layering.
- **Authentication:** JSON Web Tokens (`Authorization: Bearer <access>`) with refresh rotation.
- **Live API documentation:** Swagger UI at `/api/schema/swagger-ui/` and the OpenAPI schema at
  `/api/schema/` (versioned as `schema.yaml` in the project root).

### 1.1 Inventory of Python files

| Application | Python files (excluding migrations) | Responsibility |
|---|---|---|
| `config/` | `settings.py`, `urls.py`, `views.py`, `serializers.py`, `wsgi.py`, `asgi.py` | Settings, root routing, health check and shared serializers |
| `users/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed.py`, `management/commands/seed_all.py` | JWT authentication and staff management |
| `members/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed_members.py` | Gym customers with soft deletion |
| `plans/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed_plans.py` | Subscription plan catalog |
| `memberships/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed_memberships.py` | Customer ↔ plan subscriptions |
| `payments/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed_payments.py` | Financial record of payments |
| `attendance/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `services.py`, `admin.py`, `apps.py`, `tests.py`, `management/commands/seed_attendance.py`, `management/commands/close_stale_attendances.py` | Physical access control and QR scanning |
| `dashboard/` | `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, `models.py` | Aggregated dashboard metrics |
| `coaches/` | `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py` | Coaches and their attendance |
| `history/` | `serializers.py`, `views.py`, `urls.py`, `apps.py`, `tests.py` | Aggregated customer history and global timeline |
| `scripts/` | `generar_diccionario_datos.py`, `generar_datos_prueba.py` | Utilities that produce the complementary files |
| root | `manage.py` | Django command-line utility |

**Totals:** 122 `.py` files (101 project files + 21 files under `migrations/`, of which 13 are schema migrations and 8 are `__init__.py`).

### 1.2 Public endpoints

| Method | Route | View / class | Module |
|---|---|---|---|
| GET | `/api/health/` | `config.views.HealthView.get` | config |
| POST | `/api/auth/login/` | `users.views.LoginView.post` | users |
| POST | `/api/auth/refresh/` | `users.views.RefreshView.post` | users |
| GET/PUT/PATCH | `/api/auth/me/` | `users.views.MeView` | users |
| GET/POST | `/api/users/` | `users.views.UserListCreateView` | users |
| GET/PUT/PATCH/DELETE | `/api/users/{id}/` | `users.views.UserDetailView` | users |
| GET/POST | `/api/members/` | `members.views.MemberListCreateView` | members |
| GET/PUT/PATCH | `/api/members/{id}/` | `members.views.MemberDetailView` | members |
| DELETE | `/api/members/{id}/delete/` | `members.views.MemberDeleteView.delete` | members |
| POST | `/api/members/{id}/restore/` | `members.views.MemberRestoreView.post` | members |
| GET/POST | `/api/plans/` | `plans.views.PlanListCreateView` | plans |
| GET/PUT/PATCH/DELETE | `/api/plans/{id}/` | `plans.views.PlanDetailView` | plans |
| GET/POST | `/api/memberships/` | `memberships.views.MembershipListCreateView` | memberships |
| GET/PUT/PATCH | `/api/memberships/{id}/` | `memberships.views.MembershipDetailView` | memberships |
| GET/POST | `/api/payments/` | `payments.views.PaymentListCreateView` | payments |
| GET/PUT/PATCH | `/api/payments/{id}/` | `payments.views.PaymentDetailView` | payments |
| GET | `/api/attendance/` | `attendance.views.AttendanceListView` | attendance |
| POST | `/api/attendance/check-in/` | `attendance.views.CheckInView.post` | attendance |
| POST | `/api/attendance/scan/` | `attendance.views.ScanQrView.post` | attendance |
| POST | `/api/attendance/{id}/check-out/` | `attendance.views.CheckOutView.post` | attendance |
| GET | `/api/dashboard/` | `dashboard.views.DashboardStatsView.get` | dashboard |
| GET/POST | `/api/coaches/` | `coaches.views.CoachListCreateView` | coaches |
| GET/PUT/PATCH/DELETE | `/api/coaches/{id}/` | `coaches.views.CoachDetailView` | coaches |
| GET | `/api/coaches/{id}/history/` | `coaches.views.CoachHistoryView.get` | coaches |
| POST | `/api/coaches/{id}/check-in/` | `coaches.views.CoachCheckInView.post` | coaches |
| POST | `/api/coaches/{id}/check-out/` | `coaches.views.CoachCheckOutView.post` | coaches |
| GET | `/api/members/{id}/history/` | `history.views.MemberHistoryView.get` | history |
| GET | `/api/history/` | `history.views.GlobalHistoryView.get` | history |
| GET | `/api/schema/`, `/api/schema/swagger-ui/` | drf-spectacular | config |

---

## 2. Map of the topics studied during the course

Numbering (`1`–`40`) follows the *Source code validation checklist*. Every row states the **file**,
the **class / function / method** and **what is implemented**.

### A. Programming and Python fundamentals (items 1–8)

| # | Topic | File(s) | Class / function / method | Implementation |
|---|---|---|---|---|
| 1 | Identified problem or need | `README.md`, `attendance/services.py`, `members/models.py`, `memberships/models.py` | business docstrings | Gym administration: `attendance/services.py` documents access control; `members/models.py` preserves the accounting trail through soft deletion; `memberships/models.py` computes the end date |
| 2 | Identifiable functional requirements | `users/views.py`, `attendance/views.py`, `memberships/views.py`, `payments/views.py`, `dashboard/views.py`, `history/views.py` | `LoginView`, `RefreshView`, `MeView`, `CheckInView`, `CheckOutView`, `ScanQrView`, `MembershipListCreateView`, `PaymentListCreateView`, `DashboardStatsView`, `MemberHistoryView`, `GlobalHistoryView` | 11 requirements implemented and documented in `schema.yaml` |
| 3 | Descriptive variable names | `dashboard/views.py`, `attendance/services.py`, `members/management/commands/seed_members.py` | `active_members_count`, `monthly_revenue`, `next_week`, `expiring_memberships`, `start_of_today`, `closed`, `created_count`, `skipped_count` | Self-explanatory names throughout the project |
| 4 | `int`, `float`, `str`, `bool` types | `plans/models.py`, `dashboard/serializers.py`, `attendance/serializers.py`, `members/serializers.py`, `users/management/commands/seed_all.py` | `DecimalField`, `PositiveIntegerField`, `BooleanField`, `IntegerField`, `FloatField`, `ChoiceField`, `type=int` | Types used in models, serializers and CLI arguments |
| 5 | Arithmetic operators | `memberships/models.py`, `dashboard/views.py`, `coaches/models.py`, `history/views.py` | `Membership.save`, `DashboardStatsView.get`, `CoachAttendance.duration_minutes`, `MemberHistoryView.get` | `start_date + timedelta(days=plan.duration_days)`, `today + timedelta(days=7)`, `total_seconds() // 60`, `Sum('amount')` |
| 6 | Comparison and logical operators | `memberships/models.py`, `history/views.py`, `coaches/views.py`, `users/serializers.py`, `config/settings.py`, `attendance/models.py` | `Membership.is_valid`, `_parse_date_range`, `IsAdminOrReceptionist.has_permission`, `UserUpdateSerializer.update` | `==`, `>=`, `and`, `or`, `not`; `Q(...)` conditions in database constraints |
| 7 | Data input and result output | `attendance/views.py`, `history/views.py`, `users/management/commands/seed_all.py`, `dashboard/views.py`, seeders | `CheckInView.post`, `_parse_date_param`, `Command.add_arguments`, `self.stdout.write` | HTTP input (`request.data`, query parameters) and CLI input; JSON output (`Response`) and the Django console |
| 8 | Data type conversions | `attendance/views.py`, `history/views.py`, `dashboard/views.py`, `history/serializers.py` | `_resolve_qr_code`, `_parse_int_param`, `DashboardStatsView.get`, `HistorySummarySerializer` | `int(value)` on `isdigit()`, `float(monthly_revenue)`, `Decimal(...).quantize(Decimal('0.01'))` |

### B. Conditional and repetitive structures (items 9–15)

| # | Topic | File(s) | Class / function / method | Implementation |
|---|---|---|---|---|
| 9 | `if`, `elif`, `else` | `members/management/commands/seed_members.py`, `users/management/commands/seed.py`, `attendance/views.py` | `Command.handle`, `_scan_member` | Branches by gender/status and by open attendance presence |
| 10 | Compound or nested conditions | `history/views.py`, `coaches/views.py`, `attendance/views.py`, `memberships/management/commands/seed_memberships.py` | `_parse_date_range`, `CoachHistoryView.get`, `_resolve_qr_code`, `Command.handle` | Three operands joined by `and`; nested `for` → `if` → `if` |
| 11 | `while` loop | `entrypoint.sh` (inline Python heredoc) | `for attempt in range(30)` with `else: raise SystemExit` | Database availability wait with termination control |
| 12 | `for` loops | `attendance/management/commands/seed_attendance.py`, `members/management/commands/seed_members.py`, `attendance/services.py`, `users/management/commands/seed_all.py` | `Command.handle`, `close_stale_attendances`, `Command.handle` | `for i in range(7)`, `for _ in range(count)`, queryset iteration, `enumerate(steps, start=1)` |
| 13 | Nested loops | `attendance/management/commands/seed_attendance.py`, `history/views.py` | `Command.handle`, `_parse_types` | `for i in range(7)` → `for member in daily_visitors`; inner `split/strip` comprehension |
| 14 | `break` and `continue` | `entrypoint.sh`, `attendance/migrations/0002_close_duplicate_open_attendances.py`, `coaches/migrations/0003_close_duplicate_open_coach_attendances.py` | database wait loop; migration `RunPython` | `break` once connected; `continue` skipping duplicated rows in migrations |
| 15 | Termination conditions | `members/management/commands/seed_members.py`, `history/views.py`, `attendance/views.py`, `entrypoint.sh` | `Command.add_arguments`, `GlobalHistoryView.get`, `_resolve_qr_code` | `range(count)`, bounded pagination `max(1, min(limit, MAX_EVENT_LIMIT))`, early `return` |

### C. Strings and data structures (items 16–23)

| # | Topic | File(s) | Class / function / method | Implementation |
|---|---|---|---|---|
| 16 | String manipulation | `attendance/views.py`, `history/views.py`, `users/management/commands/seed.py`, `plans/management/commands/seed_plans.py`, `attendance/models.py` | `_resolve_qr_code`, `_parse_types`, `Command.handle`, `Attendance.__str__` | `.strip().upper()`, `.startswith()`, `.isdigit()`, `.split(',')`, `', '.join(...)`, f-strings, `strftime` |
| 17 | Indexing elements | `attendance/views.py`, `history/views.py`, `members/management/commands/seed_members.py` | `_resolve_qr_code`, `GlobalHistoryView.get`, `Command.handle` | String slice `code[len(prefix):]`, list slice `events[offset:offset + limit]`, `choice[0]` |
| 18 | Lists to store elements | `members/models.py`, `payments/models.py`, `users/models.py`, `config/settings.py`, `attendance/serializers.py` | `TextChoices` `Status`/`Gender`, `Method`, `Role`, `INSTALLED_APPS`, `ChoiceField` | Option lists and project configuration lists |
| 19 | Adding, querying and updating list items | `config/settings.py`, `history/views.py`, `users/management/commands/seed.py` | `ALLOWED_HOSTS.append`, `CSRF_TRUSTED_ORIGINS.append`, `GlobalHistoryView.get`, `users_data` | `events = []`, `events.extend(...)`, `dict.fromkeys(...)` |
| 20 | `append()`, `remove()` or `len()` | `config/settings.py`, `history/views.py`, `users/management/commands/seed_all.py`, `attendance/management/commands/seed_attendance.py` | two `append()` calls in settings, `len(events)`, `len(steps)`, `min(len(members), ...)` | Note: `remove()` is not used; deletion is logical (`deleted_at`) |
| 21 | Tuples for immutable values | `history/serializers.py`, `attendance/views.py`, `config/settings.py` | `HistoryEventType.CHOICES`, `return kind, int(value)`, `permission_classes = (IsAdminOrReceptionist,)`, `AUTH_HEADER_TYPES` | Option tuples, multiple return values and permission tuples |
| 22 | Dictionaries as records | `dashboard/views.py`, `history/views.py`, `users/management/commands/seed.py`, `config/settings.py` | `DashboardStatsView.get` payload, `summary`/`data`/`metadata`, `users_data`, `DATABASES` | Dictionaries for JSON payloads and configurations |
| 23 | Querying and updating dictionaries | `attendance/views.py`, `payments/views.py`, `users/serializers.py`, `history/views.py`, `payments/serializers.py` | `.get()` on query params, `data["user"] = ...`, `metadata['duration_minutes'] = ...`, `validated_data['received_by'] = ...` | Key reading and key assignment |

### D. Vectors, matrices and aggregations (items 24–30)

| # | Topic | File(s) | Class / function / method | Implementation |
|---|---|---|---|---|
| 24 | One-dimensional structure | `history/views.py`, `users/management/commands/seed_all.py`, `plans/management/commands/seed_plans.py`, `attendance/management/commands/seed_attendance.py` | `events = []`, `steps`, `plans_data`, `members = list(...)` | Working lists of each command and view |
| 25 | Traversal by index or loop | `plans/management/commands/seed_plans.py`, `attendance/management/commands/seed_attendance.py`, `users/management/commands/seed_all.py`, `history/views.py` | `for data in plans_data`, `for i in range(7)`, `enumerate(steps, start=1)`, access through `offset` | Loops with explicit indexing |
| 26 | Ascending or descending ordering | `history/views.py`, `memberships/models.py`, `plans/models.py`, `payments/models.py` | `events.sort(key=lambda event: event['date'], reverse=True)`, `Meta.ordering` | Descending by date; ascending by `price` on plans |
| 27 | Searching inside a collection | `dashboard/views.py`, `payments/views.py`, `memberships/views.py`, `members/views.py`, `attendance/services.py` | `.filter()`, `.get()`, `.exists()`, `.first()` | Sequential search through the ORM |
| 28 | Matrix / two-dimensional structure | `attendance/views.py`, `users/management/commands/seed_all.py`, `config/settings.py` | `for prefix, kind in ((MEMBER_QR_PREFIX, 'member'), ...)`, `steps = [(name, [args]), ...]`, `TEMPLATES`, `SPECTACULAR_SETTINGS['TAGS']` | Tuple tables and nested dictionaries instead of literal matrices |
| 29 | Accessing rows and columns | `attendance/views.py`, `users/management/commands/seed_all.py`, `plans/management/commands/seed_plans.py`, `config/settings.py` | row unpacking, `data["name"]`, `DATABASES['default']['ENGINE']` | Access by position and by key |
| 30 | Sums, totals and averages | `dashboard/views.py`, `history/views.py`, `coaches/views.py`, `history/serializers.py` | `aggregate(total=Sum('amount'))`, `Coalesce(Sum(...))`, `sum(... duration_minutes ...)`, `get_total_paid` | Totals and counts through ORM aggregation functions |

### E. Functions, procedures and modularization (items 31–36)

| # | Topic | File(s) | Class / function / method | Implementation |
|---|---|---|---|---|
| 31 | Functions with `def` | `attendance/services.py`, `history/views.py`, `members/views.py`, `manage.py` | the 5 functions in `services.py`, 6 helpers in `history/views.py`, `IsAdminOrReceptionist.has_permission`, `main` | Main reuse unit of the project |
| 32 | Functions with parameters and arguments | `attendance/services.py`, `history/views.py`, `attendance/tests.py` | `check_out_time(attendance, now=None)`, `create_attendance(model, **fields)`, `_parse_date_param(request, name)`, `_filter_by_date(queryset, field, date_from, date_to)`, `local_datetime(day, hour, ...)` | Parameterized functions with default arguments |
| 33 | Functions with `return` | `attendance/services.py`, `config/views.py`, `members/views.py`, `history/views.py` | the 5 functions of `services.py`, `HealthView.get`, `has_permission`, multiple returns | Explicit return in every service function |
| 34 | Procedures without return value | `*/management/commands/seed*.py`, `attendance/management/commands/close_stale_attendances.py`, `members/models.py` | `handle()`, `flush_related()`, `Member.delete()` | Side-effect procedures: seeding, clean-up and logical deletion |
| 35 | At least one `lambda` function | `history/views.py` | `events.sort(key=lambda event: event['date'], reverse=True)` | Sorting with a key function |
| 36 | Reusable functions and proper variable scope | `attendance/services.py`, `members/models.py`, `members/views.py`, `history/views.py` | `SoftDeleteManager`, `AllObjectsManager`, `IsAdminOrReceptionist` (used by 8 apps), `_parse_date_param` | Core logic shared by several applications |

### F. Object-oriented programming (classes, inheritance, encapsulation)

| Topic | File(s) | Class / method | Implementation |
|---|---|---|---|
| Domain model | `users/models.py`, `members/models.py`, `plans/models.py`, `memberships/models.py`, `payments/models.py`, `attendance/models.py`, `coaches/models.py` | `User`, `Member`, `Plan`, `Membership`, `Payment`, `Attendance`, `Coach`, `CoachAttendance` | 8 models with fields, choices (`TextChoices`) and `Meta.ordering` |
| Inheritance | `users/models.py`, `members/models.py` | `User(AbstractUser)`, `SoftDeleteManager(models.Manager)`, `AllObjectsManager(models.Manager)` | Specialization of the Django user and custom managers |
| Encapsulation and properties | `members/models.py`, `memberships/models.py`, `coaches/models.py` | `full_name`, `qr_code`, `is_deleted`, `is_valid`, `duration_minutes` | Read-only `@property` for derived data |
| Behaviour inside the model | `members/models.py`, `memberships/models.py` | `Member.delete()`, `Member.restore()`, `Member.hard_delete()`, `Membership.save()` | Business rules in the model (automatic `end_date` calculation) |
| Polymorphism / reusable views | `members/views.py`, `plans/views.py`, `memberships/views.py`, `payments/views.py`, `attendance/views.py` | DRF `ListCreateAPIView`, `RetrieveUpdateAPIView`, `ListAPIView` | Generic classes reused across the 9 modules |
| Service composition | `attendance/services.py`, `attendance/views.py`, `coaches/views.py` | `create_attendance(model, **fields)` | One service handles both `Attendance` and `CoachAttendance` |

### G. Documentation, quality and operation (items 37–40)

| # | Topic | File(s) | Class / function / method | Implementation |
|---|---|---|---|---|
| 37 | Documented code with comments | `attendance/services.py`, `dashboard/views.py`, `attendance/views.py`, `history/views.py`, seeders | docstrings and numbered comments (`# 1. Total de miembros activos` …) | Inline documentation of the business logic |
| 38 | Correct execution without errors | `*/tests.py`, `config/views.py`, `entrypoint.sh`, `Dockerfile`, `docker-compose.yml` | 53 tests, `HealthView.get`, `manage.py migrate`, `collectstatic` | See section **5. Evidence of operation** |
| 39 | Data validation and error handling | `users/serializers.py`, `attendance/serializers.py`, `attendance/views.py`, `members/views.py`, `history/views.py`, `attendance/models.py` | `min_length=8`, `IntegerField`, `ChoiceField`, `ValidationError`, `try/except` → 404, `_parse_int_param`, `UniqueConstraint` | Validation in serializers, views and the database |
| 40 | Integrated and demonstrable features | `config/urls.py`, `users/management/commands/seed_all.py`, `schema.yaml`, `README.md` | `urlpatterns`, `Command.handle`, `flush_related` | 28 endpoints mounted under `/api/` + Swagger + chained seeders |

---

## 3. Complementary files

| File | Description |
|---|---|
| `complementos/diccionario_datos.xlsx` | Data dictionary of the 8 model tables. Sheets: **Modelos / Models** (table, class, record count), **Campos / Fields** (type, detail, constraints, relation) and **Relaciones / Relations** (FK / OneToOne with `on_delete`) |
| `complementos/datos_prueba.xlsx` | Export of the data produced by the seeders. Sheets: **Resumen / Summary**, **Usuarios / Users**, **Clientes / Members**, **Planes / Plans**, **Membresías / Memberships**, **Pagos / Payments**, **Asistencias / Attendance**, **Entrenadores / Coaches**, **Asistencias entrenadores / Coach attendance** |
| `scripts/generar_diccionario_datos.py` | Script that produces the data dictionary (walks `apps.get_models()` and `model._meta.get_fields()`) |
| `scripts/generar_datos_prueba.py` | Script that exports database records to Excel |
| `requirements.txt` | Runtime dependencies of the API |
| `requirements-dev.txt` | Extra dependencies to regenerate the Excel files (`openpyxl`) |
| `.env.example` | Environment variable template (copy to `.env`) |
| `schema.yaml` | Versioned OpenAPI 3 schema (source of truth for the frontend) |
| `seed.sh` | Chained execution of the 6 individual seeders |
| `Dockerfile`, `docker-compose.yml`, `docker-compose.dev.yml`, `entrypoint.sh`, `render.yaml` | Reproducible deployment (containers, development, production) |
| `logo.png` | Official logo used in README and Swagger |

> Regenerating the Excel files:
> ```bash
> pip install -r requirements-dev.txt
> python scripts/generar_diccionario_datos.py
> python scripts/generar_datos_prueba.py
> ```

---

## 4. Dependencies and execution instructions

### 4.1 Dependencies

| Library | Version | Use in the project |
|---|---|---|
| `Django` | 6.1.1 | Web framework, ORM, migrations, admin |
| `djangorestframework` | 3.18.1 | Serializers, generic views, permissions |
| `djangorestframework_simplejwt` | 5.5.1 | JWT issuance and rotation |
| `PyJWT` | 2.15.1 | Token signing/verification |
| `drf-spectacular` (+ `sidecar`) | 0.30.0 / 2026.10.1 | OpenAPI schema generation and local Swagger UI |
| `django-cors-headers` | 4.9.0 | API consumption from the React frontend |
| `dj-database-url` | 3.1.2 | `DATABASE_URL` connection (Render / Neon / Supabase) |
| `python-decouple` | 3.8 | Typed environment variable reading |
| `psycopg[binary]` | 3.3.6 | PostgreSQL driver |
| `whitenoise` | 6.12.0 | Static file serving without Nginx |
| `gunicorn` | 26.2.0 | Production WSGI server |
| `Faker` | 40.40.0 | Fake data in the seeders |
| `openpyxl` (*dev*) | 3.1.5 | Generation of the complementary Excel files |

### 4.2 Local execution (without Docker)

```bash
# 1. Virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Dependencies
pip install -r requirements.txt

# 3. Environment variables
cp .env.example .env               # in .env: SECRET_KEY, DEBUG=True and the SQLite block

# 4. Database
python manage.py migrate

# 5. Sample data (optional)
python manage.py seed_all --count=100

# 6. Server
python manage.py runserver          # http://127.0.0.1:8000/
```

### 4.3 Execution with Docker

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build   # development
docker compose up --build -d                                              # production (gunicorn)
docker compose exec web python manage.py seed_all                          # sample data
```

### 4.4 Custom management commands

| Command | Purpose |
|---|---|
| `python manage.py seed` | Default administrator (`admin` / `admin1234`) and roles |
| `python manage.py seed_members [--count=N]` | Fake customers |
| `python manage.py seed_plans` | Plan catalog |
| `python manage.py seed_memberships` | Assigns memberships to customers |
| `python manage.py seed_payments` | Generates the payments of those memberships |
| `python manage.py seed_attendance` | Simulates access over the last 7 days |
| `python manage.py seed_all [--count=N] [--flush]` | Runs the 6 seeders in order |
| `python manage.py close_stale_attendances` | Closes attendances left open on previous days |
| `python manage.py spectacular --file schema.yaml --validate` | Regenerates and validates the OpenAPI schema |
| `python manage.py test` | Runs the 53 tests |

### 4.5 Test authentication

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin1234"}'
# → {"access":"<JWT>","refresh":"<JWT>","user":{...}}

curl http://127.0.0.1:8000/api/dashboard/ -H "Authorization: Bearer <JWT>"
```

---

## 5. Evidence of operation

| Evidence | Location | Content |
|---|---|---|
| Test suite output | `evidencias/pruebas_integracion.txt` | Full run of `python manage.py test -v 2`: **53 tests, 0 failures, exit code 0** |

**Coverage per application** (53 unit and integration tests):

| Application | Tests | Type | What it verifies |
|---|---|---|---|
| `attendance` | 14 | Unit / API | Check-in, check-out, QR scanning, closing of stale attendances, one-open-attendance-per-person constraint, filters by date and customer |
| `history` | 8 | API | Customer history (sections and totals), date-range filters, 400 errors, ordered global timeline, type filters, pagination |
| `users` | 9 | API | JWT login, refresh rotation, `/auth/me/`, admin-only user listing, password hashing, minimum length, `is_staff` ↔ role synchronization |
| `members` | 6 | API | Role permissions, customer creation, duplicate email, soft delete that keeps the row, admin-only restore |
| `coaches` | 4 | API | Creation and listing, check-in/check-out flow, aggregated history, logical deletion |
| `dashboard` | 3 | API | Metrics computed from real data, empty dashboard, role restriction |
| `memberships` | 3 | API | Automatic `end_date` calculation, filter by customer, membership cancellation |
| `payments` | 3 | API | Receiver registration, filters by membership and customer, anonymous access rejected |
| `plans` | 3 | API | Receptionist can list but not create, admin creates and updates, anonymous rejected |

**Reproducing the evidence:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # use the SQLite block
python manage.py test -v 2
```

**Defects found and fixed by these tests during this delivery:**

1. `members/views.py → IsAdminOrReceptionist.has_permission`: an anonymous user raised
   `AttributeError: 'AnonymousUser' object has no attribute 'role'` (HTTP 500). It now validates
   `is_authenticated` and answers 401.
2. `dashboard/views.py → DashboardStatsView.get`: the current-month filter emitted
   `RuntimeWarning: DateTimeField Payment.payment_date received a naive datetime`. It now uses
   `payment_date__date__gte=first_day_of_month`.

