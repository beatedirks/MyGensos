
import GlobalStrategies as GlobStrat


class Global_Strategy(): 
    '''
    Global Investment Strategies can differ in the way investment decisions are taken. 
    Hence this information is stored in a Global_Strategy object, which receives a 
    customized list of parameters (see Main-Simulation.py -> load_global_strategy),
    as defined in the table 'ISL_I_global_strategy_parameters'
    and a customized decision making function as imported from the file 'GlobalStrategies.py'.
    ''' 
    def __init__(self, global_strategy_id, cnxn):
        cursor = cnxn.cursor()
        cursor.execute('select global_strategy_name from "ISL_P_GlobalInvestmentStrategyParameters" where global_strategy_id = ' + str(global_strategy_id))
        self.name = cursor.fetchone()[0]
        param_data = list(cursor.execute('select * from "ISL_P_GlobalInvestmentStrategyParameters" where global_strategy_id = ' + str(global_strategy_id)))
        # pull in parameters and name them based on the parameter_name field
        for new_param in param_data:
            exec 'self.%s=%s(%s)' % (new_param[-4],new_param[-3],new_param[-2])
        cursor.close()
    
    def make_decisions(self, IS, performance):
        decision_function = GlobStrat.global_strategy_decision_making(self.name)
        return decision_function(IS, performance, self)
 
class Global_Scenario():
    '''
    The Global Scenario is decisive for the demands for specific keyservices and also
    for available supply of options to cater for these keyservices. 
    In the functions load_global_strategy in Main-Simulation.py, a list of customized parameters, 
    as defined in table 'isl_i_global_socioeconomic_scenario_parameters', is added to the Global_Scenario object.
    '''
    def __init__(self, global_scenario_id, cnxn):
        cursor = cnxn.cursor()
        cursor.execute('select scenario_id, global_scenario_name from "ISL_P_GlobalSocioeconomicScenarioParameters" where scenario_id = ' + str(global_scenario_id))
        self.id, self.name = cursor.fetchone()
        param_data = list(cursor.execute('select * from "ISL_P_GlobalSocioeconomicScenarioParameters" where scenario_id = ' + str(global_scenario_id)))
        for new_param in param_data:
            exec 'self.%s=%s(%s)' % (new_param[-5],new_param[-4],new_param[-3])
        cursor.close()

class Local_Strategies():
    def __init__(self, submodel_strategies_id, cnxn):
        self.local_strategies = {}
        submodels = ['Transport', 'Water', 'WW', 'SW', 'Energy', 'ES']  # translation of ITRC names into my model names        
        cursor = cnxn.cursor()
        theSQL = 'SELECT "TR_substrategy_id", "WS_substrategy_id", "WW_substrategy_id", "SW_substrategy_id", "ED_substrategy_id", "ES_substrategy_id" \
                        FROM "ISL_S_LocalStrategiesPortfolios" WHERE submodel_strategy_id =' + str(submodel_strategies_id)
        cursor.execute(theSQL)
        submodel_strategies_ids = cursor.fetchone()  
        for (submodel, strategy_id) in zip(submodels, submodel_strategies_ids):
            new_local_strategy = Local_Strategy(submodel, strategy_id, cnxn)
            theSQL = 'SELECT parameter_name, parameter_datatype, parameter_value FROM "ISL_P_LocalStrategyParameters" WHERE \
                        submodel =' + str("'") + str(submodel) + str("'") + ' AND local_strategy_id = ' + str(strategy_id)
            param_data = list(cursor.execute(theSQL))
            for new_param in param_data:
                exec 'new_local_strategy.%s=%s(%s)' % (new_param[0],new_param[1],new_param[2])
            self.local_strategies[submodel] = new_local_strategy

    def __getitem__(self, submodel):
        return self.local_strategies[submodel]
    
class Local_Strategy():
    def __init__(self, submodel_name, strategy_id, cnxn):
        self.submodel_name = submodel_name
        self.strategy_id = strategy_id
        
class Modelrun_Params():
    def __init__(self, start_year, end_year, no_build):
        self.start_year = start_year
        self.end_year = end_year
        self.no_build = no_build
 
