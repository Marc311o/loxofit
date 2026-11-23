#!/bin/sh
# A dump of the database, kept for 14 days. Daily from cron:
#   30 3 * * * /home/loxofit/loxofit/deploy/backup.sh >> /home/loxofit/backup.log 2>&1
# Restore: docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' < FILE
set -eu
cd "$(dirname "$0")/.."

DIR="${BACKUP_DIR:-$HOME/backups}"
mkdir -p "$DIR"
FILE="$DIR/loxofit-$(date +%Y-%m-%d-%H%M).dump"

docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "$FILE"
find "$DIR" -name 'loxofit-*.dump' -mtime +14 -delete
echo "$(date '+%F %T') saved $FILE ($(du -h "$FILE" | cut -f1))"