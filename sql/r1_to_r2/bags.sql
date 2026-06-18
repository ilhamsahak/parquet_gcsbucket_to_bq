-- ------------------------------------------------------------
-- Bags R1 to R2 incremental upload
-- ------------------------------------------------------------

DELETE FROM `prod-raw-landing.ds_crm_r2.Bags` AS a
WHERE EXISTS (
    SELECT 1
    FROM `prod-raw-landing.ds_crm_r1.Bags` AS b
    WHERE a.`AWARDED_DATE` = b.`AWARDED_DATE`
);

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Bags` (
    `USER_ID`,
    `BILL_ID`,
    `BILL_NUMBER`,
    `AWARDED_DATE`,
    `ALLOCATED_BAGS`,
    `DEDUCTED_BAGS`,
    `BAGS_REDEEMED_TXN`
)
SELECT
    `USER_ID`,
    `BILL_ID`,
    `BILL_NUMBER`,
    `AWARDED_DATE`,
    `ALLOCATED_BAGS`,
    `DEDUCTED_BAGS`,
    `BAGS_REDEEMED_TXN`
FROM `prod-raw-landing.ds_crm_r1.Bags`;
