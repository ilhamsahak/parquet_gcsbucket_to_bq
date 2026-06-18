-- ------------------------------------------------------------
-- Users R1 to R2 full table upload
-- ------------------------------------------------------------

TRUNCATE TABLE `prod-raw-landing.ds_crm_r2.Users`;

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Users` (
    `USER_ID`,
    `SLAB_NAME`,
    `LOYALTY_TYPE`,
    `CUSTOMER_EXTERNAL_ID`,
    `FRAUD_STATUS`,
    `IS_MERGED_CUSTOMER`,
    `MERGED_USER_ID`,
    `SLAB_EXPIRY_DATE`,
    `SUBSCRIPTION_STATUS_WECHAT_BULK`,
    `SUBSCRIPTION_STATUS_WECHAT_TRANS`,
    `SUBSCRIPTION_STATUS_SMS_TRANS`,
    `SUBSCRIPTION_STATUS_SMS_BULK`,
    `SUBSCRIPTION_STATUS_EMAIL_BULK`,
    `SUBSCRIPTION_STATUS_EMAIL_TRANS`,
    `COUNTRY_ID`
)
SELECT
    `USER_ID`,
    `SLAB_NAME`,
    `LOYALTY_TYPE`,
    `CUSTOMER_EXTERNAL_ID`,
    `FRAUD_STATUS`,
    `IS_MERGED_CUSTOMER`,
    `MERGED_USER_ID`,
    `SLAB_EXPIRY_DATE`,
    `SUBSCRIPTION_STATUS_WECHAT_BULK`,
    `SUBSCRIPTION_STATUS_WECHAT_TRANS`,
    `SUBSCRIPTION_STATUS_SMS_TRANS`,
    `SUBSCRIPTION_STATUS_SMS_BULK`,
    `SUBSCRIPTION_STATUS_EMAIL_BULK`,
    `SUBSCRIPTION_STATUS_EMAIL_TRANS`,
    `COUNTRY_ID`
FROM `prod-raw-landing.ds_crm_r1.Users`;
