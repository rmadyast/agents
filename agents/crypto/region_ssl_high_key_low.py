import csv
from collections import defaultdict

ENRICHED = "crypto_latency_output/crypto_latency_enriched.20260407.csv"
MCM = "crypto_latency_output/mcm_machines_generated.20260407.csv"

# Heuristic used to define "ssl large but keysign not large":
#   ssl_p95 > 50ms AND key_p95 <= 10ms
# Also show a broader candidate set:
#   ssl_p50 > 20ms AND key_p50 <= 10ms

def percentile(vals, p):
    n = len(vals)
    if n == 0:
        return None
    idx = (p / 100.0) * (n - 1)
    lo = int(idx)
    hi = lo + 1
    if hi >= n:
        return vals[lo]
    return vals[lo] + (idx - lo) * (vals[hi] - vals[lo])

# Map ghost service IP -> freeflow regionname
region_by_ghostip = {}
with open(MCM, newline="") as f:
    r = csv.DictReader(f)
    for row in r:
        if row.get("network", "").strip() == "freeflow":
            ip = row.get("serviceip", "").strip()
            region = row.get("regionname", "").strip()
            if ip and region:
                region_by_ghostip[ip] = region

stats = defaultdict(lambda: {
    "n": 0,
    "ssl": [],
    "key": [],
    "ssl_gt20": 0,
    "ssl_gt50": 0,
    "key_gt10": 0,
})

with open(ENRICHED, newline="") as f:
    r = csv.DictReader(f)
    for row in r:
        region = region_by_ghostip.get(row.get("ghostip", "").strip())
        if not region:
            continue
        try:
            ssl = float(row.get("ssltime", ""))
            key = float(row.get("keysign_lat", "")) if row.get("keysign_lat", "") else 0.0
        except ValueError:
            continue

        s = stats[region]
        s["n"] += 1
        s["ssl"].append(ssl)
        s["key"].append(key)
        if ssl > 20:
            s["ssl_gt20"] += 1
        if ssl > 50:
            s["ssl_gt50"] += 1
        if key > 10:
            s["key_gt10"] += 1

rows = []
for region, s in stats.items():
    n = s["n"]
    if n < 30:
        continue
    ssl_s = sorted(s["ssl"])
    key_s = sorted(s["key"])
    ssl_p50 = percentile(ssl_s, 50)
    ssl_p95 = percentile(ssl_s, 95)
    key_p50 = percentile(key_s, 50)
    key_p95 = percentile(key_s, 95)
    rows.append({
        "region": region,
        "n": n,
        "ssl_p50": ssl_p50,
        "ssl_p95": ssl_p95,
        "key_p50": key_p50,
        "key_p95": key_p95,
        "ssl_gt20": 100.0 * s["ssl_gt20"] / n,
        "ssl_gt50": 100.0 * s["ssl_gt50"] / n,
        "key_gt10": 100.0 * s["key_gt10"] / n,
    })

strict = [
    r for r in rows
    if r["ssl_p95"] > 50 and r["key_p95"] <= 10
]
strict.sort(key=lambda x: (x["ssl_p95"], x["ssl_p50"]), reverse=True)

broad = [
    r for r in rows
    if r["ssl_p50"] > 20 and r["key_p50"] <= 10
]
broad.sort(key=lambda x: (x["ssl_p50"], x["ssl_p95"]), reverse=True)

print("STRICT (ssl_p95 > 50ms AND key_p95 <= 10ms)")
print("regionname                n   ssl_p50  ssl_p95  key_p50  key_p95  ssl>20  ssl>50  key>10")
print("---------------------------------------------------------------------------------------------")
for r in strict:
    print(f"{r['region']:<24} {r['n']:>6,}  {r['ssl_p50']:>6.1f}   {r['ssl_p95']:>6.1f}   {r['key_p50']:>6.1f}   {r['key_p95']:>6.1f}  {r['ssl_gt20']:>6.1f}% {r['ssl_gt50']:>6.1f}% {r['key_gt10']:>6.1f}%")

print("\nBROAD (ssl_p50 > 20ms AND key_p50 <= 10ms)")
print("regionname                n   ssl_p50  ssl_p95  key_p50  key_p95  ssl>20  ssl>50  key>10")
print("---------------------------------------------------------------------------------------------")
for r in broad:
    print(f"{r['region']:<24} {r['n']:>6,}  {r['ssl_p50']:>6.1f}   {r['ssl_p95']:>6.1f}   {r['key_p50']:>6.1f}   {r['key_p95']:>6.1f}  {r['ssl_gt20']:>6.1f}% {r['ssl_gt50']:>6.1f}% {r['key_gt10']:>6.1f}%")

print(f"\nstrict_count={len(strict)} broad_count={len(broad)}")
