-- ------------------------------------------------------------
-- Redeemed Voucher R1 to R2 incremental upload
-- ------------------------------------------------------------

DELETE FROM `prod-raw-landing.ds_crm_r2.Redeemed_Voucher` AS a
WHERE EXISTS (
    SELECT 1
    FROM `prod-raw-landing.ds_crm_r1.Redeemed_Voucher` AS b
    WHERE DATE(a.`REDEEMED_DATE`) = DATE(b.`REDEEMED_DATE`)
);

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Redeemed_Voucher` (
    `VOUCHER`,
    `VOUCHER_REDEEMED_BY_USER_ID`,
    `ISSUAL_COUPON_ID`,
    `DIM_COUPON_SERIES_ID`,
    `ISSUAL_DATE_TIME`,
    `EXPIRY_DATE`,
    `DIM_COUPON_EVENT_TYPE_ID`,
    `DIM_ISSUAL_ZONE_TILL_ID`,
    `BILL_ID`,
    `USED_BILL_NUMBER`,
    `REDEMPTION_BILL_AMOUNT`,
    `COUNTRY_ID`,
    `REDEEMED_DATE`
)
SELECT
    `VOUCHER`,
    `VOUCHER_REDEEMED_BY_USER_ID`,
    `ISSUAL_COUPON_ID`,
    `DIM_COUPON_SERIES_ID`,
    `ISSUAL_DATE_TIME`,
    `EXPIRY_DATE`,
    `DIM_COUPON_EVENT_TYPE_ID`,
    `DIM_ISSUAL_ZONE_TILL_ID`,
    `BILL_ID`,
    `USED_BILL_NUMBER`,
    `REDEMPTION_BILL_AMOUNT`,
    `COUNTRY_ID`,
    `REDEEMED_DATE`
FROM `prod-raw-landing.ds_crm_r1.Redeemed_Voucher`;
