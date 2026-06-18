-- ------------------------------------------------------------
-- User Entity Status R1 to R2 full table upload
-- ------------------------------------------------------------

TRUNCATE TABLE `prod-raw-landing.ds_crm_r2.User_Entity_Status`;

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.User_Entity_Status` (
    `USER_ID`,
    `CUSTOMER_STATUS`,
    `CREATED_ON`,
    `AUTO_UPDATE_TIME`,
    `DELETION_DATE`
)
SELECT
    `USER_ID`,
    `CUSTOMER_STATUS`,
    `CREATED_ON`,
    `AUTO_UPDATE_TIME`,
    `DELETION_DATE`
FROM `prod-raw-landing.ds_crm_r1.User_Entity_Status`;
