# Bucket to BigQuery

Python loaders for moving Parquet files from GCS into BigQuery R1 tables, then
running SQL from R1 into R2 tables.

## Requirements
- Python 3.10 or above
- Google Cloud service account credentials stored outside the codebase and referenced from `.env`
- Access to:
  - Google Cloud Storage bucket that contains the Parquet files
  - BigQuery dataset and target tables
- Python packages:
  - `google-cloud-bigquery`
  - `google-cloud-storage`
  - `python-dotenv`
- Airflow 3.x to the loaders from DAGs

## The workflow
- Reads Parquet data from GCS
- Loads it into a temporary staging table in BigQuery
- Matches source and target columns automatically using case-insensitive column mapping
- Keeps the existing target table schema
- Overwrites the target table only after validation passes

## Setup
Copy `.env.example` to `.env`, then update the values for your environment.

Use `service_account/service-account.example.json` as the reference structure for your own service account key file.

Install the required packages:

```powershell
pip install google-cloud-bigquery google-cloud-storage python-dotenv
```

Shared variables:
- `GOOGLE_APPLICATION_CREDENTIALS`
- `DESTINATION_PROJECT_ID`
- `DATASET_ID`

Table-specific variables depend on the table name.

Examples:
- `users` uses `USERS_TABLE_ID` and `USERS_GCS_URI`
- `bags` uses `BAGS_TABLE_ID` and `BAGS_GCS_URI`

## Public publishing
- Keep the real `.env` file private.
- Keep real service account JSON files inside `service_account/`.
- Commit only `.env.example` and `service_account/service-account.example.json`.
- Review the values in `README.md` and SQL files before making the repository public.

## Run all tables
From the project root, run the full bucket to R1 and R1 to R2 pipeline for every configured table:

```bash
# ------------------------------------------------------------
# Move into the project directory
# ------------------------------------------------------------
cd /opt/itsd/crm-bucket_r2/bucket_bq

# ------------------------------------------------------------
# Run all bucket to R1 and R1 to R2 tables
# ------------------------------------------------------------
./venv/bin/python run_all_table/run_bucket_r1_r2_all.py >> /opt/itsd/logs/crm-bucket_r2.log 2>&1
```

## Run a specific table
From the project root, run the bucket to R1 loader first, then run the R1 to R2 SQL loader for the same table.

Example for `customer_summary`:

```bash
# ------------------------------------------------------------
# Move into the project directory
# ------------------------------------------------------------
cd /opt/itsd/crm-bucket_r2/bucket_bq

# ------------------------------------------------------------
# Run bucket to R1, then R1 to R2 for one table
# ------------------------------------------------------------
./venv/bin/python python_file/bucket_to_r1/loader.py --table_name customer_summary >> /opt/itsd/logs/crm-bucket_r2.log 2>&1 && \
./venv/bin/python python_file/r1_to_r2/loader.py --table_name customer_summary >> /opt/itsd/logs/crm-bucket_r2.log 2>&1
```

## Airflow
Import the loader function and call it from a DAG.

```python
from python_file.bucket_to_r1.loader import run_bucket_to_r1_table

run_bucket_to_r1_table("users")
```

## Loader flow
The shared loader inside `python_file/bucket_to_r1/` follows this flow:

1. Read shared and table-specific values from `.env`
2. Create a BigQuery client
3. Build the target table id and a temporary staging table id
4. Resolve wildcard GCS URIs to the latest matching Parquet file
5. Load the latest Parquet file from GCS into the staging table
6. Read the target schema from the existing BigQuery table
7. Read the staging schema from the loaded Parquet data
8. Build a case-insensitive lookup for source columns
9. Validate that the staging table contains rows
10. Validate required target columns exist in the source
11. Validate required target values are not null after casting
12. Build a `SELECT` using the exact target schema from BigQuery
13. Overwrite the target table from the staging `SELECT`, 
14. Drop the staging table in `finally`

## Safety controls
- The loaders do not hardcode credentials. Credentials come from `.env`.
- Wildcard GCS URIs are resolved to one latest matching file before BigQuery loads data.
- The final schema follows the existing BigQuery target table schema.
- Source-to-target column matching is case-insensitive.
- Extra source columns are ignored.
- Missing required target columns fail the job.
- Invalid or null values in required target columns fail the job.
- Nullable target columns can safely become `NULL`. (just incase null column created later)
- Empty staging loads fail before the target table is overwritten.
- The target table is overwritten using a destination query job instead of `TRUNCATE TABLE` plus `INSERT`.
- Temporary staging tables are always cleaned up after the run.

## Latest file selection
For source values like `gs://your-bucket/path/Bags_*.parquet`, the loaders list
matching GCS objects and load only the latest object.

Files with names like `Bags_YYYYMMDD_HHMMSS.parquet` are sorted by the timestamp
in the filename. If no filename timestamp exists, the loader falls back to the
GCS object updated time.

## Available bucket to R1 table names
- `bags`
- `customer_summary`
- `expired_voucher`
- `group_details`
- `group_transaction`
- `group_users_details`
- `issued_voucher`
- `member_transaction`
- `payment_mode`
- `payment_mode_details`
- `redeemed_voucher`
- `user_entity_status`
- `users`
- `voucher_event_type`
- `voucher_series`
- `zone_tills`

## Notes
- Target BigQuery tables must already exist.
- The scripts do not create or change the target schema.
- Missing or invalid required values stop the loader before the target table is overwritten.
