# Bucket to BigQuery

Python scripts for loading Parquet files from GCS into BigQuery tables.

## Requirements
- Python 3.10 or above
- Google Cloud service account credentials stored outside the codebase and referenced from `.env`
- Access to:
  - Google Cloud Storage bucket that contains the Parquet files
  - BigQuery dataset and target tables
- Python packages:
  - `google-cloud-bigquery`
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
pip install google-cloud-bigquery python-dotenv
```

Shared variables:
- `GOOGLE_APPLICATION_CREDENTIALS`
- `DESTINATION_PROJECT_ID`
- `DATASET_ID`

Table-specific variables depend on the script.

Examples:
- `python_file/bucket_to_bq_users.py` uses `USERS_TABLE_ID` and `USERS_GCS_URI`
- `python_file/bucket_to_bq_bags.py` uses `BAGS_TABLE_ID` and `BAGS_GCS_URI`

## Public publishing
- Keep the real `.env` file private.
- Keep real service account JSON files inside `service_account/`.
- Commit only `.env.example` and `service_account/service-account.example.json`.
- Review the values in `README.md` and SQL files before making the repository public.

## Run a loader
From the project root:

```powershell
python python_file/bucket_to_bq_users.py
```

## Airflow
Import the loader function and call it from a DAG.

```python
from python_file.bucket_to_bq_users import load_users
```

## Loader flow
Each file inside `python_file/` follows the same flow:

1. Read shared and table-specific values from `.env`
2. Create a BigQuery client
3. Build the target table id and a temporary staging table id
4. Load the Parquet file from GCS into the staging table
5. Read the target schema from the existing BigQuery table
6. Read the staging schema from the loaded Parquet data
7. Build a case-insensitive lookup for source columns
8. Validate that the staging table contains rows
9. Validate required target columns exist in the source
10. Validate required target values are not null after casting
11. Build a `SELECT` using the exact target schema from BigQuery
12. Overwrite the target table from the staging `SELECT`, 
13. Drop the staging table in `finally`

## Safety controls
- The loaders do not hardcode credentials. Credentials come from `.env`.
- The final schema follows the existing BigQuery target table schema.
- Source-to-target column matching is case-insensitive.
- Extra source columns are ignored.
- Missing required target columns fail the job.
- Invalid or null values in required target columns fail the job.
- Nullable target columns can safely become `NULL`. (just incase null column created later)
- Empty staging loads fail before the target table is overwritten.
- The target table is overwritten using a destination query job instead of `TRUNCATE TABLE` plus `INSERT`.
- Temporary staging tables are always cleaned up after the run.

## Available scripts (total of 16)
- `bucket_to_bq_bags.py`
- `bucket_to_bq_customer_summary.py`
- `bucket_to_bq_expired_voucher.py`
- `bucket_to_bq_group_details.py`
- `bucket_to_bq_group_transaction.py`
- `bucket_to_bq_group_users_details.py`
- `bucket_to_bq_issued_voucher.py`
- `bucket_to_bq_member_transaction.py`
- `bucket_to_bq_payment_mode.py`
- `bucket_to_bq_payment_mode_details.py`
- `bucket_to_bq_redeemed_voucher.py`
- `bucket_to_bq_user_entity_status.py`
- `bucket_to_bq_users.py`
- `bucket_to_bq_voucher_event_type.py`
- `bucket_to_bq_voucher_series.py`
- `bucket_to_bq_zone_tills.py`

## Notes
- Target BigQuery tables must already exist.
- The scripts do not create or change the target schema.
- Missing or invalid required values stop the loader before the target table is overwritten.
