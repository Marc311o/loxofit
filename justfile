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