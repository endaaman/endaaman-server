set -eu
cd $(realpath $(dirname "$0"))

docker compose pull -q
docker compose up -d --build --quiet-pull

echo done
