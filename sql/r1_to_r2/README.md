# R1 to R2 SQL Loads

SQL scripts for loading data from `prod-raw-landing.ds_crm_r1` into
`prod-raw-landing.ds_crm_r2`.

## Flow

Each SQL file handles one table.

The SQL files are designed to be called by Python or Airflow as BigQuery
multi-statement queries.

```text
Read SQL file
Execute SQL in BigQuery
Wait for query_job.result()
Fail the task if BigQuery returns an error
```

## Python Callers

Use the shared Python loader in `python_file/r1_to_r2`.

```powershell
python python_file/r1_to_r2/loader.py --table_name customer_summary
```

For Airflow, import the shared function:

```python
from python_file.r1_to_r2.loader import run_r1_to_r2_table

run_r1_to_r2_table("customer_summary")
```

The shared executor is:

```text
python_file/r1_to_r2/sql_executor.py
```

The executor logs:

- SQL file name
- Success or failure status
- BigQuery job ID when a query job is created
- BigQuery error reason, location, and message when available

On failure, the Python function raises the exception again so Airflow can mark
the task as failed.

## Table Naming

Source tables:

```text
prod-raw-landing.ds_crm_r1.<Table_Name>
```

Target tables:

```text
prod-raw-landing.ds_crm_r2.<Table_Name>
```

## Full Table Upload

Full table upload scripts use this pattern:

```sql
-- ------------------------------------------------------------
-- Full table upload
-- ------------------------------------------------------------

TRUNCATE TABLE `prod-raw-landing.ds_crm_r2.Table_Name`;

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Table_Name` (
    `COLUMN_1`,
    `COLUMN_2`
)
SELECT
    `COLUMN_1`,
    `COLUMN_2`
FROM `prod-raw-landing.ds_crm_r1.Table_Name`;
```

Full table upload tables:

- `Customer_Summary`
- `Group_Details`
- `Group_Users_Details`
- `Payment_Mode`
- `Payment_Mode_Details`
- `User_Entity_Status`
- `Users`
- `Voucher_Event_Type`
- `Voucher_Series`
- `Zone_Tills`

## Incremental Upload

Incremental scripts assume R1 contains the latest snapshot for the table.

The scripts delete matching R2 rows based on the matching snapshot key found in
R1, then insert the full current R1 snapshot into R2.

```sql
-- ------------------------------------------------------------
-- Incremental upload
-- ------------------------------------------------------------

DELETE FROM `prod-raw-landing.ds_crm_r2.Table_Name` AS a
WHERE EXISTS (
    SELECT 1
    FROM `prod-raw-landing.ds_crm_r1.Table_Name` AS b
    WHERE a.`MATCH_COLUMN` = b.`MATCH_COLUMN`
);

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Table_Name` (
    `COLUMN_1`,
    `COLUMN_2`
)
SELECT
    `COLUMN_1`,
    `COLUMN_2`
FROM `prod-raw-landing.ds_crm_r1.Table_Name`;
```

Incremental upload tables:

- `Bags`
- `Expired_Voucher`
- `Group_Transaction`
- `Issued_Voucher`
- `Member_Transaction`
- `Redeemed_Voucher`

## Column Rules

- Do not use `SELECT *`.
- List every target column explicitly in `INSERT INTO`.
- List every source column explicitly in `SELECT`.
- Keep the target column order and source column order aligned.
- Use backticks around table names and column names.

## Safety Notes

- Credentials must not be hardcoded in SQL or Python.
- R1 is expected to contain only the latest snapshot data for incremental tables.
- If R1 contains more than the expected snapshot, the incremental delete will
  affect every R2 row matching the keys present in R1.
- BigQuery errors should be surfaced by Python through `query_job.result()`.
