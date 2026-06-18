-- ------------------------------------------------------------
-- Group Transaction R1 to R2 incremental upload
-- ------------------------------------------------------------

DELETE FROM `prod-raw-landing.ds_crm_r2.Group_Transaction` AS a
WHERE EXISTS (
    SELECT 1
    FROM `prod-raw-landing.ds_crm_r1.Group_Transaction` AS b
    WHERE DATE(a.`BILL_DATETIME`) = DATE(b.`BILL_DATETIME`)
);

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Group_Transaction` (
    `GROUP_ID`,
    `GROUP_NAME`,
    `BILL_ID`,
    `BILL_NUMBER`,
    `BILL_DATETIME`,
    `STORE_EXTERNAL_ID`,
    `STORE_NAME`,
    `USER_ID`,
    `INITIAL_BILL_VALUE`,
    `BILL_DISCOUNT`,
    `BILL_AMOUNT`,
    `LINE_ITEM_ID`,
    `ITEM_CODE`,
    `ITEM_DESCRIPTION`,
    `RATE`,
    `QUANTITY`,
    `LINE_ITEM_DISCOUNT`,
    `LINE_ITEM_AMOUNT`,
    `PAYMENT_MODE`,
    `PAYMENT_MODE_VALUE`,
    `ADDITIONAL_DISCOUNT`,
    `ALLOCATED_POINTS`,
    `REDEEMED_POINTS`,
    `CENTRAL_GST`,
    `INTEGRATED_GST`,
    `ITEM_COUPON_DISCOUNT`,
    `STATE_GST`,
    `TAX_AMOUNT`,
    `LINE_ITEM_SERVICE_TAX_AMOUNT`,
    `POINT_EARNING_RATE`,
    `BAGS_ISSUED`,
    `CURRENT_BAGS`,
    `COUNTRY_ID`
)
SELECT
    `GROUP_ID`,
    `GROUP_NAME`,
    `BILL_ID`,
    `BILL_NUMBER`,
    `BILL_DATETIME`,
    `STORE_EXTERNAL_ID`,
    `STORE_NAME`,
    `USER_ID`,
    `INITIAL_BILL_VALUE`,
    `BILL_DISCOUNT`,
    `BILL_AMOUNT`,
    `LINE_ITEM_ID`,
    `ITEM_CODE`,
    `ITEM_DESCRIPTION`,
    `RATE`,
    `QUANTITY`,
    `LINE_ITEM_DISCOUNT`,
    `LINE_ITEM_AMOUNT`,
    `PAYMENT_MODE`,
    `PAYMENT_MODE_VALUE`,
    `ADDITIONAL_DISCOUNT`,
    `ALLOCATED_POINTS`,
    `REDEEMED_POINTS`,
    `CENTRAL_GST`,
    `INTEGRATED_GST`,
    `ITEM_COUPON_DISCOUNT`,
    `STATE_GST`,
    `TAX_AMOUNT`,
    `LINE_ITEM_SERVICE_TAX_AMOUNT`,
    `POINT_EARNING_RATE`,
    `BAGS_ISSUED`,
    `CURRENT_BAGS`,
    `COUNTRY_ID`
FROM `prod-raw-landing.ds_crm_r1.Group_Transaction`;
