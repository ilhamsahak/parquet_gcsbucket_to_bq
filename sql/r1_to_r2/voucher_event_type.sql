-- ------------------------------------------------------------
-- Voucher Event Type R1 to R2 full table upload
-- ------------------------------------------------------------

TRUNCATE TABLE `prod-raw-landing.ds_crm_r2.Voucher_Event_Type`;

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Voucher_Event_Type` (
    `DIM_COUPON_EVENT_TYPE_ID`,
    `VOUCHER_EVENT_TYPE`
)
SELECT
    `DIM_COUPON_EVENT_TYPE_ID`,
    `VOUCHER_EVENT_TYPE`
FROM `prod-raw-landing.ds_crm_r1.Voucher_Event_Type`;
