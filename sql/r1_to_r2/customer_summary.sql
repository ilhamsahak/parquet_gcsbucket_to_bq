-- ------------------------------------------------------------
-- Customer Summary R1 to R2 full table upload
-- ------------------------------------------------------------

TRUNCATE TABLE `prod-raw-landing.ds_crm_r2.Customer_Summary`;

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Customer_Summary` (
    `USER_ID`,
    `POINTS_ISSUED`,
    `POINTS_REDEEMED`,
    `POINTS_EXPIRED`,
    `CURRENT_POINTS`,
    `MODIFIED_DATE`,
    `ENROLLEMENT_DATE`,
    `REGISTERED_TILL_ID`,
    `TOTAL_BAGS`,
    `REDEEMED_BAGS`,
    `EXPIRED_BAGS`,
    `CURRENT_BAGS`,
    `REGISTRATION_CHANNEL`
)
SELECT
    `USER_ID`,
    `POINTS_ISSUED`,
    `POINTS_REDEEMED`,
    `POINTS_EXPIRED`,
    `CURRENT_POINTS`,
    `MODIFIED_DATE`,
    `ENROLLEMENT_DATE`,
    `REGISTERED_TILL_ID`,
    `TOTAL_BAGS`,
    `REDEEMED_BAGS`,
    `EXPIRED_BAGS`,
    `CURRENT_BAGS`,
    `REGISTRATION_CHANNEL`
FROM `prod-raw-landing.ds_crm_r1.Customer_Summary`;
