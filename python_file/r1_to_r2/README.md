# R1 to R2 Python Loader

Python entrypoint for running SQL files from `sql/r1_to_r2`.

## Folder Contents

```text
python_file/r1_to_r2/
+-- loader.py
+-- sql_executor.py
+-- README.md
```

## Command Line Usage

Run one table by passing `--table_name`.

```powershell
python python_file/r1_to_r2/loader.py --table_name customer_summary
```

When `LARK_WEBHOOK_URL` is configured in `.env`, this direct command sends one
Lark notification for only the selected table.

Other examples:

```powershell
python python_file/r1_to_r2/loader.py --table_name bags
python python_file/r1_to_r2/loader.py --table_name payment_mode
python python_file/r1_to_r2/loader.py --table_name redeemed_voucher
```

The loader also accepts uppercase and hyphenated names.

```powershell
python python_file/r1_to_r2/loader.py --table_name Customer_Summary
python python_file/r1_to_r2/loader.py --table_name customer-summary
```

## Airflow Usage

Import `run_r1_to_r2_table` from `loader.py`.

```python
from python_file.r1_to_r2.loader import run_r1_to_r2_table

run_r1_to_r2_table("customer_summary")
```

For Airflow 3.x, call the function from a task and pass the table name you want
to load. Calling the function directly does not send a Lark notification; the
notification is only sent by the command-line entrypoint.

## Execution Flow

```text
loader.py receives table_name
loader.py maps table_name to a SQL file
sql_executor.py reads the SQL file
sql_executor.py creates the BigQuery client
BigQuery executes the SQL
query_job.result() waits for success or failure
```

## Success Logging

On success, the loader logs:

- SQL file name
- BigQuery job ID
- Success status

The Python function also returns a dictionary:

```python
{
    "sql_file_name": "customer_summary.sql",
    "status": "SUCCESS",
    "job_id": "<bigquery-job-id>",
    "message": "SQL completed successfully.",
}
```

The command-line entrypoint also sends a single-table Lark notification after a
successful SQL run when `LARK_WEBHOOK_URL` is configured.

## Error Logging

On failure, the loader logs:

- SQL file name
- BigQuery job ID, if created
- BigQuery error reason
- BigQuery error location
- BigQuery error message

After logging the error, the exception is raised again so Airflow can mark the
task as failed.

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
- SQL files are read from `sql/r1_to_r2`.
- Do not hardcode credentials in Python or SQL files.
- Running the loader executes the SQL, including `DELETE`, `TRUNCATE`, and
  `INSERT` statements.
