#!/bin/bash

cd /var/www
docker-compose stop
/usr/local/lib/letsencrypt/certbot-auto renew --force-renew
docker-compose up -d
