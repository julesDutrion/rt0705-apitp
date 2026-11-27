#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON="${PYTHON:-python3}"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    "$PYTHON" -m venv "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" -c \
    'import bcrypt, dotenv, flasgger, flask, jwt, mongomock, pymongo, pytest' \
    >/dev/null 2>&1; then
    "$VENV_DIR/bin/python" -m pip install \
        -r "$PROJECT_DIR/requirements-dev.txt"
fi

cd "$PROJECT_DIR"
exec "$VENV_DIR/bin/python" -m pytest "$@"
