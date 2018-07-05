-- existing road capacities are given by number of trips of 2 people in a car that the respective arc can support
-- road capacities are given bidirectional in the input tables, hence the UNION ALL and factor 0.5, to split caps into the two opposite directions

-- START QUERY --
DELETE FROM "TR_LU_RoadCapacities"

-- START QUERY --
-- existing asets
INSERT INTO "TR_LU_RoadCapacities" (gor_1, gor_2, maxcap, network, submodel, instduration, maxlifetime, instdate, modelrun_id, capex, com_type, cap_ceiling)
SELECT gor_1, gor_2, SUM(maxcap), 'Road', 'Transport', '5', '1000', '2009', '1802', '0', 'road', '0.9' FROM
((SELECT  tab1.gor_id as gor_1, tab2.gor_id as gor_2, 0.5*2*SUM(tab1.total_usage_in_pcu) as maxcap FROM 
--((SELECT  tab1.gor_id as gor_1, tab2.gor_id as gor_2, 2*(2330*SUM(tab1.m_lanes) + 2100*SUM(tab1.d_lanes) + 1380*SUM(tab1.s_lanes)) as maxcap FROM 
("TR_LU_RoadLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RoadLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab1
INNER JOIN
("TR_LU_RoadLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RoadLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab2
ON (tab1.flow_id = tab2.flow_id) GROUP BY tab1.gor_id, tab2.gor_id)
UNION ALL
(SELECT  tab4.gor_id as gor_1, tab3.gor_id as gor_2, 2*SUM(tab3.total_usage_in_pcu) as maxcap FROM 
--(SELECT  tab4.gor_id as gor_1, tab3.gor_id as gor_2, 2*(2330*SUM(tab3.m_lanes) + 2100*SUM(tab3.d_lanes) + 1380*SUM(tab3.s_lanes)) as maxcap FROM 
("TR_LU_RoadLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RoadLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab3
INNER JOIN
("TR_LU_RoadLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RoadLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab4 
ON (tab3.flow_id = tab4.flow_id) GROUP BY tab3.gor_id, tab4.gor_id))AS tabelle
GROUP BY gor_1, gor_2

-- START QUERY --
-- optional expansions: 20% of existing assets
DO
$do$
BEGIN
-- all positive model_schema_ids stand for build scenarios, msi = 0 stands for no-build scenario
IF model_schema_id_val <> 0 THEN
INSERT INTO "TR_LU_RoadCapacities" (gor_1, gor_2, maxcap, network, submodel, instduration, maxlifetime, instdate, modelrun_id, capex, com_type, cap_ceiling)
SELECT gor_1, gor_2, 0.2*SUM(maxcap), 'Road', 'Transport', '5', '1000', '100000000', '1802', '100000000', 'road', '0.9' FROM
((SELECT  tab1.gor_id as gor_1, tab2.gor_id as gor_2, 2*SUM(tab1.total_usage_in_pcu) as maxcap FROM 
--((SELECT  tab1.gor_id as gor_1, tab2.gor_id as gor_2, 2*(2330*SUM(tab1.m_lanes) + 2100*SUM(tab1.d_lanes) + 1380*SUM(tab1.s_lanes)) as maxcap FROM 
("TR_LU_RoadLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RoadLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab1
INNER JOIN
("TR_LU_RoadLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RoadLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab2
ON (tab1.flow_id = tab2.flow_id) GROUP BY tab1.gor_id, tab2.gor_id)
UNION ALL
(SELECT  tab4.gor_id as gor_1, tab3.gor_id as gor_2, 2*SUM(tab3.total_usage_in_pcu) as maxcap FROM 
--(SELECT  tab4.gor_id as gor_1, tab3.gor_id as gor_2, 2*(2330*SUM(tab3.m_lanes) + 2100*SUM(tab3.d_lanes) + 1380*SUM(tab3.s_lanes)) as maxcap FROM 
("TR_LU_RoadLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RoadLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab3
INNER JOIN
("TR_LU_RoadLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RoadLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab4 
ON (tab3.flow_id = tab4.flow_id) GROUP BY tab3.gor_id, tab4.gor_id))AS tabelle
GROUP BY gor_1, gor_2;
END IF;
END 
$do$

