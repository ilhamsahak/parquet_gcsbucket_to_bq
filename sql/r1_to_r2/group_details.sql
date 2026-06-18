-- ------------------------------------------------------------
-- Group Details R1 to R2 full table upload
-- ------------------------------------------------------------

TRUNCATE TABLE `prod-raw-landing.ds_crm_r2.Group_Details`;

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Group_Details` (
    `GROUP_ID`,
    `GROUP_NAME`,
    `GROUP_STATUS`,
    `GROUP_CREATED_DATE`
)
SELECT
    `GROUP_ID`,
    `GROUP_NAME`,
    `GROUP_STATUS`,
    `GROUP_CREATED_DATE`
FROM `prod-raw-landing.ds_crm_r1.Group_Details`;
