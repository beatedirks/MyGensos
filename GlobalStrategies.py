
'''
Created on 18 Aug 2015

@author: Beate Dirks
'''

def global_strategy_decision_making(name):
    # choose decision function based on the global_strategy_name in ISL_P_GlobalInvestmentStrategyParameters
    #if name == 'necessary_investments':
    return forecast_planning_decision_making
        
def forecast_planning_decision_making(IS, performance, strategy_object):
        (demands_met, demands_meetable, total_metric, total_margin) = performance
        #if not demands_met: 
        #    #return 'simulation_failed'
        #    return 'keep_going'
        #else:
            #if (total_metric > self.max_metric) or (total_margin < self.min_margin):
        if not (demands_meetable):
            return 'schedule_investment_plan'
        else:
            return 'keep_going'
    
 