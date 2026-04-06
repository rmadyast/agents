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


def pearson(s):
    n = s['total']
    num = n * s['sum_xy'] - s['sum_x'] * s['sum_y']
    den_x = n * s['sum_x2'] - s['sum_x'] ** 2
    den_y = n * s['sum_y2'] - s['sum_y'] ** 2
    if den_x <= 0 or den_y <= 0:
        return 'N/A'
    return f"{num / (den_x * den_y) ** 0.5:.3f}"


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
        'sum_x': 0.0, 'sum_y': 0.0, 'sum_xy': 0.0, 'sum_x2': 0.0, 'sum_y2': 0.0,
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

    def pct(n, total):
        return f"{100*n/total:.1f}%" if total > 0 else "N/A"

    print()
    header = (
        f"{'country':<10} {'n':>7} {'ssl>20':>7} {'ssl>30':>7} {'ssl>50':>7} "
        f"{'key>10':>7} {'key>20':>7} {'key>30':>7} {'diff_metro':>10} "
        f"{'ssl>20&key<10':>13} {'ssl>30&key<10':>13} {'ssl>50&key<10':>13} {'ssl>50&key<20':>13} {'pearson_r':>9}"
    )
    print(header)
    print('-' * len(header))
    for country in sorted(stats.keys()):
        s = stats[country]
        n = s['total']
        print(
            f"{country:<10} {n:>7} {pct(s['ssl_gt20'],n):>7} {pct(s['ssl_gt30'],n):>7} {pct(s['ssl_gt50'],n):>7} "
            f"{pct(s['key_gt10'],n):>7} {pct(s['key_gt20'],n):>7} {pct(s['key_gt30'],n):>7} {pct(s['diff_metro'],n):>10} "
            f"{pct(s['ssl_gt20_key_lt10'],n):>13} {pct(s['ssl_gt30_key_lt10'],n):>13} "
            f"{pct(s['ssl_gt50_key_lt10'],n):>13} {pct(s['ssl_gt50_key_lt20'],n):>13} {pearson(s):>9}"
        )
    return stats


def write_tsv(stats, tsv_file):
    def pct(n, total):
        return f"{100*n/total:.1f}%" if total > 0 else "N/A"

    columns = ['country', 'n', 'ssl>20', 'ssl>30', 'ssl>50',
               'key>10', 'key>20', 'key>30', 'diff_metro',
               'ssl>20&key<10', 'ssl>30&key<10', 'ssl>50&key<10', 'ssl>50&key<20',
               'pearson_r']

    with open(tsv_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(columns)
        for country in sorted(stats.keys()):
            s = stats[country]
            n = s['total']
            writer.writerow([
                country, n,
                pct(s['ssl_gt20'], n), pct(s['ssl_gt30'], n), pct(s['ssl_gt50'], n),
                pct(s['key_gt10'], n), pct(s['key_gt20'], n), pct(s['key_gt30'], n),
                pct(s['diff_metro'], n),
                pct(s['ssl_gt20_key_lt10'], n), pct(s['ssl_gt30_key_lt10'], n),
                pct(s['ssl_gt50_key_lt10'], n), pct(s['ssl_gt50_key_lt20'], n),
                pearson(s),
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

    # Write TSV output to same directory as the output files
    output_dir = os.path.dirname(output_file)
    tsv_file = os.path.join(output_dir, "crypto_latency_stats.tsv")
    write_tsv(stats, tsv_file)
    print(f"\nStats table written to {tsv_file}")


if __name__ == '__main__':
    main()
