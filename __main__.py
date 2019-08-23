#!/usr/bin/env python
# coding: utf-8

# # Momentum Indicator 
# - wrangles excel spreadsheet data with initial_wrangler.py
# - uses functions from toolbox 
# - and stores/retrieves information for sql 'database'
# 

# In[3]:

'''Libraries'''

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import timeit
import time
import sqlite3

from initial_wrangler import wrangler # functions to clean raw data 
from toolbox import tools # functions to transform dataset 

'''Request User for input parameters'''
default_parameters = input('Use DEFAULT parameters: Yes or No? ')
try:
    default_parameters = str(default_parameters).lower()
    if  default_parameters == 'yes':
        threshold = 100 
        window_list = [1,3,6,9,12]
        imputation_method = '2_weeks'
        database_name = '__m_factor_data.sqlite' # some functions interact with the database directly
        dataset_name =  'Weekly Returns - Russel1000 - weekly.xlsx'
    else:
        threshold = input('Specify threshold for outliers (RETURNS), e.g. 100: ') 
        window_list = input('Specify months (list) for rolling windows (5), e.g. [1,3,6,9,12]: ')
        imputation_method = input('Currently only "2_weeks" imputation is available, select "2_weeks": ')
        database_name = input('Sepecify name for SQL database, eg "__m_factor_data.sqlite": ') # some functions interact with the database directly
        dataset_name =  input("Specify dataset name (xlsx), e.g. 'Weekly Returns - Russel1000 - weekly.xlsx': ")        

except:
    print('Invalid Selection')

# CONNECT TO SQL DATABASE
conn = sqlite3.connect(database_name) # Name and connect to the sqlite3 database
cur = conn.cursor() # cursor allows to execute SQL queries 

# In[3]:

'''Structure Dataset into desired format''' 
start = timeit.timeit()
try: # RENAME ORIGINAL COLUMNS AND CHANGE TYPES
    print('Wrangling')
    df = wrangler.data_wrangling(dataset_name)
except:
    print('Error Wrangling')    
    
df2 = wrangler.add_breaker_row(df,'COMPANY')# STRUCTURE FOR IMPUTATION

df2_2_weeks = wrangler.imputated_returns(df2,imputation_method)# TRY DIFFERENT IMPUTATIONS

df_clean = wrangler.replace_outliers(df2_2_weeks,threshold)# REPLACE OUTLIERS WITH BEST IMPUTATION

df_clean['CUMULATIVE_RETURNS'] = np.nan # used in later functions
df_clean = df_clean.drop(['FROM_DATE','LOCAL_RETURN'],axis=1) # redundant 

end = timeit.timeit()# END WRANGLING TIMER
print ('Wrangling Complete. Time: ', end - start)


df_clean.to_sql('CleanData',con = conn, if_exists = 'replace', 
                    index = False)
df_clean.to_sql('CompoundedReturns',con = conn, if_exists = 'replace',   # use a copy of the dataset for CR
                    index = False)

# In[4]:

'''Calculate Compounded Returns for entire Index and by week'''
df_index = tools.build_index_returns(df_clean) # BUILD AN INDEX FOR ALL COMPANIES 
df_index.to_sql('IndexData',con = conn, if_exists = 'replace', index = True)

# In[29]:

'''Calculate Compounded Returns by Company by week'''
companies_list = df_clean.COMPANY.unique() 
tools.compounded_returns(database_name,companies_list) #df_clean modified in sql 


# In[29]:

'''Calculate Z-Scores for each window by Company and by week'''
start = time.time()

df_CR = pd.read_sql('select * from CompoundedReturns',conn)

for monthly_window in window_list: # 35 mins Time:  3635.4724400043488
    df_z_scores = tools.rolling_window_sql(df_CR, monthly_window,database_name)
    print('Finished Month_:'+str(monthly_window))
    
end = time.time()
print('Z-Scores Complete. Time: ', end - start)   

df_z_scores.to_sql('Z_Scores',con = conn, if_exists = 'replace', index = False)


# In[37]:

''' Generate Company Scores '''

df_z_scores = pd.read_sql("SELECT * from Z_Scores", conn)

'''Calculate the average of the Z-Scores of each company on a week by week basis'''

df_z_scores2 = tools.weekly_avg_returns(df_z_scores)
df_z_scores2.to_sql('Z_Scores_2',con = conn, if_exists = 'replace', # update Z_Scores table 
                    index = False)

# VITAL TO RETRIEVE THIS DATA FROM SQL TABLE
df_z_scores_sql = pd.read_sql_query('select * from Z_Scores_2 group by TO_DATE, AVG_Z_SCORE;' ,conn)
dict_weekly_groups, dates = tools.weekly_data_dict(df_z_scores_sql,'AVG_Z_SCORE')# BREAKS DF INTO SECTIONS BY DATE     

''' FOR EACH SECTION (WEEK) CALCULATE AVG & STD OF COMPANY AVG_Z_SCORE'''
weekly_avg_returns_mean,weekly_avg_returns_std = tools.weekly_mean_std_dict(dict_weekly_groups, dates)
df_weekly_quintiles  = tools.append_weekly_mean_std (df_z_scores_sql ,weekly_avg_returns_mean,weekly_avg_returns_std,dates)

''' CALCULATE Z-SCORES #2 FOR EACH COMPANY BY WEEK '''
df_weekly_quintiles['COMPANY_SCORE'] = (df_weekly_quintiles['AVG_Z_SCORE'] - df_weekly_quintiles['WEEKLY_MEAN'] ) / df_weekly_quintiles['WEEKLY_STD']

df_weekly_quintiles.to_sql('WeeklyQuintiles',con = conn, if_exists = 'replace', # update Z_Scores table 
                    index = False)

''' FOR EACH WEEK ASSIGN COMPANY TO QUINTILE ACCORDING TO Z-SCORE. STORE IN NEW SQL TABLE '''
# ¡ THIS IS A FUNCTION !
tools.weekly_quantiles_to_sql(dates,database_name)

# In[ ]:

'''STEP 5: Generate Compounded Returns by Quintile and create Quintile Indices'''

df_quintiles = pd.read_sql_query("SELECT * from WeeklyQuintiles_2", conn)
df_quintiles = df_quintiles.set_index('TO_DATE')

df_q_returns = tools.total_weekly_quintile_return(df_quintiles) # AGGREGATE WEEKLY RETURNS

# CALCULATE COMPOUNDED RETURNS BY WEEK FOR EACH QUINTILE
df_q_compounded_returns = tools.quintile_compounded_returns(df_q_returns)

df_q_compounded_returns.to_sql('QuintileIndices',con = conn, if_exists = 'replace', # update Z_Scores table 
                    index = True)

# In[463]:

''' Can visualize results '''

print(df_q_compounded_returns.describe())
df_q_compounded_returns.plot(subplots=True,figsize=(20,20))


# In[ ]:

''' Generate Relative Compounded Quintile Returns '''

# for WeeklyQuintiles_2 , divide each Quintile's CR by the Average CR for that week to make them relative
df_q_index = pd.read_sql_query("SELECT * from QuintileIndices", conn)

df_q_index.columns =['TO_DATE','QUINTILE_1','QUINTILE_2','QUINTILE_3','QUINTILE_4','QUINTILE_5']
df_q_index = df_q_index[1:].set_index('TO_DATE')

df_relative_returns = tools.relative_quintile_returns(df_q_index)

df_relative_returns.to_sql('QuintileRelativeReturns',con = conn, if_exists = 'replace', # update Z_Scores table 
                    index = True)


# In[ ]:




conn.close()

