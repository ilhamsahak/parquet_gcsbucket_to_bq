import fnmatch
import os
import re
from pathlib import Path
from typing import Sequence

from google.cloud import storage


# ------------------------------------------------------------
# Filename timestamp parsing
# ------------------------------------------------------------
FILENAME_TIMESTAMP_PATTERN = re.compile(r"(?P<date>\d{8})[_-](?P<time>\d{6})")
GCS_WILDCARD_CHARACTERS = ("*", "?", "[")


def extract_filename_timestamp(object_name: str) -> str | None:
    file_name = object_name.rsplit("/", 1)[-1]
    timestamp_match = FILENAME_TIMESTAMP_PATTERN.search(file_name)

    if not timestamp_match:
        return None

    return timestamp_match.group("date") + timestamp_match.group("time")


# ------------------------------------------------------------
# GCS URI parsing
# ------------------------------------------------------------
def parse_gcs_uri(gcs_uri: str) -> tuple[str, str]:
    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI. Expected gs:// URI: {gcs_uri}")

    uri_without_scheme = gcs_uri[len("gs://") :]
    bucket_name, separator, object_pattern = uri_without_scheme.partition("/")

    if not bucket_name or not separator or not object_pattern:
        raise ValueError(f"Invalid GCS URI. Missing bucket or object path: {gcs_uri}")

    return bucket_name, object_pattern


def get_first_wildcard_position(object_pattern: str) -> int | None:
    wildcard_positions = [
        object_pattern.find(wildcard_character)
        for wildcard_character in GCS_WILDCARD_CHARACTERS
        if wildcard_character in object_pattern
    ]

    if not wildcard_positions:
        return None

    return min(wildcard_positions)


def get_listing_prefix(object_pattern: str) -> str:
    wildcard_position = get_first_wildcard_position(object_pattern)

    if wildcard_position is None:
        return object_pattern

    return object_pattern[:wildcard_position]


def has_gcs_wildcard(gcs_uri: str) -> bool:
    _, object_pattern = parse_gcs_uri(gcs_uri)
    return get_first_wildcard_position(object_pattern) is not None


# ------------------------------------------------------------
# Storage client helper
# ------------------------------------------------------------
def create_storage_client(project_root: Path | None = None) -> storage.Client:
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if credentials_path:
        resolved_credentials_path = Path(credentials_path)

        if not resolved_credentials_path.is_absolute() and project_root:
            resolved_credentials_path = project_root / resolved_credentials_path

        return storage.Client.from_service_account_json(str(resolved_credentials_path))

    return storage.Client()


# ------------------------------------------------------------
# Latest GCS object resolver
# ------------------------------------------------------------
def get_blob_latest_sort_key(blob: storage.Blob) -> tuple[int, str, str, str]:
    filename_timestamp = extract_filename_timestamp(blob.name)
    updated_timestamp = blob.updated.isoformat() if blob.updated else ""

    if filename_timestamp:
        return (1, filename_timestamp, updated_timestamp, blob.name)

    return (0, updated_timestamp, updated_timestamp, blob.name)


def resolve_latest_gcs_uri(
    gcs_uri: str,
    project_root: Path | None = None,
    excluded_file_prefixes: Sequence[str] | None = None,
) -> str:
    if not has_gcs_wildcard(gcs_uri):
        return gcs_uri

    bucket_name, object_pattern = parse_gcs_uri(gcs_uri)
    listing_prefix = get_listing_prefix(object_pattern)
    storage_client = create_storage_client(project_root=project_root)
    excluded_file_prefixes = excluded_file_prefixes or ()
    matching_blobs: list[storage.Blob] = []

    for blob in storage_client.list_blobs(bucket_name, prefix=listing_prefix):
        file_name = blob.name.rsplit("/", 1)[-1]

        if any(file_name.startswith(prefix) for prefix in excluded_file_prefixes):
            continue

        if fnmatch.fnmatchcase(blob.name, object_pattern):
            matching_blobs.append(blob)

    if not matching_blobs:
        raise ValueError(f"No GCS objects matched source URI: {gcs_uri}")

    latest_blob = max(matching_blobs, key=get_blob_latest_sort_key)
    return f"gs://{bucket_name}/{latest_blob.name}"
