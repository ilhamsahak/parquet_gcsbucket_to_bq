import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery


# ------------------------------------------------------------
# Environment bootstrap
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = PROJECT_ROOT / "sql" / "r1_to_r2"
load_dotenv(PROJECT_ROOT / ".env")


# ------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

LOGGER = logging.getLogger(__name__)


# ------------------------------------------------------------
# BigQuery client helpers
# ------------------------------------------------------------
def create_bigquery_client() -> bigquery.Client:
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if credentials_path:
        resolved_credentials_path = Path(credentials_path)

        if not resolved_credentials_path.is_absolute():
            resolved_credentials_path = PROJECT_ROOT / resolved_credentials_path

        return bigquery.Client.from_service_account_json(str(resolved_credentials_path))

    return bigquery.Client()


# ------------------------------------------------------------
# SQL file helpers
# ------------------------------------------------------------
def get_sql_file_path(sql_file_name: str) -> Path:
    sql_file_path = SQL_DIR / sql_file_name

    if not sql_file_path.is_file():
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")

    return sql_file_path


def read_sql_file(sql_file_name: str) -> str:
    sql_file_path = get_sql_file_path(sql_file_name)
    sql_text = sql_file_path.read_text(encoding="utf-8").strip()

    if not sql_text:
        raise ValueError(f"SQL file is empty: {sql_file_path}")

    return sql_text


# ------------------------------------------------------------
# BigQuery error logging helpers
# ------------------------------------------------------------
def log_bigquery_error_details(
    sql_file_name: str,
    query_job: bigquery.QueryJob | None,
    error: Exception,
) -> None:
    LOGGER.exception("R1 to R2 SQL failed: %s", sql_file_name)

    if query_job:
        LOGGER.error("BigQuery job ID: %s", query_job.job_id)

        if query_job.errors:
            for job_error in query_job.errors:
                LOGGER.error(
                    "BigQuery error reason=%s location=%s message=%s",
                    job_error.get("reason", ""),
                    job_error.get("location", ""),
                    job_error.get("message", ""),
                )

    if isinstance(error, GoogleAPIError) and getattr(error, "errors", None):
        for api_error in error.errors:
            LOGGER.error(
                "API error reason=%s location=%s message=%s",
                api_error.get("reason", ""),
                api_error.get("location", ""),
                api_error.get("message", ""),
            )


# ------------------------------------------------------------
# SQL execution logic
# ------------------------------------------------------------
def execute_r1_to_r2_sql(sql_file_name: str) -> dict[str, Any]:
    query_job: bigquery.QueryJob | None = None

    try:
        client = create_bigquery_client()
        sql_text = read_sql_file(sql_file_name)

        LOGGER.info("Starting R1 to R2 SQL file: %s", sql_file_name)
        query_job = client.query(sql_text)
        query_job.result()

        result = {
            "sql_file_name": sql_file_name,
            "status": "SUCCESS",
            "job_id": query_job.job_id,
            "message": "SQL completed successfully.",
        }

        LOGGER.info("R1 to R2 SQL completed: %s", sql_file_name)
        LOGGER.info("BigQuery job ID: %s", query_job.job_id)
        return result
    except Exception as error:
        log_bigquery_error_details(
            sql_file_name=sql_file_name,
            query_job=query_job,
            error=error,
        )
        raise
