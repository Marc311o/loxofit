set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
set dotenv-load

db_user := env_var('POSTGRES_USER')
db_name := env_var('POSTGRES_DB')

# shows command list
default:
    @just --list

# =======================================================
# ENVIRONMENT
# =======================================================

# builds project with logs
[group('env')]
up:
    docker compose up --build

# builds project without logs (in the background)
[group('env')]
up-d:
    docker compose up --build -d --wait

# builds project with pgadmin
[group('env')]
tools:
    docker compose --profile tools up --build -d

# stops project
[group('env')]
down:
    docker compose --profile tools down

# restarts container
[group('env')]
restart service:
    docker compose restart {{service}}

# rebuilds containers
[group('env')]
rebuild:
    docker compose up --build --renew-anon-volumes -d

# container status
[group('env')]
ps:
    docker compose ps

# logs
[group('env')]
logs service="":
    docker compose logs -f {{service}}

# =======================================================
# CODE QUALITY
# =======================================================

# linter (ruff + oxlint)
[group('quality')]
lint:
    docker compose exec api ruff check .
    docker compose exec frontend npm run lint

# linter (Ruff + Prettier)
[group('quality')]
format:
    docker compose exec api ruff check . --fix
    docker compose exec api ruff format .
    docker compose exec frontend npm run format

# backend tests
[group('test')]
test *args:
    docker compose exec api pytest {{args}}

# only failed tests
[group('test')]
test-failed:
    docker compose exec api pytest --lf -x

# test coverage
[group('test')]
test-cov:
    docker compose exec api pytest --cov=app --cov-report=term-missing --cov-report=html

# =======================================================
# CLEAN
# =======================================================

# cleans everything
[group('clean')]
[confirm("Are you sure? This will remove containers, volumes, data and images. This is irreversible.")]
clean:
    docker compose --profile tools down -v --rmi local --remove-orphans

# =======================================================
# DATABASE
# =======================================================

# initiate migration
[group('db')]
migrate:
    docker compose exec api alembic upgrade head

# creates new migration
[group('db')]
makemigration message:
    docker compose exec api alembic revision --autogenerate -m "{{message}}"

# Undo migration
[group('db')]
[confirm("Undo newest migration?")]
downgrade:
    docker compose exec api alembic downgrade -1

# Seeds catalog data
[group('db')]
seed-catalog:
    docker compose exec api python -m app.scripts.seed_catalog

# Seeds superuser
[group('db')]
seed-admin:
    docker compose exec api python -m app.scripts.seed_admin

# Seeds available model configs
[group('db')]
seed-config:
    docker compose exec api python -m app.scripts.seed_config

# Seeds all
[group('db')]
seed-all:
    docker compose exec api python -m app.scripts.seed_admin
    docker compose exec api python -m app.scripts.seed_catalog
    docker compose exec api python -m app.scripts.seed_config

[group('db')]
[confirm("This action will clear ALL data from the database. Continue?")]
reset-db:
    docker compose --profile tools down -v
    docker compose up --build -d --wait
    just migrate
    just seed

# =======================================================
# SHELLS
# =======================================================

[group('shell')]
psql:
    docker compose exec db psql -U {{db_user}} -d {{db_name}}

[group('shell')]
shell-api:
    docker compose exec api bash