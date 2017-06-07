######################################################################
# fetch data from sidra's api
# initial data: 13/01/2017
######################################################################
import pandas as pd
import xlwings as xw
import requests
from concurrent import futures
import time



__all__ = ['update_db']


_series ={'mom': 63, 'peso': 66} #ipca
_table = 1419 #ipca

#_series ={'mom': 355, 'peso': 357} #ipca-15
#_table = 1705  #ipca-15

def _parse_data(resp):
    '''
    fetch the appropriated data about ipca from the ibge, by building
    the ibge's api url
    input:
    ----
    - resp: requests response
    output:
    ------
    - dataframe
    '''
    df = pd.read_json(resp.content).loc[:, ['D1C', 'D3C', 'V']]
    p = pd.to_datetime(df.D1C.unique(),format="%Y%m")
    df_new = pd.DataFrame(df[["V"]].values, index=df["D3C"].T.values, columns=[p])
    df_new.index.name = 'date'
    return df_new


def _fetch_ipca(period):
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
    session = requests.Session()
    session.mount("http://api.sidra.ibge.gov.br/values/t/1419",
                  requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=2))
    address_mom = "http://api.sidra.ibge.gov.br/values/" + \
               "t/{}/p/{}/v/{}/c315/all/h/n/n1/1/f/a".format(_table, period, _series['mom'])
    address_peso = "http://api.sidra.ibge.gov.br/values/" + \
                "t/{}/p/{}/v/{}/c315/all/h/n/n1/1/f/a".format(_table, period, _series['peso'])

    executor = futures.ThreadPoolExecutor(max_workers=2)
    resps = executor.map(session.get, [address_mom, address_peso])
    session.close()
    ddfs = [_parse_data(r) for r in resps]
    return {'mom': ddfs[0], 'peso':ddfs[1]}


def update_db(dat_file, dat):
    """
    Given a period, fetches all ipca changes and weight of the all items
    that's not yet in the db and saves it
    input:
    -----
    - data_file: str
    - info: str
    - dat: str (ex: all, 201612)
    output:
    - side effect
    """
    wb = xw.Book(dat_file)
    d = pd.to_datetime(dat, format="%Y%m").strftime(format="%Y-%m-%d")
    dmom =  wb.sheets('mom').range('a1').options(pd.DataFrame, expand='table').value
    dmom.columns = pd.to_datetime(map(lambda x: pd.to_datetime(x), dmom.columns))
    dpeso = wb.sheets('peso').range('a1').options(pd.DataFrame, expand='table').value
    dpeso.columns = pd.to_datetime(map(lambda x: pd.to_datetime(x), dpeso.columns))
    ddobs = {'mom': dmom, 'peso': dpeso}
    if not (d in dmom.columns):
        att = 0
        while (True and (att <= 10)):
            try:
                ddfs = _fetch_ipca(dat)
                print "New Data ({}) is available".format(dat)
            except:
                att += 1
                print "New Data ({}) is not yet available in attempt {}".format(dat, att)
                time.sleep(0.2)
            else:
                for info in ['mom', 'peso']:
                    df = ddobs[info]
                    dnew = ddfs[info]
                    df.columns = pd.to_datetime(map(lambda x: pd.to_datetime(x), df.columns))
                    #df.columns = pd.to_datetime([pd.to_datetime(x) for x in df.columns])
                    df = pd.merge(ddobs[info], ddfs[info], left_index=True, right_index=True, how='outer')
                    # df.columns = pd.to_datetime(map(lambda x: str(x), df.columns), format="%Y-%m-%d")
                    df.columns = pd.to_datetime([str(x) for x in df.columns], format="%Y-%m-%d")
                    df.sort_index(axis=1)
                    wb.sheets(info).range('a1').value = df
                break
    else:
        print "data for ({}) is already in the database".format(d)
