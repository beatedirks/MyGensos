'''
Created on 16 Sep 2013

@author: Beate Dirks
'''

import pyodbc
import ExecuteSQL as ESQL

def demand_function(keyservice):
    #if keyservice == 'heat':
    #    return test_heat_demand
    #elif keyservice == 'electricity':
    #    return test_elec_demand        
    #elif keyservice == 'personaltransport':
    #    return test_transport_demand
    #elif keyservice == 'gas':
    #    return test_gas_demand
    #elif keyservice == 'aircon':
    #    return test_cooling_demand
    if keyservice == 'water':
        return water_demand
    elif keyservice == 'electricity':
        return electricity_demand
    elif keyservice == 'heat':
        return heat_demand
    elif keyservice == 'transport':
        return transport_demand
    elif keyservice == 'gas':
        return gas_demand
    elif keyservice == 'localtransport':
        return localtransport_demand

def water_demand(submodel, region, year, global_scenario, local_strategies, cnxn):
    # water demand from submodel tables in units Ml/year
    #(submodel, region) = submodel_region.split('_')
    cursor = cnxn.cursor()
    #modelrun_id = local_strategies['Water'].input_submodelrun_id
    theSQL = 'SELECT demand FROM "WS_LU_WaterDemandByGor" WHERE scenario_id=' + str(global_scenario.id) + ' AND year = ' + str(year) + ' AND gor_id = ' + str(region)
    #theSQL = 'SELECT "WS_O_WRZones".totaldemand FROM "WS_O_WRZones" WHERE ((("WS_O_WRZones".modelrun_id)=' + str(modelrun_id) + ') \
    #AND (("WS_O_WRZones".wrz_id)=' + str(region) + ' AND (("WS_O_WRZones".year)='+ str(year) + ')));'
    cursor.execute(theSQL) 
    Pop_Data = cursor.fetchall()
    if Pop_Data[0][0]: 
        return int(Pop_Data[0][0])
    else:
        print 'error for water demand in region:' + str(region)
    #return 10000

def electricity_demand(submodel, region, year, global_scenario, local_strategies, cnxn):
    # in GWhrs/year
    cursor = cnxn.cursor()
   # modelrun_id = local_strategies['Energy'].input_submodelrun_id
    theSQL = 'SELECT SUM(bus_peak) FROM "EE_LU_ElectricityDemandByGOR" WHERE year = ' + str(year) + '\
             AND "GOR" = ' + str(region) + ' AND scenario_id=' + str(global_scenario.id)
    cursor.execute(theSQL) 
    Pop_Data = cursor.fetchall()
    try:
        demand = Pop_Data[0][0] # demand comes in peak power in MW
    except:
        print 'error - electricity demand for year ' + str(year) + 'not found'
    return 365*24*int(demand)/1000 # convert to GWhrs/year from MW

    #cursor = cnxn.cursor()
    #modelrun_id = local_strategies['Energy'].modelrun_id
    #theSQL = 'SELECT population FROM "GNE_LU_PopulationByGorAndScenarioAndYear" WHERE year = ' + str(year) + '\
    #         AND gor_id = ' + str(region) + ' AND scenario_id = '  + str("'") + str(global_scenario.population_scenario) + str("'")
    #cursor.execute(theSQL) 
    #Pop_Data = cursor.fetchall()
    #try:
    #    population = Pop_Data[0][0]
    #except:
    #    print 'error - population for year not found'
    #theSQL = 'SELECT "GVA" FROM "GNE_LU_GvaByGorAndScenarioAndYear" WHERE year = ' + str(year) + '\
    #         AND gor_id = ' + str(region) + ' AND scenario_id = '  + str("'") + str(global_scenario.gva_scenario) + str("'")
    #cursor.execute(theSQL) 
    #Pop_Data = cursor.fetchall()
    #try:
    #    GVA = Pop_Data[0][0]
    #except:
    #    print 'error - GVA for year not found'
    #demand = -120+1.88E-6*population + 1.54E-9*GVA # GWhrs/year
    #return int(demand)

def heat_demand(submodel, region, year, global_scenario, local_strategies, cnxn):
    #modelrun_id = local_strategies['Energy'].input_submodelrun_id
    theSQL = 'SELECT SUM(Peak_Gas) FROM "EE_LU_GasDemandByGOR" WHERE year = ' + str(year) + ' AND "GOR" = ' + str(region) + ' AND scenario_id=' + str(global_scenario.id)  
    [(gas_demand,)] = ESQL.execute_SQL(theSQL, [], [], cnxn)  # gas demand is measured in GWhrs/day
    demand = 365*gas_demand # in GWhrs/year
    return int(demand)




    #theSQL = 'SELECT population FROM "GNE_LU_PopulationByGorAndScenarioAndYear" WHERE year = ' + str(year) + '\
    #         AND gor_id = ' + str(region) + ' AND scenario_id = ' + str("'") + str(global_scenario.population_scenario) + str("'")
    #cursor.execute(theSQL) 
    #Pop_Data = cursor.fetchall()
    #try:
    #    population = Pop_Data[0][0]
    #except:
    #    print 'error - population for year not found'
    #theSQL = 'SELECT "GVA" FROM "GNE_LU_GvaByGorAndScenarioAndYear" WHERE year = ' + str(year) + '\
    #         AND gor_id = ' + str(region) + ' AND scenario_id = '  + str("'") + str(global_scenario.gva_scenario) + str("'")
    #cursor.execute(theSQL) 
    #Pop_Data = cursor.fetchall()
    #try:
    #    GVA = Pop_Data[0][0]
    #except:
    #    print 'error - GVA for year not found'
    #demand = (-145.5+6.96E-10*population + 1.05E-5*GVA) # GWhrs/year
    #return int(demand)

def gas_demand(submodel, region, year, global_scenario, local_strategies, cnxn):
    return 0
     
def transport_demand(submodel, regions, year, global_scenario, local_strategies, cnxn):
    # demand for transport is estimated by summing rail and road usage
    (origin, destination) = regions
    #modelrun_id = local_strategies['Transport'].input_submodelrun_id
    theSQL = 'SELECT "demand_trips" FROM "TR_LU_RoadDemandsByGOR" WHERE scenario_id = ' + str(global_scenario.id) + ' AND year = ' + str(year) + '\
             AND gor_1 = ' + str(origin) + 'AND gor_2 = ' + str(destination)
    try:
        [(road_demand,)] = ESQL.execute_SQL(theSQL, [], [], cnxn)  
    except:
        #print 'error? - no road demand found:' + str(origin) + ', ' + str(destination)
        pass
    theSQL = 'SELECT "demand_trips" FROM "TR_LU_RailDemandByGOR" WHERE scenario_id = ' + str(global_scenario.id) + ' AND year = ' + str(year) + '\
             AND gor_1 = ' + str(origin) + 'AND gor_2 = ' + str(destination)
    try:
        [(rail_demand,)] = ESQL.execute_SQL(theSQL, [], [], cnxn) 
    except:
        #print 'error? - no rail demand found:' + str(origin) + ', ' + str(destination)
        pass
    try:
        #print str(origin) + '->' + str(destination) + ': rail demand - ' + str(rail_demand) + ': road demand - ' + str(road_demand)
        return int(road_demand)+int(rail_demand) # 
    except:
        return None
        
    #cursor = cnxn.cursor()
    #modelrun_id = local_strategies['Transport'].modelrun_id
    #theSQL = 'SELECT population FROM "GNE_LU_PopulationByGorAndScenarioAndYear" WHERE year = ' + str(year) + '\
    #         AND gor_id = ' + str(region) + ' AND scenario_id = ' + str("'") + str(global_scenario.population_scenario) + str("'")
    #cursor.execute(theSQL) 
    #Pop_Data = cursor.fetchall()
    #try:
    #    population = Pop_Data[0][0]
    #except:
    #    print 'error - population for year not found'
    #theSQL = 'SELECT "GVA" FROM "GNE_LU_GvaByGorAndScenarioAndYear" WHERE year = ' + str(year) + '\
    #         AND gor_id = ' + str(region) + ' AND scenario_id = '  + str("'") + str(global_scenario.gva_scenario) + str("'")
    #cursor.execute(theSQL) 
    #Pop_Data = cursor.fetchall()
    #try:
    #    GVA = Pop_Data[0][0]
    #except:
    #    print 'error - GVA for year not found'
    #rail_demand = -459600000+2379*GVA  # in trips
    #road_demand = -80570000+12.28*GVA+1.739*Population # in pcu's
    #demand = rail_demand + 2*road_demand # road + rail as estimate for transport demand
    #return demand

def localtransport_demand(submodel, region, year, global_scenario, local_strategies, cnxn):
    # demand for transport is estimated by summing rail and road usage
    #modelrun_id = local_strategies['Transport'].input_submodelrun_id
    theSQL = 'SELECT "demand_trips" FROM "TR_LU_RoadDemandsByGOR" WHERE scenario_id = ' + str(global_scenario.id) + ' AND year = ' + str(year) + '\
             AND gor_1 = ' + str(region) + 'AND gor_2 = ' + str(region)
    try:
        [(road_demand,), (x,)] = ESQL.execute_SQL(theSQL, [], [], cnxn)
    except:
        print 'error? - no local road demand found:' + str(region) 
    theSQL = 'SELECT "demand_trips" FROM "TR_LU_RailDemandByGOR" WHERE scenario_id = ' + str(global_scenario.id) + ' AND year = ' + str(year) + '\
             AND gor_1 = ' + str(region) + 'AND gor_2 = ' + str(region)
    try:
        [(rail_demand,), (x,)] = ESQL.execute_SQL(theSQL, [], [], cnxn) 
    except:
        print 'error? - no local rail demand found:' + str(region) 
    try:
        return int(road_demand)+int(rail_demand) # 
    except:
        return 0






   
#def test_heat_demand(submodel_region, year, global_scenario):
#    return int(global_scenario.heat_demand_factor*test_regional_data(submodel_region, year, 'pop', global_scenario))

#def test_cooling_demand(submodel_region, year, global_scenario):
#    return int(global_scenario.cooling_demand_factor*test_regional_data(submodel_region, year, 'pop', global_scenario))
    
#def test_elec_demand(submodel_region, year, global_scenario):
#    return int(global_scenario.electricity_demand_factor*test_regional_data(submodel_region, year, 'pop', global_scenario))

#def test_transport_demand(submodel_regions, year, global_scenario):
#    (x,y) = submodel_regions
#    popx = test_regional_data(x, year, 'pop', global_scenario)
#    popy = test_regional_data(y, year, 'pop', global_scenario)
#    econx = test_regional_data(x, year, 'econ', global_scenario)
#    econy = test_regional_data(y, year, 'econ', global_scenario)
#    return int(global_scenario.transport_demand_factor*econx*econy*(popx+popy))

#def test_gas_demand(submodel_regions, year, global_scenario):
#    return 0

#def test_regional_data(submodel_region, year, variable_name, global_scenario):
#    x = {'transport_Anatolia' : {'pop' : 100, 'econ' : 50},
#         'energy_Anatolia' : {'pop' : 100, 'econ' : 50},
#         'transport_Bern' : {'pop': 50, 'econ': 20},
#         'energy_Bern' : {'pop': 50, 'econ': 20}
#         }
#    if variable_name == 'pop':
#       return x[submodel_region]['pop'] * (1 + global_scenario.pop_growth)**year
#    if variable_name == 'econ':
#       return x[submodel_region]['econ'] * (1 + global_scenario.econ_growth)**year



