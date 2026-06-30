# Bucket to R1 Python Loader

Python entrypoint for loading the latest parquet file from GCS into BigQuery R1
tables.

## Folder Contents

```text
python_file/bucket_to_r1/
+-- loader.py
+-- parquet_loader.py
+-- table_config.py
+-- gcs_latest_resolver.py
+-- README.md
```

## Command Line Usage

Run one table by passing `--table_name`.

```powershell
python python_file/bucket_to_r1/loader.py --table_name customer_summary
```

When `LARK_WEBHOOK_URL` is configured in `.env`, this direct command sends one
Lark notification for only the selected table.

Other examples:

```powershell
python python_file/bucket_to_r1/loader.py --table_name bags
python python_file/bucket_to_r1/loader.py --table_name payment_mode
python python_file/bucket_to_r1/loader.py --table_name redeemed_voucher
```

The loader also accepts uppercase and hyphenated names.

```powershell
python python_file/bucket_to_r1/loader.py --table_name Customer_Summary
python python_file/bucket_to_r1/loader.py --table_name customer-summary
```

## Airflow Usage

Import `run_bucket_to_r1_table` from `loader.py`.

```python
from python_file.bucket_to_r1.loader import run_bucket_to_r1_table

run_bucket_to_r1_table("customer_summary")
```

For Airflow 3.x, call the function from a task and pass the table name you want
to load. Calling the function directly does not send a Lark notification; the
notification is only sent by the command-line entrypoint.

## Execution Flow

```text
loader.py receives table_name
table_config.py maps table_name to .env variable names
parquet_loader.py resolves the latest matching GCS parquet file
parquet_loader.py loads parquet into a temporary staging table
parquet_loader.py validates rows and required fields
parquet_loader.py overwrites the target R1 table
parquet_loader.py drops the staging table
```

## Success Logging

On success, the loader logs:

- table name
- target table ID
- resolved GCS URI
- staging row count
- target row count after overwrite

The command-line entrypoint also sends a single-table Lark notification after a
successful load when `LARK_WEBHOOK_URL` is configured.

The Python function also returns a dictionary:

```python
{
    "table_name": "Customer_Summary",
    "target_table_id": "project.dataset.Customer_Summary",
    "status": "SUCCESS",
    "staging_row_count": 123,
    "message": "Parquet load completed successfully.",
}
```

## Error Logging

On failure, the loader logs the target table and exception details, then raises
the exception again so Airflow can mark the task as failed.

The command-line entrypoint sends a failed single-table Lark notification before
raising the exception again.

## Valid Table Names

```text
bags
customer_summary
expired_voucher
group_details
group_transaction
group_users_details
issued_voucher
member_transaction
payment_mode
payment_mode_details
redeemed_voucher
user_entity_status
users
voucher_event_type
voucher_series
zone_tills
```

## Notes

- Credentials are read from `.env`.
- `DESTINATION_PROJECT_ID` and `DATASET_ID` are read from `.env`.
- Table-specific `*_TABLE_ID` and `*_GCS_URI` values are read from `.env`.
- Do not hardcode credentials in Python files.
- `payment_mode` excludes files starting with `Payment_Mode_Details_`.
- `payment_mode_details` does not use that exclusion, so it can load
  `Payment_Mode_Details_*.parquet` files from its own wildcard path.
