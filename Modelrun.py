'''
@last updated 07/11/2017
@author: Beate Dirks, Matt Ives

______________________________________________________________________________________

Main Functions for Running the Simulation
--------------------------------------------------------------------------------------

#READ_ME - For details about the CONCEPT of the simulation and details about the optimization algorithm, please refer to our publication (cf. #?)

#DOC - OVERVIEW OF THE IMPLEMENTATION OF THE SIMULATION:

For each modelrun the following steps are executed:
0) Initially the database will be cleared from any remaining modelrun data of respective modelrun_id. 
1) Following this the functions of Modelrun.py call a series of SQL scripts (in Modelrun.aggregate_and_load_submodel_data_into_input_tables()), to read in 
   case-study specific data about all the submodels. These data are imported into the generic input tables "ISL_I_...". Modelrun specific variables are also read into 
   respective objects.
        PLEASE NOTE: The SQL scripts that read-in the data are SPECIFIC to the individual case-study, i.e the respective data delivered by external partners. They have 
        to therefore be generated specifically for each case study and Modelrun.aggregate_and_load_submodel_data_into_input_tables() has to be altered accordingly. 
        (#UPGRADE: outsource contents of aggregate_and_load_submodel_data_into_input_tables into separate function per case-study (similar to demand functions), and
        call aggregate_and_load_submodel_data_into_input_tables with name of case-study as argument.)
2) In Modelrun.run_simulation() the generic infrastructure data from the "ISL_I_..." is translatted into a hierarchical object structure, called the IS (for 
   infrastructure system). The IS is the infrastructure data management structure that is used throughout the modelrun to tracks all changes to infrastructure assets, e.g. 
   changes in installation date, if an asset get's scheduled for construction.
3) For each time-step in the simulation, the function IS.derive_demands_and_generate_extended_network() translates the infrastructure asset data and information
   about keyservice demands into a generic network structure called the "extended network" (ExtNet) - the network which hosts the infrastructure resource allocation algorithm.
4) Within Modelrun.run_simulation() the simulation is operated according to the given global strategy, by calling functions of the IS and the ExtNet. In the current 
   implementation (which could be altered to be more generic #UPGRADE), infrastructure resource allocation is optimized and evaluated via ExtNet.test_performance().
   Based on the performance parameters returned by this function, the global strategy evaluates what action to take with regards to any necessary infrastructure 
   planning via global_strategy.make_decisions(). Optionally ExtNet.forecast_necessary_investments() and IS.schedule_and_initialise() are called to look for suitable 
   infrastructure expansion options and schedule their installation.
5) At the end of each simulation time step, IS.time_development() is called to update all changes of infrastructure asset data according to the performed modelrun step.
6) Within all simulation functions and after completing all simulation time steps, intermediate and final infrastructure asset, usage and performance data will be 
   documented in various input-output "ISL_IO_..." and output "ISL_O_..." tables, that serve to provide data for analysis and the visualization tools. Please refer to 
   Modelrun_Analysis.py and Modelrun_Visulisation.py for more information on these additional modules.

'''
 
import InfrastructureSystem as InfSys
import pickle
import pyodbc
#import GlobalStrategies as GlobStrat
import Modelrun_Objects as MO
#import process_region_shapes as prs
import numpy
import ExecuteSQL as ESQL
import gc
import datetime


__INF__ = 100000000
        
#functions used in the main programme ---------------------------------------------

def aggregate_and_load_submodel_data_into_input_tables(cnxn, local_strategies, modelrun_id, model_schema_id):
    '''
    This function loads the infrastructure data required for a modelrun into the ISL input tables. This is performed in several steps. 
    The contents of this function are currently SPECIFIC FOR THE GNE CASE STUDY!!! #UPGRADE
    
    # CURRENT IMPLEMENTATION:
    # FIRST the scenario independent infrastructure asset (generation and transmission) data needs to be aggregated from its submodel region level to the required modelrun region resolution
    #   this is performed in separate SQL scripts which feed into submodel specific intermediate tables
    # SECOND we fill the ISL input tables with required data
    #   regions, keyservices and their supply options, which are accounted for in the modelrun will be loaded first
    #   based on this information asset data from the submodel intermediate tables is copied to the ISL input tables
    #   prices and potentially asset capacities then need updating according to the modelrun specific scenario
    #   finally all interdependencies specified for the modelrun need to be loaded into the ISL input tables
    
    #UPGRADE: Ideally this function would either call a generic 'jumper function', similar to the implementation of different key-service demands,
            or its components would be more generically organised. However, the actual transformation of submodel specific data into the generic 
            format has to be performed for every case study seperately anyway. 

    # PLEASE NOTE: The infrastructure data has to be in generic format, when written into the ISL_I_... tables, such that the simulation can give 
                   appropriate results. Please refer to the READ_ME/Generic_Input_Data_Format.doc for details and explanations.
                    
    '''


    cursor = cnxn.cursor()
    #TODO pull this from modelRUN TABLE

    # load submodel data: assets and networks, keyservices, demands, interdependencies
    ###### TRANSPORT #######
    if local_strategies['Transport'].strategy_id != 0: # load TR model
            
        # Aggregation of transfer asset capacities from zones into GORs has to be done only once
        # results are stored in TR_LU_Existing Rail/Road Capacities tables
        ESQL.execute_SQL_script('SQLscripts\RoadCapacitiesByGOR.sql', [], [('model_schema_id_val', model_schema_id)], cnxn) # aggregate road capacities from zones into GORs
        ESQL.execute_SQL_script('SQLscripts\RailCapacitiesByGOR.sql', [], [('model_schema_id_val', model_schema_id)], cnxn) # aggregate rail capacities from zones into GORs
            
        # Demands aggregated from zones to GORs - need to be done only once
        # results are stored in TR_LU_ Rail/Road DemandByGOR tables
        ESQL.execute_SQL_script('SQLscripts\RailDemandByGOR.sql', [], [], cnxn)
        ESQL.execute_SQL_script('SQLscripts\RoadDemandByGOR.sql', [], [], cnxn)

        # Loading submodel data into ISL_I tables
        ESQL.execute_SQL_script('SQLscripts\InterregionalTransport.sql', [], [('modelrun_id_val', modelrun_id), ('submodel_id_val', local_strategies['Transport'].input_submodelrun_id), ('model_schema_id_val', model_schema_id)], cnxn)

    ###### ENERGY #######
    if local_strategies['Energy'].strategy_id != 0: # load ED model: Electricity and Gas networks -> electricity and heat keyservices

        # Aggregation of EXISTING AND POTENTIAL ASSETS - GENERATION AND TRANSMISSION - needs to be done only once
        ESQL.execute_SQL_script('SQLscripts\ElectricitySupplyByGor.sql', [], [('model_schema_id_val', model_schema_id)], cnxn)
        ESQL.execute_SQL_script('SQLscripts\GasSupplyByGor.sql', [], [('model_schema_id_val', model_schema_id)], cnxn)

        # Loading submodel data into ISL_I tables
        ESQL.execute_SQL_script('SQLscripts\Energy.sql', [], [('submodelrun_id_val', str(local_strategies['Energy'].input_submodelrun_id)), ('modelrun_id_val', modelrun_id),('model_schema_id_val', model_schema_id)], cnxn)

    ###### WATER #######                    
    if local_strategies['Water'].strategy_id != 0: # load WS model
        cap_ceiling_generationassets = 0.9 # change
        cap_ceiling_arcs = 0.9 # change
        local_strategy_id = local_strategies['Water'].strategy_id
        water_modelrun_id = local_strategies['Water'].input_submodelrun_id
        region_level = local_strategies['Water'].region_level
        # KEY SERVICE 
        # fresh water supply in Ml/year
        list_of_values = [('ks_val', 'water'), ('kstype_val', 'C'), ('supplynw_val', 'Water'), \
                            ('rc_val', 0), ('epi_val', 0), ('comfortfactorname_val', 'water'), ('submodel_val', 'Water'), ('modelrun_id_val', modelrun_id)]
        ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_Keyservice.sql', [], list_of_values, cnxn)
        
        # Aggregate Demands into new table from Wrzs to Gors if necessary - has to be done only once
        ESQL.execute_SQL_script('SQLscripts\WaterDemandAggregationFromWrzsToGors.sql', [], [], cnxn)
        
        # REGIONS and ASSETS
        if region_level == 'GOR':
            # REGIONS (nodes)
            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_Water_Regions_GORs.sql', [], [('water_modelrun_id_val', water_modelrun_id), ('modelrun_id_val', modelrun_id)], cnxn)               
            # EXISTING INTER-GOR ARCS
            Transfers_Data = ESQL.execute_SQL('SELECT origin_id, area_id AS dest_id, startyear, startcapacity FROM "WS_LU_ExistingAssets" WHERE active=1 AND assetoption_id=3', [], [], cnxn)
            index = 0
            for (compfrom_id, compto_id, startyear, capacity) in Transfers_Data:
                #Transfer between the first WRZone in each companies list of WRZones
                #TODO - make the cost and epi dependent on distance of transfer
                [(GOR_from,)] = ESQL.execute_SQL('SELECT gor_id FROM "WS_LU_Companies" WHERE company_id = company_val', [], [('company_val', compfrom_id)], cnxn)
                [(GOR_to,)] = ESQL.execute_SQL('SELECT gor_id FROM "WS_LU_Companies" WHERE company_id = company_val', [], [('company_val', compto_id)], cnxn)
                if GOR_from != None and GOR_to != None:
                    list_of_values = [ ('cort_val', 'C'), ('dn_val', 'Water'), ('origin_val', GOR_from), ('destination_val', GOR_to), \
                                        ('maxcap_val', capacity), ('capex_val', 0), ('instduration_val', 1), ('maxlifetime_val', 1000), \
                                        ('runcostperunit_val', 5), ('instdate_val', startyear), ('epi_val', 100), ('com_type_val', 'dummy'), \
                                        ('cap_ceiling_val', cap_ceiling_arcs), ('submodel_val', 'Water'), ('asset_name_val', 'WaterExistingArc'+str(index)), ('modelrun_id_val', modelrun_id)]
                    ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_NetworkArcs.sql', [], list_of_values, cnxn)    
                    index += 1                    
            # ALLOWABLE INTER-COMPANY ARCS come from combinations in WS_I_Transfers_Allowed_Run table for each company
            Transfers_Data = ESQL.execute_SQL('SELECT origin_id, destin_id AS dest_id, capacity, costrate FROM "WS_I_Transfers_Allowed_Run" WHERE modelrun_id = ', [('modelrun_id', water_modelrun_id)], [], cnxn)
            if Transfers_Data != None:
                #Get transfer costs
                ResCost_Data = ESQL.execute_SQL('SELECT capexslope, capexintercept, opexslope, opexintercept FROM "WS_I_AssetOptions_Run" WHERE modelrun_id =  AND assetoption_id=4 ', \
                                                        [('modelrun_id', water_modelrun_id)], [], cnxn)
                (capexslope, capexintercept, opexslope, opexintercept) = ResCost_Data[0]
                index = 0
                for (compfrom_id, compto_id, tran_capacity, costrate) in Transfers_Data:  
                    tran_capacity = int(tran_capacity)
                    tran_yield = tran_capacity
                    tran_capex = int(capexintercept + capexslope * tran_capacity  * costrate) # capex * costrate is taking into account distance between origin and destination companies
                    tran_opex = int((opexintercept + opexslope * tran_capacity)/tran_yield * costrate) # opex is stored as operating costs per unit (ML) per year, costrate is to account for distance between origin and destination companies
                    #Transfer between the first WRZone in each company's list of WRZones
                    [(GOR_from,)] = ESQL.execute_SQL('SELECT gor_id FROM "WS_LU_Companies" WHERE company_id = company_val', [], [('company_val', compfrom_id)], cnxn)
                    [(GOR_to,)] = ESQL.execute_SQL('SELECT gor_id FROM "WS_LU_Companies" WHERE company_id = company_val', [], [('company_val', compto_id)], cnxn)
                    if GOR_from != None and GOR_to != None:
                        arc_name = 'WaterAllowableArc' + str(index)
                        # 16_04_23 changed inst date in this to 2000 for the sake of it ;)
                        list_of_values = [ ('cort_val', 'C'), ('dn_val', 'Water'), ('origin_val', GOR_from), ('destination_val', GOR_to), \
                                                ('maxcap_val', tran_capacity), ('capex_val', tran_capex), ('instduration_val', 1), ('maxlifetime_val', 1000), \
                                                ('runcostperunit_val', tran_opex), ('instdate_val', 2000), ('epi_val', 0), ('com_type_val', 'dummy'), \
                                                ('cap_ceiling_val', cap_ceiling_arcs), ('submodel_val', 'Water'), ('asset_name_val', arc_name), ('modelrun_id_val', modelrun_id)]
                        ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_NetworkArcs.sql', [], list_of_values, cnxn)
                        index += 1
                
            # GENERATION ASSET OPTIONS (RESERVOIRS FOR NOW)
            index = 0
            #Get reservoir costs
            ResCost_Data = ESQL.execute_SQL('SELECT capexslope, capexintercept, opexslope, opexintercept FROM "WS_I_AssetOptions_Run" WHERE modelrun_id =  AND assetoption_id=1',\
                                                [('modelrun_id', water_modelrun_id)], [], cnxn)
            (capexslope, capexintercept, opexslope, opexintercept) = ResCost_Data[0]
            #get a list of existing reservoirs and put them in the right WRZones
            WRZones_Data = ESQL.execute_SQL('SELECT wrz_id FROM "WS_I_WRZones_Run" WHERE modelrun_id = ', [('modelrun_id', water_modelrun_id)], [], cnxn)
            for (wrz_id,) in WRZones_Data:
                #use these two variable = 0 as a signal for whether a reservoir exists in the area to reduce the capacity and yield of an additional Possible Asset
                res_yield = 0 
                res_capacity = 0
                theSQL = 'SELECT startyear, startcapacity FROM "WS_LU_ExistingAssets" WHERE startcapacity>0 AND active=1 AND assetoption_id=1 AND area_id = ' + str(wrz_id)
                Res_Data = ESQL.execute_SQL(theSQL,[], [], cnxn)
                #if there is an existing asset with capacity greater than 0 then get the max yield
                if Res_Data != []:
                    capacity = int(Res_Data[0][1])
                    #get the yield for this existing asset
                    #TODO - this is only the yield for 2030 but should be based on the closest year to which decisions are being made
                    Yield_Data = ESQL.execute_SQL_script('SQLscripts\ESQL_GET_Water_Yields.sql', [], \
                                    [('modelrun_id_val', water_modelrun_id), ('wrz_id_val', wrz_id), ('capacity_val', capacity)], cnxn)
                    for [(capacity, water_yield)] in Yield_Data:
                        #Add any existing reservoirs
                        for res in Res_Data:
                            #index += 1
                            res_capacity = int(res[1])
                            res_yield = int(water_yield*365) #yields are daily
                            res_capex = int(capexintercept + capexslope * res_capacity*1000) # capex is stored as '000� per Ml so * 1000 
                            res_opex = int((opexintercept + opexslope * res_capacity)/res_yield*1000) # opex is stored as operating costs per unit of reservoir capacity in '000� per Ml so * 1000 
                            [(GOR,)] = ESQL.execute_SQL('SELECT gor_id FROM "WS_LU_WrzMappingOnGors" WHERE wrz_id = wrz_id_val', [], [('wrz_id_val', wrz_id)], cnxn)
                            list_of_values = [('region_val', GOR), ('dn_val', 'Water'), ('capex_val', res_capex), ('instduration_val', 1), ('maxlifetime_val', 1000), \
                                                ('maxcap_val', res_yield), ('rampspeed_val', 0), ('runcostperunit_val', res_opex), ('instdate_val', res[0]), \
                                                ('index_val', index), ('epi_val', 1), ('comtype_val', 'dummy'), ('submodel_val', 'Water'),\
                                                ('cap_ceiling_val', cap_ceiling_generationassets), ('asset_name_val', 'WaterExistingReservoir'+str(index)), ('modelrun_id_val', modelrun_id)]
                            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_GenerationAssets.sql', [], list_of_values, cnxn)
                            # add interdependency
                            list_of_values = [('intdp_type_val', 'dir'), ('caus_subm_val', 'Water'), ('caus_netw_val', 'Water'), ('caus_ass_type_val', 'gen'), \
                                ('caus_ass_reg1_val', str(GOR)), ('caus_ass_reg2_val', None), ('caus_ass_name_val', 'WaterExistingReservoir'+str(index)), \
                                ('aff_asset_type_val', None), ('aff_subm_val', 'Energy'), ('aff_netw_or_keys_val', 'electricity'), ('aff_reg1_val', str(GOR)), \
                                ('aff_reg2_val', None), ('aff_ass_name_val', None), ('conversion_factor_val', '0.001'), ('max_cap_val', None), ('modelrun_id_val', modelrun_id)]
                            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_Interdependencies.sql', [], list_of_values, cnxn)
                            index += 1
                #Add POSSIBLE ASSETS:
                if model_schema_id != 0:
                    #If the asset has the same area_id or an area_id of 0 then add this possible asset with an instdate of 100000000
                    theSQL = 'SELECT asset_id, name, assetoption_id, area_id, mincapacity, maxcapacity, origin_id FROM "WS_I_PossibleAssets_Run" WHERE modelrun_id =  AND active = 1 AND assetoption_id=1 AND (area_id = 0 OR area_id = area_id_2 )' 
                    Ass_Data = ESQL.execute_SQL(theSQL, [('modelrun_id', water_modelrun_id)], [('area_id_2', wrz_id)], cnxn)
                    #assetoption_id=1 - reservoirs                  
                    #try:
                    for (asset_id, name, assetoption_id, area_id, mincapacity, max_capacity, origin_id) in Ass_Data:
                        #if area_id = 0 then the asset can go anywhere otherwise only pick possible assets that go into this area
                        #only doing assetoption_id=1 (reservoirs) for now
                        if assetoption_id == 1:
                            #Get the maximum yield in 2030 given the climate scenario
                            #TODO - this is only the yield for 2030 but should be based on the closest year to which decisions are being made
                            strSQL = 'SELECT "WS_LU_FutureFlow_Yields".capacity, "WS_LU_FutureFlow_Yields".yield FROM "ISL_S_ModelRuns" INNER JOIN "WS_LU_FutureFlow_Yields" ON "ISL_S_ModelRuns".climate_id = "WS_LU_FutureFlow_Yields".climate_id WHERE (("WS_LU_FutureFlow_Yields".year)=2030) AND "ISL_S_ModelRuns".modelrun_id = ' + str(water_modelrun_id) + ' AND "WS_LU_FutureFlow_Yields".wrz_id = ' + str(wrz_id) + '  AND "WS_LU_FutureFlow_Yields".capacity = ' + str(max_capacity) 
                            Res_Data = ESQL.execute_SQL(strSQL, [], [], cnxn) 
                            #ESQL.execute_SQL_script('SQLscripts\ESQL_GET_Water_Yields2.sql', \
                                            #[('"ISL_S_ModelRuns".modelrun_id', water_modelrun_id), ('"WS_LU_FutureFlow_Yields".wrz_id', wrz_id), ('"WS_LU_FutureFlow_Yields".capacity', max_capacity)], [], cnxn)               
                            for res in Res_Data:
                                if res_yield == 0:
                                    res_yield = res[1]*365 #yields are daily
                                else:
                                    res_yield = res[1]*365 - res_yield #reduce the yield of the new plant by the yield of the old
                                #Get the minimum capacity that will achieve this yield given the climate scenario
                                #theSQL = 'SELECT Min("WS_LU_FutureFlow_Yields".capacity) AS MinOfcapacity FROM "WS_LU_FutureFlow_Yields" INNER JOIN "ISL_S_ModelRuns" ON "WS_LU_FutureFlow_Yields".climate_id = "ISL_S_ModelRuns".climate_id \
                                #        WHERE ((("WS_LU_FutureFlow_Yields".wrz_id)=' + str(wrz_id) + ') AND (("WS_LU_FutureFlow_Yields".year)=2030) AND (("WS_LU_FutureFlow_Yields".yield)<' + str(res_yield) + ')) \
                                #        GROUP BY "ISL_S_ModelRuns".modelrun_id HAVING ((("ISL_S_ModelRuns".modelrun_id)=' + str(modelrun_id) + '));'

                                #cursor4.execute(theSQL)
                                #Cap_Data = cursor4.fetchall()                        
                                #for cap in Cap_Data:
                                if res_capacity == 0:
                                    res_capacity = res[0]
                                else:
                                    res_capacity = res[0] - res_capacity #reduce the capacity of the new plant by the capacity of the existing reservoir
                                res_capex = capexintercept + capexslope * res_capacity 
                                res_opex = (opexintercept + opexslope * res_capacity)/res_yield # opex is stored as operating costs per unit (ML) per year
                                [(GOR,)] = ESQL.execute_SQL('SELECT gor_id FROM "WS_LU_WrzMappingOnGors" WHERE wrz_id = wrz_id_val', [], [('wrz_id_val', wrz_id)], cnxn)
                                list_of_values = [('region_val', GOR), ('dn_val', 'Water'), ('capex_val', int(res_capex)), ('instduration_val', 1), ('maxlifetime_val', 1000), \
                                                    ('maxcap_val', res_yield), ('rampspeed_val', 0), ('runcostperunit_val', int(res_opex)), ('instdate_val', 100000000), \
                                                    ('index_val', index), ('epi_val', 1), ('comtype_val', 'dummy'), ('submodel_val', 'Water'), \
                                                    ('cap_ceiling_val', cap_ceiling_generationassets), ('asset_name_val', 'WaterPossibleReservoir'+str(index)), ('modelrun_id_val', modelrun_id)]
                                ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_GenerationAssets.sql', [], list_of_values, cnxn)
                                index += 1
                        #else all other assetoption than the yield = the capacity and we need different capex and opex slope and intercept values
                        else:
                            res_yield = res[0]
                    #except:
                        #pass
        if region_level == 'WRZ':
            cap_ceiling_generationassets = 0.9
            cap_ceiling_arcs = 0.9

            # REGIONS (nodes): the WRZs
            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_Water_Regions_WRZs.sql', [('modelrun_id', water_modelrun_id)], [], cnxn)

            # INTRA-COMPANY ARCS come from combinations in WS_I_WRZones_Run table for each company
            Companies_Data = ESQL.execute_SQL_script('SQLscripts\ESQL_GET_Water_Companies.sql', [('modelrun_id', water_modelrun_id)], [], cnxn)
            for (company_id,) in Companies_Data:
                WRZones_Data = ESQL.execute_SQL_script('SQLscripts\ESQL_GET_Water_Regions_WRZs.sql', [('modelrun_id', water_modelrun_id), ('company_id', company_id)], [], cnxn)
                for (wrz_from,) in WRZones_Data:
                    for (wrz_to,) in WRZones_Data:
                        if wrz_from != wrz_to: # connection arcs between neighbouring WRZs - one for each direction
                            list_of_values = [ ('cort_value', 'C'), ('dn_value', 'Water'), ('origin_value', wrz_from), ('destination_value', wrz_to), \
                                                ('maxcap_value', 10000000), ('capex_value', 0), ('instduration_value', 1), ('maxlifetime_value', 1000), \
                                                ('runcostperunit_value', 1), ('instdate_value', 2000), ('epi_value', 0), ('com_type_value', 'dummy'), \
                                                ('cap_ceiling_value', cap_ceiling_arcs), ('submodel_value', 'Water')]
                            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_NetworkArcs.sql', [], list_of_values, cnxn)
                            list_of_values = [ ('cort_value', 'C'), ('dn_value', 'Water'), ('origin_value', wrz_to), ('destination_value', wrz_from), \
                                                ('maxcap_value', 10000000), ('capex_value', 0), ('instduration_value', 1), ('maxlifetime_value', 1000), \
                                                ('runcostperunit_value', 1), ('instdate_value', 2000), ('epi_value', 0), ('com_type_value', 'dummy'), \
                                                ('cap_ceiling_value', cap_ceiling_arcs), ('submodel_value', 'Water')]
                            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_NetworkArcs.sql', [], list_of_values, cnxn)
                
            # EXISTING INTER-COMPANY ARCS come from combinations in WS_LU_ExistingAssets table for each company
            Transfers_Data = ESQL.execute_SQL('SELECT wrz_id FROM "WS_I_WRZones_Run" WHERE modelrun_id = ',  [('modelrun_id', water_modelrun_id)], [], cnxn)
            for (compfrom_id, compto_id, startyear, capacity) in Transfers_Data:
                #Transfer between the first WRZone in each companies list of WRZones
                WRZones_Data = ESQL.execute_SQL('SELECT wrz_id FROM "WS_I_WRZones_Run" WHERE modelrun_id =  AND company_id =  ', \
                                                [('modelrun_id', water_modelrun_id), ('company_id', compfrom_id)], [], cnxn)
                for (wrz_from,) in WRZones_Data:
                    WRZones2_Data = ESQL.execute_SQL('SELECT wrz_id FROM "WS_I_WRZones_Run" WHERE modelrun_id =  AND company_id =  ', \
                                                [('modelrun_id', water_modelrun_id), ('company_id', compto_id)], [], cnxn)
                    if (wrz_to,) in WRZones2_Data:
                            list_of_values = [ ('cort_value', 'C'), ('dn_value', 'Water'), ('origin_value', wrz_from), ('destination_value', wrz_to), \
                                                ('maxcap_value', capacity), ('capex_value', 0), ('instduration_value', 1), ('maxlifetime_value', 1000), \
                                                ('runcostperunit_value', 5), ('instdate_value', startyear), ('epi_value', 0), ('com_type_value', 'dummy'), \
                                                ('cap_ceiling_value', cap_ceiling_arcs), ('submodel_value', 'Water')]
                            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_NetworkArcs.sql', [], list_of_values, cnxn)
                ### DODGY SECTION ABOVE...
                            
            # ALLOWABLE INTER-COMPANY ARCS come from combinations in WS_I_Transfers_Allowed_Run table for each company
            Transfers_Data = ESQL.execute_SQL_script('SELECT origin_id, destin_id AS dest_id, capacity, costrate FROM "WS_I_Transfers_Allowed_Run" WHERE modelrun_id = ', \
                                                        [('modelrun_id', water_modelrun_id)], [], cnxn)
            for transfer in Transfers_Data:
                #Get transfer costs
                ResCost_Data = ESQL.execute_SQL_script('SELECT capexslope, capexintercept, opexslope, opexintercept FROM "WS_I_AssetOptions_Run" WHERE modelrun_id =  AND assetoption_id=4 ', \
                                                        [('modelrun_id', water_modelrun_id)], [], cnxn)
                for (capexslope, capexintercept, opexslope, opexintercept) in ResCost_Data:
                    pass
                ### DODGY INDENT
                for (compfrom_id, compto_id, tran_capacity, costrate) in Transfers_Data:  
                    tran_yield = tran_capacity             
                    tran_capex = capexintercept + capexslope * tran_capacity  * costrate # capex * costrate is taking into account distance between origin and destination companies
                    tran_opex = (opexintercept + opexslope * tran_capacity)/tran_yield * costrate # opex is stored as operating costs per unit (ML) per year, costrate is to account for distance between origin and destination companies
                    #Transfer between the first WRZone in each company's list of WRZones
                    WRZones_Data = ESQL.execute_SQL('SELECT wrz_id FROM "WS_I_WRZones_Run" WHERE modelrun_id =  AND company_id =  ', \
                                                [('modelrun_id', water_modelrun_id), ('company_id', compfrom_id)], [], cnxn)
                    try:
                        #get the first wrz in the From company
                        (wrz_from,) = WRZones_Data[0]
                        WRZones_Data = ESQL.execute_SQL('SELECT wrz_id FROM "WS_I_WRZones_Run" WHERE modelrun_id =  AND company_id =  ', \
                                                [('modelrun_id', water_modelrun_id), ('company_id', compto_id)], [], cnxn)
                        try:
                            #get the first wrz in the To company
                            (wrz_to, ) = WRZones_Data[0]
                            list_of_values = [ ('cort_value', 'C'), ('dn_value', 'Water'), ('origin_value', wrz_from), ('destination_value', wrz_to), \
                                                ('maxcap_value', tran_capacity), ('capex_value', tran_capex), ('instduration_value', 1), ('maxlifetime_value', 1000), \
                                                ('runcostperunit_value', tran_opex), ('instdate_value', 100000000), ('epi_value', 0), ('com_type_value', 'dummy'), \
                                                ('cap_ceiling_value', cap_ceiling_arcs), ('submodel_value', 'Water')]
                            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_NetworkArcs.sql', [], list_of_values, cnxn)
                        except:
                            print 'error in  ALLOWABLE INTER-COMPANY ARCS - get the first wrz in the To company'
                    except:
                        print 'error in  ALLOWABLE INTER-COMPANY ARCS - get the first wrz in the From company'
                
            # GENERATION ASSET OPTIONS (RESERVOIRS FOR NOW)
            index = 0
            #Get reservoir costs
            ResCost_Data = ESQL.execute_SQL('SELECT capexslope, capexintercept, opexslope, opexintercept FROM "WS_I_AssetOptions_Run" WHERE modelrun_id =  AND assetoption_id=1',\
                                                [('modelrun_id', water_modelrun_id)], [], cnxn)
            for (capexslope, capexintercept, opexslope, opexintercept) in ResCost_Data:
                pass ### dodgy code!!!
            #get a list of existing reservoirs and put them in the right WRZones
            WRZones_Data = ESQL.execute_SQL('SELECT wrz_id FROM "WS_I_WRZones_Run" WHERE modelrun_id = ', [('modelrun_id', water_modelrun_id)], [], cnxn)
            for (wrz_id) in WRZones_Data:
                #use these two variable = 0 as a signal for whether a reservoir exists in the area to reduce the capacity and yield of an additional Possible Asset
                res_yield = 0 
                res_capacity = 0
                Res_Data = ESQL.execute_SQL('SELECT startyear, startcapacity FROM "WS_LU_ExistingAssets" WHERE startcapacity>0 AND active=1 AND assetoption_id=1 AND area_id = ', \
                                            [('area_id', wrz_id)], [], cnxn)
                #if there is an existing asset with capacity greater than 0 then get the max yield
                try:
                    for res in Res_Data:
                        capacity = res[1]
                    #get the yield for this existing asset
                    #TODO - this is only the yield for 2030 but should be based on the closest year to which decisions are being made
                    Yield_Data = ESQL.execute_SQL_script('SQLscripts\ESQL_GET_Water_Yields.sql', \
                                    [('"ISL_S_ModelRuns".modelrun_id', water_modelrun_id), ('"WS_LU_FutureFlow_Yields".wrz_id', wrz_id), ('"WS_LU_FutureFlow_Yields".capacity', capacity)], [], cnxn)
                    for (capacity, water_yield) in Yield_Data:
                        #Add any existing reservoirs
                        try:
                            for res in Res_Data:
                                #index += 1
                                res_capacity = res[1]
                                res_yield = water_yield*365 #yields are daily
                                res_capex = capexintercept + capexslope * res_capacity 
                                res_opex = (opexintercept + opexslope * res_capacity)/res_yield # opex is stored as operating costs per unit (ML) per year
                                list_of_values = [('region_val', wrz_id), ('dn_val', 'Water'), ('capex_val', res_capex), ('instduration_val', 1), ('maxlifetime_val', 1000), \
                                                    ('maxcap_val', res_yield), ('rampspeed_val', 0), ('runcostperunit_val', res_opex), ('instdate_val', res[0]), \
                                                    ('index_val', index), ('epi_val', 1), ('comtype_val', 'dummy'), ('submodel_val', 'Water'), ('cap_ceiling_val', cap_ceiling_generationassets)]
                                ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_GenerationAssets.sql', [], list_of_values, cnxn)
                                index += 1
                        except:
                            pass
                except:
                    pass
                #Add possible assets
                #If the asset has the same area_id or an area_id of 0 then add this possible asset with an instdate of 100000000
                theSQL = 'SELECT asset_id, name, assetoption_id, area_id, mincapacity, maxcapacity, origin_id FROM "WS_I_PossibleAssets_Run" WHERE modelrun_id =  AND active = 1 AND assetoption_id=1 AND (area_id = 0 OR area_id = area_id_2 )' 
                Ass_Data = ESQL.execute_SQL(theSQL, [('modelrun_id', water_modelrun_id)], [('area_id_2', wrz_id)], cnxn)
                #assetoption_id=1 - reservoirs                  
                try:
                    for (x, y, assoption_id, area_id, z, max_capacity) in Ass_Data:
                        #if area_id = 0 then the asset can go anywhere otherwise only pick possible assets that go into this area
                        #only doing assetoption_id=1 (reservoirs) for now
                        if assoption_id == 1:
                            #Get the maximum yield in 2030 given the climate scenario
                            #TODO - this is only the yield for 2030 but should be based on the closest year to which decisions are being made
                            Res_Data = ESQL.execute_SQL_script('SQLscripts\ESQL_GET_Water_Yields2', \
                                            [('"ISL_S_ModelRuns".modelrun_id', water_modelrun_id), ('"WS_LU_FutureFlow_Yields".wrz_id', wrz_id), ('"WS_LU_FutureFlow_Yields".capacity', max_capacity)], [], cnxn)               
                            for res in Res_Data:
                                if res_yield == 0:
                                    res_yield = res[1]*365 #yields are daily
                                else:
                                    res_yield = res[1]*365 - res_yield #reduce the yield of the new plant by the yield of the old
                                #Get the minimum capacity that will achieve this yield given the climate scenario
                                #theSQL = 'SELECT Min("WS_LU_FutureFlow_Yields".capacity) AS MinOfcapacity FROM "WS_LU_FutureFlow_Yields" INNER JOIN "ISL_S_ModelRuns" ON "WS_LU_FutureFlow_Yields".climate_id = "ISL_S_ModelRuns".climate_id \
                                #        WHERE ((("WS_LU_FutureFlow_Yields".wrz_id)=' + str(wrz_id) + ') AND (("WS_LU_FutureFlow_Yields".year)=2030) AND (("WS_LU_FutureFlow_Yields".yield)<' + str(res_yield) + ')) \
                                #        GROUP BY "ISL_S_ModelRuns".modelrun_id HAVING ((("ISL_S_ModelRuns".modelrun_id)=' + str(modelrun_id) + '));'

                                #cursor4.execute(theSQL)
                                #Cap_Data = cursor4.fetchall()                        
                                #for cap in Cap_Data:
                                if res_capacity == 0:
                                    res_capacity = res[0]
                                else:
                                    res_capacity = res[0] - res_capacity #reduce the capacity of the new plant by the capacity of the existing reservoir
                                res_capex = capexintercept + capexslope * res_capacity 
                                res_opex = (opexintercept + opexslope * res_capacity)/res_yield # opex is stored as operating costs per unit (ML) per year
                                list_of_values = [('region_val', wrz_id), ('dn_val', 'Water'), ('capex_val', res_capex), ('instduration_val', 1), ('maxlifetime_val', 1000), \
                                                    ('maxcap_val', res_yield), ('rampspeed_val', 0), ('runcostperunit_val', res_opex), ('instdate_val', 100000000), \
                                                    ('index_val', index), ('epi_val', 1), ('comtype_val', 'dummy'), ('submodel_val', 'Water'), ('cap_ceiling_val', cap_ceiling_generationassets)]
                                ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_GenerationAssets.sql', [], list_of_values, cnxn)
                                index += 1
                        #else all other assetoption than the yield = the capacity and we need different capex and opex slope and intercept values
                        else:
                            res_yield = res[0]
                except:
                    pass

def run_simulation(modelrun_id, global_strategy, global_scenario, local_strategies, modelrun_params , cnxn):
    ''' runs the simulation of a given modelrun through all its simulation time steps '''
    # Create InfrastructureSystem object: __init__ automatically retrieves the data from teh "ISL_I_..." tables
    IS = InfSys.InfrastructureSystem(modelrun_params.start_year, modelrun_id, modelrun_params)
    year = modelrun_params.start_year
    performance_ok = True
    # The infrastructure performance parameter "total_margin" is time consuming to calculate, for which reason the former margins are handed over between simulation steps.
    # Its default value is zero, for the algorithm to decide how to identify the total_margin best.
    former_total_margin = 0 
    while year <= modelrun_params.end_year : 
        print 'Simulation of year ' + str(year) + ' of modelrun ' + str(modelrun_id)
        # Run a specific time step of the simulation. Retrieve the new value of the total_margin, to hand it over to the next optimization step.
        new_total_margin = simulation_step(modelrun_id, global_strategy, global_scenario, local_strategies, modelrun_params, IS, year, former_total_margin, cnxn)
        former_total_margin = new_total_margin
        year += global_strategy.planning_interval
    # document which potential infrastructure assets were scheduled to be built in the course of the simulation
    IS.document_built_assets(cnxn, modelrun_id)
    del IS

def simulation_step(modelrun_id, global_strategy, global_scenario, local_strategies, modelrun_params, IS, year, former_total_margin, cnxn):
    ''' simulate infrastructure dynamics for a given time step'''
    # translate the relevant infrastructure data and demand information into a entended network structure 
    ExtNet = IS.derive_demands_and_generate_extended_network(modelrun_id, cnxn, global_strategy, global_scenario, local_strategies, modelrun_params, year)
    # Call the resource allocation optimization routine. It match demands with available supply (in the extended network) and returns performance measures of the found optimum.
    performance = ExtNet.test_performance(former_total_margin) # (keeping track of the total margin saves computing time)
    print 'Performance_' + global_strategy.name + '_' + global_scenario.name + '_' + str(year) + " : " + str(performance)
    # investment decision making: feed performance of calculated allocation into the decision making of the global strategy
    decision = global_strategy.make_decisions(IS, performance)
    new_total_margin = performance[-1]
    # implement investment/simulation decision based on result
    if modelrun_params.no_build == 1: # in case of no-build modelrun, skip the investment search step
        pass
    elif decision == 'schedule_investment_plan':
        # Call ExtNet routine for planning infrastructure expansion investments to cater for unmet demands.
        investment_list = ExtNet.forecast_necessary_investments()
        if investment_list != []: # If any investment projects were suggested by the former routine, call the scheduling function to plan when the installation should take place.
            IS.schedule_and_initialise(investment_list, global_strategy.planning_horizon, year)
    # update all capacities of the infrastructure assets in preparation of the next simulation step
    IS.time_development(year+global_strategy.planning_interval, global_scenario)
    del ExtNet
    return new_total_margin

def clear_intermediate_tables(cnxn):
    ''' clear all intermediate tables - CLEAN UP TOOL ONLY'''
    print 'WARNING - you are about to delete input and output data of all your past modelruns'
    confirmation = raw_input('Confirm deleting all modelrun data by typing Y - otherwise press any other key to cancel the process')
    if confirmation == 'Y':
        cursor = cnxn.cursor()
        #cursor.execute('delete from SM_TEST_modelrundocumentation')
        cursor.execute('delete from "ISL_I_GenerationAssets"')
        cursor.execute('delete from "ISL_I_Interdependencies"')
        cursor.execute('delete from "ISL_I_KeyServices"')
        cursor.execute('delete from "ISL_I_NetworkArcs"')
        cursor.execute('delete from "ISL_I_NetworkRegions"')
        cursor.execute('delete from "ISL_IO_FinalFlows_DemandFulfillments"')
        cursor.execute('delete from "ISL_IO_FinalFlows_SupplyPathsByIteration"')
        cursor.execute('delete from "ISL_IO_FinalFlows_DistributionNetworks"')
        cursor.execute('delete from "ISL_IO_FinalFlows_GenerationAssets"')
        cursor.execute('delete from "ISL_IO_FinalFlows_SuppliesByNetwork"')
        cursor.execute('delete from "ISL_IO_FinalFlows_InterdependencyCapacities"')
        cursor.execute('delete from "ISL_O_BuiltAssets_Generation"')
        cursor.execute('delete from "ISL_O_BuiltAssets_Transmission"')
        cursor.execute('delete from "ISL_IO_ExtNet_Interdependencies"')
        cursor.execute('delete from "ISL_IO_ExtNet_Edges"')
        # water submodel specific outputs
        cursor.execute('delete from "ISL_O_WS_NewBuiltAssets"')
        cursor.execute('delete from "ISL_O_WS_Transfers"')
        cursor.commit()
        print 'all ISL_I, I/O, O tables have been cleared'
    else:
        print 'no data has been deleted'

def clear_specific_modelrun(cnxn, modelrun_id):
    ''' clears all ISL tables from all data of any former modelrun with identical modelrun_id'''
    #print 'WARNING - you are about to delete input and output data of the specified modelrun:' + str(modelrun_id)
    #confirmation = raw_input('Confirm deleting all the specified modelrun data by typing y - otherwise press any other key to cancel the process')
    confirmation = 'y'
    if confirmation == 'y':
        cursor = cnxn.cursor()
        cursor.execute('delete from "ISL_I_GenerationAssets" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_I_Interdependencies" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_I_KeyServices" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_I_NetworkArcs" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_I_NetworkRegions" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_IO_FinalFlows_DemandFulfillments" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_IO_FinalFlows_SupplyPathsByIteration" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_IO_FinalFlows_DistributionNetworks" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_IO_FinalFlows_GenerationAssets" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_IO_FinalFlows_SuppliesByNetwork" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_IO_FinalFlows_InterdependencyCapacities" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_O_BuiltAssets_Generation" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_O_BuiltAssets_Transmission" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_IO_ExtNet_Interdependencies" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_IO_ExtNet_Edges" where modelrun_id = ' + str(modelrun_id))
        # water submodel specific outputs
        cursor.execute('delete from "ISL_O_WS_NewBuiltAssets" where modelrun_id = ' + str(modelrun_id))
        cursor.execute('delete from "ISL_O_WS_Transfers" where modelrun_id = ' + str(modelrun_id))            
        #cursor.commit() # this is the pyodbc version
        cnxn.commit()
        #print 'all ISL_I, I/O, O tables have been cleared of the specified modelrun data'
    else:
        #print 'no data has been deleted'
        pass

def run_modelrun(cnxn, modelrun_id):
    ''' main function to run one specific modelrun - load all relevant data and fills the generic input tables; triggers the modelrun'''
    
    import datetime
    print "Model " + str(modelrun_id) + " started " + str(datetime.datetime.now())
    #Set the model run start time
    cursor = cnxn.cursor()
    #cursor.execute('UPDATE "ISL_S_ModelRuns" SET run_start_time = ? WHERE modelrun_id = ?', (str(datetime.datetime.now()), str(modelrun_id)))
   
    #clear ISL tables of modelrun data with identical modelrun id
    clear_specific_modelrun(cnxn, modelrun_id)
    
    #load modelrun data
    cursor = cnxn.cursor()
    cursor.execute('select global_strategy_id, scenario_id, submodel_portfolio_id, startyear, endyear, "Notes", model_schema_id, no_build from "ISL_S_ModelRuns" where modelrun_id = ' + str(modelrun_id))
    (global_strategy_id, global_scenario_id, submodel_portfolio_id, start_year, end_year, Notes, model_schema_id, no_build) = cursor.fetchone()
    
    # create objects that carry all modelrun parameters
    global_strategy = MO.Global_Strategy(global_strategy_id, cnxn)
    global_scenario = MO.Global_Scenario(global_scenario_id, cnxn)
    local_strategies = MO.Local_Strategies(submodel_portfolio_id, cnxn)
    modelrun_params = MO.Modelrun_Params(start_year, end_year, no_build) 
    
    # load submodel specific infrastructure information (assets and demands) from respective user provided tables, transform the data to the generic format and fill the ISL input tables accordingly
    aggregate_and_load_submodel_data_into_input_tables(cnxn, local_strategies, modelrun_id, model_schema_id)
    
    # print Notes from modelrun table
    print Notes
    
    # trigger the modelrun
    run_simulation(modelrun_id, global_strategy, global_scenario, local_strategies, modelrun_params , cnxn)

    #Set the model run end time
    cursor = cnxn.cursor()
    cursor.execute('UPDATE "ISL_S_ModelRuns" SET run_end_time = ? WHERE modelrun_id = ?' , (str(datetime.datetime.now()),str(modelrun_id)))
    cursor.commit()
    cursor.close()
    print "Model " + str(modelrun_id) + " completed " + str(datetime.datetime.now())

def run_modelruns(cnxn, list_of_modelrun_ids):
    for modelrun_id in list_of_modelrun_ids:
        gc.collect()
        run_modelrun(cnxn, modelrun_id)

