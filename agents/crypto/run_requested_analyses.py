import csv
from collections import defaultdict
from pathlib import Path

enriched = Path('crypto_latency_output/crypto_latency_enriched.20260407.csv')
mcm = Path('crypto_latency_output/mcm_machines_generated.20260407.csv')
outdir = Path('crypto_latency_output')


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


def pearson_from_sums(n, sx, sy, sxy, sx2, sy2):
    num = n * sxy - sx * sy
    dx = n * sx2 - sx * sx
    dy = n * sy2 - sy * sy
    if dx <= 0 or dy <= 0:
        return None
    r = num / (dx * dy) ** 0.5
    return max(-1.0, min(1.0, r))


def spearman(pairs):
    n = len(pairs)
    if n < 2:
        return None

    def ranks(vals):
        idx = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and vals[idx[j + 1]] == vals[idx[j]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[idx[k]] = avg
            i = j + 1
        return r

    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    rx = ranks(xs)
    ry = ranks(ys)
    sx = sum(rx)
    sy = sum(ry)
    sxy = sum(rx[i] * ry[i] for i in range(n))
    sx2 = sum(v * v for v in rx)
    sy2 = sum(v * v for v in ry)
    return pearson_from_sums(n, sx, sy, sxy, sx2, sy2)


# region map
region_by_ghostip = {}
with mcm.open(newline='') as f:
    r = csv.DictReader(f)
    for row in r:
        if row.get('network', '').strip() == 'freeflow':
            ip = row.get('serviceip', '').strip()
            region = row.get('regionname', '').strip()
            if ip and region:
                region_by_ghostip[ip] = region

country = defaultdict(lambda: {'n': 0, 'ssl': [], 'key': [], 'sx': 0.0, 'sy': 0.0, 'sxy': 0.0, 'sx2': 0.0, 'sy2': 0.0, 'pairs': []})
metro = defaultdict(lambda: {'n': 0, 'ssl': [], 'key': [], 'sx': 0.0, 'sy': 0.0, 'sxy': 0.0, 'sx2': 0.0, 'sy2': 0.0, 'pairs': []})
region = defaultdict(lambda: {'n': 0, 'sx': 0.0, 'sy': 0.0, 'sxy': 0.0, 'sx2': 0.0, 'sy2': 0.0})

with enriched.open(newline='') as f:
    r = csv.DictReader(f)
    for row in r:
        c = row['test_country']
        gm = row['ghost_metro'] or '(none)'
        rg = region_by_ghostip.get(row['ghostip'].strip(), '')
        try:
            ssl = float(row['ssltime'])
            key = float(row['keysign_lat']) if row['keysign_lat'] else 0.0
        except ValueError:
            continue

        for bucket, k in ((country, c), (metro, (c, gm))):
            s = bucket[k]
            s['n'] += 1
            s['ssl'].append(ssl)
            s['key'].append(key)
            s['sx'] += ssl
            s['sy'] += key
            s['sxy'] += ssl * key
            s['sx2'] += ssl * ssl
            s['sy2'] += key * key
            s['pairs'].append((ssl, key))

        if rg:
            s = region[(c, rg)]
            s['n'] += 1
            s['sx'] += ssl
            s['sy'] += key
            s['sxy'] += ssl * key
            s['sx2'] += ssl * ssl
            s['sy2'] += key * key

# 1) by-country view
f1 = outdir / 'by_country_corr.20260407.tsv'
with f1.open('w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['country', 'n', 'ssl_p50', 'ssl_p95', 'key_p50', 'key_p95', 'pearson_r', 'spearman_r'])
    for c in sorted(country):
        s = country[c]
        ssl_s = sorted(s['ssl'])
        key_s = sorted(s['key'])
        pr = pearson_from_sums(s['n'], s['sx'], s['sy'], s['sxy'], s['sx2'], s['sy2'])
        sr = spearman(s['pairs'])
        w.writerow([
            c, s['n'],
            f"{percentile(ssl_s, 50):.1f}", f"{percentile(ssl_s, 95):.1f}",
            f"{percentile(key_s, 50):.1f}", f"{percentile(key_s, 95):.1f}",
            f"{pr:.3f}" if pr is not None else 'N/A',
            f"{sr:.3f}" if sr is not None else 'N/A',
        ])

# 2) metros with key_p95 > 10
f2 = outdir / 'metros_keyp95_gt10.20260407.tsv'
rows2 = []
for (c, gm), s in metro.items():
    if s['n'] < 30:
        continue
    ssl_s = sorted(s['ssl'])
    key_s = sorted(s['key'])
    kp95 = percentile(key_s, 95)
    if kp95 is None or kp95 <= 10:
        continue
    pr = pearson_from_sums(s['n'], s['sx'], s['sy'], s['sxy'], s['sx2'], s['sy2'])
    sr = spearman(s['pairs'])
    rows2.append([
        c, gm, s['n'],
        f"{percentile(ssl_s, 50):.1f}", f"{percentile(ssl_s, 95):.1f}",
        f"{percentile(key_s, 50):.1f}", f"{kp95:.1f}",
        f"{pr:.3f}" if pr is not None else 'N/A',
        f"{sr:.3f}" if sr is not None else 'N/A',
    ])
rows2.sort(key=lambda r: (r[0], -float(r[6]), -r[2]))
with f2.open('w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['country', 'metro', 'n', 'ssl_p50', 'ssl_p95', 'key_p50', 'key_p95', 'Pearson_r', 'Spearman_r'])
    w.writerows(rows2)

# 3) strong country-region correlation ordered by country,n
f3 = outdir / 'country_region_strong_corr.20260407.tsv'
rows3 = []
for (c, rg), s in region.items():
    if s['n'] < 30:
        continue
    pr = pearson_from_sums(s['n'], s['sx'], s['sy'], s['sxy'], s['sx2'], s['sy2'])
    if pr is not None and pr >= 0.5:
        rows3.append([c, rg, s['n'], f"{pr:.3f}"])
rows3.sort(key=lambda r: (r[0], -r[2]))
with f3.open('w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['country', 'regionname', 'n', 'pearson_r'])
    w.writerows(rows3)

print(f"Wrote: {f1}")
print(f"Wrote: {f2} (rows={len(rows2)})")
print(f"Wrote: {f3} (rows={len(rows3)})")
