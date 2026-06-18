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
    start([START<br/>Get list of 16 tables])

    start --> phase1

    subgraph phase1[PHASE 1: bucket_to_r1]
        p1_start[Run bucket_to_r1 for all 16 tables]
        p1_each[Process each table<br/>1 to 16]
        p1_run[Run bucket_to_r1]
        p1_success{bucket_to_r1<br/>success?}
        p1_record_success[Record SUCCESS]
        p1_record_failed[Record FAILED<br/>and error]
        p1_done[All 16 tables processed<br/>for bucket_to_r1]

        p1_start --> p1_each --> p1_run --> p1_success
        p1_success -->|Yes| p1_record_success --> p1_each
        p1_success -->|No| p1_record_failed --> p1_each
        p1_each --> p1_done
    end

    phase1 --> phase2

    subgraph phase2[PHASE 2: r1_to_r2]
        p2_start[Run r1_to_r2 based on Phase 1 results]
        p2_each[Process each table<br/>1 to 16]
        p2_check{bucket_to_r1<br/>result for table}
        p2_run[Run r1_to_r2]
        p2_success{r1_to_r2<br/>success?}
        p2_record_success[Record SUCCESS]
        p2_record_failed[Record FAILED<br/>and error]
        p2_skip[Skip r1_to_r2<br/>Reason: bucket_to_r1 failed]
        p2_record_skipped[Record SKIPPED]
        p2_done[All 16 tables evaluated<br/>for r1_to_r2]

        p2_start --> p2_each --> p2_check
        p2_check -->|bucket_to_r1 SUCCESS| p2_run --> p2_success
        p2_success -->|Yes| p2_record_success --> p2_each
        p2_success -->|No| p2_record_failed --> p2_each
        p2_check -->|bucket_to_r1 FAILED| p2_skip --> p2_record_skipped --> p2_each
        p2_each --> p2_done
    end

    phase2 --> summary

    subgraph summary[FINAL SUMMARY]
        s1[Bucket to R1 summary<br/>bags | SUCCESS<br/>customer_summary | FAILED | error message<br/>expired_voucher | SUCCESS]
        s2[R1 to R2 summary<br/>bags | SUCCESS<br/>customer_summary | SKIPPED | bucket_to_r1 failed<br/>expired_voucher | SUCCESS]
        s3[Completed. Success=4, Failed=1, Skipped=1]

        s1 --> s3
        s2 --> s3
    end
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
