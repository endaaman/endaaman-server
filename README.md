# endaaman-server

自宅サーバー enda-web の入口まわり。外から来た通信はルーターがまとめてここへ流し、何を通してどこへ渡すかをこの repo が決める。

| 置き場 | 役割 | 反映 |
|---|---|---|
| `portmap/ports` | 外から届かせるポートの宣言（ここに無いポートは捨てる。別の機械へ流す行も書ける） | `make -C portmap check && make -C portmap apply` |
| `Caddyfile` | 80 / 443 で受けた名前ごとの振り分けと証明書（本体の Caddy） | `make caddy-check && make caddy-apply` |
| `docker-compose.yml` | ブログ（`blog-frontend` / `blog-backend`）。`127.0.0.1:8001` だけで待ち受け、Caddy が中継する | `docker compose up -d` |
| `ddns/` | `home.endaaman.com` の A レコードを出口の IPv4 に合わせる（ユーザーの systemd タイマー、5 分おき） | `systemctl --user list-timers ddns-home.timer` |
| `.env` | 秘密の値（git 管理外）。`CF_API_TOKEN` = ゾーン `endaaman.com` の DNS 編集 + キャッシュ消去 | — |

## 名前を足す

1. `Caddyfile` にブロックを足して `make caddy-check && make caddy-apply`。
2. DNS のレコードを足す（Cloudflare を通さない名前は、A レコードを `home.endaaman.com` と同じアドレスへ）。

80 / 443 以外のポートを開けるときだけ `portmap/ports` に行を足す。

## 通り道

- `endaaman.com`: Cloudflare → Cloudflare Tunnel（`cloudflared`、この機械で動いている）→ `https://localhost:443` の Caddy → `blog-frontend`。
  Cloudflare の裏なので、Caddy は内部 CA の証明書で受ける（`tls internal`）。
- `home.endaaman.com`: DNS が直接この家を指す → ルーター → `portmap` → Caddy。証明書は Caddy が Let's Encrypt から自動で取る。
  中身は `home.endaaman.com/html/`（`make caddy-apply` が `/srv/home.endaaman.com` へ写す）。

## 機械を作り直したとき

```
make caddy-install && make caddy-apply
make -C portmap apply && make -C portmap install
systemctl --user link $PWD/ddns/ddns-home.service $PWD/ddns/ddns-home.timer
systemctl --user enable --now ddns-home.timer      # loginctl enable-linger が要る
docker compose up -d
```
