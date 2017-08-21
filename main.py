######################################################################
# main interface to retrive data and calculate core measures
# initial date: 16/01/2017
######################################################################
import xlwings as xw
from fetch_data import update_db
from consolidate import consolidate

wb = xw.Book('ipca.xlsx')
dates = [int(x) for x in  wb.sheets('Dates').range("a1").expand().value]

# for d in dates:
#     update_db('ipca.xlsx', d)

update_db('ipca.xlsx', dates[-1])

consolidate(dates)
