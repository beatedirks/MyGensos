'''
@last updated 07/11/2017
@author: Beate Dirks, Matt Ives

______________________________________________________________________________________

Infrastructure System Class - Data management structure for all infrastructure asset information
--------------------------------------------------------------------------------------

Infrastructure System is the root of a hierarchical object structure that aims to map real dependencies of infrastructure asset information into an object structure.
It tracks all infrastructure asset related information, such as capacities, installation dates, costs etc. throughout the simulation process.
It also contains functions to translate the infrastructure asset information into the "extended network" structure, wich is being used to run the optimization steps of the simulation.  

'''

import FlowNetwork as FloNet # extended network class file
import copy # for deep-copying objects
import pyodbc # database access
import DemandFunctions as DemFun
import ExecuteSQL as ESQL

__INF__ = 100000000

class InfrastructureSystem(): 
 
    def __init__(self, start_year, modelrun_id, modelrun_params):
        ''' reads data from ISL input tables and translates them into respective objects for the data management throughout the simulation'''

        # opens the database connection
        #cnxn = pyodbc.connect('Driver={PostgreSQL ODBC Driver(ANSI)};DSN=PostgreSQL30;Server=localhost;Port=5432;Database=infrastructuresystem;UId=postgres;Password=Bubbles33@cmp;')
        cnxn = pyodbc.connect('Driver={PostgreSQL ODBC Driver(ANSI)};DSN=infrastructuresystem;Server=localhost;Port=5432;Database=infrastructuresystem;UId=postgres;Password=P0stgr3s;')
        self.start_year = start_year

        self.spatial_network = {} # dictionary of the regions for each submodel: e.g. self.spatial_network[submodel][region] = spatial node object
        self.region_itter = {} # dictionary of the itteration lists for regions in each submodel: e.g. self.region_itter[submodel] = list of region objects of this submodel
        self.add_regions('"ISL_I_NetworkRegions"', modelrun_id,  cnxn)

        # creates the distribution networks (dictionary) and their transmission arcs and a respective itteration list
        self.distribution_networks = {} # dictionary of all distribution networks: e.g. self.distribution_networks[submodel][dn].transmission_arcs[arc.id] = arc object
        self.arc_itter = [] # lists of all arc objects in all distribution networks for itteration 
        self.add_distribution_networks('"ISL_I_NetworkArcs"', modelrun_id,  cnxn, modelrun_params)

        # create a itteration of the assets in the network for easy access to data
        self.generation_asset_itter = [] # # lists of all generation asset objects in all distribution networks for itteration 
        # load the generation assets 
        self.add_generation_assets('"ISL_I_GenerationAssets"', modelrun_id, cnxn, modelrun_params)        

        # creates the set_of_key_services and the list of keyservices
        self.key_services = {} # dictionary of all keyservices, e.g. self.key_services[ks] = keyservice_object with details about supply networks stored as:
                               # self.key_services[ks].list_of_supply_networks[supply_network] = (runcost, epi, comf_name)
        self.add_keyservices('"ISL_I_KeyServices"', modelrun_id, cnxn)
        
        #adds the interdependencies amongst and within submodels
        # interdependencies are stored with the causing object, e.g. gen_asset.interdependencies.append(interdependency) or arc.interdependencies.append(interdependency) 
        self.add_interdependencies('"ISL_I_Interdependencies"', modelrun_id, cnxn)

        #close database connection
        cnxn.close()

        # inititalize the capacities of all infrastructure assets
        self.update_current_capacities(self.start_year)


    def add_regions(self, tablename, modelrun_id,  cnxn):
        regions = ESQL.execute_SQL('SELECT submodel, regionname FROM "ISL_I_NetworkRegions" WHERE modelrun_id = ' + str(modelrun_id) + 'order by id', [], [], cnxn)
        for new_region in regions:
            [submodel, name] = new_region
            if submodel not in self.spatial_network:
                self.spatial_network[submodel] = {}
            self.spatial_network[submodel][str(name)] = SpatialNode(name)
        for submodel in self.spatial_network:
            self.region_itter[submodel] = [self.spatial_network[submodel][region] for region in self.spatial_network[submodel]]
  
    def add_distribution_networks(self, tablename, modelrun_id, cnxn, modelrun_params):
        arc_id = 1 # arc_id is a unique id issued in IS 
        # load all the arcs from the database for this modelrun
        arcs = ESQL.execute_SQL('SELECT * FROM ' + tablename + ' WHERE modelrun_id = ' + str(modelrun_id)+ 'order by id', [], [], cnxn)
        # loop through the list of arcs and add them to the distribution_network for each submodel
        for new_arc in arcs:
            [tableid, cORt, submodel, dn, origin, destination, asset_name, maxcap, cap_ceiling, instdate, instd, maxlt, capex, rc, epi, com_type, modelrun_id] = new_arc
            # if submodel doesn't exist yet then add it to the distribution_networks (e.g. Energy, Trasport)
            if submodel not in self.distribution_networks:
                self.distribution_networks[submodel] = {}
            # if a distribution network doesn't exist yet then add it to the distribution_networks (e.g. Electricity, Gas, Road, Rail)
            if dn not in self.distribution_networks[submodel]: # if this network does not yet exist: create network
                self.distribution_networks[submodel][dn] = DistributionNetwork(cORt, submodel, dn)
                #self.distributionnetworks[submodel].append(dn)
            # create and add arc to respective network
            # now add the arc to IS, unless, it is an optional asset in a no-build modelrun
            if modelrun_params.no_build == 1 and instdate == 100000000: # checking whether we are in a no-build modelrun and whether it is an optional asset
                pass
            else: # in all other cases add the asset to IS
                arc = Arc(arc_id, cORt, submodel, dn, origin, destination, asset_name, maxcap, cap_ceiling, instdate, instd, maxlt, capex, rc, epi, com_type)
                self.distribution_networks[submodel][dn].transmission_arcs[arc.id] = arc
                self.arc_itter.append(arc)
                arc_id += 1
                
    def add_generation_assets(self, tablename, modelrun_id, cnxn, modelrun_params):
        asset_id = 1 # asset_id is a unique id issued in IS
        theSQL = "SELECT dn, capex, instduration, maxlifetime, maxcap, rampspeed, runcostperunit, instdate, asset_name, epi, comtype, submodel, cap_ceiling, region, asset_type FROM " + tablename + ' WHERE modelrun_id = ' + str(modelrun_id) + ' order by id'
        gen_assets = ESQL.execute_SQL(theSQL, [], [], cnxn)
        for new_ga in gen_assets:
            [dn, capex, instd, maxlt, maxcap, rs, rc, instdate, asset_name, epi, com_type, submodel, cap_ceiling, region, asset_type] = new_ga
            if modelrun_params.no_build == 1 and instdate == 100000000: # checking whether we are in a no-build modelrun and whether it is an optional asset
                pass
            else: # in all other cases add the asset to IS
                asset_object = GenerationAsset(asset_id, submodel, dn, region, asset_name, instd, maxlt, instdate, maxcap, cap_ceiling, rs, capex, rc, epi, com_type, asset_type)
                self.spatial_network[submodel][str(region)].generation_assets[asset_object.id] = asset_object 
                self.generation_asset_itter.append(asset_object) 
                asset_id += 1  

    def add_keyservices(self, tablename, modelrun_id, cnxn):
        keyservices = ESQL.execute_SQL("select * from " + tablename + ' WHERE modelrun_id = ' + str(modelrun_id)+ 'order by id', [], [], cnxn)
        for new_keyservice in keyservices:
            [table_id, ks, kstype, supply_network, runcost, epi, comf_name, submodel, modelrun_id] = new_keyservice
            if ks in self.key_services:
                self.key_services[ks].list_of_supply_networks[supply_network] = (runcost, epi, comf_name)
            else:
                keyservice_object = KeyService(ks, kstype, submodel)
                self.key_services[ks] = keyservice_object
                self.key_services[ks].list_of_supply_networks[supply_network] = (runcost, epi, comf_name)

    def add_interdependencies(self, tablename, modelrun_id,  cnxn):
        new_interdependencies = ESQL.execute_SQL("select * from " + tablename + ' WHERE modelrun_id = ' + str(modelrun_id) + 'order by id', [], [], cnxn)
        for new_interdependency in new_interdependencies:
            [id, intdp_type, caus_subm, caus_netw, caus_ass_type, caus_ass_reg1, caus_ass_reg2, caus_ass_name, aff_asset_type, aff_subm, aff_netw_or_keys, conversion_factor, aff_reg1, aff_reg2, aff_ass_name, max_cap, modelrun_id] = new_interdependency
            #TODO - Use a more permanent solution. This try/except is for the no_build strategy 
            # it is necessary to catch errors from interdependencies that don't have an option to meet demand 
            try:
                if intdp_type == 'dir': # find type of keyservice: Commodity or Transport
                    affCorT = self.key_services[aff_netw_or_keys].kstype
                else:  # find type of submodel: Commodity or Transport
                    affCorT = self.distribution_networks[aff_subm][aff_netw_or_keys].dntype
                if aff_asset_type == 'gen':
                    aff_ass_name_in_IS = [gen_asset.id for gen_asset in self.generation_asset_itter if  gen_asset.asset_name == aff_ass_name][0]  
                elif aff_asset_type == 'dist':
                    aff_ass_name_in_IS = [arc.id for arc in self.arc_itter if  arc.asset_name == aff_ass_name][0] 
                else:
                    aff_ass_name_in_IS = None
                interdependency = (intdp_type, aff_asset_type, aff_subm, aff_netw_or_keys, aff_reg1, aff_reg2, aff_ass_name_in_IS, conversion_factor, max_cap, affCorT)
                if caus_ass_type == 'gen': # commodity generation asset causes the interdependency
                    gen_asset =  [gen_asset for gen_asset in self.generation_asset_itter if  gen_asset.asset_name == caus_ass_name][0]  
                    gen_asset.interdependencies.append(interdependency)
                elif caus_ass_type == 'dist': # transmission arc interdependency
                    arc = [arc for arc in self.arc_itter if  arc.asset_name == caus_ass_name][0]  
                    arc.interdependencies.append(interdependency)  
            except:
                pass  
                

### functions used during the simulation ###

    def derive_demands_and_generate_extended_network(self, modelrun_id, cnxn, global_strategy, global_scenario, local_strategies, modelrun_params, year):
        ''' derive demands for all keyservies via inquiry to the submodels; in accordance to the info stored in the IS objects generate the extended network '''
        # derive demands and create respective edges for extended network       
        for ks in self.key_services:
            self.key_services[ks].generate_edges_for_ExtNet(self, year, global_strategy, global_scenario, local_strategies, modelrun_id, cnxn)
        # distribution network arcs + their interdependencies
        for arc in self.arc_itter:
            arc.generate_ExtNet_edge(year, global_strategy, global_scenario, modelrun_id, cnxn) 
        # generation assets + their interdependencies
        for gen_asset in self.generation_asset_itter:
            gen_asset.generate_edges_for_ExtNet(self, year, global_strategy, global_scenario, local_strategies, modelrun_id, cnxn) 
        # generate and return extended network
        return FloNet.FlowNetwork('"ISL_IO_ExtNet_Edges"', '"ISL_IO_ExtNet_Interdependencies"', year, modelrun_id, global_strategy.metric_weight, modelrun_params.no_build)                

    def time_development(self, year, scenario):
        ''' implement time evolution (currently only updating asset capacities according to investment decisions and natural asset ageing) '''
        self.update_current_capacities(year)
   
    def update_current_capacities(self, year):
        ''' update the capacities for all infrastructure assets to the current year in the simulation '''
        for genasset in self.generation_asset_itter:
            genasset.update_current_capacity(year)
        for arc in self.arc_itter:
            arc.update_current_capacity(year)
    
    def schedule_and_initialise(self, investment_list, forecast_time_span, year):
        ''' if investments were found necessary in the extended network algorithm, scheduling of the investments is performed here in IS   '''
        projects = {}
        total_budget = 0
        schedule_time_span = forecast_time_span - 2 # assets need to be installed in time for usage
        for asset in investment_list:
            if asset[0] == 'G': # generation asset
                gen_asset =  [gen_asset for gen_asset in self.generation_asset_itter if  gen_asset.id == asset][0]            
                if gen_asset.installation_date == __INF__: # asset not scheduled for installation yet, then...
                    total_budget += gen_asset.capex
                    annual_installation_cost = gen_asset.capex/gen_asset.instd
                    projects[gen_asset.id] = [gen_asset, gen_asset.instd, annual_installation_cost, -1] 
            elif asset[0] == 'A': # transmission arc
                arc = [arc for arc in self.arc_itter if  arc.id == asset][0]    
                if arc.installation_date == __INF__:
                    total_budget += arc.capex
                    annual_installation_cost = arc.capex/arc.instd
                    projects[arc.id] = [arc, arc.instd, annual_installation_cost, -1]
        budget = [1.0*total_budget/schedule_time_span for i in range(schedule_time_span)]
        if projects != {}:
            not_scheduled = True
            while not_scheduled:
                schedule = self.find_schedule(budget, projects, schedule_time_span)
                if schedule == {}:
                    budget = [0.1*b for b in budget]
                else: 
                    for project in schedule:
                        asset = schedule[project][0]
                        asset.installation_date = year + schedule[project][3]
                        asset.scheduled_in = year
                        print(asset.asset_name + ' (' + asset.id + ') in dn ' + asset.dn + ' to be built by ' + str(year + schedule[project][3]) )
                    not_scheduled = False
            
    def find_schedule(self, budget, projects, time_span):
        ''' search algorithm to schedule all those assets that were found necessary to install in the future x years, such that an average annual budget is not exceeded '''
        all_scheduled = True
        for project in projects:
            if projects[project][3] < 0:
                all_scheduled = False
        if all_scheduled:
            return projects
        else:
            for project in projects:
                [asset, duration, ann_cost, inst_date] = projects[project]
                if inst_date < 0: # not scheduled yet
                    for i in range(time_span - duration + 1):
                        project_schedule = [0 for y in range(time_span)]
                        for j in range(duration):
                            project_schedule[i+j] = int(ann_cost)
                        remaining_budget = [0 for y in range(time_span)]
                        for k in range(time_span):
                            remaining_budget[k] = budget[k] - project_schedule[k]
                        if remaining_budget >= [0 for y in range(time_span)]:
                            updated_projects = projects
                            updated_projects[project][3] = i + duration # update installation date of the current project
                            print project + ' was scheduled to be installed in year ' + str(i+duration)
                            schedule = self.find_schedule(remaining_budget, updated_projects, time_span)
                            if schedule != None:
                                return schedule
                            else:
                                print 'error'

    def document_built_assets(self, cnxn, modelrun_id):
        ''' document the installation of all assets, that were scheduled and built during a modelrun in the "ISL_O_...." tables '''
        start_year = self.start_year
        sqote = "'"
        for gen_asset in self.generation_asset_itter:
            if gen_asset.scheduled_in > 0 and gen_asset.installation_date < 100000000:
                theSQL = 'INSERT INTO "ISL_O_BuiltAssets_Generation"(modelrun_id, installed_by_year, submodel, network, region, asset_index, capacity, asset_name, scheduled_in, asset_type) VALUES ( \
                ' + str(modelrun_id) + ', ' +  str(gen_asset.installation_date) + ', ' + sqote + str(gen_asset.submodel) + sqote + ', ' + sqote + str(gen_asset.dn) + sqote + ', \
                ' + str(gen_asset.region) + ', ' + sqote + str(gen_asset.id) + sqote + ', ' + str(gen_asset.maxcap) + ', ' + sqote + str(gen_asset.asset_name) + sqote + ', \
                ' + sqote + str(gen_asset.scheduled_in) + sqote + ', ' + sqote + str(gen_asset.asset_type) + sqote +  ')'
                ESQL.execute_SQL(theSQL, [], [], cnxn) 
        for arc_obj in self.arc_itter:
            if arc_obj.scheduled_in > 0 and arc_obj.installation_date < 100000000:
                theSQL = 'INSERT INTO "ISL_O_BuiltAssets_Transmission"(modelrun_id, installed_by_year, submodel, network, origin, destination, capacity, asset_id, asset_name, scheduled_in) VALUES ( \
                ' + str(modelrun_id) + ', ' +  str(arc_obj.installation_date) + ', ' + sqote + str(arc_obj.submodel) + sqote + ', ' + sqote + str(arc_obj.dn) + sqote + ', \
                ' + sqote + str(arc_obj.origin)  + sqote + ', '  + sqote + str(arc_obj.destination)  + sqote + ', ' + str(arc_obj.maxcap) + ', '  + sqote + str(arc_obj.id)  + sqote + ', \
                ' + sqote + str(arc_obj.asset_name)  + sqote  + ', '  + sqote + str(arc_obj.scheduled_in)  + sqote + ')'
                ESQL.execute_SQL(theSQL, [], [], cnxn)               

class Project():
    def __init__(self, asset, duration, ann_cost, inst_date):
        ''' object that tracks all info regarding an infrastructure asset installation project '''
        self.asset = asset
        self.duration = int(duration)
        self.ann_cost = int(ann_cost)
        self.inst_date = int(inst_date)

### definitions of infrastructure object classes ###
                               
class SpatialNode():
    def __init__(self, name):
        self.name = str(name)
        self.generation_assets = {}
       
class GenerationAsset():
    def __init__(self, genass_id, submodel, dn, region, asset_name, instd, maxlt, instdate, maxcap, cap_ceiling, rs, capex, rc, epi, com_type, asset_type):
        self.id = 'GA' + str(genass_id) # used to uniquely identify this generation asset in IS + USED AS NODE-TERMINAL IN FLOW NETWORK!!!
        self.asset_name = asset_name # asset name as used by infrastructure planner
        self.ExtNet_identifier = 'C_G_' + submodel + '_' + dn + '_' + str(region) + '_' + self.id
        self.submodel = submodel
        self.dn = dn 
        self.region = str(region)
        self.asset_type = asset_type

        self.instd = int(instd) # installation duration in years
        self.maxlt = int(maxlt) # maximum lifetime in years
        self.installation_date = int(instdate)
        self.scheduled_in = 0 # year in which the asset got scheduled to be built, default 0 
        self.maxcap = int(maxcap) # maximum generation capacity
        self.current_capacity = 0 
        self.cap_ceiling = cap_ceiling
        #self.rs = int(rs) # maximum ramp speed 

        self.capex = int(capex) # total installation cost
        self.rc = int(rc) # running cost per supply unit
        self.fc = int(1.0*self.capex/self.maxlt) # fixcost 
        self.epi = epi
        self.com_type = com_type

        self.interdependencies = []
     
    def metric(self, scenario):
        comfactor_name = self.com_type + '_comfactor'
        exec 'comfactor = scenario.' + comfactor_name
        # TODO - might want to change this so that it doesn't include planned
        if self.installation_date < __INF__: # if asset already existing or planned to be installed, capex shouldn't be accounted for anymore, since it is an unavoidable cost
            fixcost = 0
        else:
            fixcost = self.fc # only if asset is still optional to be scheduled, capex should be accounted for!
        return (fixcost, self.rc, self.epi, comfactor)

           
    def update_current_capacity(self, t):
        if t >= self.installation_date and t < (self.installation_date + self.maxlt):
            self.current_capacity = self.maxcap  
        else:
            self.current_capacity = 0             

    def get_future_capacities(self, year, global_strategy):
        # planned_capacity is for testing future performance with only already existing or planned assets, 
        # planned_and_possible_capacity is for planning additional investments
        
        # asset not yet planned to be built:
        if self.installation_date == __INF__: 
            planned_capacity = 0
            planned_and_possible_capacity = self.maxcap
        # asset is already existing or has been scheduled to be built:
        else:
            # will not be built yet
            if (year + global_strategy.planning_horizon < self.installation_date):
                planned_capacity = 0
                planned_and_possible_capacity = 0
            # asset will be in use
            elif (year + global_strategy.planning_horizon >=  self.installation_date) and (year + global_strategy.planning_horizon <  self.installation_date + self.maxlt):
                planned_capacity = self.maxcap
                planned_and_possible_capacity = self.maxcap     
           # asset will be already decommissioned       
            elif (year + global_strategy.planning_horizon >=  self.installation_date + self.maxlt):
                planned_capacity = 0
                planned_and_possible_capacity = 0
            else: 
                print 'error in generation asset future capacities'
        return planned_capacity, planned_and_possible_capacity

    def generate_edges_for_ExtNet(self, IS, year, global_strategy, global_scenario, local_strategies, modelrun_id, cnxn):  
        # SOURCE EDGE : S -> GA
        source_edge_values = [('origin_val', 'S'), ('destination_val',self.ExtNet_identifier), ('curr_capacity_val',__INF__),\
                               ('planned_capacity_val',__INF__), ('planned_and_possible_capacity_val',__INF__),\
                               ('fixcost_val',0), ('runcost_val',0), ('epi_val',0),\
                               ('comfort_factor_val',0), ('cap_ceiling_val',1), ('edge_name_val', ''), ('modelrun_id_val', modelrun_id), ('year_val', year), ('asset_type_val', "")]
        ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_ExtNet_Edge.sql', [], source_edge_values, cnxn)
        planned_capacity, planned_and_possible_capacity = self.get_future_capacities(year, global_strategy)
        (fc, rc, epi, com_fac) = self.metric(global_scenario)
        # GENERATION EDGE : GA -> spatial_node
        spatial_node = 'C_N_'  + self.submodel + '_' + self.dn + '_' + self.region 
        generation_edge_values = [('origin_val',self.ExtNet_identifier), ('destination_val',spatial_node), ('curr_capacity_val',self.current_capacity),\
                               ('planned_capacity_val',planned_capacity), ('planned_and_possible_capacity_val', planned_and_possible_capacity),\
                               ('fixcost_val',fc), ('runcost_val',rc), ('epi_val',epi),\
                               ('comfort_factor_val',com_fac), ('cap_ceiling_val',self.cap_ceiling), ('edge_name_val', self.id),\
                               ('modelrun_id_val', modelrun_id), ('year_val', year), ('asset_type_val', "'" + str(self.asset_type) + "'")]
        ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_ExtNet_Edge.sql', [], generation_edge_values, cnxn)
        # INTERDEPENDENCIES
        causing_arc_source = self.ExtNet_identifier
        causing_arc_sink = spatial_node
        for interdep in self.interdependencies:
            (intdp_type, aff_type, aff_subm, aff_netw_or_keys, aff_reg1, aff_reg2, aff_ass_name, conversion_factor, max_cap, affCorT) = interdep
            if intdp_type == 'dir': # direct interdependency:= affects a ks-demand 
                if affCorT == 'C':
                    affected_arc_source = 'C_D_' + aff_subm  + '_' + aff_netw_or_keys + '_' + aff_reg1
                elif affCorT == 'T':
                    affected_arc_source = 'T_D_' +  aff_subm + '_' + aff_netw_or_keys + '_' + aff_reg1 + '_' + aff_reg2                           
                affected_arc_sink = 'T'
            elif intdp_type == 'syn' or intdp_type == 'mult': # synergy or multiuse := affects a generation (C only) or a distribution (C or T) asset
                if aff_type == 'gen':
                    affected_arc_source = 'C_G_' + aff_subm  + '_' + aff_netw_or_keys + '_' + aff_reg1+ '_' + aff_ass_name
                    affected_arc_sink = 'C_N_' + aff_subm  + '_' + aff_netw_or_keys + '_' + aff_reg1
                elif aff_type == 'dist':
                    if affCorT == 'Transport':
                        CorT = 'T'
                    elif affCorT == 'Commodity':
                        CorT = 'C'
                    affected_arc_source = CorT + '_N_' + aff_subm  + '_' + aff_netw_or_keys + '_' + aff_reg1 + '_' + aff_ass_name
                    affected_arc_sink = CorT + '_N_' + aff_subm  + '_' + aff_netw_or_keys + '_' + aff_reg2
            # add interdependency caused by generation asset
            interdependency_values = (intdp_type, causing_arc_source, causing_arc_sink, affected_arc_source, affected_arc_sink, conversion_factor, max_cap, modelrun_id, year)
            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_ExtNet_Interdependency.sql', [], [('interdependency_values', interdependency_values)], cnxn)

class DistributionNetwork():
    def __init__(self, dntype, submodel, distributionnetwork):
        self.identifier = distributionnetwork
        self.dntype = dntype
        self.submodel = submodel
        self.transmission_arcs = {}         

class Arc():
    def __init__(self, arc_id, cORt, submodel, dn, origin, destination, asset_name, maxcap, cap_ceiling, instdate, instd, maxlt, capex, rc, epi, com_type):
        self.id = 'ARC' + str(arc_id)  # used to uniquely identify this arc in IS + USED AS NODE-TERMINAL IN FLOW NETWORK!!!
        self.asset_name = asset_name # asset name as used by the infrastructure planner
         
        self.submodel = submodel
        self.dn = dn
        self.dntype = cORt
        self.origin = str(origin)
        self.destination = str(destination)
        self.ExtNet_origin = self.dntype + '_N_' + submodel + '_' + dn + '_' + self.origin + '_' + self.id
        self.ExtNet_destination = self.dntype + '_N_' + submodel + '_'  + dn + '_' + self.destination 

        self.maxcap = int(maxcap) # maximum transmission capacity of arc 
        self.current_capacity = 0
        self.cap_ceiling = cap_ceiling

        self.capex = int(capex) # annual installation costs
        self.instd = int(instd) # installation duration in years
        self.maxlt = int(maxlt) # maximum lifetime in years
        self.installation_date = int(instdate)
        self.scheduled_in = 0 # year in which the asset got scheduled to be built: 0 is default
                
        self.rc = int(rc) # running cost per transmission unit
        self.fc = int(1.0*self.capex/self.maxlt) # fixcost 
        self.epi = epi
        self.com_type = com_type

        self.interdependencies = []
     
    def metric(self, scenario):
        comfactor_name = self.com_type + '_comfactor'
        exec 'comfactor = scenario.' + comfactor_name
        if self.installation_date < __INF__: # if asset already existing or planned to be installed, capex shouldn't be accounted for anymore, since it is an unavoidable cost
            fixcost = 0
        else:
            fixcost = self.fc # only if asset is still optional to be scheduled, capex should be accounted for!
        return (fixcost, self.rc, self.epi, comfactor)
        
    def update_current_capacity(self, t):
        if t >= int(self.installation_date) and t < (int(self.installation_date) + int(self.maxlt)):
            self.current_capacity = self.maxcap
        else:
            self.current_capacity = 0
 
    def get_future_capacities(self, year, global_strategy):
        # planned_capacity is for testing future performance with only already existing or planned assets, 
        # planned_and_possible_capacity is for planning additional investments
        
        # asset not yet planned to be built:
        if self.installation_date == __INF__: 
            planned_capacity = 0
            planned_and_possible_capacity = self.maxcap
        # asset is already existing or has been scheduled to be built:
        else:
            # will not be built yet
            if (year + global_strategy.planning_horizon < self.installation_date):
                planned_capacity = 0
                planned_and_possible_capacity = 0
            # asset will be in use
            elif (year + global_strategy.planning_horizon >=  self.installation_date) and (year + global_strategy.planning_horizon <  self.installation_date + self.maxlt):
                planned_capacity = self.maxcap
                planned_and_possible_capacity = self.maxcap     
           # asset will be already decommissioned       
            elif (year + global_strategy.planning_horizon >=  self.installation_date + self.maxlt):
                planned_capacity = 0
                planned_and_possible_capacity = 0
            else: 
                print 'error in generation asset future capacities'
        return planned_capacity, planned_and_possible_capacity

    def generate_ExtNet_edge(self, year, global_strategy, global_scenario, modelrun_id, cnxn):
        planned_capacity, planned_and_possible_capacity = self.get_future_capacities(year, global_strategy)
        (fc, rc, epi, com_fac) = self.metric(global_scenario)
        # distribution network edge
        dn_edge_values = [('origin_val',self.ExtNet_origin), ('destination_val',self.ExtNet_destination), ('curr_capacity_val',self.current_capacity),\
                               ('planned_capacity_val',planned_capacity), ('planned_and_possible_capacity_val',planned_and_possible_capacity),\
                               ('fixcost_val',fc), ('runcost_val',rc), ('epi_val',epi),\
                               ('comfort_factor_val',com_fac), ('cap_ceiling_val',self.cap_ceiling), ('edge_name_val', self.id), ('modelrun_id_val', modelrun_id), ('year_val', year), ('asset_type_val', "") ]
        ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_ExtNet_Edge.sql', [], dn_edge_values, cnxn)
        # interdependencies
        causing_arc_source = self.ExtNet_origin
        causing_arc_sink = self.ExtNet_destination
        for interdep in self.interdependencies:
            (intdp_type, aff_asset_type, aff_subm, aff_netw_or_keys, aff_reg1, aff_reg2, aff_ass_name, conversion_factor, max_cap, affCorT) = interdep
            if intdp_type == 'dir': # direct interdependency:= affects a ks-demand 
                if affCorT == 'C':
                    affected_arc_source = 'C_D_' + aff_subm  + '_' + aff_netw_or_keys + '_' + aff_reg1 
                elif affCorT == 'T':
                    affected_arc_source = 'T_D_' +  aff_subm + '_' + aff_netw_or_keys + '_' + aff_reg1 + '_' + aff_reg2                        
                affected_arc_sink = 'T'
            elif intdp_type == 'syn' or intdp_type == 'mult': # synergy or multiuse
                if aff_asset_type == 'gen':
                    affected_arc_source = 'C_G_' + aff_subm  + '_' + aff_netw_or_keys + '_' + aff_reg1+ '_' + aff_ass_name
                    affected_arc_sink = 'C_N_' + aff_subm  + '_' + aff_netw_or_keys + '_' + aff_reg1
                elif aff_asset_type == 'dist':
                    affected_arc_source = affCorT + '_N_' + aff_subm  + '_' + aff_netw_or_keys + '_' + aff_reg1 + '_' + aff_ass_name
                    affected_arc_sink = affCorT + '_N_' + aff_subm  + '_' + aff_netw_or_keys + '_' + aff_reg2
                max_cap = int(max_cap)
            # add interdependency caused by generation asset
            interdependency_values = (intdp_type, causing_arc_source, causing_arc_sink, affected_arc_source, affected_arc_sink, conversion_factor, max_cap, modelrun_id, year)
            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_ExtNet_Interdependency.sql', [], [('interdependency_values', interdependency_values)], cnxn)
  
class KeyService():
    def __init__(self, key_service, kstype, submodel):
        self.name = key_service
        self.submodel = submodel
        self.kstype = kstype
        self.list_of_supply_networks = {}
        
    def derive_demand(self, submodel, region, year, global_scenario, local_strategies, cnxn):
        function = DemFun.demand_function(self.name)
        return function(submodel, region, year, global_scenario, local_strategies, cnxn)

    def generate_edges_for_ExtNet(self, IS, year, global_strategy, global_scenario, local_strategies, modelrun_id, cnxn):
        if self.kstype == 'C':
            for region in IS.region_itter[self.submodel]:
                demand = self.derive_demand(self.submodel, region.name, year, global_scenario, local_strategies, cnxn)
                forecast_demand = self.derive_demand(self.submodel, region.name, year+global_strategy.planning_horizon, global_scenario, local_strategies, cnxn)
                if (demand != None) and (forecast_demand != None):
                    dem_ident = str(self.kstype + '_D_' + self.submodel + '_' + self.name + '_' + region.name)
                    demand_edge_values = [('origin_val',dem_ident), ('destination_val','T'), ('curr_capacity_val',demand),\
                                   ('planned_capacity_val',forecast_demand), ('planned_and_possible_capacity_val',forecast_demand),\
                                   ('fixcost_val',0), ('runcost_val',0), ('epi_val',0),\
                                   ('comfort_factor_val',0), ('cap_ceiling_val',1), ('edge_name_val', ''), ('modelrun_id_val', modelrun_id), ('year_val', year), ('asset_type_val', "")]
                    ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_ExtNet_Edge.sql', [], demand_edge_values, cnxn)
                    for dn in self.list_of_supply_networks: # for every supplying network add edge to demand
                        sup_node = str('C_N_' + self.submodel + '_' + dn + '_' + region.name + '_0')
                        (rc, epi, name) = self.list_of_supply_networks[dn]
                        fc = 0
                        exec 'com_fac = global_scenario.' + name + '_comfactor'
                        supply_edge_values = [('origin_val',sup_node), ('destination_val',dem_ident), ('curr_capacity_val',__INF__),\
                                   ('planned_capacity_val',__INF__), ('planned_and_possible_capacity_val',__INF__),\
                                   ('fixcost_val',fc), ('runcost_val',rc), ('epi_val',epi),\
                                   ('comfort_factor_val',com_fac), ('cap_ceiling_val',1), ('edge_name_val', ''), ('modelrun_id_val', modelrun_id), ('year_val', year), ('asset_type_val', "")]
                        ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_ExtNet_Edge.sql', [], supply_edge_values, cnxn)
        elif self.kstype == 'T':
            for origin in IS.region_itter[self.submodel]:
                for destination in IS.region_itter[self.submodel]:
                    if origin == destination:
                        continue
                    demand = self.derive_demand(self.submodel, (origin.name, destination.name), year, global_scenario, local_strategies, cnxn)
                    forecast_demand = self.derive_demand(self.submodel, (origin.name, destination.name), year+global_strategy.planning_horizon, global_scenario, local_strategies, cnxn)
                    if (demand != None) and (forecast_demand != None): 
                        dem_node = str(self.kstype) + '_D_' + str(self.submodel) + '_' + (self.name) + '_' + str(origin.name) + '_' + str(destination.name) 
                        demand_edge_values = [('origin_val',dem_node), ('destination_val','T'), ('curr_capacity_val',demand),\
                               ('planned_capacity_val',forecast_demand), ('planned_and_possible_capacity_val',forecast_demand),\
                               ('fixcost_val',0), ('runcost_val',0), ('epi_val',0),\
                               ('comfort_factor_val',0), ('cap_ceiling_val',1), ('edge_name_val', ''), ('modelrun_id_val', modelrun_id), ('year_val', year), ('asset_type_val', "")]
                        ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_ExtNet_Edge.sql', [], demand_edge_values, cnxn)
                        sup_node = 'T_G_' + dem_node[4:]
                        source_edge_values = [('origin_val','S'), ('destination_val',sup_node), ('curr_capacity_val',__INF__),\
                               ('planned_capacity_val',__INF__), ('planned_and_possible_capacity_val',__INF__),\
                               ('fixcost_val',0), ('runcost_val',0), ('epi_val',0),\
                               ('comfort_factor_val',0), ('cap_ceiling_val',1), ('edge_name_val', ''), ('modelrun_id_val', modelrun_id), ('year_val', year), ('asset_type_val', "")]
                        ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_ExtNet_Edge.sql', [], source_edge_values, cnxn)
                        for dn in self.list_of_supply_networks: # for every supplying network add edge to demand
                            (rc, epi, name) = self.list_of_supply_networks[dn]
                            fc = 0
                            exec 'com_fac = global_scenario.' + name + '_comfactor'
                            edge_destination = str('T_N_'+ str(self.submodel) + '_'+ dn +'_'+origin.name)
                            generation_edge_values = [('origin_val',sup_node), ('destination_val',edge_destination), ('curr_capacity_val',__INF__),\
                               ('planned_capacity_val',__INF__), ('planned_and_possible_capacity_val',__INF__),\
                               ('fixcost_val',0), ('runcost_val',0), ('epi_val',0),\
                               ('comfort_factor_val',0), ('cap_ceiling_val',1), ('edge_name_val', ''), ('modelrun_id_val', modelrun_id), ('year_val', year), ('asset_type_val', "")]
                            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_ExtNet_Edge.sql', [], generation_edge_values, cnxn)
                            edge_origin = str('T_N_'+ self.submodel + '_'+ dn +'_'+ destination.name + '_0')
                            supply_edge_values = [('origin_val',edge_origin), ('destination_val',dem_node), ('curr_capacity_val',__INF__),\
                               ('planned_capacity_val',__INF__), ('planned_and_possible_capacity_val',__INF__),\
                               ('fixcost_val',fc), ('runcost_val',rc), ('epi_val',epi),\
                               ('comfort_factor_val',com_fac), ('cap_ceiling_val',1), ('edge_name_val', ''), ('modelrun_id_val', modelrun_id), ('year_val', year), ('asset_type_val', "")]
                            ESQL.execute_SQL_script('SQLscripts\ESQL_INSERT_ISL_I_ExtNet_Edge.sql', [], supply_edge_values, cnxn)  


      


            

