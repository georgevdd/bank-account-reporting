#!/usr/bin/env python

from datetime import date
from GUI import Window, Table, application
import Model as M
import Queries

def invoiceableSymbol(t):
  if t.isInvoiceable:
    return 'I'
  elif t.isLikelyInvoiceable:
    return '?'
  else:
    return ''

def paymentSymbol(t):
  if t.isPayment:
    return 'P'
  elif t.isLikelyPayment:
    return '?'
  else:
    return ''

def showStatements():
  columns = [
    ("Day", lambda t: t.date.day),
    ("i?", invoiceableSymbol),
    ("p?", paymentSymbol),
    ("Amount", lambda t: float(t.amount)),
    ("Memo", lambda t: str(t.memo)),
    ]
  transactions_tbl = Table(columns = columns, scrolling='hv')
  
  rows = Queries.allTransactionMonths()
  columns = [
    ("Month", lambda (y, m): date(y, m, 1).strftime("%Y %b")),
    ]
  months_tbl = Table(rows=rows, columns=columns, scrolling='v')

  def month_changed():
    y, m = rows[months_tbl.selected_row]
    transactions_tbl.rows = Queries.transactionsForMonth(y, m)
  months_tbl.selection_changed_action = month_changed

  win = Window(title = "Statements")
  win.size = (500, 500)
  win.place(months_tbl, left=0, right=100, top=0, bottom=0, sticky='nsw')
  win.place(transactions_tbl,
            left=months_tbl, right=0, top=0, bottom=0, sticky='nesw')
  win.show()

showStatements()

application().run()
