import argparse
import logging
from typing import Any

try:
    from python_file.bucket_to_r1.parquet_loader import load_bucket_to_r1_table
    from python_file.bucket_to_r1.table_config import get_table_load_config
except ModuleNotFoundError:
    from parquet_loader import load_bucket_to_r1_table
    from table_config import get_table_load_config


# ------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------
LOGGER = logging.getLogger(__name__)


# ------------------------------------------------------------
# Public execution function for Airflow
# ------------------------------------------------------------
def run_bucket_to_r1_table(table_name: str) -> dict[str, Any]:
    table_config = get_table_load_config(table_name)
    LOGGER.info("Resolved table_name=%s to target table=%s", table_name, table_config.table_name)
    return load_bucket_to_r1_table(table_config)


# ------------------------------------------------------------
# CLI argument parsing
# ------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load one latest bucket parquet file into a BigQuery R1 table."
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
    result = run_bucket_to_r1_table(args.table_name)
    LOGGER.info("Bucket to R1 result: %s", result)


if __name__ == "__main__":
    main()
