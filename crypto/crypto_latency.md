# Crypto Latency Analysis Agent

## High-Level Goal

Analyze SSL time latencies across countries to determine:
1. Which countries experience excessive SSL times (10ms+, 20ms+)
2. Whether high SSL times are caused by keysign latencies or ghost-side delays
3. Whether ghost and cryptoserver machines are in different metros (potential root cause)

## Data Source and Directory Structure

**Host:** envy.akamai.com
**Base Path:** `/datastore1/svc_epremo/fill_log`

### Directory Hierarchy

1. **Parent Directories:** Directories containing the string 'amd' in their name
   - Example: `google-jp-26-amd-static-xlarge`
   - Contains: Date subdirectories

2. **Date Subdirectories:** Named as YYYYMMDD format
   - Example: `20260403`
   - Contains: Gzipped log files

3. **Target Specification:** Specific date subdirectories are specified in a config file

## Processing Workflow

### Step 1: Identify Parent Directories

Search `/datastore1/svc_epremo/fill_log` for all directories containing the string 'amd'. These are the parent directories to process.

### Step 2: Locate Target Date Subdirectories

Within each parent directory, identify date subdirectories (YYYYMMDD format) that match the config specification. These are the directories whose gzipped files will be processed.

### Step 3: Extract 6 Columns from Gzipped Files

For each gzipped file in the target date subdirectories across all parent directories:

#### Column Definitions

1. **test_country** (Column 1): 2-letter country code
   - Extracted from parent directory name
   - The second string in the '-' separated parent directory name
   - Example: From `google-jp-26-amd-static-xlarge` → extract `jp`

2. **competitor** (Column 2): The first string in the '-' separated parent directory name
   - Example: From `google-jp-26-amd-static-xlarge` → extract `google`

3. **ghostip** (Column 3): Value from the first field in the gzip file

4. **cryptoip** (Column 4): Extracted from the gzip file
   - Located between the string `cs=` and the next `|` character

5. **ssltime** (Column 5): SSL time value from the gzip file
   - Must be numeric and > 0
   - Lines where this condition is not met should be filtered out

6. **keysign_lat** (Column 6): If second field is 'r', then the 77th field from the gzip file; if the second field is 'S', then the 61st field from the gzip file.

#### Filtering Rules

- Only process lines where column 5 (ssltime) is:
  - A valid number (numeric)
  - Greater than 0

### Step 4: Aggregate by Date Subdirectory

For each date subdirectory, concatenate all 6-column data from every gzipped file in that directory (within that parent directory context) into a single file.

Result: One 6-column file per date subdirectory per parent directory.

### Step 5: Global Concatenation

Concatenate all 6-column files across all parent directories identified in Step 1.

### Step 6: Add Header

Add column headers to the concatenated output:
```
test_country,competitor,ghostip,cryptoip,ssltime,keysign_lat
```

### Step 7: Enrich with Metro Information

If query2 is available:
Use query2 to add metro information from the `mcm_machines` table:
- **ghost_metro**: The regionname associated with the ghostip (from 'freeflow' network)
- **crypto_metro**: The regionname associated with the cryptoip (from 'crypto' network)

Result columns (8 total):
```
test_country,competitor,ghostip,cryptoip,ssltime,keysign_lat,ghost_metro,crypto_metro
```
If query2 is not-available (Default):
Search for a file that is called mcm_machines_file in the config file. That csv file will have columns that contain ip, region, regionname, network (and maybe others that are not relevant here). We need to join that file with the previously obtained data file twice, once for the ghostip column and once for the cryptoip column. Both the joins are going to be on the column in the mcm_machines_file that is labeled 'ip'. You may need to use the 'network' column to distinguish between the two joins - if so, use network=freeflow for the ghostip column and network=crypto for the cryptoip column. Each time you are going to extract the 3-letter string that contains the metro name from the column regionname. This will be the first 3 characters after the '-' in the regionname string. Create 2 new columns - ghost_metro and crypto_metro.

## Analysis and Statistics

For each test_country, calculate the following metrics:

### Latency Thresholds
- Percent of ssltime > 20ms
- Percent of ssltime > 30ms
- Percent of ssltime > 50ms
- Percent of keysign latencies > 10ms
- Percent of keysign latencies > 20ms
- Percent of keysign latencies > 30ms

### Metro Distribution
- Percent of cases where ghostip and cryptoip are in different metros

### Combined Conditions
- Percent of cases where ssltime > 20ms AND keysign < 10ms
- Percent of cases where ssltime > 30ms AND keysign < 10ms
- Percent of cases where ssltime > 50ms AND keysign < 10ms
- Percent of cases where ssltime > 50ms AND keysign < 20ms

## Output

Summary statistics table by test_country with the 10 metrics above, used to:
1. Identify countries with SSL time issues
2. Correlate with keysign latencies
3. Identify metro mismatch patterns as a contributing factor
