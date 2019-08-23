#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 08:34:42 2019

@author: e03529
"""
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import timeit
import statsmodels.api as sm
from pylab import rcParams
import sqlite3

class tools():
     
    
    
    ############## COMPOUNDED RETURN INDICES ##############
    
    
       
    def build_index_returns(df):
        # companies by week
        companies_by_week = df['RETURNS'].groupby(df['TO_DATE']).count()
        
        # new dataframe 
        df_index = pd.DataFrame()

    
        # index dataframe added companies by week
        df_index['Companies/Week'] = companies_by_week
        df_index.head()
    
        # total returns by week 
        df_index['Total_Returns'] = (df['RETURNS'].groupby(df['TO_DATE']).sum())
    
        # average returns by week 
        df_index['Avg_Returns'] = df_index['Total_Returns'].div(df_index['Companies/Week'])
        df_index = df_index.reset_index()
    
        # convert from % returns. Insert row with value 100
        data = []
        data.insert(-1, {'Avg_Returns': 0})
        df_index = pd.concat([pd.DataFrame(data), df_index], ignore_index=False,sort=False)
    
        # calculate cummulative returns 
        list1 = df_index['Avg_Returns'][1:].values;
        list2 = [100] # starting point
        for i,j in enumerate( list1 ):
            list2.append((1+j/100)*list2[i])
        df_index['CUMULATIVE_RETURNS'] = list2
    
        # set index column to FROM_DATE
        df_index = df_index.set_index(['TO_DATE'])  
    
        return df_index #['Cum_Returns']
    
    def build_company_returns(df,company_name):
        df_company = df.loc[df['COMPANY'] == company_name]
    
        data = []
        data.insert(-1, {'CUMULATIVE_RETURNS': 0})
        df_company = pd.concat([pd.DataFrame(data), df_company], ignore_index=False,sort=False)
    
        # calculate cummulative returns 
        list1 = df_company['RETURNS'][1:].values;
        list2 = [100] # starting point
        for i,j in enumerate( list1 ):
            list2.append((1+j/100)*list2[i])
        df_company['CUMULATIVE_RETURNS'] = list2
        
        # set index column to FROM_DATE
        df_company = df_company.set_index(['TO_DATE'])  
    
        return df_company
    
    def build_sector_returns(df):
        # GET ALL SECTORS
        sectors = df['SECTOR'].unique()
        frames = []
        
        # GENERATE CUM RETURNS FOR EACH SECTOR
        for s in sectors:
            df_sector = df.loc[df['SECTOR'] == s]
            df_sector = df_sector.reset_index()    
            data = []
            data.insert(-1, {'CUMULATIVE_RETURNS': 0})
            df_sector = pd.concat([pd.DataFrame(data), df_sector], ignore_index=False,sort=False)
    
            # calculate cummulative returns 
            list1 = df_sector['RETURNS'][1:].values;
            list2 = [100] # starting point
            for i,j in enumerate( list1 ):
                list2.append((1+j/100)*list2[i])
            df_sector['CUMULATIVE_RETURNS'] = list2
            frames.append(df_sector[['CUMULATIVE_RETURNS','SECTOR','TO_DATE']])
        
        # CONCATENATE DFs
        df_all_sectors = pd.concat(frames)
        # PIVOT TO TURN ROWS INTO COLUMNS
        reshaped_df = df_all_sectors.pivot_table(index = ['TO_DATE'], columns = ['SECTOR'], values = ['CUMULATIVE_RETURNS'])
        
        return reshaped_df
    
    ''' NEW FUNCTION FOR COMPOUNDED RETURNS BY COMP BY WEEK '''
    def compounded_returns(database_name, companies_list ):
        conn = sqlite3.connect(database_name) # Name and connect to the sqlite3 database
        cur = conn.cursor() # cursor allows to execute SQL queries     
        
        for comp in companies_list:
    
            # RETRIEVE NON-NAN VALUES BY COMPANY
            df_p = pd.read_sql('select * from CompoundedReturns where COMPANY == "{}" and RETURNS is not null;'.format(str(comp)),conn)
    
            # DELETE EXTRACTED DATA
            cur.execute('DELETE from CompoundedReturns where COMPANY = "{}" and RETURNS is not null;'.format(str(comp)))
            conn.commit() # need thiis
    
            # INSERT EMPTY ROW TO BEGIN AT PAR
            data = []
            data.insert(-1, {'RETURNS': 0})
            df_p = pd.concat([pd.DataFrame(data), df_p], ignore_index=False,sort=False)
    
            list1 = df_p['RETURNS'][1:].values
            list2 = [100] # starting point
    
            # COMPOUNDING RETURNS EQUATION
            for i,j in enumerate( list1 ):
                list2.append((1+j/100)*list2[i])
            df_p['CUMULATIVE_RETURNS'] = list2     
            #df_p['RETURNS'] = list2  
    
            df_p = df_p[1:] # remove extra row
    
            # APPEND DELETED ROWS WITH NEW VALUES
            df_p.to_sql('CompoundedReturns',conn, if_exists='append',index=False)
        
        conn.close()    
    
    ''' NEW FUNCTION THAT USES CR FROM CompoundedReturns DB'''
    def rolling_window_sql(df, monthly_window,database_name):
        
        conn = sqlite3.connect(database_name)
        cur = conn.cursor() # cursor allows to execute SQL queries 
        # CONVERT WINDOW INTO WEEKS ~4W/1M
        window = monthly_window * 4 
        
        # used to name new columns
        w_name = str(monthly_window)+'M_WINDOW'
        z_name = str(monthly_window)+'M_Z-SCORE'
        
        # RETRIEVE C. RETURNS FOR INDEX
        df_index = pd.read_sql('select * from IndexData',conn)
        df_index = df_index[1:] 
        
        
        # CREATE WINDOW FOR INDEX 
        df_index[w_name] = df_index['CUMULATIVE_RETURNS'].rolling(window).mean() # 4 rows, each row is a week
        
        # CREATE NEW COLUMN Z-SCORES
        #df = pd.read_sql('select * from CompoundedReturns',conn)
        df[z_name] = np.nan
        
        # CALCULATE Z-SCORE FOR EACH COMPANY
        for company_name in df['COMPANY'].unique():
            
            # GENERATE X. RETURNS FOR COMPANY
            df_comp = df.loc[df['COMPANY']==company_name]
            
            # CREATE WINDOW FOR COMPANY  #CUMULATIVE_RETURNS
            df_comp[w_name] = df_comp['CUMULATIVE_RETURNS'].rolling(window).mean() # 4 rows, each row is a week
            
            # CALCULATE Z-SCORES FOR WINDOW            
            df[z_name].loc[df['COMPANY']==company_name] = (
                        (df_comp[w_name] - df_index[w_name].mean()) / 
                        df_index[w_name].std()
                        )
        conn.close()
        return df    
    ############## INDEX ANALYSIS ##############
    
    
    
    def index_decomposition(df):
        rcParams['figure.figsize'] = 14, 12

        decomposed_index = sm.tsa.seasonal_decompose(df['CUMULATIVE_RETURNS'],freq=52) # The frequncy is annual
        
        #figure = decomposed_index.plot()
        #return plt.show()
        
        observed = decomposed_index.observed
        trend = decomposed_index.trend 
        seasonal = decomposed_index.seasonal 
        resid = decomposed_index.resid 
            
        return observed,trend,seasonal,resid
    
    
    # WORK IN PROGRESS !!!!!!!!!
    def sector_3D_plot (df):
        # My companies list # 'Communications', REMOVED!!!
        xlist = [ 'Services','Consumer', 'Discretionary','Consumer' 'Staples','Energy','Financials','Health' ,'Care','Industrials','Materials','Utilities']

        # My dates list
        t = df.reset_index()
        ylist = list(t["TO_DATE"])
    
        # My returns list
        zlist = []
        for row in df.iterrows():
            index, data = row
            zlist.append(data.tolist())        
        zlist = np.log(zlist)  #normalize scale 
        
        return xlist, ylist, zlist
    
    

    ############## MOMENTUM INDICATOR ##############



    # CALCULATES THE Z-SCORE OF COMPANIES ACCORDING TO WINDOW SIZE (MONTHS)
    def rolling_window(df,window_size_months,database_name):
        # CONVERT WINDOW INTO WEEKS ~4W/1M
        window = window_size_months * 4 
        #conn = sqlite3.connect(database_name)
        #cur = conn.cursor() # cursor allows to execute SQL queries 


        # GENERATE C. RETURNS FOR INDEX
        df_index = tools.build_index_returns(df)
        #df_index = pd.read_sql('select * from IndexData;' ,conn)
        #df_index = df_index.reset_index()
        #drop first row else error: index must be monotonic
        #df_index = df_index.drop(df.index[[0]])
        
        # CREATE WINDOW FOR INDEX 
        #df_index['1M_WINDOW'] = df_index['CUMULATIVE_RETURNS'].rolling('30D').mean() # 30 days
        df_index[str(window_size_months)+'M_WINDOW'] = df_index['CUMULATIVE_RETURNS'].rolling(window).mean() # 4 rows, each row is a week
        
        # CREATE NEW COLUMN Z-SCORES
        df[str(window_size_months)+'M_Z-SCORE'] = np.nan
        df['CUMULATIVE_RETURNS'] = np.nan
        # CALCULATE Z-SCORE FOR EACH COMPANY
        for company_name in df['COMPANY'].unique():
            
            # GENERATE X. RETURNS FOR COMPANY
            df_comp = tools.build_company_returns(df,company_name)
            #drop first row else error: index must be monotonic
            #df_comp = df_comp.drop(df_comp.index[[0]])
            df_comp = df_comp.reset_index()
            
            # CREATE WINDOW FOR COMPANY 
            df_comp[str(window_size_months)+'M_WINDOW'] = df_comp['CUMULATIVE_RETURNS'].rolling(window).mean() # 4 rows, each row is a week
            
            # CALCULATE Z-SCORES FOR WINDOW            
            df[str(window_size_months)+'M_Z-SCORE'].loc[df['COMPANY']==company_name] = (
                        (df_comp[str(window_size_months)+'M_WINDOW'] - df_index[str(window_size_months)+'M_WINDOW'].mean()) / 
                        df_index[str(window_size_months)+'M_WINDOW'].std()
                        )
            df['CUMULATIVE_RETURNS'].loc[df['COMPANY']==company_name] = df_comp['CUMULATIVE_RETURNS']
        #conn.close()
        # RETURN UPDATED DF
        return df
    
    def weekly_avg_returns (df): 
        # the average z-scores of a company accross all its windoes for a specific week (row wise mean not column wise)
        df['AVG_Z_SCORE'] = df[['1M_Z-SCORE','3M_Z-SCORE','6M_Z-SCORE','9M_Z-SCORE','12M_Z-SCORE']].mean(axis=1)
        return df    
        
    
    # ____________ PART OF Z-SCORES #2 CALCULATION
    # BREAKS DF INTO SECTIONS BY DATE
    def weekly_data_dict (df,variable_name):
        # COLLECT ALL DATES
        dates = list(df['TO_DATE'].unique())
        # CREATE HASH TABLE FOR DATA BASED ON INDIVIDUAL WEEKS AS KEYS
        data = dict(tuple(df[['COMPANY',variable_name]].groupby(df['TO_DATE'])))#dict(tuple(df2['AVG_Z-SCORE'].groupby(inputdata['TO_DATE'])))
    
        return data, dates 
        
    # FOR EACH SECTION (WEEK) CALCULATE AVG & STD OF COMPANY AVG_Z_SCORE
    def weekly_mean_std_dict (data_dict,dates):    
        # GET m and s FOR POPULATION TO APPLY SECOND Z-SCORE. (POP = COMPANIES IN SAME WEEK)
        weekly_avg_returns_mean = {} # can plot 
        weekly_avg_returns_std = {}
    
        for week in dates:
            # using dictionaries instead of lists 
            weekly_avg_returns_mean[week] = data_dict[week].mean()
            weekly_avg_returns_std[week] = data_dict[week].std()
            
        return weekly_avg_returns_mean,weekly_avg_returns_std 
    
    def append_weekly_mean_std(df,weekly_avg_returns_mean,weekly_avg_returns_std,dates):  # COULD CALL PREVIOUS FUNCTION
        df['WEEKLY_MEAN'] =np.nan
        df['WEEKLY_STD'] =np.nan
        for i in dates:               # ADD TOOLS 
            df.loc[df['TO_DATE'] == i, 'WEEKLY_MEAN'] = float(weekly_avg_returns_mean[i])   #w_s['AVG_Z_SCORE'] #w_s['AVG_Z_SCORE'].loc['index'==i]
            df.loc[df['TO_DATE'] == i, 'WEEKLY_STD'] = float(weekly_avg_returns_std[i])   #w_s['AVG_Z_SCORE'] #w_s['AVG_Z_SCORE'].loc['index'==i]
        return df 
    
    
    def weekly_quantiles_to_sql(dates,database_name):
        conn = sqlite3.connect(database_name) # Name and connect to the sqlite3 database
        cur = conn.cursor() 
        for i in dates[1:]:  # MANY MISSING VALUES IN 1st WEEK. SKIP IT 
            # CREATE AN MUTABLE STRING THAT QUERIES DATA
            querystring = "select * from WeeklyQuintiles where TO_DATE = '{}';".format(i)
            # RETRIEVE SECTIONS BY WEEK
            section = pd.read_sql_query(querystring ,conn)
            # CREATE QUINTILES
            section['QUINTILES'] = pd.qcut(section['COMPANY_SCORE'][1:], 5, labels=False,duplicates='drop')

    
            # BUILD A NEW DB WEEK BY WEEK
            section.to_sql("WeeklyQuintiles_2", conn, if_exists="append",index = False) # Insert new values to the existing table.
        conn.close()
    
    # AGGREGATE WEEKLY RETURNS
    def total_weekly_quintile_return(df):
        data = df.reset_index()[ ['QUINTILES','TO_DATE','RETURNS','COMPANY' ] ]
        # sorted by quintile
        # aggregated by date by summing all Returns
        # return data.pivot_table(index='TO_DATE',columns='QUINTILES',values='RETURNS',aggfunc=np.sum)
        return data.pivot_table(index='TO_DATE',columns='QUINTILES',values='RETURNS',aggfunc=np.mean)
        
    # CALCULATE COMPOUNDED RETURNS BY WEEK FOR EACH QUINTILE
    def quintile_compounded_returns(df):
        quintiles = list(df.columns)
        df_q = df
        
        blank_row = pd.DataFrame({'0.0': 0, '1.0': 0, '2.0': 0, '3.0': 0, '4.0': 0, 
                            }, index =[0]) 
            
        # Concatenate new_row with df  
        df_q = pd.concat([blank_row, df_q[:]])#.reset_index(drop = True) 
    
        for q in quintiles:
            # col_name = (str(q)+'_Q_COMP.R.')
            col_name = ('QUINTILE_{}'.format(int(q)+1))
            df_q[col_name] = df_q.iloc[:,:1]
                
            list1 = df_q[str(q)][1:].values
            list2 = [100] # starting point
            for i,j in enumerate( list1 ):
                list2.append((1+j/100)*list2[i])
            df_q[col_name] = list2    
                
        return df_q.iloc[:,5:]        
    
    # EACH QUINTILE'S CR IS DIVIDED BY THE AVG WEEKLY CR 
    # FOR RELATIVE COMPARISON
    

    def relative_quintile_returns (df):
        df['INDEX_AVG'] = df.mean(axis=1)
        df = df.reset_index()
        for i in ['QUINTILE_1','QUINTILE_2','QUINTILE_3','QUINTILE_4','QUINTILE_5']:
            df[i] = ( df[i] / df['INDEX_AVG'] ) -1
        df['INDEX_AVG'] = (df['INDEX_AVG'] / df['INDEX_AVG']) -1     #  should divide by 100
        df = df.set_index('TO_DATE')
        return df[['INDEX_AVG','QUINTILE_1','QUINTILE_2','QUINTILE_3','QUINTILE_4','QUINTILE_5']]

    
    
    ############## 3D SUR ##############
    
    
    
    def _create_axis(axis_type, title = None):
        """
        Creates a 2d or 3d axis.
        :params axis_type: 2d or 3d axis
        :params variation: axis type (log, line, linear, etc)
        :parmas title: axis title
        :returns: plotly axis dictionnary
        """
        
        variation="Linear",
        
        if axis_type not in ["3d", "2d"]:
            return None

        default_style = {
            "background": "rgb(230, 230, 230)",
            "gridcolor": "rgb(255, 255, 255)",
            "zerolinecolor": "rgb(255, 255, 255)",
        }

        if axis_type == "3d":
            return {
                "showbackground": True,
                "backgroundcolor": default_style["background"],
                "gridcolor": default_style["gridcolor"],
                "title": title,
                "type": variation,
                "zerolinecolor": default_style["zerolinecolor"],
            }    
    
    def _create_layout(layout_type, xlabel, ylabel,zlabel):
        """ Return dash plot layout. """
        xlabel="SECTOR",
        ylabel="DATE",
        zlabel="COMPANY SCORE",
        base_layout = {
            "xaxis": xlabel,
            "yaxis": ylabel,
            "zaxis": zlabel,                
            "font": {"family": "Raleway"},
            "hovermode": "closest",
            "margin": {"r": 20, "t": 0, "l": 0, "b": 0},
            "showlegend": True,
            "height" : 900,

        }

        
        base_layout["scene"] = {
            "xaxis": tools._create_axis(axis_type="3d", title= xlabel),
            "yaxis": tools._create_axis(axis_type="3d", title= ylabel),
            "zaxis": tools._create_axis(axis_type="3d", title= zlabel),
            "camera": {
                "up": {"x": 0, "y": 0, "z": 1},
                "center": {"x": 0, "y": 0, "z": 0},
                "eye": {"x": 0.08, "y": 2.2, "z": 0.08},
            }},
        
        return base_layout
    
    def create_plot(x,y,z,plot_type="surface"):
        xlabel="SECTOR",
        ylabel="DATE",
        zlabel="COMPANY SCORE",
    #     colorscale = [
    #         [0, "rgb(244,236,21)"],
    #         [0.3, "rgb(249,210,41)"],
    #         [0.4, "rgb(134,191,118)"],
    #         [0.5, "rgb(37,180,167)"],
    #         [0.65, "rgb(17,123,215)"],
    #         [1, "rgb(54,50,153)"],
    #     ]
        data = [
            {
                "x": x,
                "y": y,
                "z": z,
    #             "mode": "markers",
    #             "marker": {
    #                 "colorscale": colorscale,
    #                 "colorbar": {"title": "Molecular<br>Weight"},
    #                 "line": {"color": "#444"},
    #                 "reversescale": True,
    #                 "sizeref": 45,
    #                 "sizemode": "diameter",
    #                 "opacity": 0.7,
    #                 "size": size,
    #                 "color": color,
    #             },
    #             "text": name,
                "type": plot_type,
            }
        ]


        layout = tools._create_layout(plot_type, xlabel, ylabel,zlabel)

    #     if len(markers) > 0:
    #         data = data + _add_markers(data, markers, plot_type=plot_type)

        return {"data": data, "layout": layout}








# __ METHODOLOGY __
''' FORECASTING

- using cum returns for Z-Scores calculations 
    # otherwise why build index net change in 
    # to be able to track change in returns over time 
    
- use raw returns for rolling window forecast, not c. returns 
    # interested in performance in specified period (window)
    # otherwise all large c.return stocks will dominate, even if worse-off in specified period 
    
- use weekly Z score for groupings not average Z score by company
    # because want composition of quintile to be fluid, so that best performing stocks are chosen
    
### NOTES
- Z-Score #1 allows cross-frequency comparison (population all companies by window freq)
    - averaging z scores horizontally (by week for all freqs), not vertically 
- Z-Score #2 allows cross-company comparison (population all companies by avg z-score)

#### ISSUE 
- companies with returns are missing Z-score values
- 'bebe stores, inc.' is mostly intact but has no z-scores
- issue may be with company returns function
- since data completeness between windows within expected bounds

'''
    
    