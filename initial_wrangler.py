#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 11:45:30 2019

@author: e03529
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import timeit

#dataset_name = 'Weekly Returns - Russel1000 - weekly.xlsx' #replace as required 

class wrangler():
    def data_wrangling (dataset_name):
        df = pd.read_excel(dataset_name,index_col = None,sheet_name = 'Sector Attribution (2 Factor)')
        #df = pd.read_excel(dataset_name,index_col = None,sheet_name = 'Sheet1')
        # reshape to desired format 
        df2 = pd.melt(frame=df,id_vars=['Unnamed: 0','Unnamed: 1', '^=FG_FACTSET_SECTOR'])
        df2.columns =['SEDOL','COMPANY','SECTOR','tempDate','LOCAL_RETURN']
        
        # split date
        df2[['FROM_DATE','TO_DATE']] = df2['tempDate'].str.split('to', expand=True)
        # drop obsolete date 
        df2 = df2.drop(['tempDate'],axis=1)    
            
        # fix dataTime types
        df2['FROM_DATE'] = pd.to_datetime(df2['FROM_DATE']);
        df2['TO_DATE'] = pd.to_datetime(df2['TO_DATE']);\
        return df2
                 
    
    # Imputation
    def add_breaker_row(df, comp_name):
        x = df.groupby(comp_name)
        # Adding 2 empty rows will prevent values from other companies being called during imputation calculations  
        out = pd.concat([ i.append({'Comp_Break': 'New_Comp'},
                                  ignore_index=True,) for _ , i in x])
        out[comp_name] = out[comp_name].ffill().astype(str)
        
        # add a 2nd empty row 
        q = out.groupby(comp_name)
        out2 = pd.concat([ y.append({'Comp_Break': '2nd Row'},
                                  ignore_index=True,) for _ , y in q])
        out2[comp_name] = out2[comp_name].ffill().astype(str)
        return out2
        
    def imputated_returns (df, number_of_weeks):
        # sort by company name and date for correct calculation
        df = df.sort_values(['COMPANY','TO_DATE']) 
        
        # add column and populate with the average of the previous 2 and subsequent 2 values weeks of returns
        if number_of_weeks == '4_weeks':
            df['IMPUTATED_RETURNS'] = pd.DataFrame
            df['IMPUTATED_RETURNS'] =                      ( 
                                                            (df['LOCAL_RETURN'].shift( 1) +
                                                             df['LOCAL_RETURN'].shift( 2) +
                                                             df['LOCAL_RETURN'].shift(-1) +
                                                             df['LOCAL_RETURN'].shift(-2)
                                                            ) / 4 )
        else:
            df['IMPUTATED_RETURNS'] = pd.DataFrame
            df['IMPUTATED_RETURNS'] =                      ( 
                                                            (df['LOCAL_RETURN'].shift( 1) +
                                                             df['LOCAL_RETURN'].shift(-1) 
                                                            ) / 2 )        
        return df
    
    def replace_outliers (df,threshold):
        returns = df['LOCAL_RETURN']
        imputated_returns = df['IMPUTATED_RETURNS']
        
        # identify outliers, where outlier use imputated values, else original 
        df['RETURNS'] = np.where(abs(returns)>threshold, imputated_returns , returns)
        df['RETURNS'] = np.where(abs(returns)>threshold, threshold , df['RETURNS']) # second filter to 
        
        # drop extra rows
        df = df[~df['Comp_Break'].isin(["2nd Row",'New_Comp'])] #.str.contains('New_Comp')] .str.contains('New_Comp')] #.isin(["2nd Row",'New_Comp'])] #.str.contains('New_Comp')]
        
        # drop obsolete columns
        df = df.drop( ['Comp_Break','IMPUTATED_RETURNS'],axis=1)
        
        return df 


    
    def pickle_file(df,str_name):
        # saves formats
        df.to_pickle(str_name)



    def plot_index(df):
        df['Cum_Returns'].plot(figsize=(20,10))
        plt.ylabel('INDEX')
    
    
    # COMPARE DIFFERENT IMPUTATIONS
    def save_to_speadsheet (df1, df2):
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter('Russel_Index_Imputation.xlsx', engine='xlsxwriter')
        
        # Write each dataframe to a different worksheet.
        df1.to_excel(writer, sheet_name='2_week_imputation')
        df2.to_excel(writer, sheet_name='4_week_imputation')
        
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()



# ------- COMMENTS -------- #

#- Some companies have no return data at all
#- Number of companies falls abruplty after 2016
#- Flactuating number of companies by week
#- The returns of certain companies like TranSwitch Corporation are clearly outliers
#- 4W imputation sucks towards the end due to missing values, can add logic to exclude and move to next available val

'''


