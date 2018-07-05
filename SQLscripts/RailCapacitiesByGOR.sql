-- rail capacities in number of people , i.e. trips it can support
-- run each part of code once to ensure caps in both directions, but since they are given as bidirectional split in half for opposite directions with factor 0.5

-- START QUERY --
DELETE FROM "TR_LU_RailCapacities"

-- EXISTING ASSETS

-- START QUERY --
INSERT INTO "TR_LU_RailCapacities" (gor_1, gor_2, maxcap, network, submodel, instduration, maxlifetime, instdate, modelrun_id, capex, runcostperunit, epi, com_type, cap_ceiling, diesel_or_electric)
SELECT gor_1, gor_2, SUM(maxcap), 'Rail', 'Transport', '0', '1000', '2009', '1802', '0', '20', '0', 'rail', '0.9', 'electric' FROM
((SELECT  tab1.gor_id as gor_1, tab2.gor_id as gor_2, 0.5*750*SUM(tab1.trains*tab1.el_percent) as maxcap FROM 
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab1
INNER JOIN
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab2
ON (tab1.flow_id = tab2.flow_id) GROUP BY tab1.gor_id, tab2.gor_id)
UNION ALL
(SELECT  tab4.gor_id as gor_1, tab3.gor_id as gor_2, 0.5*750*SUM(tab3.trains*tab3.el_percent) as maxcap FROM 
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab3
INNER JOIN
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab4
ON (tab3.flow_id = tab4.flow_id) GROUP BY tab3.gor_id, tab4.gor_id)) AS tabelle
GROUP BY gor_1, gor_2    


-- START QUERY --
INSERT INTO "TR_LU_RailCapacities" (gor_1, gor_2, maxcap, network, submodel, instduration, maxlifetime, instdate, modelrun_id, capex, runcostperunit, epi, com_type, cap_ceiling, diesel_or_electric)
SELECT gor_1, gor_2, SUM(maxcap), 'Rail', 'Transport', '0', '1000', '2009', '1802', '0', '20', '0', 'rail', '0.9', 'diesel' FROM
((SELECT  tab1.gor_id as gor_1, tab2.gor_id as gor_2, 0.5*750*SUM(tab1.trains*(1-tab1.el_percent)) as maxcap FROM 
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab1
INNER JOIN
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab2
ON (tab1.flow_id = tab2.flow_id) GROUP BY tab1.gor_id, tab2.gor_id)
UNION ALL
(SELECT  tab4.gor_id as gor_1, tab3.gor_id as gor_2, 0.5*750*SUM(tab3.trains*(1-tab3.el_percent)) as maxcap FROM 
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab3
INNER JOIN
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab4
ON (tab3.flow_id = tab4.flow_id) GROUP BY tab3.gor_id, tab4.gor_id)) AS tabelle
GROUP BY gor_1, gor_2 

 --OPTIONAL ASSETS
 --20% of existing

-- START QUERY --
DO
$do$
BEGIN
-- all positive model_schema_ids stand for build scenarios, msi = 0 stands for no-build scenario
IF model_schema_id_val <> 0 THEN
INSERT INTO "TR_LU_RailCapacities" (gor_1, gor_2, maxcap, network, submodel, instduration, maxlifetime, instdate, modelrun_id, capex, runcostperunit, epi, com_type, cap_ceiling, diesel_or_electric)
SELECT gor_1, gor_2, 0.2*SUM(maxcap), 'Rail', 'Transport', '5', '1000', '100000000', '1802', '100000000', '20', '0', 'rail', '0.9', 'electric' FROM
((SELECT  tab1.gor_id as gor_1, tab2.gor_id as gor_2, 0.5*750*SUM(tab1.trains*tab1.el_percent) as maxcap FROM 
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab1
INNER JOIN
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab2
ON (tab1.flow_id = tab2.flow_id) GROUP BY tab1.gor_id, tab2.gor_id)
UNION ALL
(SELECT  tab4.gor_id as gor_1, tab3.gor_id as gor_2, 0.5*750*SUM(tab3.trains*tab3.el_percent) as maxcap FROM 
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab3
INNER JOIN
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab4
ON (tab3.flow_id = tab4.flow_id) GROUP BY tab3.gor_id, tab4.gor_id)) AS tabelle
GROUP BY gor_1, gor_2;
END IF;
END 
$do$



-- START QUERY --
DO
$do$
BEGIN
-- all positive model_schema_ids stand for build scenarios, msi = 0 stands for no-build scenario
IF model_schema_id_val <> 0 THEN
INSERT INTO "TR_LU_RailCapacities" (gor_1, gor_2, maxcap, network, submodel, instduration, maxlifetime, instdate, modelrun_id, capex, runcostperunit, epi, com_type, cap_ceiling, diesel_or_electric)
SELECT gor_1, gor_2, 0.2*SUM(maxcap), 'Rail', 'Transport', '5', '1000', '100000000', '1802', '100000000', '20', '0', 'rail', '0.9', 'diesel' FROM
((SELECT  tab1.gor_id as gor_1, tab2.gor_id as gor_2, 0.5*750*SUM(tab1.trains*(1-tab1.el_percent)) as maxcap FROM 
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab1
INNER JOIN
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab2
ON (tab1.flow_id = tab2.flow_id) GROUP BY tab1.gor_id, tab2.gor_id)
UNION ALL
(SELECT  tab4.gor_id as gor_1, tab3.gor_id as gor_2, 0.5*750*SUM(tab3.trains*(1-tab3.el_percent)) as maxcap FROM 
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone1_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab3
INNER JOIN
("TR_LU_RailLink_InitialData" INNER JOIN "TR_LU_GOR_RoadRailZoneMappingIDS" ON "TR_LU_RailLink_InitialData".zone2_id = "TR_LU_GOR_RoadRailZoneMappingIDS".zone_id) AS tab4
ON (tab3.flow_id = tab4.flow_id) GROUP BY tab3.gor_id, tab4.gor_id)) AS tabelle
GROUP BY gor_1, gor_2;
END IF;
END 
$do$


