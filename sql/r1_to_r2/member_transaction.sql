-- ------------------------------------------------------------
-- Member Transaction R1 to R2 incremental upload
-- ------------------------------------------------------------

DELETE FROM `prod-raw-landing.ds_crm_r2.Member_Transaction` AS a
WHERE EXISTS (
    SELECT 1
    FROM `prod-raw-landing.ds_crm_r1.Member_Transaction` AS b
    WHERE a.`BILL_DATE` = b.`BILL_DATE`
);

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Member_Transaction` (
    `BILL_ID`,
    `BILL_NUMBER`,
    `BILL_DATE`,
    `USER_ID`,
    `DIM_EVENT_ZONE_TILL_ID`,
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
    `ADDITIONAL_DISCOUNT`,
    `ALLOCATED_POINTS`,
    `REDEEMED_POINTS`,
    `CENTRAL_GST`,
    `INTEGRATED_GST`,
    `ITEM_COUPON_DISCOUNT`,
    `STATE_GST`,
    `TAX_AMOUNT`,
    `LINEITEM_SERVICE_TAX_AMOUNT`,
    `POINTS_EARNING_RATE`,
    `BAGS_ISSUED`,
    `CURRENT_BAGS`,
    `COUNTRY_ID`
)
SELECT
    `BILL_ID`,
    `BILL_NUMBER`,
    `BILL_DATE`,
    `USER_ID`,
    `DIM_EVENT_ZONE_TILL_ID`,
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
    `ADDITIONAL_DISCOUNT`,
    `ALLOCATED_POINTS`,
    `REDEEMED_POINTS`,
    `CENTRAL_GST`,
    `INTEGRATED_GST`,
    `ITEM_COUPON_DISCOUNT`,
    `STATE_GST`,
    `TAX_AMOUNT`,
    `LINEITEM_SERVICE_TAX_AMOUNT`,
    `POINTS_EARNING_RATE`,
    `BAGS_ISSUED`,
    `CURRENT_BAGS`,
    `COUNTRY_ID`
FROM `prod-raw-landing.ds_crm_r1.Member_Transaction`;
