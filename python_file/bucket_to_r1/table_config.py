from dataclasses import dataclass


# ------------------------------------------------------------
# Table load configuration model
# ------------------------------------------------------------
@dataclass(frozen=True)
class TableLoadConfig:
    table_name: str
    table_id_env: str
    gcs_uri_env: str
    excluded_file_prefixes: tuple[str, ...] = ()


# ------------------------------------------------------------
# Table load configuration
# ------------------------------------------------------------
TABLE_LOAD_CONFIGS = {
    "bags": TableLoadConfig(
        table_name="Bags",
        table_id_env="BAGS_TABLE_ID",
        gcs_uri_env="BAGS_GCS_URI",
    ),
    "customer_summary": TableLoadConfig(
        table_name="Customer_Summary",
        table_id_env="CUSTOMER_SUMMARY_TABLE_ID",
        gcs_uri_env="CUSTOMER_SUMMARY_GCS_URI",
    ),
    "expired_voucher": TableLoadConfig(
        table_name="Expired_Voucher",
        table_id_env="EXPIRED_VOUCHER_TABLE_ID",
        gcs_uri_env="EXPIRED_VOUCHER_GCS_URI",
    ),
    "group_details": TableLoadConfig(
        table_name="Group_Details",
        table_id_env="GROUP_DETAILS_TABLE_ID",
        gcs_uri_env="GROUP_DETAILS_GCS_URI",
    ),
    "group_transaction": TableLoadConfig(
        table_name="Group_Transaction",
        table_id_env="GROUP_TRANSACTION_TABLE_ID",
        gcs_uri_env="GROUP_TRANSACTION_GCS_URI",
    ),
    "group_users_details": TableLoadConfig(
        table_name="Group_Users_Details",
        table_id_env="GROUP_USERS_DETAILS_TABLE_ID",
        gcs_uri_env="GROUP_USERS_DETAILS_GCS_URI",
    ),
    "issued_voucher": TableLoadConfig(
        table_name="Issued_Voucher",
        table_id_env="ISSUED_VOUCHER_TABLE_ID",
        gcs_uri_env="ISSUED_VOUCHER_GCS_URI",
    ),
    "member_transaction": TableLoadConfig(
        table_name="Member_Transaction",
        table_id_env="MEMBER_TRANSACTION_TABLE_ID",
        gcs_uri_env="MEMBER_TRANSACTION_GCS_URI",
    ),
    "payment_mode": TableLoadConfig(
        table_name="Payment_Mode",
        table_id_env="PAYMENT_MODE_TABLE_ID",
        gcs_uri_env="PAYMENT_MODE_GCS_URI",
        excluded_file_prefixes=("Payment_Mode_Details_",),
    ),
    "payment_mode_details": TableLoadConfig(
        table_name="Payment_Mode_Details",
        table_id_env="PAYMENT_MODE_DETAILS_TABLE_ID",
        gcs_uri_env="PAYMENT_MODE_DETAILS_GCS_URI",
    ),
    "redeemed_voucher": TableLoadConfig(
        table_name="Redeemed_Voucher",
        table_id_env="REDEEMED_VOUCHER_TABLE_ID",
        gcs_uri_env="REDEEMED_VOUCHER_GCS_URI",
    ),
    "user_entity_status": TableLoadConfig(
        table_name="User_Entity_Status",
        table_id_env="USER_ENTITY_STATUS_TABLE_ID",
        gcs_uri_env="USER_ENTITY_STATUS_GCS_URI",
    ),
    "users": TableLoadConfig(
        table_name="Users",
        table_id_env="USERS_TABLE_ID",
        gcs_uri_env="USERS_GCS_URI",
    ),
    "voucher_event_type": TableLoadConfig(
        table_name="Voucher_Event_Type",
        table_id_env="VOUCHER_EVENT_TYPE_TABLE_ID",
        gcs_uri_env="VOUCHER_EVENT_TYPE_GCS_URI",
    ),
    "voucher_series": TableLoadConfig(
        table_name="Voucher_Series",
        table_id_env="VOUCHER_SERIES_TABLE_ID",
        gcs_uri_env="VOUCHER_SERIES_GCS_URI",
    ),
    "zone_tills": TableLoadConfig(
        table_name="Zone_Tills",
        table_id_env="ZONE_TILLS_TABLE_ID",
        gcs_uri_env="ZONE_TILLS_GCS_URI",
    ),
}


# ------------------------------------------------------------
# Table name helpers
# ------------------------------------------------------------
def normalize_table_name(table_name: str) -> str:
    return table_name.strip().lower().replace("-", "_")


def get_table_load_config(table_name: str) -> TableLoadConfig:
    normalized_table_name = normalize_table_name(table_name)
    table_config = TABLE_LOAD_CONFIGS.get(normalized_table_name)

    if not table_config:
        valid_table_names = ", ".join(sorted(TABLE_LOAD_CONFIGS))
        raise ValueError(
            f"Unsupported table_name: {table_name}. "
            f"Valid table_name values: {valid_table_names}"
        )

    return table_config
