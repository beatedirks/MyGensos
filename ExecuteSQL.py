'''
Created on 04/02/2016 

awesome tool to run SQL scripts prepared in pgAdmin in python,
accepts list of variable names and respective values to run the SQL code with

@author: Beate Dirks
'''


import string

###  EXECUTION OF SQL SCIRPTS SAVED IN pgAdmin

def execute_SQL_script(filename, variables, values, cnxn):
    theSQLs = read_SQL_file(filename)
    return execute_SQL(theSQLs, variables, values, cnxn)

###EXECUTION OF SQL-QUERY strings

def execute_SQL(theSQLs, variables, values, cnxn):
    if isinstance(theSQLs, (list, tuple)): # list of SQL queries
        results = []
        for theSQL in theSQLs:
            theSQL = insert_variables(theSQL, variables) # fill in variable values, e.g.: 'modelrun_id = ' -> 'modelrun_id = 1802'
            theSQL = insert_values(theSQL, values)       # fill in values into denotes spaces, e.g.: 'year' -> '2010'
            #theSQL = insert_values(theSQL, [('None', 'NULL')])
            cursor = cnxn.cursor()
            cursor.execute(theSQL)
            try: # if a SELECT statement, return the result of the query
                result = cursor.fetchall()
                cursor.close()
                results.append(result)
            except: # if an INSERT statement, commit the changes to the database
                cursor.commit()
                cursor.close()
                results.append(None)
        return results
    elif isinstance(theSQLs, str): # single SQL query
        theSQL = theSQLs
        theSQL = insert_variables(theSQL, variables) # fill in variable values, e.g.: 'modelrun_id = ' -> 'modelrun_id = 1802'
        theSQL = insert_values(theSQL, values)       # fill in values into denotes spaces, e.g.: 'year' -> '2010'
        #theSQL = insert_values(theSQL, [('None', 'NULL')])
        cursor = cnxn.cursor()
        cursor.execute(theSQL)
        try: # if a SELECT statement, return the result of the query
            result = cursor.fetchall()
            cursor.close()
            return result
        except: # if an INSERT statement, commit the changes to the database
            cursor.commit()
            cursor.close()
            return None

def read_SQL_file(filename):
    with open(filename, 'r') as SQLfile:
        theSQLs = []
        theSQL = ''
        for line in SQLfile:
            if line == '-- START QUERY --\n':
                if theSQL != '' :
                    theSQLs.append(theSQL) # query has been read -> add to the list
                theSQL = '' # reset string for next query
            elif line[0:2] != '--' and line[0:1] != '\xef' and line[0:1] != '\n':
                theSQL = theSQL + line
        if theSQL != '':
            theSQLs.append(theSQL) #  add last or only query to the list
        theSQLs = [string.replace(theSQL, '\n', ' ') for theSQL in theSQLs] # remove line breaks
        #theSQL = string.replace(theSQL, '\n', ' ') # remove line breaks
        #theSQL = string.replace(theSQL, "\'", "'") NOT NECESSARY
        return theSQLs

def insert_variables(theSQL, variables):
    temp_SQL = theSQL
    for (variable, value) in variables:
        old_string = variable + ' = '
        new_string = variable + ' = ' + str(value)
        temp_SQL = string.replace(temp_SQL, old_string, new_string) # replace all occurances for the variable
    return temp_SQL

def insert_values(theSQL, values):
    temp_SQL = theSQL
    for (valuename, value) in values:
        if value == None:
            temp_SQL = string.replace(temp_SQL, valuename, 'NULL') # insert values into value-places hold by the valuenames
        elif isinstance(value, (list, tuple)):
            list_str = string.replace(str(value), 'None', 'NULL') # convert python Nones into SQL Nulls
            temp_SQL = string.replace(temp_SQL, valuename, list_str) # insert values into value-places hold by the valuenames
        elif isinstance(value, str) and value != '':
            if value[0] == '"' or value[0] == "'":
                temp_SQL = string.replace(temp_SQL, valuename, str(value)) # insert without any extra ', if string value comes with "" 
            else:
                temp_SQL = string.replace(temp_SQL, valuename, str("'") + str(value) + str("'")) # insert values into value-places hold by the valuenames
        else: # number values and empty strings
            temp_SQL = string.replace(temp_SQL, valuename, str("'") + str(value) + str("'")) # insert values into value-places hold by the valuenames
    return temp_SQL




