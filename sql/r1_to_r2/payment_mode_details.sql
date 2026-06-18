-- ------------------------------------------------------------
-- Payment Mode Details R1 to R2 full table upload
-- ------------------------------------------------------------

TRUNCATE TABLE `prod-raw-landing.ds_crm_r2.Payment_Mode_Details`;

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Payment_Mode_Details` (
    `PAYMENT_MODE_BILL_ID`,
    `PAYMENT_MODE_ID`,
    `PAYMENT_MODE_VALUE`
)
SELECT
    `PAYMENT_MODE_BILL_ID`,
    `PAYMENT_MODE_ID`,
    `PAYMENT_MODE_VALUE`
FROM `prod-raw-landing.ds_crm_r1.Payment_Mode_Details`;
