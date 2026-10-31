#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_HOST:?POSTGRES_HOST is required}"
: "${POSTGRES_PORT:?POSTGRES_PORT is required}"
: "${PRIVATE_MEDIA_ROOT:?PRIVATE_MEDIA_ROOT is required}"
: "${PGPASSFILE:?Set PGPASSFILE to the protected PostgreSQL password file}"

backup_root="${CREATORHUB_BACKUP_ROOT:-/var/backups/creatorhub}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$backup_root"
chmod 0700 "$backup_root"
work_dir="$(mktemp -d "$backup_root/.creatorhub-${timestamp}.XXXXXX")"
final_dir="$backup_root/$timestamp"
cleanup() { rm -rf -- "$work_dir"; }
trap cleanup EXIT

export PGPASSFILE
if [[ -n "${POSTGRES_SSLMODE:-}" ]]; then export PGSSLMODE="$POSTGRES_SSLMODE"; fi
pg_dump --no-password --host="$POSTGRES_HOST" --port="$POSTGRES_PORT" --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --format=custom --file="$work_dir/database.dump"
tar --create --gzip --file="$work_dir/private-files.tar.gz" --directory="$PRIVATE_MEDIA_ROOT" .
(cd "$work_dir" && sha256sum database.dump private-files.tar.gz > SHA256SUMS)
mv -- "$work_dir" "$final_dir"
trap - EXIT
printf 'CreatorHub backup written to %s\n' "$final_dir"
