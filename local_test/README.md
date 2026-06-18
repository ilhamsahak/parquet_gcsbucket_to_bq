# Local Test Runner

Local orchestration script for testing the full daily flow:

```text
bucket_to_r1
then
r1_to_r2
```

## Script

```text
local_test/run_bucket_to_r1_then_r1_to_r2.py
```

## Run

From the project root:

```powershell
python local_test/run_bucket_to_r1_then_r1_to_r2.py
```

## Flow

```text
Run bucket_to_r1 for all tables
Continue to the next table if one table fails
Run r1_to_r2 for tables where bucket_to_r1 succeeded
Skip r1_to_r2 immediately if bucket_to_r1 failed for that same table
Continue to the next table if r1_to_r2 fails
Print phase summaries and final counts
```

## Flow Diagram

```mermaid
flowchart TD
    start["START<br/>Get list of 16 tables"]

    start --> p1_start

    subgraph phase1["PHASE 1: bucket_to_r1"]
        p1_start["Run bucket_to_r1 for all 16 tables"]
        p1_loop["For each table<br/>Run bucket_to_r1<br/>Continue even if one table fails"]
        p1_result["Record result<br/>SUCCESS or FAILED"]
        p1_done["All 16 tables processed for bucket_to_r1"]

        p1_start --> p1_loop --> p1_result --> p1_done
    end

    p1_done --> p2_start

    subgraph phase2["PHASE 2: r1_to_r2"]
        p2_start["Run r1_to_r2 based on Phase 1 results"]
        p2_check{"For each table<br/>bucket_to_r1 succeeded?"}
        p2_run["Run r1_to_r2<br/>Record SUCCESS or FAILED"]
        p2_skip["Skip r1_to_r2<br/>Reason: bucket_to_r1 failed"]
        p2_done["All 16 tables evaluated for r1_to_r2"]

        p2_start --> p2_check
        p2_check -->|Yes| p2_run --> p2_done
        p2_check -->|No| p2_skip --> p2_done
    end

    p2_done --> summary

    subgraph final_summary["FINAL SUMMARY"]
        summary["Show only after all processing is complete<br/>Bucket to R1 summary<br/>R1 to R2 summary<br/>Completed counts"]
    end

    summary --> done["Completed<br/>Success, Failed, Skipped"]
```

## Skip Rule

If `bucket_to_r1` fails for a table, the script does not run `r1_to_r2` for
that table.

Example:

```text
bucket_to_r1 customer_summary -> FAILED
r1_to_r2 customer_summary     -> SKIPPED
```

Other tables continue normally.

## Output

The script prints:

- Bucket to R1 summary
- R1 to R2 summary
- Final success, failed, and skipped counts

It also logs detailed exception messages for failed tables.

## Notes

- This script runs real loads and real SQL.
- Credentials and table configuration come from `.env`.
- Use this only when you want to test the full pipeline locally.
- For Airflow, use the individual loader functions instead of this local test
  script.
