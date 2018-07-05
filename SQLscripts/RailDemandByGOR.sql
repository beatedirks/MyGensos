-- estimate of 750 people per train, i.e. number of trips = trains*750
-- number of trains are bidirectional, i.e. half of it for each direction, the specified one and the opposite one, hence the UNION ALL and factor 0.5

-- START QUERY --
DELETE FROM "TR_LU_RailDemandByGOR"

-- START QUERY --
INSERT INTO "TR_LU_RailDemandByGOR"(year, gor_1, gor_2, scenario_id, "demand_trips")
SELECT year, gor1, gor2, scenario_id, 0.5*750*SUM(trains)FROM
((SELECT gor1_id as gor1, gor2_id as gor2, trains, year, scenario_id FROM "TR_O_RailLinkOutputData")
UNION ALL
(SELECT gor2_id as gor1, gor1_id as gor2, trains, year, scenario_id FROM "TR_O_RailLinkOutputData")) AS tabelle
GROUP BY gor1, gor2, year, scenario_id;
