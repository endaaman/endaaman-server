# portmap: 外から受けるポートを ports に宣言し、nftables（テーブル inet portmap）へ流し込む。
#
#   make show     生成されるルールを表示する（何も変えない）
#   make check    生成して文法を確かめる（何も変えない。sudo）
#   make apply    確かめてから適用する（sudo）。再起動後も入るよう /etc/portmap/ にも置く
#   make status   今入っているルールとカウンタを表示する（sudo）
#   make install  起動時に自動で適用する systemd unit を入れる（初回だけ。sudo）
#   make down     ルールを外す（sudo）。外からの制限が無くなるので注意
#
# ufw や Docker のルール、/etc/nftables.conf（flush ruleset が入っている）には触らない。
# nftables.service は有効にしないこと。
#
# 例外が 1 つ: 別の機械へ流す通信は FORWARD を通るが、ufw も Docker も FORWARD の既定が DROP なので、
# 「portmap が DNAT した通信だけ通す」ルールを iptables の FORWARD の先頭に 1 本入れる（PERMIT）。

SHELL  := /bin/bash
GEN    := python3 gen.py ports
ETC    := /etc/portmap/portmap.nft
PERMIT := -i ens18 -o ens18 -m conntrack --ctstate DNAT -m comment --comment portmap -j ACCEPT

.PHONY: show check apply status install down

show:
	@$(GEN)

check:
	@t=$$(mktemp) && trap 'rm -f $$t' EXIT && $(GEN) > $$t && sudo nft -c -f $$t && echo "文法 OK"

apply:
	@t=$$(mktemp) && trap 'rm -f $$t' EXIT && $(GEN) > $$t \
	  && sudo nft -c -f $$t \
	  && sudo install -D -m 644 $$t $(ETC) \
	  && sudo nft -f $(ETC) \
	  && echo "適用した（$(ETC)）"
	@sudo iptables -C FORWARD $(PERMIT) 2>/dev/null || sudo iptables -I FORWARD 1 $(PERMIT)
	@$(MAKE) --no-print-directory status

status:
	@sudo nft list table inet portmap
	@echo "--- FORWARD の許可（portmap）"; sudo iptables -S FORWARD | grep portmap || echo "(無し)"

install:
	sudo install -m 644 portmap.service portmap-forward.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable portmap.service portmap-forward.service
	@echo "起動時に $(ETC) を適用する（今の適用は make apply）"

down:
	sudo nft delete table inet portmap
	-sudo iptables -D FORWARD $(PERMIT)
