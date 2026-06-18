import logging
import sys
from pathlib import Path
from typing import Any


# ------------------------------------------------------------
# Project import bootstrap
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from python_file.bucket_to_r1.loader import run_bucket_to_r1_table
from python_file.bucket_to_r1.table_config import TABLE_LOAD_CONFIGS
from python_file.r1_to_r2.loader import run_r1_to_r2_table


# ------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

LOGGER = logging.getLogger(__name__)


# ------------------------------------------------------------
# Table run configuration
# ------------------------------------------------------------
TABLE_NAMES = list(TABLE_LOAD_CONFIGS.keys())


# ------------------------------------------------------------
# Result helpers
# ------------------------------------------------------------
def format_error_message(error: Exception) -> str:
    error_message = str(error).strip()

    if not error_message:
        return error.__class__.__name__

    return error_message


def build_result(
    table_name: str,
    phase: str,
    status: str,
    message: str = "",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "table_name": table_name,
        "phase": phase,
        "status": status,
        "message": message,
        "details": details or {},
    }


def print_phase_summary(
    title: str,
    phase_results: list[dict[str, Any]],
) -> None:
    table_name_width = max(len(result["table_name"]) for result in phase_results)
    status_width = max(len(result["status"]) for result in phase_results)

    print()
    print(title)
    print("-" * len(title))

    for result in phase_results:
        summary_line = (
            f"{result['table_name']:<{table_name_width}} | "
            f"{result['status']:<{status_width}}"
        )

        if result["message"]:
            summary_line = f"{summary_line} | {result['message']}"

        print(summary_line)


def print_final_summary(
    bucket_to_r1_results: list[dict[str, Any]],
    r1_to_r2_results: list[dict[str, Any]],
) -> None:
    all_results = bucket_to_r1_results + r1_to_r2_results
    success_count = sum(result["status"] == "SUCCESS" for result in all_results)
    failed_count = sum(result["status"] == "FAILED" for result in all_results)
    skipped_count = sum(result["status"] == "SKIPPED" for result in all_results)

    print_phase_summary("Bucket to R1 summary", bucket_to_r1_results)
    print_phase_summary("R1 to R2 summary", r1_to_r2_results)

    print()
    print(
        "Completed. "
        f"Success={success_count}, Failed={failed_count}, Skipped={skipped_count}"
    )


# ------------------------------------------------------------
# Bucket to R1 phase
# ------------------------------------------------------------
def run_bucket_to_r1_phase() -> list[dict[str, Any]]:
    phase_results: list[dict[str, Any]] = []

    for table_name in TABLE_NAMES:
        LOGGER.info("Starting bucket to R1 for table: %s", table_name)

        try:
            result_details = run_bucket_to_r1_table(table_name)
            phase_results.append(
                build_result(
                    table_name=table_name,
                    phase="bucket_to_r1",
                    status="SUCCESS",
                    details=result_details,
                )
            )
            LOGGER.info("Bucket to R1 completed for table: %s", table_name)
        except Exception as error:
            formatted_error_message = format_error_message(error)
            phase_results.append(
                build_result(
                    table_name=table_name,
                    phase="bucket_to_r1",
                    status="FAILED",
                    message=formatted_error_message,
                )
            )
            LOGGER.exception("Bucket to R1 failed for table: %s", table_name)

    return phase_results


# ------------------------------------------------------------
# R1 to R2 phase
# ------------------------------------------------------------
def run_r1_to_r2_phase(
    bucket_to_r1_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    phase_results: list[dict[str, Any]] = []
    bucket_success_by_table = {
        result["table_name"]: result["status"] == "SUCCESS"
        for result in bucket_to_r1_results
    }

    for table_name in TABLE_NAMES:
        if not bucket_success_by_table.get(table_name, False):
            skip_message = "Skipped because bucket to R1 failed for this table."
            phase_results.append(
                build_result(
                    table_name=table_name,
                    phase="r1_to_r2",
                    status="SKIPPED",
                    message=skip_message,
                )
            )
            LOGGER.warning("R1 to R2 skipped for table: %s", table_name)
            continue

        LOGGER.info("Starting R1 to R2 for table: %s", table_name)

        try:
            result_details = run_r1_to_r2_table(table_name)
            phase_results.append(
                build_result(
                    table_name=table_name,
                    phase="r1_to_r2",
                    status="SUCCESS",
                    details=result_details,
                )
            )
            LOGGER.info("R1 to R2 completed for table: %s", table_name)
        except Exception as error:
            formatted_error_message = format_error_message(error)
            phase_results.append(
                build_result(
                    table_name=table_name,
                    phase="r1_to_r2",
                    status="FAILED",
                    message=formatted_error_message,
                )
            )
            LOGGER.exception("R1 to R2 failed for table: %s", table_name)

    return phase_results


# ------------------------------------------------------------
# Main orchestration logic
# ------------------------------------------------------------
def run_local_test() -> None:
    LOGGER.info("Starting local bucket to R1 and R1 to R2 test.")

    bucket_to_r1_results = run_bucket_to_r1_phase()
    r1_to_r2_results = run_r1_to_r2_phase(bucket_to_r1_results)

    print_final_summary(
        bucket_to_r1_results=bucket_to_r1_results,
        r1_to_r2_results=r1_to_r2_results,
    )
    LOGGER.info("Finished local bucket to R1 and R1 to R2 test.")


# ------------------------------------------------------------
# Direct execution entrypoint
# ------------------------------------------------------------
if __name__ == "__main__":
    run_local_test()
