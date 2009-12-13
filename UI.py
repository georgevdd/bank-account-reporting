#!/usr/bin/env python

from datetime import date
from GUI import Window, Menu, Table, application
import Model as M
import Queries as Q
import Database as D

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

class StatementsWindow(Window):
  def __init__(self):
    columns = [
      ("Day", lambda t: t.date.day),
      ("i?", invoiceableSymbol),
      ("p?", paymentSymbol),
      ("Amount", lambda t: float(t.amount)),
      ("Memo", lambda t: str(t.memo)),
      ]
    self.transactions_tbl = Table(columns = columns, scrolling='hv',
                                  multi_select=True)

    columns = [
      ("Month", lambda (y, m): date(y, m, 1).strftime("%Y %b")),
      ]
    rows = D.withSession(Q.allTransactionMonths)
    self.months_tbl = Table(rows=rows, columns=columns, scrolling='v',
                            selection_changed_action = self.month_changed)

    Window.__init__(self, title="Statements", size=(1000, 500))
    self.place(self.months_tbl, left=0, right=100, top=0, bottom=0, sticky='nsw')
    self.place(self.transactions_tbl,
              left=self.months_tbl, right=0, top=0, bottom=0, sticky='nesw')
    self.menus = [
      Menu("Statements", [
          ("Select likely invoiceables/L", "select_likely_invoiceables"),
          ("Mark selection as invoiceable/I", "mark_selection_as_invoiceable"),
           ]),
           ]

  def setup_menus(self, m):
    m.select_likely_invoiceables.enabled = bool(self.transactions_tbl.rows)
    m.mark_selection_as_invoiceable.enabled = bool(list(self.transactions_tbl.selected_rows))

  def month_changed(self):
    y, m = self.months_tbl.rows[self.months_tbl.selected_row]
    self.transactions_tbl.rows = D.withSession(lambda: Q.transactionsForMonth(y, m))
    self.transactions_tbl.selected_rows = []

  def select_likely_invoiceables(self):
    selection = []
    for i, r in enumerate(self.transactions_tbl.rows):
      if r.isLikelyInvoiceable:
        selection.append(i)
    self.transactions_tbl.selected_rows = selection

  def mark_selection_as_invoiceable(self):
    def do_mark():
      for row in self.transactions_tbl.selected_rows:
        t = self.transactions_tbl.rows[row]
        Q.markTransactionAsInvoiceable(t, True)
    D.withSession(do_mark)
    self.transactions_tbl._ns_inner_view.reloadData()

win = StatementsWindow()
win.show()

application().run()
