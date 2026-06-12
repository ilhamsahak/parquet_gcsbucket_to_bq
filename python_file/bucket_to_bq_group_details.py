import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery

try:
    from python_file.gcs_latest_resolver import resolve_latest_gcs_uri
except ModuleNotFoundError:
    from gcs_latest_resolver import resolve_latest_gcs_uri


# ------------------------------------------------------------
# Environment bootstrap
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
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
# Configuration helpers
# ------------------------------------------------------------
def get_required_env(env_name: str) -> str:
    env_value = os.getenv(env_name)

    if not env_value:
        raise ValueError(f"Missing required environment variable: {env_name}")

    return env_value


def get_config() -> dict[str, str]:
    project_id = get_required_env("DESTINATION_PROJECT_ID")
    dataset_id = get_required_env("DATASET_ID")
    target_table = get_required_env("GROUP_DETAILS_TABLE_ID")
    gcs_uri = get_required_env("GROUP_DETAILS_GCS_URI")

    return {
        "project_id": project_id,
        "dataset_id": dataset_id,
        "target_table": target_table,
        "gcs_uri": gcs_uri,
    }


def build_table_id(project_id: str, dataset_id: str, table_name: str) -> str:
    return f"{project_id}.{dataset_id}.{table_name}"


def build_staging_table_id(
    project_id: str,
    dataset_id: str,
    target_table: str,
) -> str:
    unique_suffix = uuid.uuid4().hex[:8]
    sanitized_table_name = target_table.lower().replace("-", "_")
    return f"{project_id}.{dataset_id}._stg_{sanitized_table_name}_{unique_suffix}"


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
# Staging load helpers
# ------------------------------------------------------------
def load_parquet_to_staging_table(
    client: bigquery.Client,
    gcs_uri: str,
    staging_table_id: str,
) -> None:
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
    )

    resolved_gcs_uri = resolve_latest_gcs_uri(
        gcs_uri=gcs_uri,
        project_root=PROJECT_ROOT,
    )

    LOGGER.info("Loading parquet into staging table: %s", staging_table_id)
    LOGGER.info("Resolved parquet source URI: %s", resolved_gcs_uri)
    load_job = client.load_table_from_uri(
        resolved_gcs_uri,
        staging_table_id,
        job_config=job_config,
    )
    load_job.result()
    LOGGER.info("Staging load completed successfully.")


# ------------------------------------------------------------
# Schema mapping helpers
# ------------------------------------------------------------
def build_staging_column_lookup(
    staging_schema: list[bigquery.SchemaField],
) -> dict[str, str]:
    staging_lookup: dict[str, str] = {}

    for field in staging_schema:
        staging_lookup[field.name.lower()] = field.name

    return staging_lookup


def get_source_column_reference(
    target_field_name: str,
    staging_lookup: dict[str, str],
) -> str | None:
    source_column_name = staging_lookup.get(target_field_name.lower())

    if not source_column_name:
        return None

    return f"`{source_column_name}`"


def validate_required_source_columns(
    target_schema: list[bigquery.SchemaField],
    staging_lookup: dict[str, str],
) -> None:
    missing_required_columns: list[str] = []

    for field in target_schema:
        if field.mode != "REQUIRED":
            continue

        if not get_source_column_reference(field.name, staging_lookup):
            missing_required_columns.append(field.name)

    if missing_required_columns:
        raise ValueError(
            "Required target columns missing from source parquet: "
            + ", ".join(missing_required_columns)
        )


# ------------------------------------------------------------
# SQL expression helpers
# ------------------------------------------------------------
def get_cast_type(field: bigquery.SchemaField) -> str:
    if field.field_type == "INTEGER":
        return "INT64"

    if field.field_type == "FLOAT":
        return "FLOAT64"

    if field.field_type == "BOOLEAN":
        return "BOOL"

    return field.field_type


def build_validation_expression(
    field: bigquery.SchemaField,
    source_column_reference: str | None,
) -> str:
    if not source_column_reference:
        return "NULL"

    if field.mode == "REPEATED":
        return source_column_reference

    if field.field_type == "STRING":
        return f"CAST({source_column_reference} AS STRING)"

    return f"SAFE_CAST({source_column_reference} AS {get_cast_type(field)})"


def build_select_expression(
    field: bigquery.SchemaField,
    source_column_reference: str | None,
) -> str:
    if not source_column_reference:
        return f"CAST(NULL AS {get_cast_type(field)}) AS `{field.name}`"

    if field.mode == "REPEATED":
        return f"{source_column_reference} AS `{field.name}`"

    if field.field_type == "STRING":
        return f"CAST({source_column_reference} AS STRING) AS `{field.name}`"

    if field.mode == "REQUIRED":
        return f"CAST({source_column_reference} AS {get_cast_type(field)}) AS `{field.name}`"

    return f"SAFE_CAST({source_column_reference} AS {get_cast_type(field)}) AS `{field.name}`"


# ------------------------------------------------------------
# Validation helpers
# ------------------------------------------------------------
def get_table_row_count(
    client: bigquery.Client,
    table_id: str,
) -> int:
    row_count_sql = f"""
SELECT COUNT(*) AS row_count
FROM `{table_id}`;
""".strip()

    row_count_result = list(client.query(row_count_sql).result())

    if not row_count_result:
        raise ValueError(f"Unable to read row count for table: {table_id}")

    return int(row_count_result[0]["row_count"])


def validate_staging_table_has_rows(
    client: bigquery.Client,
    staging_table_id: str,
) -> None:
    LOGGER.info("Validating staging table has rows before truncate.")
    row_count = get_table_row_count(client=client, table_id=staging_table_id)

    if row_count == 0:
        raise ValueError(
            "Staging table is empty. Aborting before truncating target table."
        )


def validate_required_field_values(
    client: bigquery.Client,
    staging_table_id: str,
    target_schema: list[bigquery.SchemaField],
    staging_lookup: dict[str, str],
) -> None:
    required_fields = [field for field in target_schema if field.mode == "REQUIRED"]

    if not required_fields:
        return

    validate_required_source_columns(
        target_schema=target_schema,
        staging_lookup=staging_lookup,
    )

    validation_checks: list[str] = []

    for field in required_fields:
        source_column_reference = get_source_column_reference(field.name, staging_lookup)
        validation_expression = build_validation_expression(field, source_column_reference)
        validation_checks.append(
            f"COUNTIF({validation_expression} IS NULL) AS `{field.name}`"
        )

    validation_sql = f"""
SELECT
    {", ".join(validation_checks)}
FROM `{staging_table_id}`;
""".strip()

    LOGGER.info("Validating required target columns before truncate.")
    validation_result = list(client.query(validation_sql).result())

    if not validation_result:
        return

    validation_row = validation_result[0]
    invalid_fields: list[str] = []

    for field in required_fields:
        invalid_count = validation_row[field.name]

        if invalid_count and invalid_count > 0:
            invalid_fields.append(f"{field.name} ({invalid_count} invalid rows)")

    if invalid_fields:
        raise ValueError(
            "Required column validation failed before truncate: "
            + ", ".join(invalid_fields)
        )


# ------------------------------------------------------------
# Select SQL builder
# ------------------------------------------------------------
def get_safe_write_disposition() -> str:
    return getattr(
        bigquery.WriteDisposition,
        "WRITE_TRUNCATE_DATA",
        bigquery.WriteDisposition.WRITE_TRUNCATE,
    )


def build_select_sql(
    staging_table_id: str,
    target_schema: list[bigquery.SchemaField],
    staging_lookup: dict[str, str],
) -> str:
    select_expressions: list[str] = []

    for field in target_schema:
        source_column_reference = get_source_column_reference(field.name, staging_lookup)
        select_expressions.append(
            build_select_expression(field, source_column_reference)
        )

    return f"""
SELECT
    {", ".join(select_expressions)}
FROM `{staging_table_id}`;
""".strip()


# ------------------------------------------------------------
# Load orchestration
# ------------------------------------------------------------
def load_staging_data_into_target(
    client: bigquery.Client,
    target_table_id: str,
    staging_table_id: str,
) -> None:
    LOGGER.info("Reading target table schema: %s", target_table_id)
    target_table = client.get_table(target_table_id)

    LOGGER.info("Reading staging table schema: %s", staging_table_id)
    staging_table = client.get_table(staging_table_id)
    staging_lookup = build_staging_column_lookup(staging_table.schema)

    validate_staging_table_has_rows(
        client=client,
        staging_table_id=staging_table_id,
    )

    validate_required_field_values(
        client=client,
        staging_table_id=staging_table_id,
        target_schema=target_table.schema,
        staging_lookup=staging_lookup,
    )

    select_sql = build_select_sql(
        staging_table_id=staging_table_id,
        target_schema=target_table.schema,
        staging_lookup=staging_lookup,
    )

    query_job_config = bigquery.QueryJobConfig(
        destination=target_table_id,
        write_disposition=get_safe_write_disposition(),
        create_disposition=bigquery.CreateDisposition.CREATE_NEVER,
    )

    LOGGER.info("Overwriting target table with staged data atomically: %s", target_table_id)
    query_job = client.query(select_sql, job_config=query_job_config)
    query_job.result()
    target_row_count = get_table_row_count(client=client, table_id=target_table_id)
    LOGGER.info("Target table row count after overwrite: %s", target_row_count)
    LOGGER.info("Target table load completed successfully.")


def drop_staging_table(
    client: bigquery.Client,
    staging_table_id: str,
) -> None:
    LOGGER.info("Dropping staging table: %s", staging_table_id)
    client.delete_table(staging_table_id, not_found_ok=True)
    LOGGER.info("Staging table dropped.")


# ------------------------------------------------------------
# Main execution flow
# ------------------------------------------------------------
def load_group_details() -> None:
    config = get_config()
    project_id = config["project_id"]
    dataset_id = config["dataset_id"]
    target_table = config["target_table"]
    gcs_uri = config["gcs_uri"]

    target_table_id = build_table_id(project_id, dataset_id, target_table)
    staging_table_id = build_staging_table_id(project_id, dataset_id, target_table)

    client = create_bigquery_client()

    try:
        LOGGER.info("Starting parquet load for target table: %s", target_table_id)
        load_parquet_to_staging_table(
            client=client,
            gcs_uri=gcs_uri,
            staging_table_id=staging_table_id,
        )
        staging_row_count = get_table_row_count(client=client, table_id=staging_table_id)
        LOGGER.info("Staging table row count after parquet load: %s", staging_row_count)
        load_staging_data_into_target(
            client=client,
            target_table_id=target_table_id,
            staging_table_id=staging_table_id,
        )
        LOGGER.info("Parquet load finished successfully for target table: %s", target_table_id)
    except Exception:
        LOGGER.exception("Parquet load failed for target table: %s", target_table_id)
        raise
    finally:
        drop_staging_table(
            client=client,
            staging_table_id=staging_table_id,
        )


if __name__ == "__main__":
    load_group_details()

