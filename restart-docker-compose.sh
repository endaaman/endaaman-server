cd $(realpath $(dirname "$0"))

docker-compose pull > /dev/null && docker-compose up -d --build > /dev/null

echo done
