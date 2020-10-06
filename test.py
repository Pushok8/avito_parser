import openpyxl

wbkName = 'avito_statistic.xlsx'
wbk = openpyxl.load_workbook(wbkName)
wks = wbk['avito_statistic']
someValue = 1337
wks.cell(row=10, column=1).value = someValue
wbk.save(wbkName)
wbk.close