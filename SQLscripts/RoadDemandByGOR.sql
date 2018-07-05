-- estimate of two people per car, i.e. number of trips = pcu*2
-- pcu_total are bidirectional, i.e. half of it for each direction, the specified one and the opposite one, hence the UNION ALL and factor 0.5

-- START QUERY --
DELETE FROM "TR_LU_RoadDemandsByGOR"

-- START QUERY --
INSERT INTO "TR_LU_RoadDemandsByGOR"(year, gor_1, gor_2, scenario_id, "demand_trips")
SELECT year, gor1, gor2, scenario_id, 0.5*2*SUM(pcu_total)FROM
((SELECT gor1_id as gor1, gor2_id as gor2, pcu_total, year, scenario_id FROM "TR_O_RoadOutputFlows")
UNION ALL
(SELECT gor2_id as gor1, gor1_id as gor2, pcu_total, year, scenario_id FROM "TR_O_RoadOutputFlows")) AS tabelle
GROUP BY gor1, gor2, year, scenario_id;

