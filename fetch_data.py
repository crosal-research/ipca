######################################################################
# fetch data from sidra's api
# initial data: 13/01/2017
######################################################################
import pandas as pd
import xlwings as xw


__all__ = ['update_db']


def _fetch_data(serie, period):
    '''
    fetch the appropriated data about ipca from the ibge, by building
    the ibge's api url
    input:
    ----
    - series: str(int) - code from ibge's api (ex: 63 fr mom or 66 for weight)
    - period: str
    output:
    ------
    - dataframe
    '''
    address = "http://api.sidra.ibge.gov.br/values/t/1419" + \
              "/p/{}/v/{}/c315/all/h/n/n1/1/f/a".format(period, serie)
    df = pd.read_json(address).loc[:, ['D1C', 'D3C', 'V']]
    p = pd.to_datetime(period, format="%Y%m").strftime(format="%Y-%m-%d")
    df_new = pd.DataFrame(df[["V"]].values, index=df["D3C"].T.values, columns=[p])
    df_new.index.name = 'date'
    return df_new


def _fetch_ipca(info, period):
    """
    Hellp function. Given a period, fetches all ipca itmes mom changes and weights
    of that period.
    input:
    -----
    - info: str [mom, peso]
    - period: str (201610)
    output:
    ------
    - dataframe
    """
    if info == 'mom':
        return _fetch_data(63, period)
    return _fetch_data(66, period)


def update_db(dat_file, dat):
    """
    Given a period, fetches all ipca changes and weight of the all items
    that's not yet in the db and saves it
    input:
    -----
    - data_file: stro
    - info: str
    - dat: str (ex: all, 201612)
    oupt:
    - side effect
    Nota: falta manter formato da data em strings no arquivo excel quanto saver l
    """
    wb = xw.Book(dat_file)
    for info in ['mom', 'peso']:
        d = pd.to_datetime(dat, format="%Y%m").strftime(format="%Y-%m-%d")
        global df
        df = wb.sheets(info).range('a1').options(pd.DataFrame, expand='table').value
        df.columns = pd.to_datetime(map(lambda x: pd.to_datetime(x), df.columns))
        if not (d in df.columns):
            try:
                dnew = _fetch_ipca(info, dat)
                print "New Data ({}) is available".format(dat)
            except:
                print "New Data {} is not yet available".format(dat)
            else:
                df = pd.merge(df, dnew, left_index=True, right_index=True, how='outer')
                df.columns = pd.to_datetime(map(lambda x: pd.to_datetime(x), df.columns))
                df.sort_index(axis=1)
                wb.sheets(info).range('a1').value = df
        
    
                
