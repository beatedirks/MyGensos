-- adding a demand edge for ExtNet

INSERT INTO "ISL_IO_ExtNet_Edges" (origin, destination, capacity, planned_capacity, planned_and_possible_capacity, fixcost, runcost, epi, comfort_factor, cap_ceiling, edge_name, modelrun_id, simulation_year, asset_type) 
VALUES ( origin_val, destination_val, curr_capacity_val, planned_capacity_val, planned_and_possible_capacity_val, fixcost_val, runcost_val, epi_val, comfort_factor_val, cap_ceiling_val, edge_name_val, modelrun_id_val, year_val, asset_type_val)