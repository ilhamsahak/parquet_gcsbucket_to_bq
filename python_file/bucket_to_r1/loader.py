import argparse
import json
import logging
import os
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

try:
    from python_file.bucket_to_r1.parquet_loader import load_bucket_to_r1_table
    from python_file.bucket_to_r1.table_config import get_table_load_config
except ModuleNotFoundError:
    from parquet_loader import load_bucket_to_r1_table
    from table_config import get_table_load_config


# ------------------------------------------------------------
# Environment bootstrap
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


# ------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------
LOGGER = logging.getLogger(__name__)


# ------------------------------------------------------------
# Lark notification configuration
# ------------------------------------------------------------
LARK_WEBHOOK_TIMEOUT_SECONDS = 15
UNRESOLVED_GCS_URI_TEXT = "Source GCS URI was not resolved before failure."
NO_ERROR_TEXT = "-"


# ------------------------------------------------------------
# Datetime helpers
# ------------------------------------------------------------
def get_local_timezone() -> ZoneInfo | timezone:
    try:
        return ZoneInfo("Asia/Kuala_Lumpur")
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=8), name="MYT")


# ------------------------------------------------------------
# Lark webhook helpers
# ------------------------------------------------------------
def get_lark_webhook_url() -> str:
    return os.getenv("LARK_WEBHOOK_URL", "").strip()


def get_lark_status_label(status: str) -> str:
    status_labels = {
        "SUCCESS": "success",
        "FAILED": "fails",
    }

    return status_labels.get(status, status.lower())


def get_lark_card_template(status: str) -> str:
    if status == "FAILED":
        return "red"

    return "green"


def get_lark_card_title(status: str) -> str:
    if status == "FAILED":
        return "Capillary Bucket to R1 Single Table Manual Run Failed"

    return "Capillary Bucket to R1 Single Table Manual Run Succeeded"


def clean_lark_table_value(value: str) -> str:
    return " ".join(value.split())


# ------------------------------------------------------------
# Lark card builders
# ------------------------------------------------------------
def build_bucket_to_r1_lark_card(
    result: dict[str, Any],
) -> dict[str, Any]:
    current_datetime = datetime.now(get_local_timezone())
    status = result["status"]
    details = result.get("details", {})
    source_gcs_uri = details.get("source_gcs_uri") or UNRESOLVED_GCS_URI_TEXT
    error_reason = clean_lark_table_value(result.get("message") or NO_ERROR_TEXT)

    return {
        "schema": "2.0",
        "config": {
            "width_mode": "fill",
            "summary": {
                "content": get_lark_card_title(status),
            },
        },
        "header": {
            "template": get_lark_card_template(status),
            "title": {
                "tag": "plain_text",
                "content": get_lark_card_title(status),
            },
        },
        "body": {
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            "**Run mode:** Single Table Manual Run\n"
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
                    "content": "### Bucket to R1 Load Details",
                },
                {
                    "tag": "table",
                    "page_size": 1,
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
                            "name": "error_reason",
                            "display_name": "Error reason",
                            "data_type": "text",
                            "width": "360px",
                        },
                    ],
                    "rows": [
                        {
                            "table_name": result["table_name"],
                            "gcs_uri": source_gcs_uri,
                            "bucket_to_r1": get_lark_status_label(status),
                            "error_reason": error_reason,
                        },
                    ],
                },
            ],
        },
    }


# ------------------------------------------------------------
# Lark notification sender
# ------------------------------------------------------------
def send_bucket_to_r1_lark_notification(result: dict[str, Any]) -> None:
    webhook_url = get_lark_webhook_url()

    if not webhook_url:
        LOGGER.warning("LARK_WEBHOOK_URL is not configured. Skipping Lark notification.")
        return

    payload = {
        "msg_type": "interactive",
        "card": build_bucket_to_r1_lark_card(result),
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
            LOGGER.info("Lark notification response: %s", response_body)
            LOGGER.info("Lark notification sent successfully.")
            return

        response_code = response_payload.get("code", response_payload.get("StatusCode", 0))

        if response_code not in (0, "0"):
            LOGGER.error("Lark notification rejected: %s", response_payload)
            return

        LOGGER.info("Lark notification sent successfully: %s", response_payload)
    except (urllib.error.URLError, TimeoutError):
        LOGGER.exception("Failed to send Lark notification.")


# ------------------------------------------------------------
# Result helpers
# ------------------------------------------------------------
def format_error_message(error: Exception) -> str:
    error_message = str(error).strip()

    if not error_message:
        return error.__class__.__name__

    return error_message


def build_cli_result(
    table_name: str,
    status: str,
    message: str = "",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "table_name": table_name,
        "phase": "bucket_to_r1",
        "status": status,
        "message": message,
        "details": details or {},
    }


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

    try:
        result_details = run_bucket_to_r1_table(args.table_name)
        result = build_cli_result(
            table_name=result_details["table_name"],
            status="SUCCESS",
            details=result_details,
        )
        LOGGER.info("Bucket to R1 result: %s", result_details)
        send_bucket_to_r1_lark_notification(result)
    except Exception as error:
        formatted_error_message = format_error_message(error)
        source_gcs_uri = getattr(error, "source_gcs_uri", "")
        result_details = {}

        if source_gcs_uri:
            result_details["source_gcs_uri"] = source_gcs_uri

        result = build_cli_result(
            table_name=args.table_name,
            status="FAILED",
            message=formatted_error_message,
            details=result_details,
        )
        send_bucket_to_r1_lark_notification(result)
        raise


if __name__ == "__main__":
    main()
