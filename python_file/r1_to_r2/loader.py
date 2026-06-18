import argparse
import logging
from typing import Any

try:
    from python_file.r1_to_r2.sql_executor import execute_r1_to_r2_sql
except ModuleNotFoundError:
    from sql_executor import execute_r1_to_r2_sql


# ------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------
LOGGER = logging.getLogger(__name__)


# ------------------------------------------------------------
# Table to SQL file mapping
# ------------------------------------------------------------
TABLE_SQL_FILES = {
    "bags": "bags.sql",
    "customer_summary": "customer_summary.sql",
    "expired_voucher": "expired_voucher.sql",
    "group_details": "group_details.sql",
    "group_transaction": "group_transaction.sql",
    "group_users_details": "group_users_details.sql",
    "issued_voucher": "issued_voucher.sql",
    "member_transaction": "member_transaction.sql",
    "payment_mode": "payment_mode.sql",
    "payment_mode_details": "payment_mode_details.sql",
    "redeemed_voucher": "redeemed_voucher.sql",
    "user_entity_status": "user_entity_status.sql",
    "users": "users.sql",
    "voucher_event_type": "voucher_event_type.sql",
    "voucher_series": "voucher_series.sql",
    "zone_tills": "zone_tills.sql",
}


# ------------------------------------------------------------
# Table name helpers
# ------------------------------------------------------------
def normalize_table_name(table_name: str) -> str:
    return table_name.strip().lower().replace("-", "_")


def get_sql_file_name(table_name: str) -> str:
    normalized_table_name = normalize_table_name(table_name)
    sql_file_name = TABLE_SQL_FILES.get(normalized_table_name)

    if not sql_file_name:
        valid_table_names = ", ".join(sorted(TABLE_SQL_FILES))
        raise ValueError(
            f"Unsupported table_name: {table_name}. "
            f"Valid table_name values: {valid_table_names}"
        )

    return sql_file_name


# ------------------------------------------------------------
# Public execution function for Airflow
# ------------------------------------------------------------
def run_r1_to_r2_table(table_name: str) -> dict[str, Any]:
    sql_file_name = get_sql_file_name(table_name)
    LOGGER.info("Resolved table_name=%s to SQL file=%s", table_name, sql_file_name)
    return execute_r1_to_r2_sql(sql_file_name)


# ------------------------------------------------------------
# CLI argument parsing
# ------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one R1 to R2 BigQuery SQL file by table name."
    )
    parser.add_argument(
        "--table_name",
        required=True,
        help="Table name to load, for example: customer_summary or Customer_Summary.",
    )

    return parser.parse_args()


# ------------------------------------------------------------
# Direct execution entrypoint
# ------------------------------------------------------------
def main() -> None:
    args = parse_args()
    result = run_r1_to_r2_table(args.table_name)
    LOGGER.info("R1 to R2 result: %s", result)


if __name__ == "__main__":
    main()
