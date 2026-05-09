#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/migration"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_DATABASE="${MYSQL_DATABASE:-gym_system}"
MYSQL_USERNAME="${MYSQL_USERNAME:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"

mkdir -p "${OUT_DIR}"

OUT_FILE="${OUT_DIR}/${MYSQL_DATABASE}_${TIMESTAMP}.sql"

MYSQLDUMP_ARGS=(
  --host="${MYSQL_HOST}"
  --port="${MYSQL_PORT}"
  --user="${MYSQL_USERNAME}"
  --single-transaction
  --routines
  --triggers
  --events
  --hex-blob
  --default-character-set=utf8mb4
  --set-gtid-purged=OFF
  --databases "${MYSQL_DATABASE}"
)

if [[ -n "${MYSQL_PASSWORD}" ]]; then
  MYSQLDUMP_ARGS+=(--password="${MYSQL_PASSWORD}")
else
  MYSQLDUMP_ARGS+=(--password)
fi

mysqldump \
  "${MYSQLDUMP_ARGS[@]}" \
  > "${OUT_FILE}"

echo "${OUT_FILE}"
