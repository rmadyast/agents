#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/crypto_latency_config_v2.json"

# Read parameters from config file
date_directories=$(jq -r '.date_directories' "$CONFIG_FILE")
base_path=$(jq -r '.base_path' "$CONFIG_FILE")
remote_host=$(jq -r '.remote_host' "$CONFIG_FILE")
query2_vm=$(jq -r '.query2_vm' "$CONFIG_FILE")
query2_host=$(jq -r '.query2_host' "$CONFIG_FILE")
mcm_machines_file=$(eval echo "$(jq -r '.mcm_machines_file' "$CONFIG_FILE")")
intermediate_file_6col=$(eval echo "$(jq -r '.intermediate_file_6col' "$CONFIG_FILE")")
final_file_8col=$(eval echo "$(jq -r '.final_file_8col' "$CONFIG_FILE")")

# Inject execution date into all output file names
EXEC_DATE=$(date +%Y%m%d)
mcm_machines_file=$(echo "$mcm_machines_file" | sed "s/\.csv$/.$EXEC_DATE.csv/")
intermediate_file_6col=$(echo "$intermediate_file_6col" | sed "s/\.csv$/.$EXEC_DATE.csv/")
final_file_8col=$(echo "$final_file_8col" | sed "s/\.csv$/.$EXEC_DATE.csv/")

# Create output directory
OUTPUT_DIR=$(dirname "$intermediate_file_6col")
mkdir -p "$OUTPUT_DIR"

TARGET_DATES="$date_directories"
OUTPUT_FILE="$intermediate_file_6col"

# ---------------------------------------------------------------------------
# Step 0: Generate MCM machines file via sql2 on query2_vm
# ---------------------------------------------------------------------------
echo "Step 0: Generating MCM machines file from Query2 on $query2_vm..."

# Write a small script that runs both sql2 queries on the remote VM
QUERY_SCRIPT="/tmp/mcm_gen_$$.sh"
cat > "$QUERY_SCRIPT" << QUERYEOF
#!/bin/bash
# Freeflow IPs: join mcm_machines with machinesvc on ghost service
# Output includes header; strip the Query2 type row (line 2)
sql2 --host "$query2_host" --csv --no-interactive \
  "SELECT m.ip AS machineip, s.serviceip AS serviceip, m.regionname AS regionname, m.network AS network \
   FROM mcm_machines m, machinesvc s \
   WHERE m.ip = s.machineip AND s.service='ghost' AND m.network='freeflow'" \
  2>/dev/null | awk 'NR!=2'

# Crypto IPs: mcm_machines with network='crypto'
# Skip header and type row (NR>2), append data only
sql2 --host "$query2_host" --csv --no-interactive \
  "SELECT ip AS machineip, ip AS serviceip, regionname, network \
   FROM mcm_machines WHERE network='crypto'" \
  2>/dev/null | awk 'NR>2'
QUERYEOF

# Copy script to VM and execute, capturing output to local mcm file
REMOTE_QUERY_PATH="/tmp/mcm_gen_$$.sh"
scp -q "$QUERY_SCRIPT" "$query2_vm:$REMOTE_QUERY_PATH"
mkdir -p "$(dirname "$mcm_machines_file")"
ssh "$query2_vm" "bash $REMOTE_QUERY_PATH" > "$mcm_machines_file" 2>/tmp/crypto_latency_debug.log

# Clean up
ssh "$query2_vm" "rm -f $REMOTE_QUERY_PATH" 2>/dev/null
rm -f "$QUERY_SCRIPT"

mcm_count=$(tail -n +2 "$mcm_machines_file" | wc -l)
echo "MCM machines file generated: $mcm_machines_file ($mcm_count rows)"

# ---------------------------------------------------------------------------
# Step 1 & 2: Extract 6-column data from log files on remote_host
# ---------------------------------------------------------------------------
echo ""
echo "Step 1: Identifying parent directories with 'amd' on $remote_host"

# Write the remote processing script with variables interpolated
REMOTE_SCRIPT="/tmp/crypto_latency_remote_$$.sh"
cat > "$REMOTE_SCRIPT" << SCRIPTEOF
#!/bin/bash
BASE_PATH="$base_path"
TARGET_DATES="$TARGET_DATES"

# Find all parent directories with 'amd' that have any target date
IFS=',' read -ra dates_array <<< "\$TARGET_DATES"
first_date="\${dates_array[0]// /}"
parent_dirs=\$(ls -d \$BASE_PATH/*amd*/\$first_date 2>/dev/null | xargs -I{} dirname {})

parent_count=\$(echo "\$parent_dirs" | wc -l)
echo "Found \$parent_count parent directories" >&2

for parent_dir in \$parent_dirs; do
    dir_name=\$(basename "\$parent_dir")
    country=\$(echo "\$dir_name" | cut -d'-' -f2)
    competitor=\$(echo "\$dir_name" | cut -d'-' -f1)
    echo "Processing parent: \$dir_name (country: \$country, competitor: \$competitor)" >&2

    for target_date in "\${dates_array[@]}"; do
        target_date=\$(echo "\$target_date" | xargs)
        date_dir="\$parent_dir/\$target_date"
        if [ ! -d "\$date_dir" ]; then continue; fi

        gzip_files=\$(ls "\$date_dir"/*.gz 2>/dev/null)
        if [ -z "\$gzip_files" ]; then continue; fi

        gzip_count=\$(echo "\$gzip_files" | wc -l)
        echo "  Found date directory: \$target_date (\$gzip_count gzip files)" >&2

        for gzip_file in \$gzip_files; do
            zcat "\$gzip_file" 2>/dev/null | awk -v country="\$country" -v competitor="\$competitor" '
            NF >= 61 {
                ghostip = \$1
                ssltime = \$4
                if (\$2 == "r" && NF >= 77) keysign_lat = \$77
                else if (\$2 == "S") keysign_lat = \$61
                else keysign_lat = ""
                if (ssltime+0 > 0) {
                    if (match(\$0, /cs=[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/)) {
                        cryptoip = substr(\$0, RSTART+3, RLENGTH-3)
                        print country "," competitor "," ghostip "," cryptoip "," ssltime "," keysign_lat
                    }
                }
            }'
        done
    done
done
SCRIPTEOF

# Write header then copy script to remote host and execute
echo "test_country,competitor,ghostip,cryptoip,ssltime,keysign_lat" > "$OUTPUT_FILE"
REMOTE_PATH="/tmp/crypto_latency_remote_$$.sh"
scp -q "$REMOTE_SCRIPT" "$remote_host:$REMOTE_PATH"
ssh "$remote_host" "bash $REMOTE_PATH" >> "$OUTPUT_FILE" 2>>/tmp/crypto_latency_debug.log

# Clean up
ssh "$remote_host" "rm -f $REMOTE_PATH" 2>/dev/null
rm -f "$REMOTE_SCRIPT"

echo ""
echo "Step 2: Output written to $OUTPUT_FILE"
final_count=$(tail -n +2 "$OUTPUT_FILE" | wc -l)
echo "Total number of rows in intermediate 6-column table: $final_count"

# ---------------------------------------------------------------------------
# Steps 7 & 8: Enrich with metro info and run analysis
# ---------------------------------------------------------------------------
echo ""

# Build a temporary config with dated file paths for the analysis step
TEMP_CONFIG="/tmp/crypto_latency_config_dated_$$.json"
jq --arg mcm "$mcm_machines_file" \
   --arg int6 "$intermediate_file_6col" \
   --arg fin8 "$final_file_8col" \
   --arg tsv "$(dirname "$intermediate_file_6col")/crypto_latency_stats.$EXEC_DATE.tsv" \
   '.mcm_machines_file = $mcm | .intermediate_file_6col = $int6 | .final_file_8col = $fin8 | .stats_file = $tsv' \
   "$CONFIG_FILE" > "$TEMP_CONFIG"

python3 "$SCRIPT_DIR/crypto_latency_analyze.py" "$TEMP_CONFIG"
rm -f "$TEMP_CONFIG"
