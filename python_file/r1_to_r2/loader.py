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
    from python_file.r1_to_r2.sql_executor import execute_r1_to_r2_sql
except ModuleNotFoundError:
    from sql_executor import execute_r1_to_r2_sql


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
UNKNOWN_SQL_FILE_TEXT = "SQL file was not resolved before failure."
NO_JOB_ID_TEXT = "-"
NO_ERROR_TEXT = "-"


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


def get_display_table_name(table_name: str) -> str:
    normalized_table_name = normalize_table_name(table_name)
    return "_".join(name_part.capitalize() for name_part in normalized_table_name.split("_"))


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
        return "Capillary R1 to R2 Single Table Manual Run Failed"

    return "Capillary R1 to R2 Single Table Manual Run Succeeded"


def clean_lark_table_value(value: str) -> str:
    return " ".join(value.split())


# ------------------------------------------------------------
# Lark card builders
# ------------------------------------------------------------
def build_r1_to_r2_lark_card(
    result: dict[str, Any],
) -> dict[str, Any]:
    current_datetime = datetime.now(get_local_timezone())
    status = result["status"]
    details = result.get("details", {})
    sql_file_name = details.get("sql_file_name") or UNKNOWN_SQL_FILE_TEXT
    job_id = details.get("job_id") or NO_JOB_ID_TEXT
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
                    "content": "### R1 to R2 Load Details",
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
                            "name": "sql_file_name",
                            "display_name": "SQL file",
                            "data_type": "text",
                            "width": "220px",
                        },
                        {
                            "name": "r1_to_r2",
                            "display_name": "r1 > r2",
                            "data_type": "text",
                            "width": "100px",
                        },
                        {
                            "name": "job_id",
                            "display_name": "BigQuery job ID",
                            "data_type": "text",
                            "width": "260px",
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
                            "sql_file_name": sql_file_name,
                            "r1_to_r2": get_lark_status_label(status),
                            "job_id": job_id,
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
def send_r1_to_r2_lark_notification(result: dict[str, Any]) -> None:
    webhook_url = get_lark_webhook_url()

    if not webhook_url:
        LOGGER.warning("LARK_WEBHOOK_URL is not configured. Skipping Lark notification.")
        return

    payload = {
        "msg_type": "interactive",
        "card": build_r1_to_r2_lark_card(result),
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
        "phase": "r1_to_r2",
        "status": status,
        "message": message,
        "details": details or {},
    }


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

    try:
        result_details = run_r1_to_r2_table(args.table_name)
        result = build_cli_result(
            table_name=get_display_table_name(args.table_name),
            status="SUCCESS",
            details=result_details,
        )
        LOGGER.info("R1 to R2 result: %s", result_details)
        send_r1_to_r2_lark_notification(result)
    except Exception as error:
        formatted_error_message = format_error_message(error)
        result_details = {}

        try:
            result_details["sql_file_name"] = get_sql_file_name(args.table_name)
        except ValueError:
            pass

        result = build_cli_result(
            table_name=args.table_name,
            status="FAILED",
            message=formatted_error_message,
            details=result_details,
        )
        send_r1_to_r2_lark_notification(result)
        raise


if __name__ == "__main__":
    main()
