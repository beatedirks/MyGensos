'''-- TO DO --

I) Demonstrate how the core of the simulation model - the allocation algorithm - works.
-- use the data of ONE year of ONE of the scenarios --
a) Demonstrate how resources (i.e. available supply) are distributed amongst competing demands, where respectively most favourable solution is determined by the metric of the supply options:
b) Demonstrate how a different metric weight leads to different choices in the allocation algorithm:
b) Demonstrate how the three types of interdependencies are being accounted for in the optimisation:
c) Demonstrate how infrastructure expansion options are chosen (when deemed necessary by the long-term investment strategy)

II) Demonstrate what kind of analysis the complete simulation system allows for. In particular demonstrate for our GNE case-study with given six scenarios...:
-- use multiple modelruns, all scenarios, build and no-build option, static versus dynamic interdependecies, different metric weights, different investment strategies --
1) ... the influence of differing demands (i.e. originally demand drivers) on the performance of the infrastructure system, measured via total costs/emissions and global capacity margins.
        -> i.e. register supply shortfalls for all scenarios in the no-build setup
2) ... how the system copes with unmet demand and which expansion options it chooses.
        -> i.e. compare the build scenarios to show which infrastructure expansion options have been chosen
3) ... how metric (cost/epi) minimisation
        -> like 2) just varying the metric weight to demonstrate how different cost/emission objectives change the choice of investment options
4) ... how the dynamic accountancy of interdependencies changes choices of infrastructure usage and future investments
        -> 
5) ... how the application of different investment strategies leads to different investment decisions and ultimately to more or less successful performance of the infrastructure system under the varying investment paradigmas.
'''

import pyodbc
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import ExecuteSQL as ESQL

def plot_pristine_demands_against_interdependent_demands(modelrun_ids, year, cnxn):
    fig = plt.figure()
    keyservices = (('electricity', 151), ('heat', 152), ('gas', 153), ('water', 154), ('transport', 155))
    i=1
    for keyservice, position in keyservices:
        plt.subplot(position, )
        plt.title(str(keyservice))
        x = 1
        data = ESQL.execute_SQL_script('SQLscripts\pristine_demand_over_interdep_demand.sql', [], [('keyservice_val', str(keyservice)), ('modelrun_ids_val', modelrun_ids), ('year_val', year)], cnxn) # aggregate road capacities from zones into GORs
        for (modelrun_id, total_demand, total_supply, percentage_of_supply) in data[0]:
            plt.bar(x, total_demand, 2, 0, align='center', color = 'blue', edgecolor = 'blue')
            plt.bar(x, total_supply, 2, 0, align='center', color = 'white', edgecolor = 'blue')
            plt.text(x, 0, str(modelrun_id), rotation=90)
            plt.axis('off')
            plt.axes.xmargin = 1000000
            x += 2.5
        i+=1
    plt.savefig('supply_for_demands.png')
    fig.show()

def plot_supply_for_demand_as_bars(modelrun_ids, year, cnxn):
    fig = plt.figure()
    keyservices = (('electricity', 151), ('heat', 152), ('gas', 153), ('water', 154), ('transport', 155))
    i=1
    for keyservice, position in keyservices:
        plt.subplot(position, )
        plt.title(str(keyservice))
        x = 1
        data = ESQL.execute_SQL_script('SQLscripts\demand_over_supply.sql', [], [('keyservice_val', str(keyservice)), ('modelrun_ids_val', modelrun_ids), ('year_val', year)], cnxn) # aggregate road capacities from zones into GORs
        for (modelrun_id, total_demand, total_supply, percentage_of_supply) in data[0]:
            plt.bar(x, total_demand, 2, 0, align='center', color = 'blue', edgecolor = 'blue')
            plt.bar(x, total_supply, 2, 0, align='center', color = 'white', edgecolor = 'blue')
            plt.text(x, 0, str(modelrun_id), rotation=90)
            plt.axis('off')
            plt.axes.xmargin = 1000000
            x += 2.5
        i+=1
    plt.savefig('supply_for_demands.png')
    fig.show()
    
