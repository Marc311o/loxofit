# Deployment

Production runs on one VPS with Docker Compose (`docker-compose.prod.yaml`):

| Service | What it does |
|---|---|
| `web` | Caddy - HTTPS with a Let's Encrypt certificate, the built web app, `/api` passed to the API |
| `api` | FastAPI; runs the migrations on start; the plan generator's worker processes live in it |
| `db` | PostgreSQL, reachable only from the API |

## Everyday use

```sh
docker compose ps                  # what is running
docker compose logs -f api         # the API's logs (web, db likewise)
./deploy/deploy.sh                 # deploy main by hand (normally GitHub Actions does it)
./deploy/backup.sh                 # a database dump to ~/backups (daily from cron)
docker compose exec api python -m app.admin.reset_password user@example.com
```

`.env` on the server sets `COMPOSE_FILE=compose.prod.yaml`, so plain `docker compose` uses
the production file. Template: `.env.prod.example`.

## Continuous deployment

`.github/workflows/deploy.yml` runs on every push to `main`: the CI checks
(`ci.yml`), then SSH to the server, which runs `deploy/deploy.sh` - pull `main`,
rebuild what changed, restart, wait for the API to be healthy.

Repository settings -> Secrets and variables -> Actions:

| Name | Kind | Value |
|---|---|---|
| `DEPLOY_HOST` | secret | the server's IP address |
| `DEPLOY_USER` | secret | the user on the server (`loxofit`) |
| `DEPLOY_SSH_KEY` | secret | the private deploy key |
| `DEPLOY_KNOWN_HOSTS` | secret | `ssh-keyscan <server-ip>` output |
| `DOMAIN` | variable | the app's domain |

The deploy key is allowed to run only `deploy/deploy.sh` (`command=` in `authorized_keys`).

## Restoring a backup

```sh
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' < ~/backups/loxofit-YYYY-MM-DD-HHMM.dump
```