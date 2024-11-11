set -eu
cd $(realpath $(dirname "$0"))

mkdir -p ./docker-volumes/acme-state
mkdir -p ./docker-volumes/le-certs

docker compose pull
docker compose up -d --build --quiet-pull

echo done
