<div align="center">
  <img src="logo.png" alt="Fit Web Logo" width="400">
  
  # Fit Web - Backend API 🚀
  **El motor inteligente detrás de la gestión de tu gimnasio.**
  
  <br>
  
  ![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)
  ![Django REST Framework](https://img.shields.io/badge/Django_REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
  ![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)
  ![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
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
- Python 3.10 o superior.
- Git.

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
