#!/bin/sh
set -e

echo "[entrypoint] Esperando a la base de datos..."
python <<'PY'
import os
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connections
from django.db.utils import OperationalError

for attempt in range(30):
    try:
        connections["default"].ensure_connection()
        print("[entrypoint] Base de datos disponible.")
        break
    except OperationalError as exc:
        print(f"[entrypoint] BD no lista ({exc}) - reintento {attempt + 1}/30")
        time.sleep(2)
else:
    raise SystemExit("[entrypoint] No se pudo conectar a la base de datos.")
PY

echo "[entrypoint] Aplicando migraciones..."
python manage.py migrate --noinput

echo "[entrypoint] Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

exec "$@"
