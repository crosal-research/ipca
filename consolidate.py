######################################################################
# consolidates ipca core data
# initial date: 16/11/2016
######################################################################
import pandas as pd
import os
import numpy as np
from decomposition import decomposition
import xlwings as xw
import numpy as np


def _build_ipca(file_name):
    '''
    returns a dataframe with merge data from mom and peso sheets
    input:
    -----
    - file_name: str
    ouput:
    - pandas dataframe
    '''
    dm = xw.Book(file_name).sheets('mom').range('a1')\
                                      .options(pd.DataFrame, expand='table').value
    dm.columns = pd.to_datetime(dm.columns)
    dmom = pd.DataFrame(dm.replace('...', np.NaN).stack().swaplevel(0, 1))
    dmom.index.levels[0].name = 'Date'
    dmom.index.levels[1].name = 'items'
    
    dp = xw.Book(file_name).sheets('peso').range('a1')\
                                      .options(pd.DataFrame, expand='table').value
    dp.columns = pd.to_datetime(dp.columns)
    dpeso = pd.DataFrame(dp.replace('...', np.NaN).stack().swaplevel(0, 1))
    dpeso.index.levels[0].name = 'Date'
    dpeso.index.levels[1].name = 'items'

    dipca = pd.merge(dmom, dpeso, left_index=True, right_index=True, how='inner')
    dipca.columns = ['mom', 'peso']
    dipca.sort_index(inplace=True)
    return dipca


def consolidate(dates):
    '''
    saves information on inflation's core onto spreadsheet
    of all dates in the input.
    input 
    -----
    - list(str)
    output:
    ------
    - side-effect
    '''
    df = xw.Book('ipca.xlsx').sheets('nucleos').range('a1')\
                                                     .options(pd.DataFrame, expand='table').value
    dipca = _build_ipca('ipca.xlsx')
    df.index = pd.to_datetime(df.index)
    df_final = df.copy()
    for dat in dates:
        d = pd.to_datetime(dat, format="%Y%m").strftime("%Y-%m-%d")
        if not d in df.index:
            global dnew
            dnew = decomposition(dipca, d)
            df_final = pd.concat([df_final, dnew], join='inner')
            df_final.index.name = 'date'
            xw.Book('ipca.xlsx').sheets('nucleos').range('a1').value = df_final
    

