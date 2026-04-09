import csv
from collections import defaultdict

ENRICHED = "crypto_latency_output/crypto_latency_enriched.20260407.csv"
MCM = "crypto_latency_output/mcm_machines_generated.20260407.csv"
MIN_N = 30
MIN_R = 0.5


def pearson(n, sx, sy, sxy, sx2, sy2):
    num = n * sxy - sx * sy
    dx = n * sx2 - sx * sx
    dy = n * sy2 - sy * sy
    if dx <= 0 or dy <= 0:
        return None
    r = num / (dx * dy) ** 0.5
    return max(-1.0, min(1.0, r))


region_by_ghostip = {}
with open(MCM, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("network", "").strip() == "freeflow":
            ip = row.get("serviceip", "").strip()
            region = row.get("regionname", "").strip()
            if ip and region:
                region_by_ghostip[ip] = region

stats = defaultdict(lambda: {
    "n": 0,
    "sx": 0.0,
    "sy": 0.0,
    "sxy": 0.0,
    "sx2": 0.0,
    "sy2": 0.0,
})

with open(ENRICHED, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        country = row.get("test_country", "")
        region = region_by_ghostip.get(row.get("ghostip", "").strip())
        if not country or not region:
            continue
        try:
            ssl = float(row.get("ssltime", ""))
            key = float(row.get("keysign_lat", "")) if row.get("keysign_lat", "") else 0.0
        except ValueError:
            continue

        s = stats[(country, region)]
        s["n"] += 1
        s["sx"] += ssl
        s["sy"] += key
        s["sxy"] += ssl * key
        s["sx2"] += ssl * ssl
        s["sy2"] += key * key

rows = []
for (country, region), s in stats.items():
    n = s["n"]
    if n < MIN_N:
        continue
    r = pearson(n, s["sx"], s["sy"], s["sxy"], s["sx2"], s["sy2"])
    if r is not None and r >= MIN_R:
        rows.append((country, region, n, r))

rows.sort(key=lambda x: (-x[3], -x[2]))

print(f"Strong correlation set: Pearson_r >= {MIN_R} with n >= {MIN_N}")
print(f"{'country':<8} {'regionname':<24} {'n':>7} {'pearson_r':>10}")
print("-" * 55)
for c, rg, n, r in rows:
    print(f"{c:<8} {rg:<24} {n:>7,} {r:>10.3f}")
print(f"\ncount={len(rows)}")
