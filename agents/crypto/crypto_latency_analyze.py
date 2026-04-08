#!/usr/bin/env python3
"""
Enrich the 5-column crypto latency CSV with metro information and compute
per-country analysis statistics.

Usage:
    python3 crypto_latency_analyze.py <config.json>
"""

import csv
import json
import os
import sys
from collections import defaultdict


def load_config(config_path):
    with open(config_path) as f:
        return json.load(f)


def build_metro_maps(mcm_file):
    ghost_metro_map = {}   # network=freeflow: ip -> metro
    crypto_metro_map = {}  # network=crypto:   ip -> metro

    with open(mcm_file, newline='') as f:
        reader = csv.DictReader(f)
        # Support both old schema (ip, regionName) and new schema (machineip/serviceip, regionname)
        sample = reader.fieldnames
        has_new_schema = 'machineip' in sample
        for row in reader:
            network = row['network'].strip()
            region_name = row['regionname' if has_new_schema else 'regionName'].strip()
            metro = region_name.split('-', 1)[1][:3] if '-' in region_name else ''
            if has_new_schema:
                if network == 'freeflow':
                    ghost_metro_map[row['serviceip'].strip()] = metro
                elif network in ('crypto', 'essl'):
                    crypto_metro_map[row['machineip'].strip()] = metro
            else:
                ip = row['ip'].strip()
                if network == 'freeflow':
                    ghost_metro_map[ip] = metro
                elif network in ('crypto', 'essl'):
                    crypto_metro_map[ip] = metro

    print(f"MCM freeflow IPs loaded: {len(ghost_metro_map)}")
    print(f"MCM crypto IPs loaded:   {len(crypto_metro_map)}")
    return ghost_metro_map, crypto_metro_map


def enrich(input_file, output_file, ghost_metro_map, crypto_metro_map):
    with open(input_file, newline='') as fin, open(output_file, 'w', newline='') as fout:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames + ['ghost_metro', 'crypto_metro']
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            row['ghost_metro'] = ghost_metro_map.get(row['ghostip'], '')
            row['crypto_metro'] = crypto_metro_map.get(row['cryptoip'], '')
            writer.writerow(row)

    enriched_count = sum(1 for _ in open(output_file)) - 1
    print(f"Enriched file written to {output_file} ({enriched_count} rows)")


def percentile(sorted_vals, p):
    """Linear-interpolation percentile on a pre-sorted list."""
    n = len(sorted_vals)
    if n == 0:
        return None
    idx = (p / 100.0) * (n - 1)
    lo = int(idx)
    hi = lo + 1
    if hi >= n:
        return sorted_vals[lo]
    return sorted_vals[lo] + (idx - lo) * (sorted_vals[hi] - sorted_vals[lo])


def fmt_ms(v):
    return f"{v:.1f}" if v is not None else 'N/A'


def pearson_from_sums(n, sx, sy, sxy, sx2, sy2):
    num = n * sxy - sx * sy
    den_x = n * sx2 - sx ** 2
    den_y = n * sy2 - sy ** 2
    if den_x <= 0 or den_y <= 0:
        return None
    return max(-1.0, min(1.0, num / (den_x * den_y) ** 0.5))


def pearson(s):
    r = pearson_from_sums(s['total'], s['sum_x'], s['sum_y'], s['sum_xy'], s['sum_x2'], s['sum_y2'])
    return f"{r:.3f}" if r is not None else 'N/A'


def r_squared(s):
    r = pearson_from_sums(s['total'], s['sum_x'], s['sum_y'], s['sum_xy'], s['sum_x2'], s['sum_y2'])
    return f"{r**2:.3f}" if r is not None else 'N/A'


def slope_beta(s):
    n = s['total']
    denom = n * s['sum_x2'] - s['sum_x'] ** 2
    if denom <= 0:
        return 'N/A'
    b = (n * s['sum_xy'] - s['sum_x'] * s['sum_y']) / denom
    return f"{b:.3f}"


def pearson_same_metro(s):
    n = s['sm_n']
    if n < 2:
        return 'N/A'
    r = pearson_from_sums(n, s['sm_sum_x'], s['sm_sum_y'], s['sm_sum_xy'], s['sm_sum_x2'], s['sm_sum_y2'])
    return f"{r:.3f}" if r is not None else 'N/A'


def spearman_r(pairs):
    n = len(pairs)
    if n < 2:
        return 'N/A'

    def rank_values(vals):
        sorted_idx = sorted(range(n), key=lambda i: vals[i])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and vals[sorted_idx[j + 1]] == vals[sorted_idx[j]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                ranks[sorted_idx[k]] = avg_rank
            i = j + 1
        return ranks

    ssls = [p[0] for p in pairs]
    keys = [p[1] for p in pairs]
    r_ssl = rank_values(ssls)
    r_key = rank_values(keys)
    sx = sum(r_ssl); sy = sum(r_key)
    sxy = sum(r_ssl[i] * r_key[i] for i in range(n))
    sx2 = sum(r * r for r in r_ssl)
    sy2 = sum(r * r for r in r_key)
    r = pearson_from_sums(n, sx, sy, sxy, sx2, sy2)
    return f"{r:.3f}" if r is not None else 'N/A'


def analyze(output_file):
    stats = defaultdict(lambda: {
        'total': 0,
        'ssl_gt20': 0, 'ssl_gt30': 0, 'ssl_gt50': 0,
        'key_gt10': 0, 'key_gt20': 0, 'key_gt30': 0,
        'diff_metro': 0,
        'ssl_gt20_key_lt10': 0,
        'ssl_gt30_key_lt10': 0,
        'ssl_gt50_key_lt10': 0,
        'ssl_gt50_key_lt20': 0,
        # full-population accumulators (Pearson, R², slope)
        'sum_x': 0.0, 'sum_y': 0.0, 'sum_xy': 0.0, 'sum_x2': 0.0, 'sum_y2': 0.0,
        # same-metro stratum accumulators
        'sm_n': 0, 'sm_sum_x': 0.0, 'sm_sum_y': 0.0,
        'sm_sum_xy': 0.0, 'sm_sum_x2': 0.0, 'sm_sum_y2': 0.0,
        # all pairs for Spearman + percentiles
        'pairs': [],
        'ssl_vals': [],
        'key_vals': [],
    })

    with open(output_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            country = row['test_country']
            try:
                ssl = float(row['ssltime'])
                key = float(row['keysign_lat']) if row['keysign_lat'] else 0.0
            except ValueError:
                continue
            s = stats[country]
            s['total'] += 1
            if ssl > 20:  s['ssl_gt20'] += 1
            if ssl > 30:  s['ssl_gt30'] += 1
            if ssl > 50:  s['ssl_gt50'] += 1
            if key > 10:  s['key_gt10'] += 1
            if key > 20:  s['key_gt20'] += 1
            if key > 30:  s['key_gt30'] += 1
            if row['ghost_metro'] and row['crypto_metro'] and row['ghost_metro'] != row['crypto_metro']:
                s['diff_metro'] += 1
            if ssl > 20 and key < 10:  s['ssl_gt20_key_lt10'] += 1
            if ssl > 30 and key < 10:  s['ssl_gt30_key_lt10'] += 1
            if ssl > 50 and key < 10:  s['ssl_gt50_key_lt10'] += 1
            if ssl > 50 and key < 20:  s['ssl_gt50_key_lt20'] += 1
            s['sum_x']  += ssl
            s['sum_y']  += key
            s['sum_xy'] += ssl * key
            s['sum_x2'] += ssl * ssl
            s['sum_y2'] += key * key
            s['pairs'].append((ssl, key))
            s['ssl_vals'].append(ssl)
            s['key_vals'].append(key)
            if row['ghost_metro'] and row['crypto_metro'] and row['ghost_metro'] == row['crypto_metro']:
                s['sm_n']      += 1
                s['sm_sum_x']  += ssl
                s['sm_sum_y']  += key
                s['sm_sum_xy'] += ssl * key
                s['sm_sum_x2'] += ssl * ssl
                s['sm_sum_y2'] += key * key

    def pct(n, total):
        return f"{100*n/total:.1f}%" if total > 0 else "N/A"

    print()
    header = (
        f"{'country':<10} {'n':>7} {'ssl_p50':>8} {'ssl_p95':>8} {'ssl>20':>7} {'ssl>30':>7} {'ssl>50':>7} "
        f"{'key_p50':>8} {'key_p95':>8} {'key>10':>7} {'key>20':>7} {'key>30':>7} {'diff_metro':>10} "
        f"{'ssl>20&key<10':>13} {'ssl>30&key<10':>13} {'ssl>50&key<10':>13} {'ssl>50&key<20':>13} "
        f"{'pearson_r':>9} {'r2':>6} {'slope':>7} {'r_samemetro':>11} {'spearman_r':>10}"
    )
    print(header)
    print('-' * len(header))
    for country in sorted(stats.keys()):
        s = stats[country]
        n = s['total']
        ssl_s = sorted(s['ssl_vals'])
        key_s = sorted(s['key_vals'])
        sp50 = fmt_ms(percentile(ssl_s, 50))
        sp95 = fmt_ms(percentile(ssl_s, 95))
        kp50 = fmt_ms(percentile(key_s, 50))
        kp95 = fmt_ms(percentile(key_s, 95))
        print(
            f"{country:<10} {n:>7} {sp50:>8} {sp95:>8} {pct(s['ssl_gt20'],n):>7} {pct(s['ssl_gt30'],n):>7} {pct(s['ssl_gt50'],n):>7} "
            f"{kp50:>8} {kp95:>8} {pct(s['key_gt10'],n):>7} {pct(s['key_gt20'],n):>7} {pct(s['key_gt30'],n):>7} {pct(s['diff_metro'],n):>10} "
            f"{pct(s['ssl_gt20_key_lt10'],n):>13} {pct(s['ssl_gt30_key_lt10'],n):>13} "
            f"{pct(s['ssl_gt50_key_lt10'],n):>13} {pct(s['ssl_gt50_key_lt20'],n):>13} "
            f"{pearson(s):>9} {r_squared(s):>6} {slope_beta(s):>7} "
            f"{pearson_same_metro(s):>11} {spearman_r(s['pairs']):>10}"
        )
    return stats


def write_tsv(stats, tsv_file):
    def pct(n, total):
        return f"{100*n/total:.1f}%" if total > 0 else "N/A"

    columns = ['country', 'n',
               'ssl_p50', 'ssl_p95', 'ssl>20', 'ssl>30', 'ssl>50',
               'key_p50', 'key_p95', 'key>10', 'key>20', 'key>30',
               'diff_metro',
               'ssl>20&key<10', 'ssl>30&key<10', 'ssl>50&key<10', 'ssl>50&key<20',
               'pearson_r', 'r2', 'slope', 'r_same_metro', 'spearman_r']

    with open(tsv_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(columns)
        for country in sorted(stats.keys()):
            s = stats[country]
            n = s['total']
            ssl_s = sorted(s['ssl_vals'])
            key_s = sorted(s['key_vals'])
            writer.writerow([
                country, n,
                fmt_ms(percentile(ssl_s, 50)), fmt_ms(percentile(ssl_s, 95)),
                pct(s['ssl_gt20'], n), pct(s['ssl_gt30'], n), pct(s['ssl_gt50'], n),
                fmt_ms(percentile(key_s, 50)), fmt_ms(percentile(key_s, 95)),
                pct(s['key_gt10'], n), pct(s['key_gt20'], n), pct(s['key_gt30'], n),
                pct(s['diff_metro'], n),
                pct(s['ssl_gt20_key_lt10'], n), pct(s['ssl_gt30_key_lt10'], n),
                pct(s['ssl_gt50_key_lt10'], n), pct(s['ssl_gt50_key_lt20'], n),
                pearson(s), r_squared(s), slope_beta(s),
                pearson_same_metro(s), spearman_r(s['pairs']),
            ])


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <config.json>")
        sys.exit(1)

    config = load_config(sys.argv[1])
    mcm_file = os.path.expanduser(config['mcm_machines_file'])
    input_file = os.path.expanduser(config['intermediate_file_6col'])
    output_file = os.path.expanduser(config['final_file_8col'])

    print("Step 7: Enriching with metro information...")
    ghost_metro_map, crypto_metro_map = build_metro_maps(mcm_file)
    enrich(input_file, output_file, ghost_metro_map, crypto_metro_map)

    print("\nStep 8: Analysis and Statistics")
    stats = analyze(output_file)

    # Write TSV output — use stats_file from config if present, else default name
    output_dir = os.path.dirname(output_file)
    tsv_file = os.path.expanduser(
        config.get('stats_file', os.path.join(output_dir, "crypto_latency_stats.tsv"))
    )
    write_tsv(stats, tsv_file)
    print(f"\nStats table written to {tsv_file}")


if __name__ == '__main__':
    main()
