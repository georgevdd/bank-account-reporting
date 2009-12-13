from decimal import Decimal
from datetime import date

def rule(o):
  print >> o, '=' * 80

def blankLine(o):
  print >> o

def pounds(n):
  return u'\u00a3' + str(n.quantize(Decimal('1.00')))

def table(o, data, cols):
  for title, getter, format in cols:
    print >> o, format % title,
  print >> o

  for row in data:
    for title, getter, format in cols:
      print >> o, format % getter(row),
    print >> o

def rjust(s):
  return '% 80s' % s

def pretty(o, invoice):
  rule(o)
  print >> o, 'Invoice for %s generated on %s' % (invoice.personTo.fullName, str(date.today()))
  blankLine(o)
  print >> o, rjust('Balance brought forward from %s: %s' % (
      str(invoice.previousInvoice.invoiceDate), pounds(-invoice.previousInvoice.amount)))
  blankLine(o)

  table(o, invoice.payments,
    [('Date', lambda p: str(p.paymentDate), '% 12s'),
     ('Amount', lambda p: pounds(p.amount), '% 9s'),
     ('', lambda p: p.transaction.name, '      %s')])
  print >> o, rjust('Total Payments: %s' % pounds(invoice.totalPayments))

  print >> o, 'Charges on or before %s:' % str(invoice.invoiceDate)
  blankLine(o)

  table(o, invoice.items,
    [('Date', lambda ii: ii.transaction.date, '% 12s'),
     ('Amount', lambda ii: pounds(-ii.transaction.amount), '% 9s'),
     ('Shared', lambda ii: ii.tenants.count(), '% 7s'),
     ('Your Share', lambda ii: pounds(-ii.amountPerTenant), '% 11s'),
     ('', lambda ii: ii.transaction.name, '%s')])
  print >> o, rjust('Total charges: %s' % pounds(-invoice.total))

  blankLine(o)
  print >> o, rjust('Amount due: %s' % pounds(-invoice.amount))

  blankLine(o)
  rule(o)

p = pretty
