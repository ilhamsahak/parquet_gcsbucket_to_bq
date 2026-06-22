# SQL Directory

This directory keeps SQL scripts separate from the Python orchestration code.

The separation is intentional because it allows SQL logic changes to be handled
separately from loader logic changes.

Each subfolder should group SQL by pipeline stage.

```text
sql/
`-- r1_to_r2/
    `-- One SQL file per R1 to R2 table load
```

Keep table-specific logic in its own SQL file where possible. 
This makes future logic changes easier to review, test, and deploy one table at a time.
