-- ------------------------------------------------------------
-- Issued Voucher R1 to R2 incremental upload
-- ------------------------------------------------------------

DELETE FROM `prod-raw-landing.ds_crm_r2.Issued_Voucher` AS a
WHERE EXISTS (
    SELECT 1
    FROM `prod-raw-landing.ds_crm_r1.Issued_Voucher` AS b
    WHERE DATE(a.`ISSUAL_DATE_TIME`) = DATE(b.`ISSUAL_DATE_TIME`)
);

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Issued_Voucher` (
    `VOUCHER`,
    `VOUCHER_ISSUED_TO_USER_ID`,
    `ISSUAL_COUPON_ID`,
    `DIM_COUPON_SERIES_ID`,
    `ISSUAL_DATE_TIME`,
    `EXPIRY_DATE`,
    `DIM_COUPON_EVENT_TYPE_ID`,
    `DIM_ISSUAL_ZONE_TILL_ID`,
    `COUNTRY_ID`
)
SELECT
    `VOUCHER`,
    `VOUCHER_ISSUED_TO_USER_ID`,
    `ISSUAL_COUPON_ID`,
    `DIM_COUPON_SERIES_ID`,
    `ISSUAL_DATE_TIME`,
    `EXPIRY_DATE`,
    `DIM_COUPON_EVENT_TYPE_ID`,
    `DIM_ISSUAL_ZONE_TILL_ID`,
    `COUNTRY_ID`
FROM `prod-raw-landing.ds_crm_r1.Issued_Voucher`;
