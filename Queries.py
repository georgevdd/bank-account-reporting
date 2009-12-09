from datetime import date
from sqlalchemy.sql import asc, cast, func
from sqlalchemy.types import INT

import Model as M
from Database import ensureSession, resetSession, requireSession

date_part = func.date_part

def allTransactionMonths():
  session = requireSession()
  parts = "year", "month"
  query = session \
      .query(*[cast(date_part(p, M.Transaction.date), INT)
               .label(p) for p in parts]) \
      .order_by(*[asc(p) for p in parts]) \
      .distinct()
  return list(query)

def transactionsInDateRange(start, end):
  session = requireSession()
  query = session \
      .query(M.transactionListMapper) \
      .filter((M.transactionListMapper.c.date >= start)
              & (M.transactionListMapper.c.date < end)) \
      .order_by(asc(M.transactionListMapper.c.date))
  return list(query)

def transactionsForMonth(year, month):
  if month == 12:
    end_year, end_month = year+1, 1
  else:
    end_year, end_month = year, month+1
  return transactionsInDateRange(date(year, month, 1),
                                 date(end_year, end_month, 1))

def markTransactionAsInvoiceable(t, invoiceable):
  session = requireSession()
  if invoiceable and not t.isInvoiceable:
    session.add(M.InvoiceableItem(t))
  elif t.isInvoiceable and not invoiceable:
    raise NotImplementedError
