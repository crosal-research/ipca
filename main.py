######################################################################
# main interface to retrive data and calculate core measures
# initial date: 16/01/2017
######################################################################
from fetch_data import update_db
import xlwings as xw
from consolidate import consolidate

wb = xw.Book('ipca.xlsx')
dates = map(lambda x: int(x), wb.sheets('Dates').range("a1").expand().value)

for d in dates:
    update_db('ipca.xlsx', d)


consolidate(dates)
