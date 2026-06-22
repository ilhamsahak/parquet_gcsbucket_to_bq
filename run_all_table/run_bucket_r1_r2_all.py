import json
import logging
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

from dotenv import load_dotenv


# ------------------------------------------------------------
# Project import bootstrap
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from python_file.bucket_to_r1.loader import run_bucket_to_r1_table
from python_file.bucket_to_r1.gcs_latest_resolver import resolve_latest_gcs_uri
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
LARK_WEBHOOK_TIMEOUT_SECONDS = 15
NO_ERROR_TEXT = "-"
UNRESOLVED_GCS_URI_TEXT = "Source GCS URI was not resolved before failure."
DUMMY_BUCKET_ERROR_TEXT = "Dummy error: bucket to R1 load failed."
DUMMY_R2_ERROR_TEXT = "Dummy error: R1 to R2 load failed."
DUMMY_SKIP_ERROR_TEXT = "Dummy error: skipped because bucket to R1 failed."


# ------------------------------------------------------------
# Datetime helpers
# ------------------------------------------------------------
def get_local_timezone() -> ZoneInfo | timezone:
    try:
        return ZoneInfo("Asia/Kuala_Lumpur")
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=8), name="MYT")


# ------------------------------------------------------------
# Lark summary configuration
# ------------------------------------------------------------
def get_lark_webhook_url() -> str:
    return os.getenv("LARK_WEBHOOK_URL", "").strip()


def resolve_source_gcs_uri_for_result(table_name: str) -> str:
    table_config = TABLE_LOAD_CONFIGS[table_name]
    gcs_uri = os.getenv(table_config.gcs_uri_env, "").strip()

    if not gcs_uri:
        return ""

    try:
        return resolve_latest_gcs_uri(
            gcs_uri=gcs_uri,
            project_root=PROJECT_ROOT,
            excluded_file_prefixes=table_config.excluded_file_prefixes,
        )
    except Exception:
        LOGGER.exception("Unable to resolve source GCS URI for table: %s", table_name)
        return ""


def get_status_label(status: str) -> str:
    status_labels = {
        "SUCCESS": "success",
        "FAILED": "fails",
        "SKIPPED": "skip",
    }

    return status_labels.get(status, status.lower())


def get_card_status_template(status_counts: dict[str, int]) -> str:
    if status_counts.get("FAILED", 0) > 0:
        return "red"

    if status_counts.get("SKIPPED", 0) > 0:
        return "yellow"

    return "green"


def get_card_title(status_counts: dict[str, int]) -> str:
    if status_counts.get("FAILED", 0) > 0:
        return "Capillary Bucket to R1 / R1 to R2 Pipeline Failed"

    if status_counts.get("SKIPPED", 0) > 0:
        return "Capillary Bucket to R1 / R1 to R2 Pipeline Completed with Skips"

    return "Capillary Bucket to R1 / R1 to R2 Pipeline Succeeded"


def get_result_by_table(
    phase_results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {result["table_name"]: result for result in phase_results}


def get_status_counts(
    bucket_to_r1_results: list[dict[str, Any]],
    r1_to_r2_results: list[dict[str, Any]],
) -> dict[str, int]:
    status_counts = {
        "SUCCESS": 0,
        "FAILED": 0,
        "SKIPPED": 0,
    }

    for result in bucket_to_r1_results + r1_to_r2_results:
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    return status_counts


def clean_table_value(value: str) -> str:
    return " ".join(value.split())


def get_bucket_source_gcs_uri(
    bucket_result: dict[str, Any],
) -> str:
    result_details = bucket_result.get("details", {})

    if isinstance(result_details, dict):
        source_gcs_uri = result_details.get("source_gcs_uri")

        if source_gcs_uri:
            return source_gcs_uri

    return UNRESOLVED_GCS_URI_TEXT


def get_result_error_reason(
    bucket_result: dict[str, Any],
    r1_result: dict[str, Any],
) -> str:
    bucket_status = bucket_result.get("status", "UNKNOWN")
    r1_status = r1_result.get("status", "UNKNOWN")

    if bucket_status == "FAILED":
        return clean_table_value(bucket_result.get("message") or DUMMY_BUCKET_ERROR_TEXT)

    if r1_status == "FAILED":
        return clean_table_value(r1_result.get("message") or DUMMY_R2_ERROR_TEXT)

    if r1_status == "SKIPPED":
        return clean_table_value(r1_result.get("message") or DUMMY_SKIP_ERROR_TEXT)

    return NO_ERROR_TEXT


def build_load_status_rows(
    bucket_to_r1_results: list[dict[str, Any]],
    r1_to_r2_results: list[dict[str, Any]],
    current_datetime: datetime,
) -> list[dict[str, str]]:
    bucket_results_by_table = get_result_by_table(bucket_to_r1_results)
    r1_results_by_table = get_result_by_table(r1_to_r2_results)
    table_rows: list[dict[str, str]] = []

    for table_name in TABLE_NAMES:
        table_config = TABLE_LOAD_CONFIGS[table_name]
        bucket_result = bucket_results_by_table.get(table_name, {})
        r1_result = r1_results_by_table.get(table_name, {})
        table_rows.append({
            "table_name": table_config.table_name,
            "gcs_uri": get_bucket_source_gcs_uri(
                bucket_result=bucket_result,
            ),
            "bucket_to_r1": get_status_label(bucket_result.get("status", "UNKNOWN")),
            "r1_to_r2": get_status_label(r1_result.get("status", "UNKNOWN")),
            "error_reason": get_result_error_reason(
                bucket_result=bucket_result,
                r1_result=r1_result,
            ),
        })

    return table_rows


def build_status_summary_rows(status_counts: dict[str, int]) -> list[dict[str, str]]:
    return [
        {"status": "success", "count": str(status_counts.get("SUCCESS", 0))},
        {"status": "fails", "count": str(status_counts.get("FAILED", 0))},
        {"status": "skip", "count": str(status_counts.get("SKIPPED", 0))},
    ]


def build_load_details_table(
    bucket_to_r1_results: list[dict[str, Any]],
    r1_to_r2_results: list[dict[str, Any]],
    current_datetime: datetime,
) -> dict[str, Any]:
    return {
        "tag": "table",
        "page_size": min(10, len(TABLE_NAMES)),
        "row_height": "low",
        "freeze_first_column": True,
        "header_style": {
            "text_align": "left",
            "text_size": "normal",
            "background_style": "grey",
            "text_color": "default",
            "bold": True,
            "lines": 1,
        },
        "columns": [
            {
                "name": "table_name",
                "display_name": "Table name",
                "data_type": "text",
                "width": "180px",
            },
            {
                "name": "gcs_uri",
                "display_name": "GCS URI",
                "data_type": "text",
                "width": "520px",
            },
            {
                "name": "bucket_to_r1",
                "display_name": "bucket > r1",
                "data_type": "text",
                "width": "120px",
            },
            {
                "name": "r1_to_r2",
                "display_name": "r1 > r2",
                "data_type": "text",
                "width": "100px",
            },
            {
                "name": "error_reason",
                "display_name": "Error reason",
                "data_type": "text",
                "width": "360px",
            },
        ],
        "rows": build_load_status_rows(
            bucket_to_r1_results=bucket_to_r1_results,
            r1_to_r2_results=r1_to_r2_results,
            current_datetime=current_datetime,
        ),
    }


def build_status_summary_table(status_counts: dict[str, int]) -> dict[str, Any]:
    return {
        "tag": "table",
        "page_size": 3,
        "row_height": "low",
        "freeze_first_column": False,
        "header_style": {
            "text_align": "left",
            "text_size": "normal",
            "background_style": "grey",
            "text_color": "default",
            "bold": True,
            "lines": 1,
        },
        "columns": [
            {
                "name": "status",
                "display_name": "Status",
                "data_type": "text",
                "width": "160px",
            },
            {
                "name": "count",
                "display_name": "Count",
                "data_type": "text",
                "width": "100px",
                "horizontal_align": "right",
            },
        ],
        "rows": build_status_summary_rows(status_counts),
    }


def build_lark_summary_card(
    bucket_to_r1_results: list[dict[str, Any]],
    r1_to_r2_results: list[dict[str, Any]],
) -> dict[str, Any]:
    current_datetime = datetime.now(get_local_timezone())
    status_counts = get_status_counts(
        bucket_to_r1_results=bucket_to_r1_results,
        r1_to_r2_results=r1_to_r2_results,
    )
    load_details_table = build_load_details_table(
        bucket_to_r1_results=bucket_to_r1_results,
        r1_to_r2_results=r1_to_r2_results,
        current_datetime=current_datetime,
    )
    status_summary_table = build_status_summary_table(status_counts)

    return {
        "schema": "2.0",
        "config": {
            "width_mode": "fill",
            "summary": {
                "content": get_card_title(status_counts),
            },
        },
        "header": {
            "template": get_card_status_template(status_counts),
            "title": {
                "tag": "plain_text",
                "content": get_card_title(status_counts),
            },
        },
        "body": {
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**Date:** {current_datetime:%Y-%m-%d}\n"
                            f"**Time:** {current_datetime:%H:%M:%S %Z}"
                        ),
                    },
                },
                {
                    "tag": "hr",
                },
                {
                    "tag": "markdown",
                    "content": "### Load Details",
                },
                load_details_table,
                {
                    "tag": "hr",
                },
                {
                    "tag": "markdown",
                    "content": "### Status Summary",
                },
                status_summary_table,
            ],
        },
    }


def send_lark_summary(card: dict[str, Any]) -> None:
    webhook_url = get_lark_webhook_url()

    if not webhook_url:
        LOGGER.warning("LARK_WEBHOOK_URL is not configured. Skipping Lark summary.")
        return

    payload = {
        "msg_type": "interactive",
        "card": card,
    }
    request_body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=LARK_WEBHOOK_TIMEOUT_SECONDS,
        ) as response:
            response_body = response.read().decode("utf-8")

        try:
            response_payload = json.loads(response_body)
        except json.JSONDecodeError:
            LOGGER.info("Lark summary response: %s", response_body)
            LOGGER.info("Lark summary sent successfully.")
            return

        response_code = response_payload.get("code", response_payload.get("StatusCode", 0))

        if response_code not in (0, "0"):
            LOGGER.error("Lark summary rejected: %s", response_payload)
            return

        LOGGER.info("Lark summary sent successfully: %s", response_payload)
    except (urllib.error.URLError, TimeoutError):
        LOGGER.exception("Failed to send Lark summary.")


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
            source_gcs_uri = (
                getattr(error, "source_gcs_uri", "")
                or resolve_source_gcs_uri_for_result(table_name)
            )
            result_details = {}

            if source_gcs_uri:
                result_details["source_gcs_uri"] = source_gcs_uri

            phase_results.append(
                build_result(
                    table_name=table_name,
                    phase="bucket_to_r1",
                    status="FAILED",
                    message=formatted_error_message,
                    details=result_details,
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
def run_all_table() -> None:
    LOGGER.info("Starting bucket to R1 and R1 to R2 run for all tables.")

    bucket_to_r1_results = run_bucket_to_r1_phase()
    r1_to_r2_results = run_r1_to_r2_phase(bucket_to_r1_results)

    print_final_summary(
        bucket_to_r1_results=bucket_to_r1_results,
        r1_to_r2_results=r1_to_r2_results,
    )
    lark_summary_card = build_lark_summary_card(
        bucket_to_r1_results=bucket_to_r1_results,
        r1_to_r2_results=r1_to_r2_results,
    )
    send_lark_summary(lark_summary_card)
    LOGGER.info("Finished bucket to R1 and R1 to R2 run for all tables.")


# ------------------------------------------------------------
# Direct execution entrypoint
# ------------------------------------------------------------
if __name__ == "__main__":
    run_all_table()
