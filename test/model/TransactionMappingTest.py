import TestSetup
import Model as M
from datetime import date
# For Python 2.3, decimal is available from
# http://sourceforge.net/projects/sigefi
from decimal import Decimal
from TestSetup import resetSession, DatabaseTestCase
from TestData import exampleTransaction

class TransactionTest(DatabaseTestCase):
    def listViewOf(self, transaction):
        return self.session \
            .query(M.transactionListMapper) \
            .filter(M.transactionListMapper.c.fitid==transaction.fitid) \
            .first()

    def testLikelyInvoiceableMatchesName(self):
        li = M.LikelyInvoiceable('%name%')
        t1 = M.Transaction(date.today(), Decimal('0.10'), 'myfitid1', '---name---', '---memo---')
        t2 = M.Transaction(date.today(), Decimal('0.10'), 'myfitid2', '---OTHER---', '---memo---')
        for t in li, t1, t2:
            self.session.add(t)
        resetSession()
        t1 = self.listViewOf(t1)
        self.engine.echo="debug"
        t2 = self.listViewOf(t2)
        self.engine.echo=False
        self.assert_(t1.isLikelyInvoiceable)
        self.assert_(not t2.isLikelyInvoiceable)

    def testIsInvoiceableIfInvoiceableItemExists(self):
        t1 = M.Transaction(date.today(), Decimal('0.10'), 'myfitid1', '---name---', '---memo---')
        t2 = M.Transaction(date.today(), Decimal('0.10'), 'myfitid2', '---OTHER---', '---memo---')
        ii1 = M.InvoiceableItem(t1)

        for x in t1, t2, ii1:
            self.session.add(x)
        resetSession()
        t1 = self.listViewOf(t1)
        t2 = self.listViewOf(t2)

        self.assert_(t1.isInvoiceable)
        self.assert_(not t2.isInvoiceable)

    def testIsLikelyPaymentDependsOnAmount(self):
        for amount, isLikely in [
                     ('-0.01', False),
                     ('0.00', False),
                     ('0.01', True),
                     (M.MAXIMUM_LIKELY_PAYMENT, True),
                     (M.MAXIMUM_LIKELY_PAYMENT + Decimal('0.01'), False)]:
            t = exampleTransaction(amount=amount)
            self.session.add(t)
            resetSession()
            t = self.listViewOf(t)
            try:
                self.assertEqual(t.isLikelyPayment, isLikely)
            except Exception, e:
                print '%s should be %s' % (amount, isLikely)
                raise

    def testIsPaymentIfCorrespondingPaymentExists(self):
        t1 = M.Transaction(date.today(), Decimal('0.10'), 'myfitid1', '---name---', '---memo---')
        t2 = M.Transaction(date.today(), Decimal('0.10'), 'myfitid2', '---OTHER---', '---memo---')
        p = M.Person('Joe', 'Bloggs')
        p.payments.append(M.PaymentWithStatementEvidence(t1))

        for x in t1, t2, p:
            self.session.add(x)
        resetSession()
        t1 = self.listViewOf(t1)
        t2 = self.listViewOf(t2)

        self.assert_(t1.isPayment)
        self.assert_(not t2.isPayment)
