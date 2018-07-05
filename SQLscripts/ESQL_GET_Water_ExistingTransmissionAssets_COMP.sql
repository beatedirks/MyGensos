
-- Water-model: find existing transmission assets

SELECT origin_id, area_id AS dest_id, startyear, startcapacity 
FROM "WS_LU_ExistingAssets" 
WHERE active=1 AND assetoption_id=3