#!/bin/sh
# Brings the server up to date with the main branch. Run by GitHub Actions over SSH
# after every push to main, or by hand: ./deploy/deploy.sh
set -eu
cd "$(dirname "$0")/.."

main() {
	echo "==> Fetching main"
	git fetch --quiet origin main
	git reset --hard origin/main

	echo "==> Building and starting"
	docker compose up -d --build --remove-orphans

	echo "==> Waiting for the API"
	for _ in $(seq 1 30); do
		if docker compose exec -T api python -c \
			"import urllib.request as u; u.urlopen('http://localhost:8000/api/v1/health')" 2>/dev/null; then
			echo "==> Deployed $(git rev-parse --short HEAD)"
			docker image prune -f >/dev/null
			exit 0
		fi
		sleep 2
	done

	echo "!! The API did not become healthy - last logs:" >&2
	docker compose logs --tail 50 api >&2
	exit 1
}

main "$@"