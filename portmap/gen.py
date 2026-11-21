#!/usr/bin/env python3
"""ports（宣言的な一覧）から nftables のルールセットを作り、標準出力へ出す。

  gen.py [ports ファイル]

やること（テーブル inet portmap だけを持つ。ufw や Docker のルールには触らない）:
  - 外（LAN 以外の送信元）から WAN_IF に来た「新しい」通信は、一覧にあるポートだけ通す。
    NAT より前で判定するので、Docker が公開しているポートにも効く。
  - 宛先が別の機械の行は、その機械へ DNAT し、送信元を自分（enda-web）に付け替える。
"""
import ipaddress
import re
import sys
from pathlib import Path

WAN_IF = "ens18"                         # 外からの通信が入ってくる口（LAN と共用の 1 枚）
LAN = ipaddress.ip_network("10.16.0.0/16")
LOCAL = {"localhost", "local"}
LINE = re.compile(r"(\d+):([^:/\s]+):(\d+)(?:/(tcp|udp))?")


def parse(path):
    entries, seen = [], {}
    for n, raw in enumerate(Path(path).read_text().splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        where = f"{path}:{n}"
        m = LINE.fullmatch(line)
        if not m:
            sys.exit(f"{where}: 書式が違う: {line!r}（外側ポート:宛先:宛先ポート[/tcp|/udp]）")
        ext, host, inn, proto = int(m[1]), m[2], int(m[3]), m[4] or "tcp"
        for p in (ext, inn):
            if not 1 <= p <= 65535:
                sys.exit(f"{where}: ポート番号が範囲外: {p}")
        if host in LOCAL:
            if ext != inn:
                sys.exit(f"{where}: localhost 宛てはポート変換できない（{ext} ≠ {inn}）")
            target = None
        else:
            try:
                ip = ipaddress.ip_address(host)
            except ValueError:
                sys.exit(f"{where}: 宛先は localhost か IPv4 アドレスで書く: {host!r}")
            if ip.version != 4 or ip not in LAN:
                sys.exit(f"{where}: 宛先 {ip} が LAN（{LAN}）の外")
            target = (str(ip), inn)
        if (proto, ext) in seen:
            sys.exit(f"{where}: {proto} の外側ポート {ext} は {seen[(proto, ext)]} 行目と重複")
        seen[(proto, ext)] = n
        entries.append((proto, ext, target))
    return entries


def render(entries, src):
    out = []
    w = out.append
    w("#!/usr/sbin/nft -f")
    w(f"# 生成物。直接編集しない（元: {src}、生成: portmap/gen.py）")
    w("")
    w("table inet portmap")
    w("delete table inet portmap")
    w("")
    w("table inet portmap {")
    w("\t# 外から来た新しい通信は、一覧にあるポートだけ通す（conntrack の後・NAT の前）")
    w("\tchain wan_filter {")
    w("\t\ttype filter hook prerouting priority mangle; policy accept;")
    w(f'\t\tiifname != "{WAN_IF}" accept')
    w("\t\tct state established,related accept")
    w(f"\t\tip saddr {LAN} accept")
    w("\t\tip6 saddr { fe80::/10, fc00::/7 } accept")
    w("\t\tmeta l4proto ipv6-icmp accept")
    for proto in ("tcp", "udp"):
        ports = sorted({e for p, e, _ in entries if p == proto})
        if ports:
            w(f"\t\t{proto} dport {{ {', '.join(map(str, ports))} }} accept")
    w("\t\ticmp type echo-request limit rate 5/second accept")
    w("\t\tcounter drop")
    w("\t}")
    fwd = [(p, e, t) for p, e, t in entries if t]
    if fwd:
        w("")
        w("\t# 別の機械へ流す分（Docker の DNAT より先に評価する）")
        w("\tchain wan_dnat {")
        w("\t\ttype nat hook prerouting priority -110; policy accept;")
        for proto, ext, (ip, port) in fwd:
            w(f'\t\tiifname "{WAN_IF}" ip saddr != {LAN} {proto} dport {ext} dnat ip to {ip}:{port}')
        w("\t}")
        w("")
        w("\t# 流した先からの返事がこの機械へ戻るよう、送信元を自分に付け替える")
        w("\tchain lan_snat {")
        w("\t\ttype nat hook postrouting priority srcnat; policy accept;")
        w(f'\t\toifname "{WAN_IF}" ip saddr != {LAN} ct status dnat masquerade')
        w("\t}")
    w("}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).with_name("ports"))
    sys.stdout.write(render(parse(src), src))
