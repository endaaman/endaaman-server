#!/usr/bin/env python3
"""home.endaaman.com の A レコードを、自宅の出口 IPv4 に合わせる（Cloudflare DNS）。

  update.py            出口 IPv4 が前回と変わっていたら（または 24 時間ぶりなら）レコードを確かめ、違えば書き換える
  update.py --dry-run  何をするかを表示するだけ（書き換えない）
  update.py --force    前回の記録を無視して必ず確かめる

トークンは repo 直下の .env の CF_API_TOKEN（ブログのキャッシュ消去と共用。ゾーン endaaman.com の DNS 編集権限が要る）。ddns-home.service の
EnvironmentFile から渡す。既存の A レコードの content だけを書き換える（TTL・プロキシ設定は触らない）。
"""
import ipaddress, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path

ZONE = "endaaman.com"
NAME = "home.endaaman.com"
API = "https://api.cloudflare.com/client/v4"
STATE = Path.home() / ".cache" / "ddns-home" / "last-ip"
RECHECK = 24 * 3600


def public_ipv4():
    """外から見える IPv4。グローバルな IPv4 でなければ採用しない。"""
    errs = []
    for url, pick in (
        ("https://1.1.1.1/cdn-cgi/trace", lambda t: dict(l.split("=", 1) for l in t.splitlines() if "=" in l)["ip"]),
        ("https://checkip.amazonaws.com", lambda t: t.strip()),
    ):
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                ip = ipaddress.ip_address(pick(r.read().decode()))
            if ip.version == 4 and ip.is_global:
                return str(ip)
            errs.append(f"{url}: グローバルな IPv4 ではない ({ip})")
        except Exception as e:
            errs.append(f"{url}: {e}")
    sys.exit("出口 IPv4 が取れない: " + " / ".join(errs))


def cf(token, method, path, body=None):
    req = urllib.request.Request(
        API + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = "; ".join(f"{x.get('code')} {x.get('message')}" for x in json.load(e).get("errors", []))
        except Exception:
            msg = ""
        sys.exit(f"Cloudflare API {method} {path.split('?')[0]}: HTTP {e.code} {msg}")
    if not d.get("success"):
        sys.exit(f"Cloudflare API {method} {path.split('?')[0]}: {d.get('errors')}")
    return d["result"]


def main():
    dry = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    ip = public_ipv4()

    if not (dry or force) and STATE.exists():
        if STATE.read_text().strip() == ip and time.time() - STATE.stat().st_mtime < RECHECK:
            return  # 変化なし。API は叩かない

    token = os.environ.get("CF_API_TOKEN", "").strip()
    if not token:
        sys.exit(f"出口 IPv4 は {ip}。CF_API_TOKEN が無いので Cloudflare は確かめていない")

    zones = cf(token, "GET", f"/zones?name={ZONE}")
    if len(zones) != 1:
        sys.exit(f"ゾーン {ZONE} が見つからない（トークンの権限を確認）")
    zid = zones[0]["id"]
    recs = cf(token, "GET", f"/zones/{zid}/dns_records?type=A&name={NAME}")
    if len(recs) != 1:
        sys.exit(f"{NAME} の A レコードが {len(recs)} 個ある（1 個のときだけ書き換える）")
    rec = recs[0]

    if rec["content"] == ip:
        print(f"{NAME} は既に {ip}")
    elif dry:
        print(f"{NAME}: {rec['content']} → {ip} に書き換える予定（dry-run。proxied={rec.get('proxied')} ttl={rec.get('ttl')}）")
        return
    else:
        cf(token, "PATCH", f"/zones/{zid}/dns_records/{rec['id']}", {"content": ip})
        print(f"{NAME}: {rec['content']} → {ip} に書き換えた")

    if not dry:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(ip + "\n")


if __name__ == "__main__":
    main()
