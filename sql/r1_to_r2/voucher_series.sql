-- ------------------------------------------------------------
-- Voucher Series R1 to R2 full table upload
-- ------------------------------------------------------------

TRUNCATE TABLE `prod-raw-landing.ds_crm_r2.Voucher_Series`;

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Voucher_Series` (
    `SERIES_ID`,
    `COUPON_VALUE`
)
SELECT
    `SERIES_ID`,
    `COUPON_VALUE`
FROM `prod-raw-landing.ds_crm_r1.Voucher_Series`;
