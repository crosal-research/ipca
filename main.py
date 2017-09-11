######################################################################
# main interface to retrive data and calculate core measures
# initial date: 16/01/2017
######################################################################
import xlwings as xw
from fetch_data import update_db
from consolidate import consolidate

cpi = "ipca"

if cpi == "ipca_15":
    series ={'mom': 355, 'peso': 357} #ipca-15
    table = 1705  #ipca-15
    filename = "ipca_15.xlsx"
else:
    series ={'mom': 63, 'peso': 66} #ipca
    table = 1419 #ipca
    filename = "ipca.xlsx"


wb = xw.Book(filename)
dates = [int(x) for x in  wb.sheets('Dates').range("a1").expand().value]
# for d in dates:
#    update_db(wb, d, series, table)

# update database
update_db(wb, dates[-1], series, table)

#calculates cores
consolidate(wb, dates)
