#!/usr/bin/env python

from datetime import date
from GUI import Window, ModalDialog, Menu, Table, application
import Model as M
import Queries as Q
import Database as D

import AppKit
AppKit.NSAnyEventMask = 0xffffffff

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

class PersonPicker(ModalDialog):
  def __init__(self):
    ModalDialog.__init__(self, resizable=True)
    self.persons_tbl = Table(columns=[('fullName', lambda p: p.fullName)],
                             scrolling='v',
                             selection_changed_action=self.person_picked)
    self.place(self.persons_tbl, left=0, right=0, top=0, bottom=0, sticky='nesw')

  def pick(self):
    session = D.requireSession()
    self.persons_tbl.rows = session.query(M.Person).all()
    return self.present()

  def person_picked(self):
    selected_person = self.persons_tbl.rows[self.persons_tbl.selected_rows.next()]
    self.dismiss(result=selected_person)

class StatementsWindow(Window):
  def __init__(self):
    columns = [
      ("Day", lambda t: t.date.day),
      ("i?", invoiceableSymbol),
      ("p?", paymentSymbol),
      ("Amount", lambda t: float(t.amount)),
      ("Memo", lambda t: str(t.memo)),
      ]
    self.transactions_tbl = Table(columns=columns, scrolling='hv',
                                  multi_select=True)

    columns = [
      ("Month", lambda (y, m): date(y, m, 1).strftime("%Y %b")),
      ]
    rows = D.withSession(Q.allTransactionMonths)
    self.months_tbl = Table(rows=rows, columns=columns, scrolling='v',
                            selection_changed_action=self.month_changed)

    Window.__init__(self, title="Statements", size=(1000, 500))
    self.place(self.months_tbl, left=0, right=100, top=0, bottom=0, sticky='nsw')
    self.place(self.transactions_tbl,
              left=self.months_tbl, right=0, top=0, bottom=0, sticky='nesw')
    self.menus = [
      Menu("Statements", [
          ("Select likely invoiceables/L", "select_likely_invoiceables"),
          ("Mark selection as invoiceable/I", "mark_selection_as_invoiceable"),
          ("Mark selection as payment/P", "mark_selection_as_payment"),
           ]),
           ]

  def setup_menus(self, m):
    m.select_likely_invoiceables.enabled = bool(self.transactions_tbl.rows)
    m.mark_selection_as_invoiceable.enabled = bool(self.transactions_tbl.selected_row)
    m.mark_selection_as_payment.enabled = len(list(self.transactions_tbl.selected_rows)) == 1

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

  def mark_selection_as_payment(self):
    def do_mark():
      t = self.transactions_tbl.rows[self.transactions_tbl.selected_row]
      person = PersonPicker().pick()
      if person:
        Q.markTransactionAsPayment(t, person)
    D.withSession(do_mark)
    

if __name__ == '__main__':
  win = StatementsWindow().show()
  application().run()
