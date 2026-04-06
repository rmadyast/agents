#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/crypto_latency_config.json"

# Read parameters from config file
date_directories=$(jq -r '.date_directories' "$CONFIG_FILE")
base_path=$(jq -r '.base_path' "$CONFIG_FILE")
remote_host=$(jq -r '.remote_host' "$CONFIG_FILE")
mcm_machines_file=$(jq -r '.mcm_machines_file' "$CONFIG_FILE")
intermediate_file_6col=$(eval echo "$(jq -r '.intermediate_file_6col' "$CONFIG_FILE")")

# Create output directory
OUTPUT_DIR=$(dirname "$intermediate_file_6col")
mkdir -p "$OUTPUT_DIR"

TARGET_DATES="$date_directories"
OUTPUT_FILE="$intermediate_file_6col"

# Write header
echo "test_country,competitor,ghostip,cryptoip,ssltime,keysign_lat" > "$OUTPUT_FILE"

# Execute processing logic on remote host via SSH
echo "Step 1: Identifying parent directories with 'amd' on $remote_host"

# Write the remote processing script to a temp file with variables interpolated
REMOTE_SCRIPT="/tmp/crypto_latency_remote_$$.sh"
cat > "$REMOTE_SCRIPT" << SCRIPTEOF
#!/bin/bash
BASE_PATH="$base_path"
TARGET_DATES="$TARGET_DATES"

# Find all parent directories with 'amd' that have any target date - limit to 5 for testing
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

# Copy script to remote host and execute, capturing stdout to local file
REMOTE_PATH="/tmp/crypto_latency_remote_$$.sh"
scp -q "$REMOTE_SCRIPT" "$remote_host:$REMOTE_PATH"
ssh "$remote_host" "bash $REMOTE_PATH" >> "$OUTPUT_FILE" 2>/tmp/crypto_latency_debug.log

# Clean up
ssh "$remote_host" "rm -f $REMOTE_PATH" 2>/dev/null
rm -f "$REMOTE_SCRIPT"

echo ""
echo "Step 2: Output written to $OUTPUT_FILE"
final_count=$(tail -n +2 "$OUTPUT_FILE" | wc -l)
echo "Total number of rows in intermediate 6-column table: $final_count"

# Steps 7 & 8: Enrich with metro info and run analysis
echo ""
python3 "$SCRIPT_DIR/crypto_latency_analyze.py" "$CONFIG_FILE"
