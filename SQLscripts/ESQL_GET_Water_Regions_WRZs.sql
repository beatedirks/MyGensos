-- SQL SCRIPT TO SELECT THE WRZs INVOLVED IN THE GIVEN MODELRUN:
-- inputs: submodel-modelrun_id as 'modelrun_id'

SELECT wrz_id FROM "WS_I_WRZones_Run" WHERE modelrun_id =  