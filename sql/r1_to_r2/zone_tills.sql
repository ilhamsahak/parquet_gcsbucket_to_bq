-- ------------------------------------------------------------
-- Zone Tills R1 to R2 full table upload
-- ------------------------------------------------------------

TRUNCATE TABLE `prod-raw-landing.ds_crm_r2.Zone_Tills`;

-- ------------------------------------------------------------
-- Insert latest R1 snapshot data into R2
-- ------------------------------------------------------------

INSERT INTO `prod-raw-landing.ds_crm_r2.Zone_Tills` (
    `TILL_ID`,
    `STORE_NAME`,
    `TILL`,
    `EXTERNAL_ID`
)
SELECT
    `TILL_ID`,
    `STORE_NAME`,
    `TILL`,
    `EXTERNAL_ID`
FROM `prod-raw-landing.ds_crm_r1.Zone_Tills`;
