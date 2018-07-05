-- Find involved water companies in a specific modelrun
-- inputs: water-modelrun_id as modelrun_id

SELECT company_id FROM "WS_I_Companies_Run" WHERE modelrun_id = 