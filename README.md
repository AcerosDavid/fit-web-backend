<div align="center">
  <img src="logo.png" alt="Fit Web Logo" width="400">
  
  # Fit Web - Backend API 🚀
  **El motor inteligente detrás de la gestión de tu gimnasio.**
  
  <br>
  
  ![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)
  ![Django REST Framework](https://img.shields.io/badge/Django_REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
  ![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)
  ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
  ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
</div>

<br/>

Este repositorio contiene exclusivamente el **Backend (API RESTful)** del sistema **Fit Web**. Está desarrollado con **Python y Django REST Framework** para proveer un núcleo robusto, seguro y escalable que alimenta las aplicaciones de cliente (Frontend / Móvil).

A través de JSON Web Tokens (JWT), esta API administra las operaciones clave: control de clientes, planes, membresías, contabilidad de pagos y el registro de asistencia mediante check-in/check-out.

---

## 🏗 Arquitectura y Módulos (Apps)

El proyecto está dividido en 7 aplicaciones modulares de Django:

1. **`users`**: Autenticación y gestión del Staff (Administradores y Recepcionistas).
2. **`members`**: Registro de clientes del gimnasio (con soporte de *soft-delete* para no borrar el historial contable).
3. **`plans`**: Catálogo de planes de suscripción (Mensual, Trimestral, Anual).
4. **`memberships`**: Suscripciones activas que conectan a un cliente con un plan (calcula la fecha de fin automáticamente).
5. **`payments`**: Registro financiero de cobros (Efectivo, Tarjeta, Transferencia).
6. **`attendance`**: Control de acceso físico (Check-in / Check-out).
7. **`dashboard`**: API que agrega métricas financieras y operativas en tiempo real para gráficas.

---

## 🚀 Requisitos Previos

Asegúrate de tener instalado en tu sistema:
- Python 3.12 o superior (Django 6.1).
- Git.

Para ejecutarlo con Docker:
- [Docker](https://docs.docker.com/get-docker/) con Docker Compose v2.

---

## 🐳 Ejecución con Docker (recomendada)

El proyecto incluye `docker-compose.yml` (producción, **gunicorn**) y `docker-compose.dev.yml` (desarrollo, `runserver` con recarga en caliente). PostgreSQL 17 corre como servicio `db` y las migraciones/estáticos se aplican automáticamente al arrancar.

### 1. Configurar variables de entorno
```bash
cp .env.example .env
```
*(Genera una clave secreta con: `python -c "import secrets; print(secrets.token_urlsafe(50))"`)*

> `DEBUG` y la base de datos en Docker los fija el propio `docker-compose.yml`: **`DEBUG=False` en producción** y **`DEBUG=True` en desarrollo**. En tu `.env` solo se usan `SECRET_KEY`, `ALLOWED_HOSTS` y las credenciales de PostgreSQL (`DB_NAME`, `DB_USER`, `DB_PASSWORD`).

### 2. Desarrollo (recarga en caliente)
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```
API en `http://127.0.0.1:8000/` y PostgreSQL publicado en el host por el puerto `5434` (configurable con `DB_HOST_PORT` en tu `.env`).

#### Adminer (solo en desarrollo)
El override de desarrollo incluye [Adminer](https://www.adminer.org/) para gestionar la BD con interfaz web en `http://127.0.0.1:8081/` (configurable con `ADMINER_PORT`). Credenciales del login:

| Campo | Valor |
|---|---|
| Sistema | PostgreSQL |
| Servidor | `db` (ya precargado) |
| Usuario | `postgres` |
| Contraseña | `postgres` |
| Base de datos | `fit_gym` |

> ⚠️ Adminer **no existe en producción** (solo se define en `docker-compose.dev.yml`).

### 3. Producción (gunicorn)
```bash
docker compose up --build -d
```
El servicio `web` solo pasa a `healthy` cuando la BD responde, las migraciones corren y los estáticos se recopilan (servidos con WhiteNoise, por lo que `/admin/` funciona con `DEBUG=False`).

### 4. Seeders de datos de prueba
Se ejecutan **una sola vez**, en este orden:
```bash
docker compose exec web python manage.py seed_all
```
`seed_all` corre los 6 seeders en orden (`seed`, `seed_members`, `seed_plans`, `seed_memberships`, `seed_payments`, `seed_attendance`). Opciones: `--count=N` (miembros, default 100) y `--flush` (borra pagos, asistencias, membresías, miembros y usuarios antes de sembrar).

O individualmente:
```bash
docker compose exec web python manage.py seed
docker compose exec web python manage.py seed_members
docker compose exec web python manage.py seed_plans
docker compose exec web python manage.py seed_memberships
docker compose exec web python manage.py seed_payments
docker compose exec web python manage.py seed_attendance
```

### 5. Otras operaciones útiles
```bash
docker compose logs -f web                 # Logs del API
docker compose exec web python manage.py shell
docker compose exec web python manage.py test
docker compose down                         # Parar (los datos persisten en el volumen pgdata)
docker compose down -v                      # Parar y borrar la base de datos
```

### Salud del servicio
`GET /api/health/` devuelve `{"status": "ok"}` y se usa como healthcheck del contenedor.

---

## 📖 Documentación de la API (Swagger)

La API se documenta con **[drf-spectacular](https://drf-spectacular.readthedocs.io)** (OpenAPI 3) y se sirve con assets locales (`drf-spectacular-sidecar`, sin CDN):

| URL | Contenido |
|---|---|
| `http://127.0.0.1:8000/api/schema/swagger-ui/` | **Swagger UI** interactiva (con "Try it out") |
| `http://127.0.0.1:8000/api/schema/` | Esquema OpenAPI (JSON; `?format=yaml` para YAML) |

Ambos son **públicos** (no requieren token). El esquema se genera automáticamente desde el código (`@extend_schema` en las vistas).

### Regenerar `schema.yaml` (versionado en el repo)
El archivo `schema.yaml` de la raíz es la fuente de verdad para los clientes (frontend/móvil). **Se regenera y se commitea en cada cambio de API:**
```bash
docker compose exec web python manage.py spectacular --file schema.yaml --validate
# o en desarrollo:
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py spectacular --file schema.yaml --validate
```
La validación debe terminar **sin warnings ni errors**.

### Mantenimiento automático con IA
Existe un skill multi-IA en [`.agents/skills/actualizar-swagger/SKILL.md`](.agents/skills/actualizar-swagger/SKILL.md) (compatible con Devin, opencode, Cursor, Codex, Gemini CLI, Copilot…): cada vez que se crea o modifica un endpoint/serializer/modelo, la IA debe anotarlo con `@extend_schema`, regenerar `schema.yaml` y verificar la UI.

---

## 🛠 Instalación y Configuración (Entorno de Desarrollo)

Sigue estos pasos para clonar y ejecutar la API en tu máquina local:

### 1. Clonar el repositorio
```bash
git clone <https://github.com/AcerosDavid/fit-web-backend.git>
cd fit-web-backend
```

### 2. Crear y activar el entorno virtual
En **Windows**:
```bash
python -m venv .venv
.venv\Scripts\activate
```
En **Mac/Linux**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno
Django necesita una clave secreta y credenciales de base de datos para funcionar. Copia el archivo de ejemplo para crear tu propio archivo `.env`:
```bash
cp .env.example .env
```
*(Puedes generar una nueva clave secreta para tu `.env` ejecutando: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)*

> ⚠️ Si vas a correr **sin Docker**, comenta el bloque de PostgreSQL en tu `.env` y descomenta el bloque de **SQLite** (`.env.example` trae PostgreSQL por defecto porque es lo que usa `docker-compose`).

### 5. Preparar la Base de Datos (Migraciones)
Corre el siguiente comando para construir el esquema de la base de datos (por defecto usará SQLite local, modificable en tu `.env`):
```bash
python manage.py migrate
```

### 6. Población de datos falsos (Seeders)
Para no probar el sistema vacío, hemos creado comandos que llenan la base de datos con información aleatoria y realista. Todos en un solo paso:

```bash
python manage.py seed_all            # options: --count=50, --flush
```

O **exactamente en este orden**:

```bash
# 1. Crea el admin por defecto y los roles
python manage.py seed

# 2. Crea 100 clientes de prueba
python manage.py seed_members

# 3. Crea los 3 planes básicos
python manage.py seed_plans

# 4. Asigna membresías aleatorias a los clientes
python manage.py seed_memberships

# 5. Genera los registros de pagos de esas membresías
python manage.py seed_payments

# 6. Simula gente entrando al gimnasio en los últimos 7 días
python manage.py seed_attendance
```

### 7. Levantar el Servidor
```bash
python manage.py runserver
```
El backend estará corriendo y escuchando peticiones en `http://127.0.0.1:8000/`.

---

## 🔑 Autenticación y Pruebas de la API

Todos los endpoints `/api/` (excepto el login) están estrictamente protegidos. Para interactuar con la API en herramientas como Postman o Insomnia:

1. Haz una petición `POST` a `http://127.0.0.1:8000/api/auth/login/` con el body:
   ```json
   {
       "username": "admin",
       "password": "admin1234"
   }
   ```
2. Copia el `access` token que te retorna el servidor.
3. En tus futuras peticiones (por ejemplo, a `/api/dashboard/`), agrega este token en los **Headers**:
   ```
   Authorization: Bearer <TU_TOKEN>
   ```

---

## ✅ Lista de chequeo – Ubicación de cada ítem en el proyecto

Mapa de los 40 ítems de la *Lista de chequeo – Validación del código fuente* (Asignatura: Diseño Funcional) sobre el código de este repositorio. Las rutas son relativas a la raíz del proyecto.

### A. Fundamentos de programación y Python (8 ítems)

| N.º | Criterio | Ubicación en el proyecto |
|---|---|---|
| 1 | Problema o necesidad identificada | `README.md` (secciones de arquitectura y módulos) y docstrings de negocio: `attendance/services.py`, `members/models.py` (soft-delete para conservar el historial contable), `memberships/models.py` (`Membership.save` calcula el `end_date` automáticamente) |
| 2 | Al menos tres requerimientos funcionales identificables | `users/views.py` (`LoginView`, `RefreshView`, `MeView`), `attendance/views.py` (`CheckInView`, `CheckOutView`, `ScanQrView`), `memberships/views.py` (`MembershipListCreateView`), `payments/views.py` (`PaymentListCreateView`), `dashboard/views.py` (`DashboardStatsView`), `history/views.py` (`MemberHistoryView`, `GlobalHistoryView`) — todos documentados en `schema.yaml` |
| 3 | Variables con nombres descriptivos | `dashboard/views.py` (`active_members_count`, `monthly_revenue`, `next_week`, `expiring_memberships`), `attendance/services.py` (`start_of_today`, `closed`), `members/management/commands/seed_members.py` (`created_count`, `skipped_count`) |
| 4 | Tipos `int`, `float`, `str`, `bool` | `plans/models.py` (`DecimalField`, `PositiveIntegerField`, `BooleanField`), `dashboard/serializers.py` (`IntegerField`, `FloatField`), `attendance/serializers.py` (`IntegerField`, `ChoiceField`), `members/serializers.py` (`BooleanField`), `users/management/commands/seed_all.py` (`type=int` en `--count`) |
| 5 | Operadores aritméticos para cálculos | `memberships/models.py` (`start_date + timedelta(days=plan.duration_days)`), `dashboard/views.py` (`today + timedelta(days=7)`, `today.replace(day=1)`), `coaches/models.py` (`duration_minutes` con `total_seconds() // 60`), `history/views.py` (`Sum('amount')`) |
| 6 | Operadores de comparación y lógicos | `memberships/models.py` (`==`, `>=`, `and` en `is_active`), `history/views.py` y `coaches/views.py` (`if date_from and date_to and date_from > date_to`), `users/serializers.py` (`is_superuser or role == ADMIN`), `config/settings.py` (`if not DEBUG and ...`), constraints `Q` en `attendance/models.py` |
| 7 | Entrada de información y salida de resultados * | **Entrada:** `request.data` (`attendance/views.py`, `CheckInView`), query params (`history/views.py`, `_parse_date_param`), argumentos CLI (`users/management/commands/seed_all.py`, `add_arguments`). **Salida:** `Response({...})` JSON (`dashboard/views.py`) y `self.stdout.write(...)` en los seeders. *Nota: al ser una API web no existen `input()`/`print()` literales; la entrada es HTTP/CLI y la salida JSON/consola de Django. El único `print()` literal está en el heredoc de `entrypoint.sh`* |
| 8 | Conversiones de tipos de datos | `attendance/views.py` (`isdigit()` → `int(value)` en `_resolve_qr_code`), `history/views.py` (`_parse_int_param` con `int()` y captura de `ValueError`), `dashboard/views.py` (`float(monthly_revenue)`), `history/serializers.py` (`Decimal(...).quantize(Decimal('0.01'))`) |

### B. Estructuras condicionales y repetitivas (7 ítems)

| N.º | Criterio | Ubicación en el proyecto |
|---|---|---|
| 9 | `if`, `elif` y `else` | `members/management/commands/seed_members.py` (`if/elif/else` según género), `users/management/commands/seed.py` (`if created ... else`), `attendance/views.py` (`_scan_member`: `if active_attendance ... else`), ternarios en `users/management/commands/seed_all.py` y `history/views.py` |
| 10 | Condiciones compuestas o anidadas | `history/views.py` y `coaches/views.py` (tres operandos con `and`), `attendance/views.py` (`_resolve_qr_code`: `for` → `if startswith` → `if isdigit` anidados), `memberships/management/commands/seed_memberships.py` (`if not members or not plans or not admin_user`), `memberships/models.py` (`if not self.end_date and self.plan`) |
| 11 | Ciclo `while` * | Sin `while` literal en el código Python. Equivalente funcional: bucle de reintentos con control de terminación en `entrypoint.sh` (`for attempt in range(30)` → `break` al conectarse → `else: raise SystemExit`). *Nota: no hay menús interactivos (la app es una API); el bucle de espera de la BD cumple el rol de repetición controlada* |
| 12 | Ciclos `for` | `attendance/management/commands/seed_attendance.py` (`for i in range(7)`), `members/management/commands/seed_members.py` (`for _ in range(count)`), `attendance/services.py` (`close_stale_attendances` recorre querysets), `users/management/commands/seed_all.py` (`for index, (name, args) in enumerate(...)`), comprehensions en `config/settings.py` |
| 13 | Ciclos anidados | `attendance/management/commands/seed_attendance.py` (`for i in range(7)` → `for member in daily_visitors`), `history/views.py` (`for raw in raw_values:` con comprehension interna de `split/strip`) |
| 14 | `break` y `continue` * | `break`: `entrypoint.sh` (heredoc Python, sale del bucle al conectar a la BD). `continue`: `attendance/migrations/0002_close_duplicate_open_attendances.py` y `coaches/migrations/0003_close_duplicate_open_coach_attendances.py` (saltan registros duplicados). *Nota: uso mínimo (arranque y migraciones); en la lógica de negocio la salida anticipada se hace con `return` temprano* |
| 15 | Control de condiciones de terminación | `members/management/commands/seed_members.py` (`range(count)` parametrizable con `--count`), `entrypoint.sh` (`range(30)` + `for/else`), `history/views.py` (paginación acotada `max(1, min(limit, MAX_EVENT_LIMIT))` y slicing `events[offset:offset + limit]`), `attendance/views.py` (`return` al primer prefijo coincidente) |

### C. Cadenas y estructuras de datos (8 ítems)

| N.º | Criterio | Ubicación en el proyecto |
|---|---|---|
| 16 | Manipulación de cadenas | `attendance/views.py` (`_resolve_qr_code`: `.strip().upper()`, `.startswith()`, `.isdigit()`), `history/views.py` (`raw.split(',')`, `.strip().lower()`, `', '.join(sorted(...))`), f-strings con formato en `users/management/commands/seed.py` y `plans/management/commands/seed_plans.py`, `strftime` en `attendance/models.py` |
| 17 | Índices para consultar elementos | `attendance/views.py` (slice de cadena `code[len(prefix):]`), `history/views.py` (slice de lista `events[offset:offset + limit]`), `members/management/commands/seed_members.py` (`choice[0] for choice in Member.Status.choices`) |
| 18 | Listas para almacenar elementos | `members/models.py` (`TextChoices` `Status`/`Gender`), `payments/models.py` (`Method`), `users/models.py` (`Role`), `config/settings.py` (`INSTALLED_APPS`, `AUTH_PASSWORD_VALIDATORS`), `attendance/serializers.py` (`ChoiceField`) |
| 19 | Agregar, consultar y modificar elementos de una lista | `config/settings.py` (`ALLOWED_HOSTS.append(...)`, `CSRF_TRUSTED_ORIGINS.append(...)`), `history/views.py` (`events = []` y `events.extend(...)` en `GlobalHistoryView.get`) |
| 20 | `append()`, `remove()` o `len()` | `config/settings.py` (dos `append()`), `history/views.py` (`len(events)`), `users/management/commands/seed_all.py` (`len(steps)`), `attendance/management/commands/seed_attendance.py` (`min(len(members), ...)`). *Nota: no hay `remove()`; los borrados se hacen con `queryset.delete()` o soft-delete (`members/models.py`)* |
| 21 | Tuplas para valores inmutables | `history/serializers.py` (`HistoryEventType.CHOICES`), retornos múltiples en `attendance/views.py` (`return kind, int(value)`), `permission_classes = (IsAdminOrReceptionist,)` en las vistas, `config/settings.py` (`SECURE_PROXY_SSL_HEADER`, `('Bearer',)`) |
| 22 | Diccionarios como registros | `dashboard/views.py` (payload JSON), `history/views.py` (`summary`, `data`, `metadata`), `users/management/commands/seed.py` (`users_data`), `config/settings.py` (`DATABASES`) |
| 23 | Consultar y actualizar diccionarios | `.get()` sobre query params en `attendance/views.py` y `payments/views.py`, `users/serializers.py` (`data["user"] = ...`), `history/views.py` (`metadata['duration_minutes'] = ...`), `payments/serializers.py` (`validated_data['received_by'] = ...`) |

### D. Vectores y matrices (7 ítems)

| N.º | Criterio | Ubicación en el proyecto |
|---|---|---|
| 24 | Estructura unidimensional | `history/views.py` (`events = []`), `users/management/commands/seed_all.py` (`steps`), `plans/management/commands/seed_plans.py` (`plans_data`), `attendance/management/commands/seed_attendance.py` (`members = list(...)`) |
| 25 | Recorridos mediante índices o ciclos | `plans/management/commands/seed_plans.py` (`for data in plans_data`), `attendance/management/commands/seed_attendance.py` (`for i in range(7)`), `users/management/commands/seed_all.py` (`enumerate(steps, start=1)`), `history/views.py` (acceso por índice con `offset`) |
| 26 | Ordenamiento ascendente o descendente | `history/views.py` (`events.sort(key=lambda event: event['date'], reverse=True)` — descendente — y `sorted()` en `_parse_types`), `order_by` en `history/views.py` y `coaches/views.py`, `Meta.ordering` en `memberships/models.py` (`-start_date`) y `plans/models.py` (`price`, ascendente) |
| 27 | Búsqueda dentro de una colección | `.filter()` en `dashboard/views.py`, `payments/views.py` y `memberships/views.py`; `.get()` en `members/views.py` (404 si no existe); `.exists()`/`.first()` en `seed_memberships.py` y `attendance/services.py`. *Nota: búsqueda secuencial vía ORM (no hay búsqueda binaria)* |
| 28 | Matriz / estructura bidimensional * | `attendance/views.py` (tabla de tuplas de 2 columnas: `for prefix, kind in ((MEMBER_QR_PREFIX, 'member'), ...)`), `users/management/commands/seed_all.py` (`steps = [(nombre, [args]), ...]`), `config/settings.py` (`TEMPLATES` y `SPECTACULAR_SETTINGS['TAGS']` anidados), listas de dicts (filas) en los seeders. *Nota: no hay matriz literal `[[...]]`; se usan tablas de tuplas y diccionarios anidados* |
| 29 | Acceder y recorrer filas y columnas | Desempaquetado de filas en `attendance/views.py` (`for prefix, kind in ...`) y `users/management/commands/seed_all.py` (`for index, (name, args) in ...`), acceso por clave de columna en `plans/management/commands/seed_plans.py` (`data["name"]`, `data["price"]`), columna anidada en `config/settings.py` (`DATABASES['default']['ENGINE']`) |
| 30 | Sumas, totales o promedios sobre datos | `dashboard/views.py` (`aggregate(total=Sum('amount'))` y `.count()` de miembros, asistencias y membresías), `history/views.py` (`Coalesce(Sum('amount'), ...)`), `coaches/views.py` (`sum(... duration_minutes ...)`), `history/serializers.py` (`get_total_paid` con `Sum` + `quantize`) |

### E. Funciones, procedimientos y modularización (6 ítems)

| N.º | Criterio | Ubicación en el proyecto |
|---|---|---|
| 31 | Funciones con `def` | `attendance/services.py` (5 funciones), `history/views.py` (10 helpers), `members/views.py` (`IsAdminOrReceptionist.has_permission`), `manage.py` (`main`), `handle()`/`add_arguments()` de los seeders |
| 32 | Funciones con parámetros y argumentos | `attendance/services.py` (`check_out_time(attendance, now=None)`, `create_attendance(model, **fields)`), `history/views.py` (`_parse_date_param(request, name)`, `_filter_by_date(queryset, field, date_from, date_to)`), `attendance/tests.py` (`local_datetime(day, hour, ...)`) |
| 33 | Funciones con `return` | `attendance/services.py` (todas sus funciones), `config/views.py` (`HealthView.get` → `Response({'status': 'ok'})`), `members/views.py` (`has_permission`), retornos múltiples en `history/views.py` |
| 34 | Procedimientos sin valor de retorno | `handle()` de los comandos de seed (`users/management/commands/seed_all.py` y `seed.py`, `members/…/seed_members.py`, `plans/…/seed_plans.py`, `memberships/…/seed_memberships.py`, `payments/…/seed_payments.py`, `attendance/…/seed_attendance.py`), `flush_related()` en `users/management/commands/seed_all.py`, `attendance/management/commands/close_stale_attendances.py`, soft-delete en `members/models.py` (`delete()` solo marca `deleted_at`) |
| 35 | Al menos una función `lambda` | `history/views.py` — `events.sort(key=lambda event: event['date'], reverse=True)` (única `lambda` del proyecto) |
| 36 | Funciones reutilizables y buen alcance de variables | `attendance/services.py` (reutilizado por `attendance/views.py` y `coaches/views.py`), `members/models.py` (`SoftDeleteManager`, `AllObjectsManager`), permiso `IsAdminOrReceptionist` (`members/views.py`) usado en 8 apps, helpers compartidos en `history/views.py` (`_parse_date_param`, `_filter_by_date`) |

### F. Documentación, calidad y funcionamiento (4 ítems)

| N.º | Criterio | Ubicación en el proyecto |
|---|---|---|
| 37 | Código documentado con comentarios | Docstrings en `attendance/services.py` (las 5 funciones), en las vistas (`attendance/views.py`, `history/views.py`, `members/views.py`, `dashboard/views.py`) y en los seeders; comentarios numerados en `dashboard/views.py` (`# 1. Total de miembros activos` … `# 4. Membresías que vencen…`); docstring de proyecto en `config/settings.py` |
| 38 | Ejecución correcta sin errores | `attendance/tests.py` (14 pruebas), healthcheck `GET /api/health/` (`config/views.py`, usado en `docker-compose.yml` y `render.yaml`), `entrypoint.sh` (espera de BD, `migrate`, `collectstatic`), `Dockerfile` + `docker-compose.yml` + `docker-compose.dev.yml` |
| 39 | Validación de datos y control de errores | Serializers: `users/serializers.py` (`min_length=8`), `attendance/serializers.py` (`IntegerField`, `ChoiceField`); `ValidationError` en `attendance/views.py` (`member` y `date`); `try/except` → 404 en `members/views.py`, `attendance/views.py` y `coaches/views.py`; colecciones vacías en los seeders (`if not members ... return`); `_parse_int_param` en `history/views.py`; `UniqueConstraint` en `attendance/models.py` y `coaches/models.py` |
| 40 | Funcionalidades integradas y demostrables | `config/urls.py` (monta las 9 apps bajo `/api/` + Swagger), `users/management/commands/seed_all.py` (orquesta los 6 seeders), `schema.yaml` + Swagger UI (`/api/schema/swagger-ui/`), secciones de ejecución de este `README.md` |

---

<div align="center">
  <b>Fit Web API</b> - Creado para revolucionar la gestión deportiva.
</div>
