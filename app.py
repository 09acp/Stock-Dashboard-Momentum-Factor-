#!/usr/bin/env python
# coding: utf-8

# - dash_dates2 version

# In[1]:

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import plotly.graph_objs as go
from datetime import datetime
import pandas as pd 
import numpy as np
import statsmodels.api as sm
import sqlite3

from toolbox import tools # FORMATS COMPANY AND INDEX DATA 

database_name = '__m_factor_data.sqlite' # some functions interact with the database directly

# CONNECT TO SQL DATABASE
conn = sqlite3.connect(database_name) # Name and connect to the sqlite3 database
cur = conn.cursor() # cursor allows to execute SQL queries 

# In[3]: 

''' TAB 1 Prerequisites: Companies '''

df_comp_returns = pd.read_sql('select * from CleanData;',conn) # USED FOR STOCK RETURNS TAB;
df_comp_returns = df_comp_returns[1:]
df_comp_returns['TO_DATE'] = pd.to_datetime(df_comp_returns['TO_DATE'], format='%Y-%m-%d', errors='coerce')

dates_companies = df_comp_returns['TO_DATE'] # SET DATE RANGE


df_comp_returns = df_comp_returns.set_index(['TO_DATE'])

companies_with_data = pd.read_sql('select COMPANY from CompoundedReturns;',conn) 

options_companies = [{'label': i, 'value': i} for i in companies_with_data.COMPANY.unique()]# CREATE A LIST WITH A DICTIONARY FOR EVERY COMPANY
options_companies.append({'label':'Russell Index','value':'Russell Index'}) # ADD INDEX TO LIST FOR USE AS A BENCHMARK

# In[3]: 

''' TAB 2 & 3 Prerequisites: Factors '''

df_factor_returns = pd.read_sql('select * from QuintileIndices;',conn) # USED FOR STOCK RETURNS TAB;
df_factor_returns = df_factor_returns[1:] # remove needless date
# convert dates to proper format 
df_factor_returns['TO_DATE'] = pd.to_datetime(df_factor_returns['index'], format='%Y-%m-%d', errors='coerce')
df_factor_returns = df_factor_returns.drop('index',axis=1)
dates_factors = df_factor_returns['TO_DATE'] # drop down option for dates 

df_factor_returns = df_factor_returns.set_index(['TO_DATE'])

# drop down options for factor selection
options_factors = [{'label': i, 'value': i} for i in list(df_factor_returns.columns)]# CREATE A LIST WITH A DICTIONARY FOR EVERY COMPANY
options_factors.append({'label':'Russell Index','value':'Russell Index'}) # ADD INDEX TO LIST FOR USE AS A BENCHMARK

conn.close()


# In[4]:

''' Dash App '''

app = dash.Dash()
# Boostrap CSS.
app.css.append_css({'external_url': 'https://codepen.io/amyoshino/pen/jzXypZ.css'})  # noqa: E501


app.layout = html.Div([
        
    dcc.Tabs(id="tabs", children=[  # ALL TABS START

        # TAB 1 Momentum Factor: Relative Quintile Returns
        dcc.Tab(label='Momentum Factor: RQRs', children=[
            html.Div([
                html.H1("Relative Quintile Returns", style={'textAlign': 'center'}),
                
                dcc.Dropdown(id='factor_dropdown',
                             options= options_factors,
                             multi=True,
                             value=['Russell Index'],style={"display": "block","margin-left": "auto","margin-right": "auto","width": "60%"}
                             ),
            
                dcc.DatePickerRange(id='factor_date_range',
                                    
                    min_date_allowed = dates_factors.min(), # SET LIMITS 
                    max_date_allowed = dates_factors.max(), 
                    start_date = dates_factors.min(),  # DEFAULT START DATE
                    end_date = dates_factors.max(),    # DEFAULT END DATE
                    
                    
                    calendar_orientation= 'vertical',
                                    ),  
            
            	html.Button(id='submit_factors',
            								n_clicks = 0,
            								children = 'Submit',
            								style = {'fontSize': 24, 'marginLeft': '30px'}),
                                 
                dcc.Graph(id='factor_graph'),
            ]),
            
        ]),
        
        # Tab 2, Momentum Factor: Compounded Quintile Returns
        dcc.Tab(label='Momentum Factor: CQRs', children=[
            html.Div([
                html.Div([
                html.H1("Compounded Quintile Returns", style={'textAlign': 'center'}),
                
                dcc.Dropdown(id='factor_dropdown_tab2',
                             options= options_factors,
                             multi=True,
                             value=['Russell Index'],style={"display": "block","margin-left": "auto","margin-right": "auto","width": "60%"}
                             ),
            
                dcc.DatePickerRange(id='factor_date_range_tab2',
                                    
                    min_date_allowed = dates_factors.min(), # SET LIMITS 
                    max_date_allowed = dates_factors.max(), 
                    start_date = dates_factors.min(),  # DEFAULT START DATE
                    end_date = dates_factors.max(),    # DEFAULT END DATE
                    
                    
                    calendar_orientation= 'vertical',
                                    ),  
            
                	html.Button(id='submit_factors_tab2',
                								n_clicks = 0,
                								children = 'Submit',
                								style = {'fontSize': 24, 'marginLeft': '30px'}),
                                     
                dcc.Graph(id='factor_graph_tab2'),
                        ]),
                ],className="row"),
                             
            html.Div([
                html.Div([    
                    # NEW FACTOR SECTOR DECOMPOSITION
                    
                    #html.H3("Quintile Composition", style={'textAlign': 'center'}),
                    dcc.Graph(id='factor_bench'),
                         ],className='pretty_container six columns',#  className='six columns',
                        ),
    
                html.Div([
                    
                    dcc.Graph(id='factor_pie'),
                         ],className='pretty_container six columns',#className='six columns',
                        ),
                    ],className="row"),          
        ]),            
         
        # TAB 3 Compounded Company Returns
        dcc.Tab(label='Company Data', children=[
            html.Div([
                html.H1("Company Analysis", style={'textAlign': 'center'}),
                html.H3("Compounded Company Returns", style={'textAlign': 'center'}),
                
                dcc.Dropdown(id='company_dropdown',
                             options= options_companies,
                             multi=True,
                             value=['Russell Index'],style={"display": "block","margin-left": "auto","margin-right": "auto","width": "60%"}
                             ),
            
                dcc.DatePickerRange(id='company_date_range',
                    min_date_allowed = dates_companies.min(), # SET LIMITS 
                    max_date_allowed = dates_companies.max(), 
                    start_date = dates_companies.min(),#'2000-01-10', # DEFAULT START DATE
                    end_date = dates_companies.max(),#'2010-01-10', # DEFAULT END DATE
                    
                    calendar_orientation= 'vertical',
                                    ),  
            
            	html.Button(id='submit_companies',
            								n_clicks = 0,
            								children = 'Submit',
            								style = {'fontSize': 24, 'marginLeft': '30px'}),
                                 
                dcc.Graph(id='company_graph'),
                
                # FLUX ELEMENT                
                html.H3("Company Flux", style={'textAlign': 'center'}),
                dcc.Graph(id='company_flux'),
                
                # NEW
                html.H3("Index Decomposition", style={'textAlign': 'center'}),
                dcc.Graph(id='a'),
                dcc.Graph(id='b'),
                dcc.Graph(id='c'),
                #dcc.Graph(id='d'),
                
            ]),
        ]), 
    
        # TAB 4 SECTOR LEVEL ANALYSIS     
        dcc.Tab(label='Sector Data', children=[
            html.Div([        
                html.H1("Sector Analysis", style={'textAlign': 'center'}),
            
                dcc.DatePickerRange(id='sector_date_range',
                                    
                    min_date_allowed = dates_factors.min(), # SET LIMITS 
                    max_date_allowed = dates_factors.max(), 
                    start_date = '1998-10-09',#dates_factors.min(),  # DEFAULT START DATE
                    end_date = dates_factors.max(),    # DEFAULT END DATE
                    
                    calendar_orientation= 'vertical',
                                    ),  
            	html.Button(id='sector_button',
            								n_clicks = 0,
            								children = 'Submit',
            								style = {'fontSize': 24, 'marginLeft': '30px'}),
                                 
                dcc.Graph(id='sector_graph'),
            ]),
        ]),      
   ]), # ALL TABS END  
], className="container")


# In[5]:

''' Tab 1, Momentum Factor: Relative Quintile Returns '''

# FACTOR ANALYSIS 
@app.callback(Output('factor_graph', 'figure'),            
              [Input('factor_dropdown', 'value'), #ACTIVATION 1 
               Input('submit_factors', 'n_clicks')], #ACTIVATION 2 
              [State('factor_date_range', 'start_date'), 
               State('factor_date_range', 'end_date')])

def factor_graph_relative(selected_dropdown_value, n_clicks, start_date,end_date ):
    factor_traces = [] # STORES SELECTED DATA
    
    conn = sqlite3.connect(database_name) # Name and connect to the sqlite3 database
    cur = conn.cursor() # 
    # GENERATES CUM RETURNS FOR EACH COMPANY SELECTED + THE BENCHMARK
    for factor in selected_dropdown_value:
        # INDEX TRACES
        if factor == 'Russell Index':  
            try:
                index_data = pd.read_sql('select * from QuintileRelativeReturns;',conn)
                index_data['TO_DATE'] = pd.to_datetime(index_data['TO_DATE'], format='%Y-%m-%d', errors='coerce')

                # retrieve data for date range
                index_data = index_data.set_index('TO_DATE')
                index_data = index_data[start_date:end_date] # SLICE REQUESTED DATE RANGE

                index_data = index_data.reset_index() # RESET INDEX FOR x-axis VAR

                factor_traces.append(
                        go.Scatter(x=index_data['TO_DATE'], y= index_data['INDEX_AVG'],
                        opacity=0.7,name='Russell Index',line = dict(color='royalblue', width=4,dash='dot')))   
            except:
                pass
        # FACTOR TRACES    
        else:
            try:
                factor_data = pd.read_sql('select * from QuintileRelativeReturns;',conn)

                factor_data['TO_DATE'] = pd.to_datetime(factor_data['TO_DATE'], format='%Y-%m-%d', errors='coerce')
                factor_data = factor_data.set_index('TO_DATE')
                factor_data = factor_data[start_date:end_date] # SLICE REQUESTED DATE RANGE
                factor_data = factor_data.reset_index()

                factor_traces.append(
                        go.Scatter(x= factor_data['TO_DATE'], y= factor_data[factor],
                        opacity=1,name=factor, line = dict(width=2))
                        )                    
            except:
                pass
                
    conn.close()                

    figure_fact_relative = {'data':factor_traces, 'layout': go.Layout(xaxis={'title': 'Weekly Time Period: {} - {}'.format(str(pd.to_datetime(start_date, format='%Y-%m-%d', errors='coerce'))[:11],
                                                                                                                      str(pd.to_datetime(end_date, format='%Y-%m-%d', errors='coerce'))[:11])},
                                                                      yaxis={'title': 'Relative Index Returns'},
                                                                      title='Momentum Factor Plot',
                                                                      height=700,
                                                                     )
                           } 
    return figure_fact_relative


# In[6]:

''' Tab 2, Momentum Factor: Compounded Quintile Returns '''

# FACTOR ANALYSIS 
@app.callback([Output('factor_graph_tab2', 'figure'),
               Output('factor_bench', 'figure'),
               Output('factor_pie', 'figure'),
              ],
               
              [Input('factor_dropdown_tab2', 'value'), #ACTIVATION 1 
               Input('submit_factors_tab2', 'n_clicks')], #ACTIVATION 2 
              [State('factor_date_range_tab2', 'start_date'), 
               State('factor_date_range_tab2', 'end_date')])

def factor_graph_tab2(selected_dropdown_value, n_clicks, start_date,end_date ):
    factor_traces = [] # quintile data
    bench_traces = [] # index pie chart 
    pie_traces = [] # quintile pie
    
    conn = sqlite3.connect(database_name) # Name and connect to the sqlite3 database
    cur = conn.cursor() # 
    # GENERATES CUM RETURNS FOR EACH COMPANY SELECTED + THE BENCHMARK
    for factor in selected_dropdown_value:
        # INDEX TRACES
        if factor == 'Russell Index':  
            try:         
                index_data = pd.read_sql('select * from IndexData;',conn)
                index_data = index_data[1:] # remove needless date
                index_data['TO_DATE'] = pd.to_datetime(index_data['TO_DATE'], format='%Y-%m-%d', errors='coerce')

                # retrieve data for date range
                index_data = index_data.set_index('TO_DATE')
                index_data = index_data[start_date:end_date] # SLICE REQUESTED DATE RANGE

                index_data = index_data.reset_index() # RESET INDEX FOR x-axis VAR

                factor_traces.append(
                        go.Scatter(x=index_data['TO_DATE'], y= index_data['CUMULATIVE_RETURNS'],
                        opacity=0.7,name='Russell Index',line = dict(color='royalblue', width=4,dash='dot')))   
                
                ''' ADD PIE CHART BENCHMARK ''' #https://github.com/plotly/dash-oil-and-gas-demo/blob/master/app.py
                pie_bench = pd.read_sql('select SECTOR, TO_DATE from WeeklyQuintiles_2;',conn)

                pie_bench = pie_bench[1:]
                pie_bench['TO_DATE'] = pd.to_datetime(pie_bench['TO_DATE'], format='%Y-%m-%d', errors='coerce')

                pie_bench = pie_bench.set_index('TO_DATE')
                pie_bench = pie_bench[start_date:end_date]
                pie_bench = pie_bench.reset_index()

                sectors_benchmark = dict(pie_bench['SECTOR'].value_counts()) # keys and values for sectors 

                # https://plot.ly/python/pie-charts/
                #pie_traces
                bench_traces.append(
                        go.Pie( labels = tuple(sorted(sectors_benchmark.keys())) , # sort to preserve colour order
                                values = tuple(sectors_benchmark.values()),
                                hole = .6, 
                                hoverinfo="label+percent"))                    

            except:
                pass
            
        # FACTOR TRACES    
        else:
            try:
                factor_data = df_factor_returns[str(factor)]  

                # retrieve data for date range
                factor_data = factor_data[start_date:end_date] # SLICE REQUESTED DATE RANGE
                factor_data = factor_data.reset_index()

                factor_traces.append(
                        go.Scatter(x= factor_data['TO_DATE'], y= factor_data[factor],
                        opacity=1,name=factor, line = dict(width=2))
                        )
                        

            
                ''' ADD PIE CHART FOR FACTOR SECTOR COMPOSITION ''' 
                #factor = 'FACTOR_1'
                factor_key = {'QUINTILE_1' : '0.0',  # keys to call  data from table with a different naming convention 
                              'QUINTILE_2' : '1.0',
                              'QUINTILE_3' : '2.0',
                              'QUINTILE_4' : '3.0',
                              'QUINTILE_5' : '4.0',
                             }
                factor_name = factor_key[str(factor)]
                pie_data = pd.read_sql('select SECTOR, COMPANY, TO_DATE, QUINTILES from WeeklyQuintiles_2 where "QUINTILES" == "{}";'.format(factor_name),conn)
                pie_data = pie_data[1:]
                pie_data['TO_DATE'] = pd.to_datetime(pie_data['TO_DATE'], format='%Y-%m-%d', errors='coerce')

                # retrieve data for date range
                pie_data = pie_data.set_index('TO_DATE')
                pie_data = pie_data[start_date:end_date]
                pie_data = pie_data.reset_index()

                quintile_sectors = dict(pie_data['SECTOR'].value_counts()) # keys and values for sectors 

                # https://plot.ly/python/pie-charts/
                pie_traces.append(
                        go.Pie( labels = tuple(sorted(quintile_sectors.keys())) , 
                                values = tuple(quintile_sectors.values()),
                                hole = .6, 
                                hoverinfo="label+percent"))
      
            except:
                pass
            
    conn.close()    
    
    # for date range in pie chart
    S = str(pd.to_datetime(start_date, format='%Y-%m-%d', errors='coerce'))[:11]
    E = str(pd.to_datetime(end_date, format='%Y-%m-%d', errors='coerce'))[:11]
    
    
    # ADD SECURITIES TO SINGLE CHART
    figure_fact = [
    {'data':factor_traces,
     'layout':go.Layout(xaxis={'title': 'Weekly Time Period: {} - {}'.format(S,E)},
                        yaxis={'title': 'Compounded Returns (%)'}, height = 600)},
                               
    #{'data':bench_traces,'layout': go.Layout(xaxis={'title': 'Russell 1000 Index: {} - {}'.format(S,E)},
    #                               yaxis={'title': 'Compounded Returns (%)'},height=300)} ,                         
    #{'data':pie_traces, 'layout':  go.Layout(xaxis={'title': str(factor)+': {} - {}'.format(S,E)},
    #                               yaxis={'title': 'Compounded Returns (%)'},height=300)}                            
                               
                               
    {'data':bench_traces,'layout': {'title': 'Russell 1000 Index: {} - {}'.format(S,E), 'height':400,'showlegend': False, }},
    {'data':pie_traces, 'layout': {'title': str(factor)+': {} - {}'.format(S,E), 'height':400,'showlegend': False, }}  
    ]

    return figure_fact #, figure_pies[1], figure_pies[2]


# In[7]:

''' Tab 3:  Compounded Company Returns '''

# COMPANY ANALYSIS 
@app.callback([Output('company_graph', 'figure'),
              Output('company_flux', 'figure'),
              Output('a', 'figure'),
              Output('b', 'figure'),
              Output('c', 'figure'),
              #Output('d', 'figure')
              ],
              [Input('company_dropdown', 'value'), #ACTIVATION 1 
               Input('submit_companies', 'n_clicks')], #ACTIVATION 2 
              [State('company_date_range', 'start_date'), 
               State('company_date_range', 'end_date')])


def company_graph(selected_dropdown_value, n_clicks, start_date,end_date ):
    traces_comp = [] # STORES SELECTED DATA
    trace_index = []
    trace_flux = []
    
    conn = sqlite3.connect(database_name) # Name and connect to the sqlite3 database
    cur = conn.cursor() # 
    
    # GENERATES CUM RETURNS FOR EACH COMPANY SELECTED + THE BENCHMARK
    for company in selected_dropdown_value:
        # INDEX TRACES
        if company == 'Russell Index':  
            try:
                index_data = pd.read_sql('select * from IndexData;',conn)
                index_data = index_data[1:] # remove needless date
                index_data['TO_DATE'] = pd.to_datetime(index_data['TO_DATE'], format='%Y-%m-%d', errors='coerce')

                index_data = index_data.set_index('TO_DATE')
                index_data = index_data[start_date:end_date] # SLICE REQUESTED DATE RANGE

                index_data = index_data.reset_index() # RESET INDEX FOR x-axis VAR

                traces_comp.append(
                        go.Scatter(x=index_data['TO_DATE'], y= index_data['CUMULATIVE_RETURNS'],
                        opacity=0.7,name='Russell Index',line = dict(color='pink', width=4)))   #,dash='dot'        


                # INDEX DECOMPOSITION TO OBSERVE TREND/SEASONALITY/NOISE 
                [observed,trend,seasonal,resid] = tools.index_decomposition(index_data)
                deco_data = {'Index':observed,'Trend':trend,'Seasonality':seasonal,'Noise':resid}

                figure_deco=[]
                # APPEND TRACES TO LIST
                for n,d in deco_data.items():  
                    #fig = go.Figure()
                    #fig.add_trace(go.Scatter(x=index_data['TO_DATE'], y= d, name = n,
                    #                  opacity=0.7,line = dict(width=2)))
                    #trace_index.append(go.Scatter(x=index_data['TO_DATE'], y= d, name = n,
                    #                  opacity=0.7,line = dict(width=2)))

                    fig = [go.Scatter(x=index_data['TO_DATE'], y= d, name = n, opacity=0.7,line = dict(width=2))]
                    figure_deco.append({'data':fig, 'layout': {'title': n,"height" : 375 }})  #'Seasonality/Trend/Noise'}}
                    
               #return figure_deco 
            except:
                pass
        
        # COMPANY TRACES   
 
        else:
            try:
                # Retrieve Data for specific company
                company_data = pd.read_sql('select * from CompoundedReturns where COMPANY = "{}";'.format(company),conn)
                company_data['TO_DATE'] = pd.to_datetime(company_data['TO_DATE'], format='%Y-%m-%d', errors='coerce')

                company_data = company_data.set_index('TO_DATE')

                company_data = company_data[start_date:end_date] # SLICE REQUESTED DATE RANGE
                company_data = company_data.reset_index() # RESET INDEX FOR x-axis VAR

                traces_comp.append(
                        go.Scatter(x=company_data['TO_DATE'], y= company_data['CUMULATIVE_RETURNS'],
                        opacity=1,name=company, line = dict(width=2))
                        )  
                        
                # COMPANY FLUX METRIC 
                flux_data = pd.read_sql('select COMPANY,TO_DATE,QUINTILES, COMPANY_SCORE from WeeklyQuintiles_2 where COMPANY ="{}";'.format(company),conn)
                flux_data['TO_DATE'] = pd.to_datetime(flux_data['TO_DATE'], format='%Y-%m-%d', errors='coerce')

                flux_data = flux_data.set_index('TO_DATE')

                flux_data = flux_data[start_date:end_date] # SLICE REQUESTED DATE RANGE
                flux_data = flux_data.reset_index() # RESET INDEX FOR x-axis VAR

                trace_flux.append(
                        go.Scatter(x=flux_data['TO_DATE'], y= flux_data['QUINTILES'],
                        opacity=1,name=company, line = dict(width=2))
                        )                  
                                        
            except:
                pass
            
    conn.close()
                    
    # ADD SECURITIES TO SINGLE CHART
    figure_comp = {'data':traces_comp, 
                   'layout':go.Layout(xaxis={'title': '[{}] Weekly Time Period: {} - {}'.format(
                                        str(company),
                                        str(pd.to_datetime(start_date, format='%Y-%m-%d', errors='coerce'))[:11],
                                        str(pd.to_datetime(end_date, format='%Y-%m-%d', errors='coerce'))[:11])},
                                      yaxis={'title': 'Compounded Returns (%)'},height=600)
    }
    figure_flux  = {'data':trace_flux, 
                   'layout':go.Layout(xaxis={'title': '[{}] Weekly Time Period: {} - {}'.format(
                                        str(company),
                                        str(pd.to_datetime(start_date, format='%Y-%m-%d', errors='coerce'))[:11],
                                        str(pd.to_datetime(end_date, format='%Y-%m-%d', errors='coerce'))[:11])},
                                      yaxis={'title': 'Quintile Flux', 'tick0' : 0,'ticklen':5                                            
                                             },
                                      height=600)
    }
    
    return figure_comp, figure_flux , figure_deco[1],figure_deco[2],figure_deco[3] # wont return index copy , figure_deco[0]
#     for i in figure_deco:
#         return i 

# In[8]:

''' Tab 4: Sector Analysis '''

@app.callback(Output('sector_graph', 'figure'),            
              [Input('sector_button', 'n_clicks')], #ACTIVATION 2 
              [State('sector_date_range', 'start_date'), 
               State('sector_date_range', 'end_date')])

def sector_graph_relative( n_clicks, start_date,end_date ):
    
    ''' TRANSFORMING DATA FOR PLOT ''' 
    # RETRIEVE DATA
    conn = sqlite3.connect(database_name) 
    cur = conn.cursor()
    df = pd.read_sql('select TO_DATE, SECTOR, COMPANY_SCORE  from WeeklyQuintiles_2;',conn)
    conn.close()

    # SELECT REQUESTED DATA RANGE
    df = df.set_index('TO_DATE')
    df = df[ start_date : end_date ]
    df= df.reset_index()

    # PIVOT TABLE
    data_z = df.pivot_table ( index='TO_DATE',columns='SECTOR',values='COMPANY_SCORE')

    # CREATE NESTED LIST FOR SECTORS
    zlist = []
    for row in data_z.iterrows():
        index, data = row
        zlist.append(data.tolist())

    xlist = list(data_z.columns) # to preserve order
    ylist = list( data_z.index)    
    
    
    # calling
    return tools.create_plot(
        x=xlist,
        y=ylist,
        z=zlist,
        plot_type= 'surface'  #'scatter3d',
   )    

# In[9]:

''' Run App '''

if __name__ == '__main__':
    app.run_server()



