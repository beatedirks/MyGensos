'''

@last updated 02/11/2017
@author: Beate Dirks, Matt Ives

#? - needs completion of documentation
#UPGRADE - suggestions for improving the system
#READ_ME - information about documentation and/or usage of the simulation environment
#DOC - actual documentation of the respective code
______________________________________________________________________________________

Main Execution File of the Integrated Infrastructure Planning System
--------------------------------------------------------------------------------------

Main.py triggers the modelruns, the data visualization or the analysis tools, as specified by the user in __main__.

MODELRUNS
In the case of a modelrun, __main__ calls Modelrun.run_modelruns(), to trigger a series of modelruns. 
#READ_ME -  PLease refer to the documentation in Modelrun.py for an overview of the simulation implementation.

MODELRUN VISUALIZATION
Modelrun visualization retrieves modelrun specific data from the "ISL_IO_..." and "ISL_O_..." tables to display the results of each time step of the simulation as a 
stack of the regions, for which the simulation was performed. Blue to red colour coded regions or colour coded arrows denote degree of supply for given commodity or transport 
demand, respectively. Red to orange colour coded arrows denote exchange of commodities between regions, eg. water, electricity or gas.

MODELRUN ANALYSIS
...

'''
 
import Modelrun as MR
#import Modelrun_Visualization as MV
#import Modelrun_Analysis as MA
import pyodbc
import psycopg2




# main programme --------------------------------------------------------------------             

if __name__ == '__main__':
    '''
    __main__ runs, according to user selection a main simulation, a data visualization or other analysis tools '''
    
    # opens the database connection
    #cnxn = pyodbc.connect('Driver={PostgreSQL ODBC Driver(ANSI)};DSN=PostgreSQL30;Server=localhost;Port=5432;Database=infrastructuresystem;UId=postgres;Password=Bubbles33@cmp;')
    cnxn = pyodbc.connect('Driver={PostgreSQL ODBC Driver(ANSI)}; Server=127.0.0.1;Port=5432;Database=infrastructuresystem;UId=beate;Password=Bubbles33@cmp;')
    #cnxn = psycopg2.connect("dbname='infrastructuresystem' user='beate' host='127.0.0.1' password='Bubbles33@cmp'")
    cursor = cnxn.cursor()
    
    #modelrun_ids = [60, 61, 62, 63, 64, 65]  
    #modelrun_ids = [4000, 4050, 5000] 
    #modelrun_ids = [2058, 2059, 2060, 2061, 2062, 2063, 2064, 2065] 
    #modelrun_ids = [1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017] 
    #modelrun_ids = [1018, 1019, 1020, 1021, 1022, 1023] 
    #modelrun_ids = [4000, 4010, 4020, 4030, 4040, 4050, 4060, 4070, 4080, 4090, 5000] 
    #modelrun_ids = [4000, 4050, 5000] 
    #modelrun_ids = [2058, 2059, 2060, 2061, 2062, 2063, 2064, 2065] 
    modelrun_ids = [1] 

    MR.run_modelruns(cnxn, modelrun_ids)   
    #MV.visualize_modelruns(modelrun_ids, cnxn)   
    #MA.plot_supply_for_demand_as_bars(modelrun_ids, 2035, cnxn)

    
    # close database connection
    cnxn.close()

     