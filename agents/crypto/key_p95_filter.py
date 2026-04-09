import csv
from collections import defaultdict

ENRICHED = "crypto_latency_output/crypto_latency_enriched.20260407.csv"
MIN_N = 30

def percentile(sv, p):
    n = len(sv)
    if not n: return None
    idx = (p/100.0)*(n-1); lo=int(idx); hi=lo+1
    if hi>=n: return sv[lo]
    return sv[lo]+(idx-lo)*(sv[hi]-sv[lo])

def pearson_r(sx,sy,sxy,sx2,sy2,n):
    num = n*sxy - sx*sy
    dx = n*sx2 - sx**2; dy = n*sy2 - sy**2
    if dx<=0 or dy<=0: return None
    return max(-1.0, min(1.0, num/(dx*dy)**0.5))

def spearman(pairs):
    n = len(pairs)
    if n < 2: return None
    def rank(vals):
        si = sorted(range(n), key=lambda i: vals[i])
        r = [0.0]*n; i = 0
        while i < n:
            j = i
            while j < n-1 and vals[si[j+1]] == vals[si[j]]: j += 1
            ar = (i+j)/2.0 + 1.0
            for k in range(i, j+1): r[si[k]] = ar
            i = j+1
        return r
    xs = [p[0] for p in pairs]; ys = [p[1] for p in pairs]
    rx = rank(xs); ry = rank(ys)
    sx = sum(rx); sy = sum(ry)
    sxy = sum(rx[i]*ry[i] for i in range(n))
    sx2 = sum(v*v for v in rx); sy2 = sum(v*v for v in ry)
    return pearson_r(sx, sy, sxy, sx2, sy2, n)

stats = defaultdict(lambda: {
    'n':0, 'ssl_vals':[], 'key_vals':[], 'pairs':[],
    'sx':0.0, 'sy':0.0, 'sxy':0.0, 'sx2':0.0, 'sy2':0.0,
})

with open(ENRICHED) as f:
    for row in csv.DictReader(f):
        try:
            ssl = float(row['ssltime'])
            key = float(row['keysign_lat']) if row['keysign_lat'] else 0.0
        except ValueError:
            continue
        c  = row['test_country']
        gm = row['ghost_metro'] or '(none)'
        s  = stats[(c, gm)]
        s['n'] += 1
        s['ssl_vals'].append(ssl)
        s['key_vals'].append(key)
        s['pairs'].append((ssl, key))
        s['sx']  += ssl;  s['sy']  += key
        s['sxy'] += ssl * key
        s['sx2'] += ssl * ssl; s['sy2'] += key * key

def fmt(v, d=3):
    return f"{v:.{d}f}" if v is not None else "N/A"

results = []
for (c, gm), s in stats.items():
    n = s['n']
    if n < MIN_N:
        continue
    key_s = sorted(s['key_vals'])
    kp95 = percentile(key_s, 95)
    if kp95 is None or kp95 <= 10:
        continue
    ssl_s = sorted(s['ssl_vals'])
    sp50  = percentile(ssl_s, 50)
    sp95  = percentile(ssl_s, 95)
    kp50  = percentile(key_s, 50)
    pr = pearson_r(s['sx'], s['sy'], s['sxy'], s['sx2'], s['sy2'], n)
    sr = spearman(s['pairs'])
    results.append((c, gm, n, sp50, sp95, kp50, kp95, pr, sr))

results.sort(key=lambda x: (x[0], -x[6]))

hdr = (f"{'Country':<9} {'Metro':<7} {'n':>6}  "
       f"{'ssl_p50':>7} {'ssl_p95':>8}  "
       f"{'key_p50':>7} {'key_p95':>8}  "
       f"{'Pearson_r':>10}  {'Spearman_r':>11}")
print()
print(hdr)
print("-" * len(hdr))
prev_c = None
for c, gm, n, sp50, sp95, kp50, kp95, pr, sr in results:
    if c != prev_c and prev_c is not None:
        print()
    prev_c = c
    print(f"{c:<9} {gm:<7} {n:>6,}  "
          f"{sp50:>6.0f}ms {sp95:>7.1f}ms  "
          f"{kp50:>6.0f}ms {kp95:>7.1f}ms  "
          f"{fmt(pr):>10}  {fmt(sr):>11}")

print(f"\nTotal: {len(results)} metros with key_p95 > 10ms and n>={MIN_N}")
