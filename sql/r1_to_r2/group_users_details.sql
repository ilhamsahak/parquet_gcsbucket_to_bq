-- ------------------------------------------------------------
-- Group Users Details R1 to R2 full table upload
-- ------------------------------------------------------------

TRUNCATE TABLE `prod-raw-landing.ds_crm_r2.Group_Users_Details`;

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Group_Users_Details` (
    `FLEET_GROUP_ID`,
    `USER_ID`,
    `USER_ROLE`,
    `USER_STATUS`,
    `USER_JOINED_DATE`,
    `USER_LEFT_DATE`,
    `CURRENT_POOL_OF_POINTS_IN_GROUP`,
    `CURRENT_POOL_OF_BAGS_IN_GROUP`,
    `POINTS_ISSUED`,
    `POINTS_REDEEMED`,
    `POINTS_EXPIRED`
)
SELECT
    `FLEET_GROUP_ID`,
    `USER_ID`,
    `USER_ROLE`,
    `USER_STATUS`,
    `USER_JOINED_DATE`,
    `USER_LEFT_DATE`,
    `CURRENT_POOL_OF_POINTS_IN_GROUP`,
    `CURRENT_POOL_OF_BAGS_IN_GROUP`,
    `POINTS_ISSUED`,
    `POINTS_REDEEMED`,
    `POINTS_EXPIRED`
FROM `prod-raw-landing.ds_crm_r1.Group_Users_Details`;
