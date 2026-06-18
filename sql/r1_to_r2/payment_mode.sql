-- ------------------------------------------------------------
-- Payment Mode R1 to R2 full table upload
-- ------------------------------------------------------------

TRUNCATE TABLE `prod-raw-landing.ds_crm_r2.Payment_Mode`;

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Payment_Mode` (
    `PAYMENT_MODE_ID`,
    `PAYMENT_MODE`
)
SELECT
    `PAYMENT_MODE_ID`,
    `PAYMENT_MODE`
FROM `prod-raw-landing.ds_crm_r1.Payment_Mode`;
