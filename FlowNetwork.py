'''
Created on 18/07/14 based on 02/06/14 version

includes adjustable metric
no intervals

@author: Beate Dirks with help
'''
 
import copy
import os
#import matplotlib.pyplot as plt
#import matplotlib.colors as col
#import matplotlib.figure as fig
import pyodbc
import gc
import ExecuteSQL as ESQL

__INF__ = 100000000 # constant denoting 'infinite': used for unlimited arc capacities and uninstalled asset installation dates

### class edges and class paths defining the arc and node objects for the extended network ###


class Edge(object):
    def __init__(self, installation_name, s, t, current_capacity, planned_capacity, planned_and_possible_capacity, fc, rc, epi, com, cap_ceiling, metric_weight, asset_type):
        '''
        edges are the arc objects of the extended network - they are defined via source and sink
        they do have 
        '''
        #identification
        self.installation_name = installation_name
        self.source = s
        self.sink = t

        self.asset_type = asset_type

        self.metric_weight = metric_weight
        
        # set all capacities
        self.cap_ceiling = cap_ceiling
        #self.cap = 0 # working capacity for respective optimization - dummy default 0
        #self.rem_cap = 0 # working variable for remaining capacity during allocation process - dummy default 0
        #self.orig_cap = 0 # working varialble to remember the original capacity of the object, even if it gets reduced due to metric fluctuations or multiuse interdependency - default dummy 0
        self.current_capacity = current_capacity # current capacity of existing infrastructure objects; 0 as default for not yet existing assets
        self.planned_capacity = planned_capacity # future capacity as already planned
        self.planned_and_possible_capacity = planned_and_possible_capacity # future capacity as planned + possible investment projects

        # set all metric variables
        self.metric = 0 # dummy value, to allow the generation of all paths without needing actual metric values
        self.metric_tracker = []
        self.cost_normalization = 50 # factor to balance order of magnitude average difference between cost and epi, i.e. found in comparison of total cost and total epi after a full optimization
        self.epi = float(epi) # 
        self.com = float(com)
        self.runcost = float(rc) # capacit
        self.fixcost = float(fc) # capacit 
        
        # structures for storing information on supply flows
        self.int_flow = {} # intermediate flows
        self.fin_flow = {} # final flows
        self.flow_tracker = []
     
    def initialize_capacities_and_metric(self):
        # capacity and interdependency:
        self.rem_cap = self.cap # initialise working variable 'remaining capacity'
        self.orig_cap = self.cap # initialise the edges original capacity as look up for the updating of interdependencies
        self.utilization_of_arc = 0
        self.interdep_cap = 0 # working variable to calculate interdependency induced capacity changes
        self.interdependency_basic_cap = self.cap # set start value of the interdependency capacity
        self.cap_reduction_factor = 1 # cap_reduction_factor tracks reductions in capacity of this edge, due to metric osscillations, i.e. 1 to start with
        self.interdependency_metric = 0 # default value, initial value set in initialization, actual value found during optimization
        self.intdp_metr_tracker = 0 # takes values 1: when intdp metric goes up, -1 when intdp metric goes down
        # initialize metric according to the new capacity:
        if self.orig_cap == 0: # avoid devision by 0
            self.cost = self.fixcost + self.runcost # cost of providing only this service
        else:
            self.cost = 1.0*self.fixcost/self.orig_cap + self.runcost # initial cost given by ideal cost when running at max capacity
        # resulting metric (if the metric_weight = 0 then it uses only epi, if it is 1 it only uses cost)
        self.metric = round(self.metric_weight*self.cost*self.cost_normalization + (1-self.metric_weight)*self.epi) + self.interdependency_metric  # metric = weighted sum of separate indicators + interdependency component
        self.metric_tracker.append(self.metric)
        # NOTE: interdependency metric can only be initialized in the whole network collectively, i.e. takes places in a function of flow network
        
    def total_flow_int(self):
        total_flow = 0
        for demand in self.int_flow:
            total_flow += self.int_flow[demand]
        return total_flow
    
    def total_flow_fin(self):
        total_flow = 0
        for demand in self.fin_flow:
            total_flow += self.fin_flow[demand]
        return total_flow
     
    def update_metric(self):
        # the metric can change for two reasons (1) in the planning stage the cost you give to a new asset you assume maximum capacity, this needs to be corrected depending on whether the asset is used
        # OR (2) if it is accounting for the metrics (costs) of interdependencies
        old_metric = self.metric
        total_flow = self.total_flow_fin()
        if total_flow == 0: # unused assets are as unattractive that they get maximum cost
            self.cost = float(self.fixcost)/1 + self.runcost # treat fixcost as having to be payed by one single unit of supply
        else:
            self.cost = float(self.fixcost)/total_flow + self.runcost
        self.metric = round(self.metric_weight*self.cost*self.cost_normalization + (1-self.metric_weight)*self.epi)
        self.metric += self.interdependency_metric
        # return whether metric has changed significantly or not 
        if old_metric == 0 and self.metric == 0: 
            return False # nothing changed
        elif old_metric == 0: # avoid division by 0 - check metric has changed by 20% to count as change 
            if abs(float(self.metric-old_metric)/self.metric) >= 0 and abs(float(self.metric-old_metric)/self.metric) <= 0.2:
                return False # metric has changed only marginally
            else:
                return True
        else: # now safe to divide by old_metric ;) - check metric has changed by 20% to count as change 
            if abs(float(self.metric-old_metric)/old_metric) >= 0 and abs(float(self.metric-old_metric)/old_metric) <= 0.2:
                return False # metric has changed only marginally
            else:
                if self.metric < old_metric:
                    #print 'metric decreased from ' + str(old_metric) + ' to ' + str(self.metric) + ' in edge: ' + self.source + ' -> ' + self.sink
                    pass
                elif self.metric > old_metric:
                    #print 'metric increased from ' + str(old_metric) + ' to ' + str(self.metric) + ' in edge: ' + self.source + ' -> ' + self.sink
                    pass
                return True
            
    #def reset_metric(self):
    #    if self.orig_cap == 0: # avoid division by 0
    #        self.cost = self.runcost
    #    else:
    #        self.cost = self.fixcost/float(self.orig_cap) + self.runcost # initial metric given by ideal cost when running at max capacity
    #    self.metric = round(self.metric_weight*self.cost + (1-self.metric_weight)*self.epi)
    #    self.metric += self.orig_interdependency_metric

class Path(object):
    def __init__(self, path, total_metric):
        self.path = path # list of nodes
        self.total_metric = float(total_metric) # total metric of path
        
### extended network class ###        
            
class FlowNetwork():

    def __init__(self, edge_table_name, interdep_table_name, year, modelrun_id, metric_weight, no_build):
        self.modelrun_id = modelrun_id
        self.year = year
        self.metric_weight = metric_weight
        self.no_build = no_build

        self.edges = {}
        self.edge_list = []
        self.predecessors = {} # backward adjacency list of the nodes
        self.cnxn = pyodbc.connect('Driver={PostgreSQL ODBC Driver(ANSI)};DSN=infrastructuresystem;Server=localhost;Port=5432;Database=infrastructuresystem;UId=postgres;Password=P0stgr3s;')
        self.add_edges(edge_table_name, self.cnxn, self.metric_weight)
        self.paths = {}      # one-dim dictionary listing paths for each demand in a set (length, generationnode, ..., demandnode)
        self.interdependencies = {'d': [],
                                  's': [],
                                  'm': {}}
        self.multiuse_edges = []
        self.add_interdependencies(interdep_table_name, self.cnxn)
        self.all_paths('S', 'T')
        #self.initialize_interdependent_metrics()
        pass
        
    def get_core_node(self, node):
        if node == 'S' or node == 'T' or node.split('_')[1] != 'N':
            return node
        else:  # network node - chop off terminal to retrieve predecesssors
            [cort, n, submodel, network, region, terminal] = node.split('_') 
            core_node = cort + '_' + n + '_' + submodel + '_' + network + '_' + region
            return core_node
            
    def get_predecessors(self, node):   # returns list of preceiding nodes from given node
        try:
            return self.predecessors[node]
        except:
            print 'error?  - node ' +  node + 'has no predecessor.'
    
    def get_edges(self, path):
        edges = []
        number_of_edges = len(path) - 1 
        for i in range(0,number_of_edges):
            edges.append(self.edges[path[i]][self.get_core_node(path[i+1])])
        return edges
 
    def add_edges(self, edge_tablename, cnxn, metric_weight):   # reads edges from file and adds them to neighbours and edges
        new_edges = ESQL.execute_SQL("select origin, destination, capacity, planned_capacity, planned_and_possible_capacity, fixcost, runcost, epi, comfort_factor, id, cap_ceiling, edge_name, asset_type from " \
                    + edge_tablename + " where modelrun_id = " + str(self.modelrun_id) + " and simulation_year = " + str(self.year), [], [], cnxn)
        for new_edge in new_edges:
            [origin, destination, capacity, planned_capacity, planned_and_possible_capacity, fixcost, runcost, epi, com_fac, table_id, cap_ceiling, name, asset_type] = new_edge
            edge_object = Edge(name, origin, destination, capacity, planned_capacity, planned_and_possible_capacity, fixcost, runcost, epi, com_fac, cap_ceiling, metric_weight, asset_type)
            #if not(capacity == 0 and planned_capacity == 0 and planned_and_possible_capacity == 0) or destination == 'T': # exclude useless arcs, i.e. all caps 0, unless they are a demand arc!
            self.add_edge(origin, destination, edge_object)

    def add_edge(self, origin, destination, edge):
        if origin not in self.edges.keys():
            self.edges[origin] = {}
        if destination not in self.predecessors.keys():
            self.predecessors[destination] = []
        self.edges[origin][destination] = edge
        self.edge_list.append(edge)
        self.predecessors[destination].append(origin)

    def add_interdependencies(self, interdep_tablename, cnxn):
        interdependencies = ESQL.execute_SQL("select type, causing_arc_origin, causing_arc_destination, affected_arc_origin, affected_arc_destination, conversion_factor, id, maxcap from " \
                           + interdep_tablename + " where modelrun_id = " + str(self.modelrun_id) + " and simulation_year = " + str(self.year), [], [], cnxn)
        for new_interdep in interdependencies:
           [type, causing_arc_origin, causing_arc_dest, affected_arc_origin, affected_arc_dest, conversion_factor, table_id, maxcap] = new_interdep
           if type == 'dir':
               self.interdependencies['d'].append(((causing_arc_origin, causing_arc_dest), (affected_arc_origin, affected_arc_dest), float(conversion_factor), maxcap))
           elif type == 'syn':
               self.interdependencies['s'].append(((causing_arc_origin, causing_arc_dest), (affected_arc_origin, affected_arc_dest), float(conversion_factor), maxcap))
           elif type == 'mult': # for multiuse there can be a list (i.e.more than one) affected arcs
               if str((causing_arc_origin, causing_arc_dest)) not in self.interdependencies['m'].keys():
                   self.interdependencies['m'][str((causing_arc_origin, causing_arc_dest))] = ((causing_arc_origin, causing_arc_dest), [(affected_arc_origin, affected_arc_dest, float(conversion_factor))], maxcap)
                   self.multiuse_edges.append((affected_arc_origin, affected_arc_dest))
               else: 
                   self.interdependencies['m'][str((causing_arc_origin, causing_arc_dest))][1].append((affected_arc_origin, affected_arc_dest, float(conversion_factor)))
                   self.multiuse_edges.append((affected_arc_origin, affected_arc_dest))
   
    def initialize_interdependent_metrics(self): 
        metrics_changed = True
        im = 0
        while metrics_changed:
            print 'im = ' + str(im)
            for edge in self.edge_list:
                edge.interdependency_metric = 0 # reset all interdependency metrics
            for direct_dep in self.interdependencies['d']: # find default interdependency metrics
                [(cao, cad), (aao, aad), feedbackfactor, maxcap] = direct_dep
                causing_arc = self.edges[cao][cad]
                affected_arc = self.edges[aao][aad]
                # TODO - possibly fix this 
                # This is a dirty solution to the problem of how to find a initial metric (cost) of an interdependency when you haven't yet calculated the metric (cost) of flows on that interdependent network
                #causing_arc.interdependency_metric += (self.paths[aao][0].total_metric + self.paths[aao][-1].total_metric)/2 * float(feedbackfactor) # ~ average metric of all supply options for the demand (aao)
                causing_arc.interdependency_metric += self.paths[aao][0].total_metric*float(feedbackfactor) # cheapest possible metric of all supply options for the demand (aao)
            metrics_changed = self.update_path_metrics() # update metrics to account for found interdependency metrics
            im += 1
        for edge in self.edge_list:
            edge.orig_interdependency_metric = edge.interdependency_metric # save initialized value to enable resetting metric for forecasting etc.
            edge.metric += edge.orig_interdependency_metric
        # all paths need resorting by metric after metric update
        self.resort_paths_by_metric()


### main algorithm ###

    '''## all functions dealing with paths: ##
    # paths are connecting demands with supply options
    # in all_paths these options are all evaluated through a search algorith and stored in the structure self.paths
    # in the allocation optimization, the paths metrics will change and need updating, hence the respective functions'''

    def all_paths(self, ultimate_source, ultimate_sink):
        # all nodes adjacent to the ultimate source are expected to be supply nodes
        # for all of them generate all paths to the ultimate sink 
        for demand_node in self.get_predecessors(ultimate_sink):
            self.paths[demand_node] = [] # initialize list of paths for each demand
            self.generate_paths(demand_node, [demand_node, 'T'], float(0), ultimate_source) 
#        for demand in self.paths.keys():
#            self.paths[demand] = sorted(self.paths[demand], key = lambda x: x.total_metric) # sort paths for shortest path first
        self.demands = self.paths.keys()
        self.demand_edges = {}
        for demand in self.demands:
            self.demand_edges[demand] = self.edges[demand][ultimate_sink]

    def generate_paths(self, current_node, current_path, metric_of_path, ultimate_source):
        # recursively sample all possible paths between ultimate source and sink 
        # and append them to respective demand list self.paths[demand] of possible paths
        # (current_path does not contain S and not current_node)
        if len(current_path) < 9:
            if current_node == ultimate_source:
                demand_node = current_path[-2] # second node is a demand node
                if demand_node[0] == 'T':
                    transport_supply_node = current_path[1]
                    # check if transport demand would be supplied by correct supply
                    if ('T_G_' + demand_node[4:]) != transport_supply_node: 
                        return # transport demand not supplied by correct node
                self.paths[demand_node].append(Path(current_path, metric_of_path))
            else:
                current_core_node = self.get_core_node(current_node)
                next_nodes = self.get_predecessors(current_core_node)
                if next_nodes != None:
                    for next_node in next_nodes:
                        if self.get_core_node(next_node) in [self.get_core_node(node) for node in current_path]:
                            pass
                        else:
                            new_current_path = [next_node] + current_path
                            new_metric_of_path = metric_of_path + self.edges[next_node][current_core_node].metric
                            self.generate_paths(next_node, new_current_path, new_metric_of_path, ultimate_source)
                            gc.collect()
    
    def update_path_metrics(self):
        metrics_changed = False # track if any metric has changed
        for edge in self.edge_list: # update the metric of each arc for the current flows
            if edge.update_metric():
                metrics_changed = True
        for demand in self.paths.keys(): # update total_metrics of paths and resort them
            for path in self.paths[demand]:
                edges = self.get_edges(path.path)
                total_metric = float(0)
                for edge in edges:
                    total_metric += edge.metric
                path.total_metric = total_metric
            self.paths[demand] = sorted(self.paths[demand], key = lambda x: x.total_metric) # sort paths for shortest path first
        return metrics_changed 
    
    def resort_paths_by_metric(self):
        for demand in self.paths.keys(): # reset total_metrics of paths and resort them
            for path in self.paths[demand]:
                edges = self.get_edges(path.path)
                total_metric = float(0)
                for edge in edges:
                    total_metric += edge.metric
                path.total_metric = total_metric
            self.paths[demand] = sorted(self.paths[demand], key = lambda x: x.total_metric) # sort paths for shortest path first

    ## main performance test as called from yearly development step in Main-Simulation.py ##
    def test_performance(self, former_total_margin):
        # test current resource allocation and extract performance indicators
        demands_met = self.test_curr_fut_flows('current')
        (total_metric, total_cost, total_epi, total_com) = self.total_metric()
        print 'total cost: ' + str(total_cost) + ' total epi: ' + str(total_epi)
        total_margin = self.test_total_margin(former_total_margin)
        # test future resource allocation
        if self.no_build == 1: # no-build-modelrun!
            demands_meetable = None # dummy
            pass # skip the forecasting step
        else: 
            demands_meetable = self.test_curr_fut_flows('forecast')
        self.document_modelrun_results_1(demands_met, demands_meetable, total_cost, total_epi, total_com, total_metric, total_margin)
        return (demands_met, demands_meetable, total_metric, total_margin)

    def test_curr_fut_flows(self, cur_fut_plan):
        #print 'test ' + cur_fut_plan + ' flows'
        # test current resource allocation:
        # initialize the edge capacities and metric
        for edge in self.edge_list: # set all edge capacities to the relevant capacities for the specific optimization step 
            if cur_fut_plan == 'current': # current capacities are stored in orig_cap of respective arcs
                edge.cap = edge.current_capacity
            elif cur_fut_plan == 'forecast': # future capacities as already installed or scheduled
                edge.cap = edge.planned_capacity 
            elif cur_fut_plan == 'planning':
                edge.cap = edge.planned_and_possible_capacity # scheduling capacity in cap for the forecasting process
            else:
                print'error in test_curr_fut_flows_flows'
                # initialize working variables - capacity and interdependency
        self.initialize_capacities_and_metrics()
        self.initialize_interdependent_metrics() # initialize interdependency metrics according to the new metrics and adds the initialized value to the edges metric
        last_mik = self.optimize_flows(cur_fut_plan)
        demands_met = self.demands_met(cur_fut_plan, last_mik)
        self.document_optimized_flows(cur_fut_plan)
        return demands_met
   
    def initialize_capacities_and_metrics(self):
        # initialize all capacities and update the metric accordingly
        for edge in self.edge_list:
            edge.initialize_capacities_and_metric()
        # all paths need resorting by metric after updating the metric
        self.resort_paths_by_metric()

    # forecasting future investments as called from yearly development step (in Main-Simulation.py) according to performance    
    def forecast_necessary_investments(self):
        print 'looking for expansion options'
        investment_projects = []
        expansion_possible = self.test_curr_fut_flows('planning')
        print 'future demands meetable with given investment options?: ' + str(expansion_possible)
        self.document_modelrun_results_2(expansion_possible)
        for edge in self.edge_list: # check which new assets have been used
            # to be an actual scheduling project, the arc needs to have finite flow (i.e. used!), 
            # to exclude already installed or scheduled assets check the second
            if edge.total_flow_fin() > 0 and edge.planned_and_possible_capacity != edge.planned_capacity and edge.installation_name != '':
                investment_projects.append(edge.installation_name)
        #print('investment projects to be scheduled (if not already scheduled): ' + str(investment_projects))
        return investment_projects

    # allocation optimization #                         
    def optimize_flows(self, cur_fut_plan):
        '''
        In a nested set of itteration loops, the allocation of supply resources to given demand is optimized. In the innerest loop, supply flows are optimized for given demands and asset capacities.
        This itteration, indexed with variable k, repeatedly optimizes the (preliminary) supply for individual demands (in optimize_single_commodity_flows), to then allocate resources amongst 
        competing demands in the allocate_flow_to_remaining_capacities function. Whenever there are no more resources to allocate, or when all demands have been met, the innerest itteration
        terminates. In the next higher itteration of interdependency updates (indexed by variable i), interdependency capacities (i.e. asset capacities and demands) are updated according to 
        the established supply-flows in the innerest optimization. If interdependency capacities were found to have changed in this step, the innerest optimization step is repeated with the 
        changed capacities. When this itteration of interdependency updating (and innerest optimization) converges, the algorithm steps into the outerest loop (indexed by variable m),
        of metric optimization. Here multiple updating steps are performed: first interdependency metrics are updated, then all path metrics and finally the capacity of any assets causing an 
        oscillation of the complete optimization algorithm is reduced. When the metric optimization converges, the function terminates and returns the index triple of final variables k, i and m.
        '''
        cursor = self.cnxn.cursor()
        metrics_changed = True
        m=0
        while metrics_changed:
            interdependencies_changed = True
            i=0
            while interdependencies_changed: # as long as the interdependencies still change
                for edge in self.edge_list:  # reset all capacities and flows
                    for demand in self.demands:
                        edge.int_flow[demand] = 0  
                        edge.fin_flow[demand] = 0
                    edge.rem_cap = edge.cap 
                # optimize multi-commodity flows until demands are sufficiently met 
                further_flows_allocated = True
                k=0
                while further_flows_allocated:
                    mik = (m,i,k)
                    intermediate_flows = self.optimize_single_commodity_flows()
                    further_flows_allocated = self.allocate_flow_to_remaining_capacities(intermediate_flows, cursor, mik, cur_fut_plan)
                    last_mik = mik
                    print 'm ' + str(m) + ' i ' + str(i) + ' k ' + str(k)
                    k+=1
                # check interdependencies
                interdependencies_changed = self.update_interdependencies(i)
                if interdependencies_changed:
                    i+=1
            self.update_interdependency_metrics() # update the interdependency metrics according to the current allocation of resources for demands
            metrics_changed = self.update_path_metrics() # update metrics according to allocated flows and resort paths accordingly
            self.reduce_capacities_of_assets_with_oscillating_usage_and_metric()
            if metrics_changed:
                m+=1
        return last_mik

    def optimize_single_commodity_flows(self): 
        '''
        # (operates on int_flow)        
        # Searches for the optimal supply for each demand individually (as if no other demands would exist):
        # To do so, it itterates through the list of possible supply options as stored in self.paths[demand] and sorted by minimum metric, i.e. the most ideal options first.
        # It provisionally adds the maximum possible flow to each available path until the demand is fulfilled (or until the algorithm has to find demand satisfaction is impossible).
        # These provisional flows are tracked in each edges int_flow variable (int for intermediate), for comparison in further loops of the itteration. 
        # The allocated flows are also stored as (path_metric, flow, path) tuples in the intermediate_flows dictionary, for use in the function allocate_flow_to_remaining_capacities.
        # rem_cap stands for remaining capacity and tracks the decrease in available capacity when provisional flows are allocated.
        '''
        intermediate_flows = {} 
        for demand in self.demands:
            # make a dictionary for all the demands
            intermediate_flows[demand] = [] # initialize list
            remaining_paths = copy.deepcopy(self.paths[demand])
            demand_edge = self.demand_edges[demand]
            remaining_demand = demand_edge.rem_cap - demand_edge.int_flow[demand] # check how much demand has not yet been fulfilled in earlier 
                                                                                  # optimize_single_commodity_flows+allocate_flow_to_remaining_capacities cycles
            #print 'remaining demand: ' + demand + ' ' + str(remaining_demand)
            while (remaining_demand > 0) and bool(remaining_paths):
                path_obj = remaining_paths.pop(0) #  take next available supply option
                path = path_obj.path
                path_metric = path_obj.total_metric
                path_edges = self.get_edges(path)
                flow = min((edge.rem_cap - edge.int_flow[demand]) for edge in path_edges) # calculate available maximum flow which could be added to this path
                if flow > 5: # check reasonable magnitude of flow to be allocated - this is a variable parameter and should be adjusted in the competition of precision of solution
                             # (small number) to speed of the algorithm (large number)
                    for edge in path_edges:
                        edge.int_flow[demand] += flow # allocate intermediate flow
                    remaining_demand = demand_edge.rem_cap - demand_edge.int_flow[demand] # reevaluate remaining demand
                    intermediate_flows[demand].append((path_metric, flow, path)) # add tuple made of ideal flow and path to list of intermediate flows
        return intermediate_flows
             
    def allocate_flow_to_remaining_capacities(self, intermediate_flows, cursor, mik, cur_fut_plan): 
        '''
        # This function is called directly after optimize_single_commodity_flows. It takes the individually optimized intermediate flows for each demand and distributes remaining 
        # infrastructure supply capacity amongst the different demands in a fair-share manner. For this, we need to find out for each edge how many itermediate flows have been allocated to it,
        # and by which factor, the edge is over-/under-used. This result is stored in the variable edge.utilization_of_arc. Then we can allocate flows to all supply paths by rescaling the demanded int_flows
        # by the maximum of the utilization_of_arc of all edges in the given supply path. These allocated flows are stored in the final flow fin_flow variables. For each allocated final flow the remaining
        # capacity variable (rem_cap) will be adjusted accordingly.
        # (increases fin_flow and reduces rem_cap)
        '''
        further_flows_allocated = False
        # determine utilization of all edges:
        for edge in self.edge_list: 
            sum_of_flows = sum(edge.int_flow[demand] for demand in self.demands)
            for demand in self.demands:
                edge.int_flow[demand] = 0
            if sum_of_flows > 0: # was any flow allocated, such that max_utilization_of_arc could be > 0?
                edge.utilization_of_arc = 1.0*sum_of_flows/edge.rem_cap # 1.0 enforces float calculation
            else: 
                edge.utilization_of_arc= 0
        # allocate final flows (fin_flow) to all supply paths, whilest rescaling all demanded flows by the maximum utilization_of_arc on this path:
        for demand in self.demands:
            demand_edge = self.demand_edges[demand]  # for documentation
            demand_value = demand_edge.cap   # for documentation
            list_of_supplies = []  # for documentation
            for used_path in intermediate_flows[demand]:
                (path_metric, ideal_flow, path) = used_path
                path_edges = self.get_edges(path)
                utilization_of_path = max((edge.utilization_of_arc) for edge in path_edges)
                if utilization_of_path > 0:
                    rescaling_factor = 1.0/utilization_of_path
                else:
                    rescaling_factor = 1
                flow_to_be_allocated = int(ideal_flow*rescaling_factor)
                if flow_to_be_allocated > 0:
                    further_flows_allocated = True
                    list_of_supplies.append((path_metric, flow_to_be_allocated, ideal_flow, path)) # for documentation
                    for edge in path_edges:
                        edge.fin_flow[demand] += flow_to_be_allocated
                        edge.rem_cap -= flow_to_be_allocated
            # document the allocated flows to database
            if list_of_supplies != []:
                sqote="'"
                (m,i,k) = mik
                for allocation_to_path in list_of_supplies:
                    (path_metric, flow_to_be_allocated, ideal_flow, path) = allocation_to_path
                    source = path[1]
                    supply_string = str(path).replace("'","") 
                    theSQL = 'insert into "ISL_IO_FinalFlows_SupplyPathsByIteration" (modelrun_id, simulation_year, demand_identifier, demand_value, supply_path, m, i, k, \
                                cur_fut_plan, metric_of_supply, requested_supply, allocated_supply, source) values \
                            (' + sqote + str(self.modelrun_id) + sqote + ', ' +  sqote +str(self.year) + sqote + ', '  + sqote + str(demand) + sqote + ', ' + str(demand_value) + '\
                            , ' + sqote + str(supply_string) + sqote + ', ' + sqote + str(m) + sqote + ', ' + sqote + str(i) + sqote  + ', ' + sqote + str(k) + sqote + ', \
                            ' + sqote + str(cur_fut_plan) + sqote + ', ' + sqote + str(int(path_metric)) + sqote+ ', ' + sqote + str(ideal_flow) + sqote+ ', \
                            ' + sqote + str(flow_to_be_allocated) + sqote+ ', ' + sqote + str(source) + sqote+ ' )'
                    cursor.execute(theSQL)
                    cursor.commit()
        return further_flows_allocated
    
    def update_interdependencies(self, i): # recalculates interdep_dem in new_interdep_dem, allocates to cap if changed more than 1
        # reset interdependency capacity variables
        for edge in self.edge_list:
            edge.interdep_cap = 0
            #edge.interdependency_cost = 0
            #edge.interdependency_epi = 0
        for direct_dep in self.interdependencies['d']:
            [(cao, cad), (aao, aad), feedbackfactor, maxcap] = direct_dep
            causing_arc = self.edges[cao][cad]
            affected_arc = self.edges[aao][aad]
            causing_flow = causing_arc.cap - causing_arc.rem_cap
            affected_arc.interdep_cap += causing_flow*float(feedbackfactor)
            #causing_arc.interdependency_cost += self.demand_cost(affected_arc)*float(feedbackfactor)
            #causing_arc.interdependency_epi += self.demand_epi(affected_arc)*float(feedbackfactor)
        for synergy in self.interdependencies['s']:
            [(cao, cad), (aao, aad), feedbackfactor, maxcap] = synergy
            causing_arc = self.edges[cao][cad]
            affected_arc = self.edges[aao][aad]
            causing_flow = causing_arc.cap - causing_arc.rem_cap
            affected_arc.interdep_cap += causing_flow*float(feedbackfactor)
        for multi_use_causing_arc in self.interdependencies['m']:
            (cao, cad) = self.interdependencies['m'][multi_use_causing_arc][0]
            list_of_affected_arcs = self.interdependencies['m'][multi_use_causing_arc][1]
            c_max = self.interdependencies['m'][multi_use_causing_arc][2]
            total_flow = 0
            for affected_arc_name in list_of_affected_arcs:
                (aao, aad, aa_convfact) = affected_arc_name
                affected_arc = self.edges[aao][aad]
                total_flow += (affected_arc.cap - affected_arc.rem_cap)*aa_convfact # convert each flow into the units of shared capacity and add up to total flow
                affected_arc.interdependency_basic_cap = 0 # the capacity of multiuse arc gets rescaled by their popularity of usage, hence the basic capacity needs to be zero
            if  total_flow != 0: # redistribute the given shared capacity amongst all sharing edges proportionally to their intended usage
                #rescaling_factor = 1.0*c_max/total_flow # shared cap redistribution: c_i = f_i*(c_max/SUM(f_j))    
                for affected_arc_name in list_of_affected_arcs:
                    (aao, aad, aa_convfact) = affected_arc_name
                    affected_arc = self.edges[aao][aad]
                    # edit for reduction in arc capacity to avoid metric fluctuation - we now need to calculate c_max for every transport mode!
                    #c_max_of_this_arc = (1.0*affected_arc.cap/affected_arc.orig_cap)*c_max
                    c_max_of_this_arc = affected_arc.cap_reduction_factor*c_max
                    rescaling_factor = 1.0*c_max_of_this_arc/total_flow # shared cap redistribution: c_i = f_i*(c_max/SUM(f_j))
                    affected_arc.interdep_cap += (affected_arc.cap - affected_arc.rem_cap)*rescaling_factor
            else:
                for affected_arc_name in list_of_affected_arcs:
                    (aao, aad, aa_convfact) = affected_arc_name
                    affected_arc = self.edges[aao][aad]
                    #affected_arc.interdep_cap += affected_arc.orig_cap 
                    affected_arc.interdep_cap += affected_arc.orig_cap * affected_arc.cap_reduction_factor
        interdependencies_changed = False 
        for edge in self.edge_list:
            cap_change = int(abs(edge.cap - (edge.interdependency_basic_cap + edge.interdep_cap)))
            if cap_change > 0: 
                if 1.0*(edge.interdependency_basic_cap + edge.interdep_cap)/cap_change < 20 : # ensure interdependency caps have changed at least by 5% to count it as change
                    interdependencies_changed = True
                    ##if i > 10:
                    #    print 'interdependency changed in ' + edge.source + ' -> ' + edge.sink + ' from ' + str(edge.cap) + ' to ' + str(int(edge.interdependency_basic_cap + edge.interdep_cap)) 
                    edge.cap = int(edge.interdependency_basic_cap + edge.interdep_cap)
                    #if edge.source == 'T_N_Transport_RoadElectricCar_8_ARC21':
                    #    print 'cap after intedependency update = ' + str(edge.cap)
        return interdependencies_changed

    def reduce_capacities_of_assets_with_oscillating_usage_and_metric(self):
        #for edge in self.edge_list:
        #    # document total flow in edge to monitor usage changes and oscillations
        #    edge_flow = edge.cap - edge.rem_cap
        #    edge.flow_tracker.append(edge_flow)
        #    edge.metric_tracker.append(edge.metric)
        #    # we should monitor usage oscillations of usage and metric on ALL edges, and reduce their capacity, if they are an infrastructure asset (and not a demand etc.)
        #    if len(edge.flow_tracker) > 2 and len(edge.metric_tracker) > 2: # flow adn metric have changed often enough for comparison    
        #        #check that metric and flow, i.e. usage have both changed:
        #        if edge.flow_tracker[-1] != edge.flow_tracker[-2] and edge.metric_tracker[-1] != edge.metric_tracker[-2]:
        #            #check that metric and flow have ascillated, by multiplying the two flow/metric differences of the last three respective values
        #            # by multiplying the two changes and looking for the product to have a negative sign, i.e. indicating oscillation
        #            # versus positive sign, which would indicate a monotonous change
        #            if (edge.flow_tracker[-1] - edge.flow_tracker[-2])*(edge.flow_tracker[-2] - edge.flow_tracker[-3]) < 0 \
        #                      and (edge.metric_tracker[-1] - edge.metric_tracker[-2])*(edge.metric_tracker[-2] - edge.metric_tracker[-3]) < 0:
        #                # so we should reduce the capacity of this edge, if it is an asset:
        #                if edge.asset_type != '': # checking it is an asset
        #                    if edge.cap_reduction_factor > 0: # making sure the assets capacity has not already been set to 0
        #                        edge.cap_reduction_factor += -0.1 # reduce capacity by 10% of original value -> linear decrease in capacity
        #                        edge.cap = int(edge.orig_cap*edge.cap_reduction_factor) # ... reduce the capacity of this asset
        #                        edge.interdependency_basic_cap = edge.cap # ... update the interdep basic capacity accordingly
        #                        print edge.source + ' -> ' + edge.sink + ' capacity reduced to ' + str(edge.cap) 
        #                        print 'with reduction factor ' + str(edge.cap_reduction_factor)
        for edge in self.edge_list:
            # document total flow in edge to monitor usage changes and oscillations
            edge_flow = edge.cap - edge.rem_cap
            edge.flow_tracker.append(edge_flow)
            edge.metric_tracker.append(edge.metric)
            # we should monitor usage oscillations of usage and metric on ALL edges, and reduce their capacity, if they are an infrastructure asset (and not a demand etc.)
            if len(edge.flow_tracker) > 2 : # flow adn metric have changed often enough for comparison    
                #check that metric and flow, i.e. usage have both changed:
                if edge.flow_tracker[-1] != edge.flow_tracker[-2]:
                    #check that metric and flow have ascillated, by multiplying the two flow/metric differences of the last three respective values
                    # by multiplying the two changes and looking for the product to have a negative sign, i.e. indicating oscillation
                    # versus positive sign, which would indicate a monotonous change
                    if (edge.flow_tracker[-1] - edge.flow_tracker[-2])*(edge.flow_tracker[-2] - edge.flow_tracker[-3]) < 0 :
                        #check the magnitude of change being more than 10%:
                        if edge.cap/abs((edge.flow_tracker[-1] - edge.flow_tracker[-2])) < 10:
                            # so we should reduce the capacity of this edge, if it is an asset:
                            if edge.asset_type != '': # checking it is an asset
                                if edge.cap_reduction_factor > 0: # making sure the assets capacity has not already been set to 0
                                    edge.cap_reduction_factor += -0.1 # reduce capacity by 10% of original value -> linear decrease in capacity
                                    edge.cap = int(edge.orig_cap*edge.cap_reduction_factor) # ... reduce the capacity of this asset
                                    edge.interdependency_basic_cap = edge.cap # ... update the interdep basic capacity accordingly
                                    print edge.source + ' -> ' + edge.sink + ' capacity reduced to ' + str(edge.cap) 
                                    print 'with reduction factor ' + str(edge.cap_reduction_factor)

    def update_interdependency_metrics(self):
        for edge in self.edge_list:
            edge.old_intdp_metric = edge.interdependency_metric # save for comparison
            edge.interdependency_metric = 0 # reset to 0 for update, basic value still captured in orig_interdependency_metric
        # now update the interdependency metrics
        for direct_dep in self.interdependencies['d']:
            [(cao, cad), (aao, aad), feedbackfactor, maxcap] = direct_dep
            causing_arc = self.edges[cao][cad] # generation or transmission asset
            affected_arc = self.edges[aao][aad] # a key-service demand
            causing_flow = causing_arc.cap - causing_arc.rem_cap
            #what is the additional metric per supply unit of the causing asset induced by the interdependent key-service?
            #caused_interdep_demand = causing_flow*float(feedbackfactor) AND causing_arc.interdependency_metric += caused_interdep_demand*self.average_supply_metric(affected_arc)/causing_flow
            #i.e., since causing flow is 'cancelled out':
            causing_arc.interdependency_metric += float(feedbackfactor)*self.average_supply_metric(affected_arc)

    def average_supply_metric(self, demand_edge): # calculate metric per supply unit for meeting a particular demand with given optimized flows
        demand = demand_edge.source
        total_metric = 0
        # calculate cummulative metric of supply for this demand
        for edge in self.edge_list:
            total_metric += edge.fin_flow[demand]*edge.metric
        demand_value = demand_edge.cap
        total_supply = demand_edge.total_flow_fin()
        if total_supply == 0:
            metric_per_flow = total_metric # avoid devision by zero, and if demand=0, then just give it total cost, as if demand was one unit
        elif total_supply*1.0/demand_value < 0.99:
             metric_per_flow = __INF__ # if demand can't be met, then this option shouldn't be available, hence put up the cost to 'inf'
        else:
            metric_per_flow = total_metric*1.0/total_supply # if demand can be met, return cost per unit of supply
        return metric_per_flow

    def demands_met(self, current_forecast, mik): # compares cap and rem_cap
#         unfulfilled_demands = sum(self.demand_edges[demand].rem_cap for demand in self.demands)
#         original_demands = sum(self.demand_edges[demand].cap for demand in self.demands)
        cursor = self.cnxn.cursor()
        demands_met = True
        for demand in self.demands:
            demand_name_list = demand.split('_')
            submodel = demand_name_list[2]
            keyservice = demand_name_list[3]
            region = demand_name_list[4]
            demand_value = self.demand_edges[demand].cap
            supply = self.demand_edges[demand].cap - self.demand_edges[demand].rem_cap
            demand_met = (supply >= 0.9*demand_value)
            sqote="'"
            (m,i,k) = mik
            theSQL = 'insert into "ISL_IO_FinalFlows_DemandFulfillments" (modelrun_id, simulation_year, demand, demand_value, supply, demand_met, current_forecast, final_m, final_i, final_k, submodel, keyservice, region) \
                      values (' + sqote + str(self.modelrun_id) + sqote + ', ' + str(self.year) + ', ' + sqote + str(demand) + sqote + ',\
                      ' + sqote + str(demand_value) + sqote + ', ' + sqote + str(supply) + sqote + ', '+ sqote + str(demand_met) + sqote + '\
                      , '+ sqote + str(current_forecast) + sqote + ', ' + sqote + str(m) + sqote + ', ' + sqote + str(i) + sqote  + ',\
                      ' + sqote + str(k) + sqote+ ', ' + sqote + str(submodel) + sqote+ ', ' + sqote + str(keyservice) + sqote + ', ' + sqote + str(region) + sqote + ')'
            cursor.execute(theSQL)
            cursor.commit()
            if not demand_met:
                demands_met = False # demands not reasonably well met
                print 'demand ' +  demand + ' not met by ' + str((demand_value-supply)*100/demand_value) + '\%'
        return demands_met

    # performance testing                
    def test_total_margin(self, former_total_margin):
        ### testing total margin currently disabled ###
        return 10
        ''' testing the margin of the system
        #for demand in self.demands: # increase all demands by 10%
        #    self.demand_edges[demand].cap = int((1+former_total_margin)*(self.demand_edges[demand].orig_cap))
        #demand_possible = self.optimize_flows()
        #if demand_possible:
        #    #print('upwards')
        #    total_margin = self.test_total_margin_upwards(former_total_margin)
        #else:
        #    #print('downwards')
        #    total_margin = self.test_total_margin_downwards(former_total_margin)
        #return total_margin'''

    def test_total_margin_upwards(self, former_total_margin):
        larger_demand_possible = True
        total_margin = former_total_margin + 1
        while larger_demand_possible:
            #print total_margin
            for demand in self.demands: # increase all demands by 10%
                self.demand_edges[demand].cap = int((1+total_margin)*(self.demand_edges[demand].orig_cap))
            larger_demand_possible = self.optimize_flows()
            if larger_demand_possible: 
                total_margin += 1
                #print(str(total_margin))
            else:
                total_margin -= 1
                larger_demand_possible = True
                while larger_demand_possible:
                    #print total_margin
                    for demand in self.demands: # increase all demands by 10%
                        self.demand_edges[demand].cap = int((1+total_margin)*(self.demand_edges[demand].orig_cap))
                    larger_demand_possible = self.optimize_flows()
                    if larger_demand_possible: 
                        total_margin += 0.1
                        #print(str(total_margin))
                    else:
                        total_margin -= 0.1
                        larger_demand_possible = True
                        while larger_demand_possible:
                            #print total_margin
                            for demand in self.demands: # increase all demands by 10%
                                self.demand_edges[demand].cap = int((1+total_margin)*(self.demand_edges[demand].orig_cap))
                            larger_demand_possible = self.optimize_flows()
                            if larger_demand_possible: 
                                total_margin += 0.01
                                #print(str(total_margin))
        return (total_margin-0.01)

    def test_total_margin_downwards(self, former_total_margin):
        larger_demand_possible = False
        total_margin = former_total_margin - 0.01
        while not larger_demand_possible:
            for demand in self.demands: # increase all demands by 10%
                self.demand_edges[demand].cap = int((1+total_margin)*(self.demand_edges[demand].orig_cap))
            larger_demand_possible = self.optimize_flows()
            if not larger_demand_possible: # until demands can be met, reduce the suggested total_margin
                total_margin -= 0.01
                #print total_margin
                if total_margin < 0:
                    return 0
                #print(str(total_margin))
        return total_margin
    
    def total_metric(self):
        # check performance of the solution and save to file
        total_metric = 0.0
        total_cost = 0.0
        total_epi = 0.0
        total_com = 0.0
        for edge in self.edge_list:  # reset all capacities and flows
            flow = edge.total_flow_fin()
            total_metric += flow*edge.metric
            total_cost += flow*edge.cost
            total_epi += flow*edge.epi
            total_com += flow*edge.com
        return (total_metric, total_cost, total_epi, total_com)
    
       
    # documentation of modelrun
    def document_optimized_flows(self, cur_fut_plan):
        sqote = "'"
        cursor = self.cnxn.cursor()
        cursor.commit()
        for edge in self.edge_list:  # 
            total_flow = edge.total_flow_fin()
            origin_list = edge.source.split('_')
            destination_list = edge.sink.split('_')
            #if origin_list[0] != 'S' and destination_list[0] != 'T':
            if origin_list[0] != 'S':
                if origin_list[1] == 'N':
                    if destination_list[1] == 'N' : # network arc - document a transfer
                        theSQL = 'INSERT INTO "ISL_IO_FinalFlows_DistributionNetworks"(modelrun_id, simulation_year, submodel, origin, destination, total_flow, cur_future_plan, network, maxcap, fincap, metric) \
                                VALUES (' + str(self.modelrun_id) + ', ' + str(self.year) + ', ' + sqote +  str(origin_list[2]) + sqote + ', ' + sqote + str(origin_list[4]) + sqote + ', ' + sqote + str(destination_list[4]) +sqote +  ', \
                                ' + str(total_flow) + ', ' +sqote +   str(cur_fut_plan) +sqote +  ', ' + sqote + str(origin_list[3]) + sqote  +  ', ' + sqote + str(edge.orig_cap) + sqote + ', ' + sqote + str(edge.cap) +sqote  +  ', ' + sqote + str(edge.metric) + sqote + ')'
                        theSQL = theSQL.replace('\\', '')
                        cursor.execute(theSQL)
                        cursor.commit()
                        if edge.interdep_cap != 0:
                            theSQL = 'INSERT INTO "ISL_IO_FinalFlows_InterdependencyCapacities"( \
                                      modelrun_id, simulation_year, "affNGD", affected_asset, interdependency_capacity, region_from, region_to, cur_fut_plan) \
                                      VALUES ('  + str(self.modelrun_id) + ', ' + str(self.year) + ', ' + sqote+'N'+sqote +  ', ' + sqote + str(edge.source) +sqote  +  ', ' \
                                      + str(edge.interdep_cap) + ', ' + sqote + str(origin_list[4]) + sqote + ', ' + sqote + str(destination_list[4]) +sqote +', ' +sqote +   str(cur_fut_plan) +sqote + ')'
                            theSQL = theSQL.replace('\\', '')
                            cursor.execute(theSQL)
                            cursor.commit()
                    if destination_list[1] == 'D': # network to demand supply
                        supply_metric = self.get_supply_metric(edge.sink, edge.source)
                        theSQL = 'INSERT INTO "ISL_IO_FinalFlows_SuppliesByNetwork"(modelrun_id, simulation_year, submodel, network, region, keyservice, total_flow, cur_fut_plan, supply_metric) \
                                VALUES (' + str(self.modelrun_id) + ', ' + str(self.year) + ', ' +sqote +  str(origin_list[2]) +sqote+', '+sqote +  str(origin_list[3]) +sqote+', '+sqote +  str(origin_list[4]) +sqote +  ', ' +sqote +  str(destination_list[3]) +sqote +  ', \
                                ' + str(total_flow) + ', ' + sqote +  cur_fut_plan   +sqote + ', ' + str(supply_metric) + ' )'
                        theSQL = theSQL.replace('\\', '')
                        cursor.execute(theSQL)
                        cursor.commit()
                elif origin_list[1] == 'G' and origin_list[0] == 'C': # generation asset feeding a network
                    theSQL = 'INSERT INTO "ISL_IO_FinalFlows_GenerationAssets"(modelrun_id, simulation_year, total_flow, cur_futur_plan, submodel, region, asset_name, network, maxcap, fincap, asset_type, metric) \
                            VALUES ( ' + str(self.modelrun_id) + ', ' + str(self.year) + ', ' + str(total_flow) + ', '+sqote +   cur_fut_plan +sqote +  ', ' + sqote + str(origin_list[2]) +sqote + ', \
                            ' +sqote +   str(origin_list[4]) +sqote +  ', ' +sqote +  str(origin_list[5]) +sqote +  ', ' +sqote +  str(origin_list[3]) +sqote  +  ', ' + sqote + str(edge.orig_cap) +sqote +  ', ' + sqote + str(edge.cap) +sqote+  ' \
                            , ' + sqote + str(edge.asset_type) + sqote + ', ' + sqote + str(edge.metric) + sqote + ')'
                    theSQL = theSQL.replace('\\','')
                    cursor.execute(theSQL)
                    cursor.commit()
                    if edge.interdep_cap != 0:
                        theSQL = 'INSERT INTO "ISL_IO_FinalFlows_InterdependencyCapacities"( \
                                    modelrun_id, simulation_year, "affNGD", affected_asset, interdependency_capacity, region_from, cur_fut_plan, interdep_metric) \
                                    VALUES ('  + str(self.modelrun_id) + ', ' + str(self.year) + ', ' + sqote+'G'+sqote +  ', ' + sqote + str(edge.source) +sqote  +  ', ' \
                                    + str(edge.interdep_cap) + ', ' + sqote + str(origin_list[4]) + sqote +', ' +sqote +   str(cur_fut_plan) +sqote+ ', ' + sqote + str(edge.interdependency_metric) + sqote + ')'
                        theSQL = theSQL.replace('\\', '')
                        cursor.execute(theSQL)
                        cursor.commit()
                elif origin_list[1] == 'D': # demand node to 'T'
                    if edge.interdep_cap != 0:
                        if origin_list[0] == 'T':
                            theSQL = 'INSERT INTO "ISL_IO_FinalFlows_InterdependencyCapacities"( \
                                    modelrun_id, simulation_year, "affNGD", affected_keyservice, interdependency_capacity, region_from, region_to, cur_fut_plan, interdep_metric) \
                                    VALUES ('  + str(self.modelrun_id) + ', ' + str(self.year) + ', ' + sqote+'D'+sqote +  ', ' + sqote + str(origin_list[3]) +sqote  +  ', ' \
                                    + str(edge.interdep_cap) + ', ' + sqote + str(origin_list[4]) + sqote + ', ' + sqote + str(origin_list[5]) + sqote +', ' +sqote +   str(cur_fut_plan) +sqote + ', ' + sqote + str(edge.interdependency_metric) + sqote+ ')'
                        elif origin_list[0] == 'C':                        
                            theSQL = 'INSERT INTO "ISL_IO_FinalFlows_InterdependencyCapacities"( \
                                    modelrun_id, simulation_year, "affNGD", affected_keyservice, interdependency_capacity, region_from, cur_fut_plan, interdep_metric) \
                                    VALUES ('  + str(self.modelrun_id) + ', ' + str(self.year) + ', ' + sqote+'D'+sqote +  ', ' + sqote + str(origin_list[3]) +sqote  +  ', ' \
                                    + str(edge.interdep_cap) + ', ' + sqote + str(origin_list[4]) + sqote +', ' +sqote +   str(cur_fut_plan) +sqote+ ', ' + sqote + str(edge.interdependency_metric) + sqote+ ')'
                        theSQL = theSQL.replace('\\', '')
                        cursor.execute(theSQL)
                        cursor.commit()
   
    def document_modelrun_results_1(self, demands_met, demands_meetable, total_cost, total_epi, total_com, total_metric, total_margin):
        squote = "'"
        theSQL = 'INSERT INTO "ISL_O_StrategyPerformance" (modelrun_id, year, demands_met, demands_meetable, total_cost, total_epi, total_com, total_metric, total_margin) VALUES (\
        ' + str(self.modelrun_id) + ', ' + str(self.year) + ', ' + squote + str(demands_met) + squote + ', ' + squote + str(demands_meetable) + squote + ', \
        ' + str(total_cost) + ', ' + str(total_epi) + ', ' + str(total_com) + ',' + str(total_metric) + ', ' + str(total_margin) + ')'
        ESQL.execute_SQL(theSQL, [], [], self.cnxn)

    def document_modelrun_results_2(self, demands_meetable_with_investments):
        cursor = self.cnxn.cursor()
        squote = "'"
        theSQL = 'UPDATE "ISL_O_StrategyPerformance" SET demands_meetable_with_investments = ' + squote + str(demands_meetable_with_investments) + squote + '   WHERE \
         modelrun_id = ' + str(self.modelrun_id) + ' AND year = ' + str(self.year)
        ESQL.execute_SQL(theSQL, [], [], self.cnxn)
                 
    def get_supply_metric(self, demand_node, supply_network_node): # for modelrun documentation
        # get a list of paths that are supplying this specific demand
        paths = self.paths[demand_node]
        total_metric = 0  
        minimum_metric = 10000000000 # metric of cheapest path for comparison - default too high value
        # for each of the paths calculate the metric based on flows of all edges in path
        for path in paths:
            # check that the network node (-3) is the supply_network_node
            if path.path[-3] == supply_network_node:
                # get the edges of this path
                edges = self.get_edges(path.path)
                generation_edge = edges[1]
                # for each path calculate a metric weighted by flow from this specific supply path to the given demand
                total_metric += generation_edge.fin_flow[demand_node]*path.total_metric
                path_edges = self.get_edges(path.path)
                # track the metric of the cheapest available supply path, in order to have a value to return, even if total_supply is 0, i.e. the minimum metric that would have had to be payed to get supply from the respective network.
                if path.total_metric < minimum_metric and min((edge.cap) for edge in path_edges) > 0:
                    minimum_metric = path.total_metric
        # return a metric divided by total supply flow from this specific network to the given demand, o the metric is normalised by flow. If total supply is 0, then return the metric of cheapest available supply path.
        supply_edge = self.edges[supply_network_node][demand_node]
        total_supply = supply_edge.fin_flow[demand_node]
        if total_supply == 0:
            return minimum_metric
        else:
            return total_metric*1.0/total_supply
