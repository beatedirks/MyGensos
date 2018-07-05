
-- start query --
SELECT modelrun_id, total_demand, total_supply, total_supply/total_demand as percentage_of_supply
FROM (
SELECT modelrun_id, sum(demand_value) as total_demand, sum(supply) as total_supply
FROM "ISL_IO_FinalFlows_DemandFulfillments"
WHERE modelrun_id IN modelrun_ids_val and simulation_year = year_val and current_forecast = 'current' and keyservice = keyservice_val
GROUP BY modelrun_id) AS alias
ORDER BY modelrun_id

SELECT modelrun_id