# coding: iso-8859-1

######################################################################
# decomposion of ipca into its differents subcomponents
# initial date: 31/10/2016
# obs: adicionar documentação
######################################################################
import pandas as pd
import numpy as np
import json
from datetime import datetime
from pandas.tseries.offsets import *
import xlwings as xw

__all__ = ['decomposition']

_decompo = xw.Book('ipca.xlsx').sheets('decomposition') \
                               .range('a1').options(pd.DataFrame, expand='table',
                                                    index=False).value
_indexes = xw.Book('ipca.xlsx').sheets('indexes') \
                               .range('a1').options(pd.DataFrame, expand='table',
                                                    index=False).value
_items = _indexes[_indexes.loc[:, 'product'].map(lambda x: len(x.split('.')[0]) == 4)]

_subitems = _indexes[_indexes.loc[:, 'product'].map(lambda x: len(x.split('.')[0]) > 4)]


_groups = _indexes[_indexes.loc[:, 'product'].map(lambda x: len(x.split('.')[0]) == 1)]

_smooth = _indexes[_indexes.loc[:, 'product'].map(lambda x: len(x.split('.')[0]) == 1)]


# help functions
def decomp(df, category, dat):
    '''
    returns index of given category of core
    input:
    -----
    - de: data frame (multiindex com datas e indices)
    - category: list (indexes of the core)
    - dat: date (ex: 2016-09-01)
    output:
    -----
    - double
    '''
    dmonth = df.loc[dat]
    ch = dmonth['mom'].loc[:, category].dropna()
    wg = dmonth['peso'].loc[:, category].dropna()
    return np.average(ch, weights=wg)


def weights(df, category, dat):
    '''
    returns weights of given category of core
    input:
    -----
    - df: data frame
    - category: list (indexes of the core)
    - dat: date (ex: 2016-09-01)
    output:
    -----
    - double
    '''
    return df['peso'].loc[dat, list(category)].sum()



def _tradables_weights(dipca, dat):
    dec = _decompo['comercializaveis'].dropna().values
    return weights(dipca, dec, dat)


def _monitored_weights(dipca, dat):
    dec = _decompo['monitorados'].dropna().values
    return weights(dipca, dec, dat)


def _ipca(dipca, dat):
    return dipca['mom'].loc[dat, 7169]


# Functions to export
def serv(dipca, dat):
    dec = _decompo['Servicos'].dropna().values
    return decomp(dipca, dec, dat)


def serv_core(dipca, dat):
    dec = _decompo['Servicos nucleo'].dropna().values
    return decomp(dipca, dec, dat)


def duraveis(dipca, dat):
    dec = _decompo['duraveis'].dropna().values
    return decomp(dipca, dec, dat)


def nduraveis(dipca, dat):
    dec = _decompo['nao-duraveis'].dropna().values
    return decomp(dipca, dec, dat)


# problemas
# def semi(dipca, dat):
#     dec = _decompo['semiduraveis'].dropna().values
#     return decomp(dipca, dec, dat)


def monitorados(dipca, dat):
    dec = _decompo['monitorados'].dropna().values
    return decomp(dipca, dec, dat)


def livres(dipca, dat):
    p = _monitored_weights(dipca, dat)/100
    return 1/(1-p) * (_ipca(dipca, dat) - p*monitorados(dipca, dat))



def comercializaveis(dipca, dat):
    dec = _decompo['comercializaveis'].dropna().values
    return decomp(dipca, dec, dat)


def ncomercializaveis(dipca, dat):
    p = _tradables_weights(dipca, dat)/100
    q = _monitored_weights(dipca, dat)/100
    return 1/(1 - p - q)*(_ipca(dipca, dat) - p*comercializaveis(dipca, dat)
                          - q*monitorados(dipca, dat))


# still missing by decimals
def core_ex2(dipca, dat):
    dec = _decompo['ex2'].dropna().values
    return decomp(dipca, dec, dat)


def core_ma(dipca, dat):
    input_ipca = dipca.copy()
    items = list(_items.loc[:, 'index'].values)
    cpi = input_ipca.ix[dat].loc[items]
    cpi = input_ipca.ix[dat].loc[items].sort_values(by='mom', ascending=True)
    cpi['cum'] = cpi['peso'].cumsum()
    indexes = cpi[(cpi['cum'] >= 20.0) & (cpi['cum'] <= 80.0)].index
    index_inf = cpi.index.get_loc(indexes[0])-1
    diff_inf = 20 - cpi.iloc[index_inf]['cum'] 
    index_sup = cpi.index.get_loc(indexes[-1]) + 1
    diff_sup = 60 - (cpi.loc[indexes]['peso'].sum()  -  diff_inf)
    input_ipca.loc[dat, indexes[0]]['peso'] =  input_ipca.loc[dat, indexes[0]]['peso'] - diff_inf
    input_ipca.loc[dat, indexes[-1]]['peso'] =  input_ipca.loc[dat, indexes[-1]]['peso'] + diff_sup
    return decomp(input_ipca, indexes, dat)
    

def core_smooth(dipca, dat):
    global indexes, dr
    if dat < "2013-01-01":
        return np.NaN
    sm_dipca = dipca.copy()
    indexes = _decompo['suavizados'].dropna().values
    ds = dipca.loc[(slice(None), indexes),:].unstack()
    dr = ds.loc[:,'mom'].rolling(window=12).apply(lambda x: (np.prod(1+x/100)))
    dmom = pd.DataFrame(((dr.applymap(lambda x: (x-1)/12))*100).stack(), columns = ['mom'])
    for ind in indexes:
        sm_dipca.loc[(slice('2013-01-01',dat), ind), 'mom'] = dmom.loc[(slice('2013-01-01', dat), ind), 'mom'].values
    return core_ma(sm_dipca,dat)


def core_dp(dipca, dat):
    if dat < "2015-01-01":
        return np.NaN
    items = list(_items.loc[:, 'index'].values)
    dat_ipca = dipca.ix[dat].loc[items]
    d = datetime.strptime(dat, "%Y-%m-%d")
    begin = d + DateOffset(years=-4) #intial period std
    end = d + DateOffset(months=-1)  # final period for std
    # recalculate weights
    sipca = dipca.swaplevel(0,1).sort_index(inplace=False).loc[items]['mom'].unstack(0).loc[begin:end]
    obs = dipca.swaplevel(0,1).sort_index(inplace=False).loc[7169]["mom"].loc[begin:end]
    net = sipca.subtract(obs, axis="index")
    std = 1/net.std()
    sm_std = std/std.sum()*100
    new_std = sm_std*(dat_ipca["peso"].sort_index())
    new_sm = new_std /(new_std.sum())*100
    # calculate de final
    return np.average(dat_ipca["mom"].sort_index(), weights=new_sm)



def difusao(dipca, dat):
    """
    takes the ipca database and the date and
    returns the difusion index for that date
    input:
    -----
    - dipca: dataframe
    - dat: date (%Y-%m-%d)
    output:
    ------
    - double
    """
    global obs, di
#    subitems = [np.round(x,0) for x in (_subitems.loc[:, 'index'].values)]
    subitems = _subitems['index'].values
    obs = dipca.loc[(dat, subitems), 'mom']
    #obs = dipca.loc[dat]["mom"].unstack()[subitems].T
    return obs[dat].apply(lambda x: 1.0 if x > 0 else 0).mean()


def groups(dipca, dat):
    """
    takes the ipca database and the date and
    returns the difusion index for that date
    input:
    -----
    - dipca: dataframe
    - dat: date (%Y-%m-%d)
    output:
    ------
    - list
    """
    groups = list(_groups.loc[:, 'index'].values)
    dv = pd.DataFrame(dipca.ix[dat]['mom'].loc[groups]).T
    dv.index = [dat]
    dv.columns = ['Foods', "Residence", "Residencial Articles",
                                          "Clothing", "Transport", "Health",
                                          "Personal Items", "Education", "Communication"]
    return dv


# consolidado
def decomposition(dipca, dat):
    '''
    return a list with inflation components
    input:
    -----
    - dipca: multiindex panda dataframe
    - dat: str (date to calculate cores)
    ouput:
    -----
    - list(double)
    '''
    consolidado = [_ipca, serv, serv_core, duraveis, nduraveis,
                   monitorados, livres, comercializaveis,
                   ncomercializaveis, core_ex2, core_ma, core_dp, core_smooth, difusao]
    names = ['ipca', 'servicos', 'nucleo - servicos', 'duraveis', 'nduraveis',
             'monitorados', 'livres', 'comercializaveis',
             'ncomercializaveis', "core_ex2", "core_ma", "core_dp", "core_smooth", "difusao"]
    df = pd.DataFrame(np.array([np.round(c(dipca, dat),
                                         2) for c in consolidado]).reshape(1, len(names)),
                      index=[dat], columns=names)
    dfinal = pd.merge(df, groups(dipca, dat), left_index=True, right_index=True, how="inner")
    return dfinal

