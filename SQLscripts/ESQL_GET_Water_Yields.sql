-- crazy code ;)

SELECT "WS_LU_FutureFlow_Yields".capacity, "WS_LU_FutureFlow_Yields".yield 
FROM 
("WS_LU_FutureFlow_Yields" INNER JOIN "WS_LU_ExistingAssets" ON ("WS_LU_FutureFlow_Yields".wrz_id = "WS_LU_ExistingAssets".area_id AND "WS_LU_FutureFlow_Yields".capacity = "WS_LU_ExistingAssets".startcapacity)) 
WHERE ("WS_LU_FutureFlow_Yields".climate_id = (SELECT climate_id FROM "ISL_O_ModelRunDocumentation" WHERE modelrun_id = modelrun_id_val)
	AND "WS_LU_FutureFlow_Yields".year=2030 AND "WS_LU_ExistingAssets".assetoption_id=1 AND "WS_LU_ExistingAssets".active=1  AND "WS_LU_FutureFlow_Yields".wrz_id = wrz_id_val AND "WS_LU_FutureFlow_Yields".capacity = capacity_val ) 