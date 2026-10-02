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
Para no probar el sistema vacío, hemos creado comandos que llenan la base de datos con información aleatoria y realista. **Debes ejecutarlos exactamente en este orden**:

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
<div align="center">
  <b>Fit Web API</b> - Creado para revolucionar la gestión deportiva.
</div>
