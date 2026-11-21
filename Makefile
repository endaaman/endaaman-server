# endaaman-server: enda-web の入口まわりの操作。
#
#   make caddy-install   Caddy を入れる（初回だけ。sudo）。入れた直後は止めておく
#   make caddy-check     Caddyfile の文法を確かめる（何も変えない）
#   make caddy-apply     確かめてから /etc/caddy/Caddyfile と静的ファイルを置き、Caddy に読み直させる（sudo）
#   make caddy-status    Caddy の状態と直近のログ
#
# nginx（Docker）→ Caddy（本体）の切り替え。1 回だけ使う。済んだらこの 2 つと docker-compose.before-caddy.yml は消してよい:
#   make caddy-cutover   nginx の 3 コンテナを止め、ufw で 80 / 443 を開け、Caddy を起動する（sudo）
#   make caddy-rollback  切り替え前の状態に戻す（sudo）
#
# 外から届くポートの宣言は portmap/（make -C portmap apply）、DDNS は ddns/。

SHELL       := /bin/bash
.SHELLFLAGS := -euo pipefail -c
.ONESHELL:

CADDY_ETC := /etc/caddy/Caddyfile
SITE_SRC  := home.endaaman.com/html
SITE_DST  := /srv/home.endaaman.com
NEW       := docker-compose.caddy.yml
OLD       := docker-compose.before-caddy.yml
UP        := docker compose up -d --remove-orphans --pull never --no-build

.PHONY: caddy-install caddy-check caddy-apply caddy-status caddy-cutover caddy-rollback

caddy-install:
	sudo apt-get install -y caddy
	# パッケージは入れた直後に :80 で起動しようとする。nginx が 80 番を持っている間は失敗するので止めておく
	sudo systemctl disable --now caddy || true
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

caddy-cutover:
	@[ -f $(NEW) ] || { echo "$(NEW) が無い（切り替え済み？）"; exit 1; }
	command -v caddy >/dev/null || { echo "caddy が入っていない。先に make caddy-install"; exit 1; }
	caddy validate --config Caddyfile --adapter caddyfile >/dev/null || { echo "Caddyfile の文法エラー"; exit 1; }
	for i in endaaman/blog-frontend endaaman/blog-backend; do
		docker image inspect "$$i" >/dev/null 2>&1 || { echo "イメージ $$i が手元に無い"; exit 1; }
	done
	docker compose -f $(NEW) config -q || { echo "$(NEW) が compose として読めない"; exit 1; }
	sudo -v
	echo "== 1/4 compose を入れ替え、nginx の 3 コンテナを止める（ブログのコンテナは作り直される）"
	[ -f $(OLD) ] || cp -p docker-compose.yml $(OLD)
	cp -p $(NEW) docker-compose.yml
	$(UP)
	echo "== 2/4 ufw で 80 / 443 を開ける（Docker のポートは ufw を素通りしていたが、本体の Caddy は ufw を通る）"
	sudo ufw allow 80/tcp
	sudo ufw allow 443/tcp
	echo "== 3/4 Caddy の設定を置いて起動する"
	make --no-print-directory caddy-apply
	echo "== 4/4 確認"
	sleep 4
	ok=1
	c=$$(curl -sk -m 10 -o /dev/null -w '%{http_code}' https://localhost/ -H 'Host: endaaman.com' || true)
	echo "ブログ（cloudflared と同じ形の要求）: $$c"; [ "$$c" = 200 ] || ok=0
	c=$$(curl -s -m 15 -o /dev/null -w '%{http_code}' https://endaaman.com/ || true)
	echo "ブログ（Cloudflare 経由）: $$c"; [ "$$c" = 200 ] || ok=0
	c=$$(curl -s -m 10 -o /dev/null -w '%{http_code}' http://127.0.0.1/ -H 'Host: home.endaaman.com' || true)
	echo "home.endaaman.com（http。308 なら https へ転送中）: $$c"
	if [ "$$ok" = 1 ]; then
		rm -f $(NEW)
		echo "切り替え完了。$(OLD) は、しばらく問題が無ければ消してよい（caddy-rollback が使う）"
	else
		echo "!! 確認に失敗。ログは make caddy-status、戻すなら make caddy-rollback"
		exit 1
	fi

caddy-rollback:
	@[ -f $(OLD) ] || { echo "$(OLD) が無い（切り替え前の控えが無いので戻せない）"; exit 1; }
	sudo -v
	echo "== 1/3 Caddy を止める（80 / 443 を空ける）"
	sudo systemctl disable --now caddy || true
	echo "== 2/3 compose を切り替え前に戻して起動する"
	[ -f $(NEW) ] || cp -p docker-compose.yml $(NEW)
	cp -p $(OLD) docker-compose.yml
	$(UP)
	echo "== 3/3 確認"
	sleep 6
	c=$$(curl -sk -m 10 -o /dev/null -w '%{http_code}' https://localhost/ -H 'Host: endaaman.com' || true)
	echo "ブログ（cloudflared と同じ形の要求）: $$c"
	c=$$(curl -s -m 15 -o /dev/null -w '%{http_code}' https://endaaman.com/ || true)
	echo "ブログ（Cloudflare 経由）: $$c"
	echo "ufw の 80 / 443 の許可は残してある（Docker のポートには影響しない）"
