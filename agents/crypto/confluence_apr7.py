data = {
    'au': {'n':16870,'ssl_p50':23.0,'ssl_p95':63.0,'s20':64.9,'s30':23.1,'s50':7.0,'key_p50':11.0,'key_p95':14.0,'k10':58.3,'k20':0.2,'k30':0.1,'dm':59.9,'s20k10':15.0,'s30k10':8.5,'s50k10':4.3,'s50k20':6.9,'r':-0.012,'r2':0.000,'slope':-0.001,'rsm':0.052,'sp':0.409},
    'br': {'n':7218,'ssl_p50':15.0,'ssl_p95':56.0,'s20':36.0,'s30':21.1,'s50':6.2,'key_p50':1.0,'key_p95':26.0,'k10':18.5,'k20':7.5,'k30':3.6,'dm':37.8,'s20k10':16.9,'s30k10':8.0,'s50k10':1.7,'s50k20':2.6,'r':0.588,'r2':0.346,'slope':0.326,'rsm':0.174,'sp':0.688},
    'ca': {'n':4304,'ssl_p50':19.0,'ssl_p95':42.0,'s20':45.7,'s30':14.5,'s50':2.0,'key_p50':6.0,'key_p95':15.0,'k10':41.2,'k20':0.9,'k30':0.2,'dm':60.4,'s20k10':15.7,'s30k10':3.9,'s50k10':0.5,'s50k20':1.8,'r':0.551,'r2':0.303,'slope':0.281,'rsm':0.064,'sp':0.641},
    'de': {'n':13103,'ssl_p50':20.0,'ssl_p95':52.0,'s20':46.8,'s30':24.2,'s50':6.1,'key_p50':9.0,'key_p95':13.0,'k10':30.8,'k20':0.4,'k30':0.1,'dm':96.0,'s20k10':31.4,'s30k10':16.9,'s50k10':3.8,'s50k20':5.8,'r':0.093,'r2':0.009,'slope':0.021,'rsm':0.056,'sp':0.112},
    'fr': {'n':13124,'ssl_p50':21.0,'ssl_p95':37.0,'s20':51.0,'s30':12.8,'s50':1.2,'key_p50':9.0,'key_p95':13.0,'k10':18.9,'k20':0.4,'k30':0.1,'dm':93.2,'s20k10':27.6,'s30k10':6.2,'s50k10':0.7,'s50k20':1.1,'r':0.425,'r2':0.181,'slope':0.147,'rsm':0.198,'sp':0.400},
    'gb': {'n':11778,'ssl_p50':21.0,'ssl_p95':45.0,'s20':50.2,'s30':19.9,'s50':3.1,'key_p50':8.0,'key_p95':15.0,'k10':32.7,'k20':0.3,'k30':0.1,'dm':88.8,'s20k10':22.6,'s30k10':10.4,'s50k10':1.1,'s50k20':2.9,'r':0.294,'r2':0.086,'slope':0.075,'rsm':0.456,'sp':0.482},
    'hk': {'n':5001,'ssl_p50':17.0,'ssl_p95':43.0,'s20':37.6,'s30':16.2,'s50':2.7,'key_p50':1.0,'key_p95':2.0,'k10':0.4,'k20':0.1,'k30':0.0,'dm':0.1,'s20k10':37.1,'s30k10':15.8,'s50k10':2.5,'s50k20':2.6,'r':0.188,'r2':0.035,'slope':0.020,'rsm':0.180,'sp':0.179},
    'id': {'n':1418,'ssl_p50':32.0,'ssl_p95':71.0,'s20':76.4,'s30':54.2,'s50':20.5,'key_p50':12.0,'key_p95':15.1,'k10':51.9,'k20':1.2,'k30':0.6,'dm':75.1,'s20k10':28.1,'s30k10':17.8,'s50k10':6.2,'s50k20':19.6,'r':0.393,'r2':0.154,'slope':0.137,'rsm':0.315,'sp':0.435},
    'in': {'n':24381,'ssl_p50':20.0,'ssl_p95':68.0,'s20':47.6,'s30':24.7,'s50':10.5,'key_p50':2.0,'key_p95':18.0,'k10':16.7,'k20':4.5,'k30':3.7,'dm':39.7,'s20k10':30.4,'s30k10':14.5,'s50k10':5.4,'s50k20':6.8,'r':0.180,'r2':0.032,'slope':0.025,'rsm':0.168,'sp':0.452},
    'it': {'n':8506,'ssl_p50':17.0,'ssl_p95':34.0,'s20':26.6,'s30':7.6,'s50':0.7,'key_p50':10.0,'key_p95':16.0,'k10':45.7,'k20':0.9,'k30':0.1,'dm':60.7,'s20k10':4.4,'s30k10':1.1,'s50k10':0.2,'s50k20':0.6,'r':0.609,'r2':0.371,'slope':0.373,'rsm':0.326,'sp':0.719},
    'jp': {'n':8958,'ssl_p50':21.0,'ssl_p95':69.0,'s20':50.9,'s30':27.5,'s50':14.5,'key_p50':2.0,'key_p95':10.0,'k10':1.9,'k20':0.2,'k30':0.1,'dm':46.1,'s20k10':45.9,'s30k10':25.3,'s50k10':13.9,'s50k20':14.4,'r':0.025,'r2':0.001,'slope':0.003,'rsm':-0.042,'sp':0.231},
    'kr': {'n':1434,'ssl_p50':19.0,'ssl_p95':42.0,'s20':42.7,'s30':16.0,'s50':2.0,'key_p50':1.0,'key_p95':3.0,'k10':0.1,'k20':0.1,'k30':0.1,'dm':0.1,'s20k10':42.5,'s30k10':15.9,'s50k10':2.0,'s50k20':2.0,'r':0.107,'r2':0.011,'slope':0.016,'rsm':0.083,'sp':0.016},
    'mx': {'n':3600,'ssl_p50':13.0,'ssl_p95':50.0,'s20':19.6,'s30':10.0,'s50':4.6,'key_p50':4.0,'key_p95':38.0,'k10':8.2,'k20':6.1,'k30':5.9,'dm':78.9,'s20k10':11.6,'s30k10':3.5,'s50k10':1.0,'s50k20':1.1,'r':0.785,'r2':0.616,'slope':0.569,'rsm':0.152,'sp':0.517},
    'sa': {'n':90,'ssl_p50':85.0,'ssl_p95':100.5,'s20':100.0,'s30':100.0,'s50':100.0,'key_p50':75.0,'key_p95':83.3,'k10':100.0,'k20':100.0,'k30':100.0,'dm':100.0,'s20k10':0.0,'s30k10':0.0,'s50k10':0.0,'s50k20':0.0,'r':0.503,'r2':0.253,'slope':0.209,'rsm':None,'sp':0.667},
    'sg': {'n':4028,'ssl_p50':14.0,'ssl_p95':46.0,'s20':34.0,'s30':15.7,'s50':3.8,'key_p50':1.0,'key_p95':13.0,'k10':12.5,'k20':0.5,'k30':0.2,'dm':13.8,'s20k10':23.0,'s30k10':11.4,'s50k10':3.1,'s50k20':3.6,'r':0.159,'r2':0.025,'slope':0.028,'rsm':0.030,'sp':0.339},
    'us': {'n':57936,'ssl_p50':18.0,'ssl_p95':60.0,'s20':42.2,'s30':23.6,'s50':8.6,'key_p50':6.0,'key_p95':25.0,'k10':26.5,'k20':7.8,'k30':2.3,'dm':60.4,'s20k10':19.1,'s30k10':9.1,'s50k10':2.6,'s50k20':3.8,'r':0.273,'r2':0.074,'slope':0.071,'rsm':0.206,'sp':0.577},
}
total_n = sum(v['n'] for v in data.values())

print(f"Crypto Latency Analysis -- 20260403-20260406")
print(f"{total_n:,} total sessions | 16 countries | Source: crypto_latency_stats.20260407.tsv")

print()
print("="*90)
print("SECTION 1: SSL Latency Severity by Country")
print("="*90)
print(f"{'Country':<8} {'N':>7}  {'ssl_p50':>8} {'ssl_p95':>8}  {'ssl>20':>7} {'ssl>30':>7} {'ssl>50':>7}  {'20-30ms':>8} {'30-50ms':>8} {'50ms+':>7}")
print("-"*90)
for c, v in sorted(data.items(), key=lambda x: -x[1]['s20']):
    b1 = v['s20'] - v['s30']
    b2 = v['s30'] - v['s50']
    b3 = v['s50']
    print(f"{c.upper():<8} {v['n']:>7,}  {v['ssl_p50']:>7.0f}ms {v['ssl_p95']:>7.1f}ms  {v['s20']:>6.1f}%  {v['s30']:>6.1f}%  {v['s50']:>6.1f}%  {b1:>7.1f}%  {b2:>7.1f}%  {b3:>6.1f}%")

print()
print("="*90)
print("SECTION 2: Keysign Latency Distribution by Country")
print("="*90)
print(f"{'Country':<8} {'N':>7}  {'key_p50':>8} {'key_p95':>8}  {'key>10':>7} {'key>20':>7} {'key>30':>7}   {'ssl>50&key<10':>14} {'ssl>50&key<20':>14}  {'%ssl>20|key<10':>15}")
print("-"*105)
for c, v in sorted(data.items(), key=lambda x: -x[1]['k10']):
    pct = (v['s20k10'] / v['s20'] * 100) if v['s20'] > 0 else 0
    print(f"{c.upper():<8} {v['n']:>7,}  {v['key_p50']:>7.0f}ms {v['key_p95']:>7.1f}ms  {v['k10']:>6.1f}%  {v['k20']:>6.1f}%  {v['k30']:>6.1f}%   {v['s50k10']:>13.1f}%  {v['s50k20']:>13.1f}%  {pct:>14.0f}%")

print()
print("="*90)
print("SECTION 3: Correlation Analysis (keysign_lat -> ssl_lat)")
print("="*90)
print(f"{'Country':<8} {'N':>7} {'Pearson r':>10} {'R2':>7} {'Slope':>8} {'Spearman r':>11}  Interpretation")
print("-"*82)
for c, v in sorted(data.items(), key=lambda x: -x[1]['r']):
    r = v['r']
    if r >= 0.5:
        interp = "STRONG -- keysign drives SSL"
    elif r >= 0.3:
        interp = "Moderate coupling"
    elif r >= 0.1:
        interp = "Weak coupling"
    else:
        interp = "No coupling"
    print(f"{c.upper():<8} {v['n']:>7,}  {r:>9.3f}  {v['r2']:>6.3f}  {v['slope']:>7.3f}  {v['sp']:>10.3f}  {interp}")

print()
print("="*90)
print("SECTION 4: Ghost->Crypto Metro Mismatch (diff_metro)")
print("="*90)
print(f"{'Country':<8} {'diff_metro':>10}  {'ssl_p50':>8} {'ssl_p95':>8}  {'r_global':>9}  {'r_same_metro':>13}  Note")
print("-"*84)
for c, v in sorted(data.items(), key=lambda x: -x[1]['dm']):
    rsm = f"{v['rsm']:.3f}" if v['rsm'] is not None else "  N/A"
    if v['dm'] >= 80:
        note = "Cross-metro dominant"
    elif v['dm'] >= 40:
        note = "Mixed routing"
    else:
        note = "Same-metro"
    print(f"{c.upper():<8} {v['dm']:>9.1f}%  {v['ssl_p50']:>7.0f}ms {v['ssl_p95']:>7.1f}ms  {v['r']:>9.3f}  {rsm:>13}  {note}")

print()
print("="*90)
print("SECTION 5: Country Clusters")
print("="*90)
clusters = [
    ("A - Keysign-driven (r>=0.5)",                   ['mx','it','br','ca']),
    ("B - Moderate coupling (0.3<=r<0.5)",             ['fr','gb','id']),
    ("C - Routing bottleneck (low r, high diff_metro)",['de','in']),
    ("D - Independent SSL bottleneck (r~0, key~0)",    ['jp','sg','hk','kr']),
    ("E - Dual independent failure modes",             ['au']),
    ("F - US baseline (moderate, large sample)",       ['us']),
    ("G - Insufficient data",                          ['sa']),
]
for name, cs in clusters:
    print(f"\n  Cluster {name}")
    for c in cs:
        v = data[c]
        rsm = f"{v['rsm']:.3f}" if v['rsm'] is not None else " N/A"
        print(
            f"    {c.upper():<4}  n={v['n']:>7,}  ssl_p50={v['ssl_p50']:>4.0f}ms"
            f"  ssl_p95={v['ssl_p95']:>5.1f}ms  key_p50={v['key_p50']:>3.0f}ms"
            f"  key_p95={v['key_p95']:>5.1f}ms  r={v['r']:>6.3f}  dm={v['dm']:>5.1f}%"
        )

print()
print("="*90)
print("SECTION 6: Actionable Findings & Recommendations")
print("="*90)

actions = [
    ("CRITICAL - SA (Saudi Arabia)",
     "ssl_p50=85ms, ssl_p95=100.5ms, key_p50=75ms, key_p95=83.3ms. Every session universally "
     "degraded -- not just the tail. r=0.503: keysign drives SSL. n=90 (directional only). "
     "This is the only country where the MEDIAN keysign (75ms) exceeds any other country's p95. "
     "Immediate MENA crypto cluster investigation required."),
    ("CRITICAL - ID (Indonesia)",
     "ssl_p50=32ms (worst non-SA median), ssl_p95=71ms. key_p50=12ms -- the MEDIAN keysign "
     "already exceeds the 10ms concern threshold. Two compounding problems: (a) 75% cross-metro "
     "routing -- fix ghost->crypto affinity. (b) Slow keysign cluster -- investigate why "
     "key_p50=12ms. r=0.393 confirms both issues contribute. n=1,418 is small; expand coverage."),
    ("HIGH - AU (Australia)",
     "ssl_p50=23ms -- the MEDIAN session already exceeds the 20ms concern line. ssl_p95=63ms. "
     "key_p50=11ms (above 10ms concern threshold at the median). Yet r=-0.012: no correlation. "
     "23% of ssl>20ms sessions have keysign<10ms -- SSL and keysign are BOTH slow but on "
     "DIFFERENT sessions. Two independent failure modes. Each requires separate investigation."),
    ("HIGH - JP (Japan)",
     "ssl_p95=69ms (second worst non-SA). key_p50=2ms, key_p95=10ms -- keysign healthy at all "
     "percentiles. r=0.025: no correlation. 90% of ssl>50ms events have keysign<10ms. "
     "The fat tail is NOT keysign-driven. r_same_metro=-0.042 (negative). Likely BGP routing, "
     "TLS handshake path, or internal edge->crypto forwarding. Requires packet-level analysis."),
    ("HIGH - IN (India)",
     "ssl_p95=68ms at n=24,381 (second largest sample). key_p95=18ms. Wide distributions in "
     "both metrics. r=0.180 (weak), diff_metro=39.7%. 30.4% of slow-SSL sessions have healthy "
     "keysign -- partially routing-driven. Metro-level sub-analysis needed to isolate the "
     "specific PoPs driving the p95 tail."),
    ("MEDIUM - US",
     "ssl_p95=60ms at n=57,936 (largest sample). key_p95=25ms. At this scale r=0.273 means "
     "keysign variance materially inflates ssl_p95. 60.4% cross-metro routing. "
     "Two actionable levers: reduce diff_metro and cap keysign p95."),
    ("MEDIUM - MX (Mexico)",
     "key_p95=38ms -- highest non-SA keysign p95 in dataset, explains r=0.785, R2=0.616. "
     "Median is healthy (ssl_p50=13ms, key_p50=4ms). ssl_p95=50ms is keysign-driven. "
     "Use key_p95 as a leading indicator: if it crosses 50ms, ssl_p95 will follow at ~0.57x slope."),
    ("MEDIUM - EU Routing (DE/FR/GB)",
     "DE ssl_p50=20ms (at threshold), ssl_p95=52ms, diff_metro=96%. "
     "FR ssl_p50=21ms, ssl_p95=37ms, diff_metro=93%. "
     "GB ssl_p50=21ms, ssl_p95=45ms, diff_metro=89%. "
     "Keysign p50 is only 8-9ms for all three -- the elevated ssl_p50 comes from routing "
     "overhead, not keysign. Fixing EU ghost->crypto affinity is the single highest-leverage action."),
    ("GOOD NEWS - IT/HK/KR/SG",
     "Italy: ssl_p50=17ms (below threshold). key_p50=10ms (borderline), key_p95=16ms. "
     "r=0.609 means keysign growth WILL eventually cascade to ssl -- preemptive action "
     "warranted before key_p50 crosses 10ms. "
     "HK: key_p50=1ms, key_p95=2ms -- best keysign performance in dataset, ssl_p50=17ms. "
     "KR: key_p95=3ms. SG: ssl_p50=14ms, key_p50=1ms. "
     "All four have ssl_p50 below 20ms -- currently lowest-risk in dataset."),
]

for i, (title, body) in enumerate(actions, 1):
    print(f"\n  {i}. [{title}]")
    words = body.split()
    line = "     "
    for w in words:
        if len(line) + len(w) + 1 > 104:
            print(line.rstrip())
            line = "     " + w + " "
        else:
            line += w + " "
    if line.strip():
        print(line.rstrip())

print()
print("="*90)
print("END OF ANALYSIS -- Source: crypto_latency_stats.20260407.tsv (181,749 sessions)")
print("="*90)
