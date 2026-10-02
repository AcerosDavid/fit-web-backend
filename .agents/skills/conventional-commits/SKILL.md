---
name: conventional-commits
description: Use when creating, amending, rewriting or reviewing any git commit message in this repository, to enforce Conventional Commits with English lowercase descriptions (prefix, type, scope, breaking changes, git log checks).
---

# Conventional Commits

Todo commit de este repo sigue **Conventional Commits**, con la descripción **en inglés y en minúsculas**. Aplica a commits hechos por humanos y por IAs (Devin, opencode, Cursor, Copilot…).

## Formato

```
tipo(ámbito)?: descripción en inglés, minúsculas, imperativo
```

- **tipo**: en inglés y minúsculas, uno de:
  `feat` · `fix` · `docs` · `style` · `refactor` · `perf` · `test` · `build` · `ci` · `chore` · `revert`
- **ámbito** (opcional): en minúsculas con guiones, ej. `attendance`, `auth`, `docker`.
- **descripción**: **inglés, minúsculas**, en **imperativo** (`add`, no `added`/`adding`), **sin punto final**, ≤72 caracteres (ideal ≤50).

Breaking changes: `!` después del tipo (`refactor(attendance)!: drop v1 endpoints`) o footer obligatorio `BREAKING CHANGE: <explicación>`.

Opcional: body separado por línea en blanco, máximo 72 caracteres por línea; footer con `Refs: #123`.

## Reglas

1. **Nunca** en español, **nunca** mayúsculas en la línea del asunto, **nunca** punto al final.
2. Un cambio lógico por commit (no mezclar feature + refactor + format en uno).
3. `chore` para tareas sin impacto funcional; `feat`/`fix` solo si cambia comportamiento observable.
4. **Regla cruzada con el skill `actualizar-swagger`**: cambios de API y `schema.yaml` regenerado van en el **mismo commit**.
5. No reescribir el historial ya publicado (los commits previos en español se quedan como están).

## Ejemplos

| ❌ Mal | ✅ Bien |
|---|---|
| `feat: agregar coaches/views.py` | `feat: add coaches views` |
| `Fix bug en login` | `fix: handle expired jwt on login` |
| `feat(members): Added restore endpoint` | `feat(members): add restore endpoint` |
| `chore: update .env` | `chore: add adminer port to env example` |
| `refactor!: cambiar API attendance` | `refactor(attendance)!: rename check-in payload` |

## Verificación antes de commitear

Validar el mensaje **antes** de ejecutar `git commit` (ambas deben decir OK):

```bash
MSG='feat: add coaches views'

# 1. Prefijo válido + primera letra en minúscula
echo "$MSG" | grep -Ev '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9-]+\))?!?: [a-z0-9]' \
  && echo "ERROR: prefijo/descripcion invalida" || echo "OK"

# 2. Sin mayúsculas ni punto final
echo "$MSG" | grep -E '[A-Z]|[.]$' && echo "ERROR: mayusculas o punto final" || echo "OK"
```

El regex valida **formato** (prefijo, minúsculas, sin punto); que la descripción esté en **inglés** lo valida quien escribe el mensaje — revisarlo a ojo. Ejemplo que el regex no detecta pero igual está mal: `feat: agregar coaches/views.py` (español).

Para revisar commits ya hechos, cambiar `MSG` por `git log -1 --pretty=%s` (o `-5` para los últimos cinco). Si un commit no cumple y aún no se pusheó: `git commit --amend`; si ya se pusheó: no reescribir historia compartida.
