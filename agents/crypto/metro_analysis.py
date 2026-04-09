import csv, math
from collections import defaultdict

ENRICHED = "/Users/rmadyast/product_metrics/competitive/agents/crypto/crypto_latency_output/crypto_latency_enriched.20260407.csv"
COUNTRIES = {'in','us','au','br'}
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
    r = num/(dx*dy)**0.5
    return max(-1.0,min(1.0,r))

def spearman(pairs):
    n=len(pairs)
    if n<2: return None
    def rank(vals):
        si=sorted(range(n),key=lambda i:vals[i])
        r=[0.0]*n; i=0
        while i<n:
            j=i
            while j<n-1 and vals[si[j+1]]==vals[si[j]]: j+=1
            ar=(i+j)/2.0+1.0
            for k in range(i,j+1): r[si[k]]=ar
            i=j+1
        return r
    xs=[p[0] for p in pairs]; ys=[p[1] for p in pairs]
    rx=rank(xs); ry=rank(ys)
    sx=sum(rx); sy=sum(ry)
    sxy=sum(rx[i]*ry[i] for i in range(n))
    sx2=sum(v*v for v in rx); sy2=sum(v*v for v in ry)
    return pearson_r(sx,sy,sxy,sx2,sy2,n)

stats = defaultdict(lambda: {
    'n':0,'ssl_vals':[],'key_vals':[],'pairs':[],
    'ssl_gt20':0,'ssl_gt50':0,'key_gt10':0,'diff_metro':0,
    'sx':0.0,'sy':0.0,'sxy':0.0,'sx2':0.0,'sy2':0.0,
})

with open(ENRICHED) as f:
    for row in csv.DictReader(f):
        c = row['test_country']
        if c not in COUNTRIES: continue
        try:
            ssl = float(row['ssltime'])
            key = float(row['keysign_lat']) if row['keysign_lat'] else 0.0
        except ValueError:
            continue
        gm = row['ghost_metro'] or '(none)'
        cm = row['crypto_metro']
        s = stats[(c, gm)]
        s['n']+=1
        s['ssl_vals'].append(ssl); s['key_vals'].append(key)
        s['pairs'].append((ssl,key))
        if ssl>20: s['ssl_gt20']+=1
        if ssl>50: s['ssl_gt50']+=1
        if key>10: s['key_gt10']+=1
        if gm!='(none)' and cm and gm!=cm: s['diff_metro']+=1
        s['sx']+=ssl; s['sy']+=key; s['sxy']+=ssl*key
        s['sx2']+=ssl*ssl; s['sy2']+=key*key

def fmt(v,d=3): return f"{v:.{d}f}" if v is not None else "N/A"

for country in ('au','br','in','us'):
    metros = [(gm,s) for (c,gm),s in stats.items() if c==country and s['n']>=MIN_N]
    metros.sort(key=lambda x:-x[1]['n'])

    print()
    print("="*108)
    print(f"  METRO-LEVEL ANALYSIS: {country.upper()}  ({len(metros)} metros with n>={MIN_N})")
    print("="*108)
    hdr = (f"{'Metro':<7} {'n':>6}  {'ssl_p50':>7} {'ssl_p95':>8}  "
           f"{'ssl>20':>7} {'ssl>50':>7}  {'key_p50':>7} {'key_p95':>8}  "
           f"{'key>10':>7}  {'diff_%':>7}  {'Pearson_r':>10}  {'Spearman_r':>11}  Note")
    print(hdr)
    print("-"*108)
    for gm, s in metros:
        n = s['n']
        ssl_s = sorted(s['ssl_vals']); key_s = sorted(s['key_vals'])
        sp50=percentile(ssl_s,50); sp95=percentile(ssl_s,95)
        kp50=percentile(key_s,50); kp95=percentile(key_s,95)
        pr = pearson_r(s['sx'],s['sy'],s['sxy'],s['sx2'],s['sy2'],n)
        sr = spearman(s['pairs'])
        def pct(x): return f"{100*x/n:.1f}%"
        r = pr if pr is not None else 0
        if r >= 0.5:    note="keysign-driven"
        elif r >= 0.3:  note="moderate coupling"
        elif r >= 0.1:  note="weak coupling"
        elif r <= -0.1: note="inverse/anomalous"
        else:            note="no coupling"
        if sp50 is not None and sp50 > 30:  note += " | HIGH MEDIAN"
        elif sp50 is not None and sp50 > 20: note += " | elevated median"
        if kp50 is not None and kp50 > 10:  note += " | SLOW KEYSIGN MEDIAN"
        print(
            f"{gm:<7} {n:>6,}  {sp50:>6.0f}ms {sp95:>7.1f}ms  "
            f"{pct(s['ssl_gt20']):>7} {pct(s['ssl_gt50']):>7}  "
            f"{kp50:>6.0f}ms {kp95:>7.1f}ms  "
            f"{pct(s['key_gt10']):>7}  {pct(s['diff_metro']):>7}  "
            f"{fmt(pr):>10}  {fmt(sr):>11}  {note}"
        )

print()
print("="*108)
print("END OF METRO ANALYSIS -- Source: crypto_latency_enriched.20260407.csv")
print("="*108)
