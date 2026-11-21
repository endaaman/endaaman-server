# endaaman-server: enda-web の入口まわりの操作。
#
#   make caddy-check     Caddyfile の文法を確かめる（何も変えない）
#   make caddy-apply     確かめてから /etc/caddy/Caddyfile と静的ファイルを置き、Caddy に読み直させる（sudo）
#   make caddy-status    Caddy の状態と直近のログ
#   make caddy-install   Caddy を入れる（機械を作り直したときだけ。sudo）
#
# 外から届くポートの宣言は portmap/（make -C portmap apply）、DDNS は ddns/。

SHELL       := /bin/bash
.SHELLFLAGS := -euo pipefail -c
.ONESHELL:

CADDY_ETC := /etc/caddy/Caddyfile
SITE_SRC  := home.endaaman.com/html
SITE_DST  := /srv/home.endaaman.com

.PHONY: caddy-install caddy-check caddy-apply caddy-status

caddy-install:
	sudo apt-get install -y caddy
	# 本体の Caddy は ufw を通る（Docker のポートと違う）ので、80 / 443 を開けておく
	sudo ufw allow 80/tcp
	sudo ufw allow 443/tcp
	caddy version

caddy-check:
	@caddy validate --config Caddyfile --adapter caddyfile >/dev/null
	echo "文法 OK"

caddy-apply: caddy-check
	@sudo install -D -m 644 Caddyfile $(CADDY_ETC)
	sudo mkdir -p $(SITE_DST)
	if [ -d $(SITE_SRC) ]; then sudo cp -rT $(SITE_SRC) $(SITE_DST); fi
	sudo systemctl enable caddy
	sudo systemctl reload caddy 2>/dev/null || sudo systemctl restart caddy
	echo "適用した（$(CADDY_ETC)）"

caddy-status:
	@systemctl --no-pager status caddy | head -12 || true
	sudo journalctl -u caddy --no-pager -n 20
