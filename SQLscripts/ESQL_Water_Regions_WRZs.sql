-- SQL SCRIPT TO SELECT THE WRZs INVOLVED IN THE GIVEN MODELRUN:
-- inputs: submodel-modelrun_id as 'modelrun_id'

INSERT INTO "ISL_I_NetworkRegions" (regionname, submodel) 

(SELECT wrz_id, 'Water' FROM "WS_I_WRZones_Run" WHERE modelrun_id =  )