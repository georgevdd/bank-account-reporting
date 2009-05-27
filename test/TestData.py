import Model as M
import itertools
import datetime
# For Python 2.3, decimal is available from
# http://sourceforge.net/projects/sigefi
from decimal import Decimal

_exampleTransactionId = itertools.count()

def exampleTransaction(date=None, amount=None):
    id = _exampleTransactionId.next()
    if date is None:
        date = datetime.date.today()
    if amount is None:
        amount = Decimal('%d.00' % id)
    return M.Transaction(date, amount,
        'FITID%d' % id, 'Transaction %d name' % id, 'Transaction %d memo' % id)
