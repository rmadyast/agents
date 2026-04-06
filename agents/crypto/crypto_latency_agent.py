#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from collections import defaultdict
import re

# Load config
with open('/Users/rmadyast/product_metrics/competitive/agents/crypto_latency_config.json') as f:
    config = json.load(f)

target_dates = config['date_directories'].split(',')

BASE_PATH = '/datastore1/svc_epremo/fill_log'
OUTPUT_DIR = '/tmp/crypto_latency_output'
REMOTE_HOST = 'envy.akamai.com'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def ssh_run(cmd):
    """Execute command on remote host"""
    result = subprocess.run(
        ['ssh', REMOTE_HOST, cmd],
        capture_output=True, text=True
    )
    return result.stdout.strip()

# Step 1: Find all parent directories with 'amd'
print("Step 1: Identifying parent directories with 'amd'")
parent_dirs_str = ssh_run(f"ls -d {BASE_PATH}/*amd* 2>/dev/null")
parent_dirs = [p for p in parent_dirs_str.split('\n') if p]
print(f"Found {len(parent_dirs)} parent directories")

# Step 2: Extract country code and find date subdirectories
data_by_date = defaultdict(list)
all_rows = []

for parent_dir in parent_dirs:
    dir_name = os.path.basename(parent_dir)
    # Extract country code (2nd element in hyphen-separated string)
    parts = dir_name.split('-')
    if len(parts) >= 2:
        country = parts[1]
    else:
        country = 'unknown'
    
    print(f"\nProcessing parent: {dir_name} (country: {country})")
    
    # Find target date subdirectories
    for target_date in target_dates:
        date_dir = os.path.join(parent_dir, target_date)
        
        # Check if date directory exists
        check_cmd = f"test -d {date_dir} && echo EXISTS || echo NOTEXISTS"
        exists = ssh_run(check_cmd)
        
        if exists != 'EXISTS':
            continue
        
        print(f"  Found date directory: {target_date}")
        
        # List gzipped files
        list_cmd = f"ls {date_dir}/*.gz 2>/dev/null"
        gzip_files_str = ssh_run(list_cmd)
        gzip_files = [f for f in gzip_files_str.split('\n') if f]
        print(f"    Processing {len(gzip_files)} gzip files")
        
        # Process each gzip file
        for gzip_file in gzip_files:
            # Create a processing script to run on remote
            process_cmd = f"""
zcat {gzip_file} 2>/dev/null | while IFS='|' read -ra fields; do
    # Check if we have at least 77 fields
    if [ ${{#fields[@]}} -lt 77 ]; then
        continue
    fi
    
    # Extract fields
    ghostip="${{fields[0]}}"
    ssltime_str="${{fields[3]}}"
    keysign_lat="${{fields[76]}}"
    
    # Check if ssltime is numeric and > 0
    if ! echo "$ssltime_str" | grep -E '^[0-9]+([.][0-9]+)?$' > /dev/null; then
        continue
    fi
    
    ssltime=$(echo "$ssltime_str" | awk '{{ if ($1 > 0) print $1; else exit 1 }}')
    if [ $? -ne 0 ]; then
        continue
    fi
    
    # Extract cryptoip from cs= field
    cryptoip=""
    for field in "${{fields[@]}}"; do
        if [[ $field == cs=* ]]; then
            cryptoip="${{field#cs=}}"
            cryptoip="${{cryptoip%%|*}}"
            break
        fi
    done
    
    # Output the 5 columns
    echo "$country|$ghostip|$cryptoip|$ssltime|$keysign_lat"
done
"""
            try:
                # Run the zcat processing on remote and collect results
                result = subprocess.run(
                    ['ssh', REMOTE_HOST, process_cmd],
                    capture_output=True, text=True, timeout=60
                )
                
                for line in result.stdout.strip().split('\n'):
                    if line:
                        fields = line.split('|')
                        if len(fields) == 5:
                            all_rows.append(fields)
                            
            except Exception as e:
                print(f"      Error processing {gzip_file}: {e}")

# Step 3: Write concatenated output with headers
output_file = os.path.join(OUTPUT_DIR, 'crypto_latency_all.csv')
with open(output_file, 'w') as f:
    f.write('test_country,ghostip,cryptoip,ssltime,keysign_lat\n')
    for row in all_rows:
        f.write(','.join(row) + '\n')

print(f"\nStep 3: Written {len(all_rows)} rows to {output_file}")
print(f"\nTotal number of rows in intermediate 5-column table: {len(all_rows)}")
