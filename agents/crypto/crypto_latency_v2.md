# Crypto Latency Analysis Agent v2

## High-Level Goal

Analyze SSL time latencies across countries to determine:
1. Which countries experience excessive SSL times (20ms+, 30ms+, 50ms+)
2. Whether high SSL times are caused by keysign latencies or ghost-side delays
3. Whether ghost and cryptoserver machines are in different metros (potential root cause)

## What's New in v2

v2 eliminates the dependency on a pre-existing `mcm_machines` CSV file. Instead, it generates the MCM machines file automatically at runtime by issuing SQL queries against the Query2 database via `sql2` on a designated VM. This makes the agent self-contained and always uses current MCM data.

## Config File

**File:** `crypto_latency_config_v2.json`

| Key | Description |
|-----|-------------|
| `date_directories` | Comma-separated list of date subdirectories in YYYYMMDD format |
| `base_path` | Base path on the remote log host |
| `remote_host` | Host where log files reside (SSH) |
| `query2_vm` | VM where `sql2` is available (SSH) |
| `query2_host` | Query2 aggregator hostname passed to `sql2 --host` |
| `mcm_machines_file` | Local path where the generated MCM CSV will be saved |
| `intermediate_file_6col` | Local path for the 6-column extracted data CSV |
| `final_file_8col` | Local path for the 8-column enriched data CSV |

## Data Source and Directory Structure

**Log host:** `envy.akamai.com`
**Base path:** `/datastore1/svc_epremo/fill_log`
**Query2 VM:** `bos-lvu2g.bos01.corp.akamai.com`
**Query2 aggregator:** `freeflow.dev.query.akadns.net`

### Log Directory Hierarchy

1. **Parent Directories:** Directories containing the string `amd` in their name
   - Example: `google-jp-26-amd-static-xlarge`
   - `competitor` = first `-`-separated token → `google`
   - `test_country` = second `-`-separated token → `jp`

2. **Date Subdirectories:** Named as `YYYYMMDD`
   - Contain gzipped log files

3. **Target Specification:** The set of date subdirectories to process is specified in the config file.

## Processing Workflow

### Step 0: Generate MCM Machines File via Query2

SSH to `query2_vm` and run two `sql2` queries against `query2_host` to build the MCM machines CSV. The queries use the **implicit join** syntax (no `JOIN` keyword) required by Query2.

#### Query 1 — Freeflow IPs (ghostip mapping)

Join `mcm_machines` with `machinesvc` to obtain the service-facing IP (`serviceip`) for each machine, filtered to `service='ghost'` and `network='freeflow'`.

```sql
SELECT m.ip AS machineip, s.serviceip AS serviceip,
       m.regionname AS regionname, m.network AS network
FROM mcm_machines m, machinesvc s
WHERE m.ip = s.machineip
  AND s.service = 'ghost'
  AND m.network = 'freeflow'
```

- `machineip` and `serviceip` are **different** in freeflow: the log records the `serviceip` as the ghost-facing IP.
- The header and Query2 type row (`ip?,ip?,string?,string?`) are included; strip the type row (line 2) with `awk 'NR!=2'`.

#### Query 2 — Crypto IPs (cryptoip mapping)

Query `mcm_machines` directly for `network='crypto'`. The `ip` column serves as both `machineip` and `serviceip`.

```sql
SELECT ip AS machineip, ip AS serviceip, regionname, network
FROM mcm_machines
WHERE network = 'crypto'
```

- Strip both the header and type row (`awk 'NR>2'`) and append directly after the freeflow data.

#### Output Schema

```
machineip,serviceip,regionname,network
```

The resulting CSV is written to `mcm_machines_file` on the local machine via `scp`. The `crypto_latency_analyze.py` script reads this file and uses:
- `serviceip` to look up `ghost_metro` (freeflow rows)
- `machineip` to look up `crypto_metro` (crypto rows)

### Step 1: Identify Parent Directories

On `remote_host`, find all directories under `base_path` whose name contains `amd` and that contain the first target date subdirectory.

### Step 2: Extract 6 Columns from Gzipped Files

For each gzipped log file across all matching parent directories and target dates, extract the following columns using AWK (space-separated log format):

#### Column Definitions

| Column | Name | Source |
|--------|------|--------|
| 1 | `test_country` | Second `-`-separated token of the parent directory name |
| 2 | `competitor` | First `-`-separated token of the parent directory name |
| 3 | `ghostip` | Field 1 of the log line |
| 4 | `cryptoip` | Extracted via regex `cs=<IP>` from the log line |
| 5 | `ssltime` | Field 4 of the log line (must be numeric and > 0) |
| 6 | `keysign_lat` | Field 77 if field 2 = `r`; field 61 if field 2 = `S`; empty otherwise |

#### AWK Logic

```awk
NF >= 61 {
    ghostip = $1
    ssltime = $4
    if ($2 == "r" && NF >= 77) keysign_lat = $77
    else if ($2 == "S")        keysign_lat = $61
    else                       keysign_lat = ""
    if (ssltime+0 > 0) {
        if (match($0, /cs=[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/)) {
            cryptoip = substr($0, RSTART+3, RLENGTH-3)
            print country "," competitor "," ghostip "," cryptoip "," ssltime "," keysign_lat
        }
    }
}
```

#### Filtering Rules

- Only emit lines where `ssltime` is numeric and > 0
- Only emit lines where a `cs=<IP>` pattern is found (i.e., a valid `cryptoip`)
- Lines with fewer than 61 fields are skipped entirely

### Step 3: Global Concatenation with Header

All extracted rows from all parent directories and all date subdirectories are concatenated into a single CSV:

```
test_country,competitor,ghostip,cryptoip,ssltime,keysign_lat
```

Written to `intermediate_file_6col`.

### Step 4: Enrich with Metro Information

Run `crypto_latency_analyze.py` which reads the generated `mcm_machines_file` and adds two columns:

- **`ghost_metro`**: 3-letter metro from `regionname` (first 3 chars after `-`) matched on `serviceip` in freeflow rows
- **`crypto_metro`**: 3-letter metro matched on `machineip` in crypto rows

Metro extraction: `SEED-TPE` → `TPE`

Result written to `final_file_8col`:

```
test_country,competitor,ghostip,cryptoip,ssltime,keysign_lat,ghost_metro,crypto_metro
```

### Step 5: Analysis and Statistics

For each `test_country`, compute the following metrics:

#### Latency Thresholds
- Percent of `ssltime` > 20ms
- Percent of `ssltime` > 30ms
- Percent of `ssltime` > 50ms
- Percent of `keysign_lat` > 10ms
- Percent of `keysign_lat` > 20ms
- Percent of `keysign_lat` > 30ms

> Note: Empty `keysign_lat` values are treated as 0ms.

#### Metro Distribution
- Percent of cases where `ghost_metro` ≠ `crypto_metro` (both non-empty)

#### Combined Conditions
- Percent of cases where `ssltime` > 20ms AND `keysign_lat` < 10ms
- Percent of cases where `ssltime` > 30ms AND `keysign_lat` < 10ms
- Percent of cases where `ssltime` > 50ms AND `keysign_lat` < 10ms
- Percent of cases where `ssltime` > 50ms AND `keysign_lat` < 20ms

## Output Files

| File | Description |
|------|-------------|
| `mcm_machines_generated.csv` | Generated MCM machines data from Query2 |
| `crypto_latency_all.csv` | 6-column intermediate extracted data |
| `crypto_latency_enriched.csv` | 8-column enriched data with metro columns |
| `crypto_latency_stats.tsv` | Tab-separated statistics table by country |

All output files are written to the directory specified by `intermediate_file_6col` in the config (default: `~/product_metrics/competitive/crypto_latency_output/`).

## SSH Requirements

The agent requires SSH access (using your SSH certificate) to two hosts:
- **`envy.akamai.com`** — for log file processing
- **`bos-lvu2g.bos01.corp.akamai.com`** — for Query2 / sql2 access

Scripts are copied via `scp`, executed remotely, and cleaned up automatically.
