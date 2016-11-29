import Model as M
import Database as D

s = D.ensureSession()

people = s.query(M.Person).all()

for p in people:
  print
  print p.fullName

  for i in p.invoices:
    print '  ', i.invoiceDate, i.amount, i.computedAmount
