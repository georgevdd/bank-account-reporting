import TestSetup
import Model as M
from datetime import date
# For Python 2.3, decimal is available from
# http://sourceforge.net/projects/sigefi
from decimal import Decimal
from TestSetup import resetSession, DatabaseTestCase

class PaymentTest(DatabaseTestCase):
    def testPersonInitiallyHasNoPayments(self):
        p = M.Person('Joe', 'Bloggs')
        self.assert_(hasattr(p, 'payments'))
        self.assertEqual(0, len(p.tenancies))
        
    def testPaymentCanBeAssignedToPerson(self):
        p = M.Person('Joe', 'Bloggs')
        pmt = M.Payment(date(2000, 1, 1), Decimal('123.45'))
        p.payments.append(pmt)
        self.assert_(pmt in p.payments)
        self.assertEqual(p, pmt.personFrom)

class PaymentWithOtherEvidenceTest(DatabaseTestCase):
    def testPaymentWithOtherEvidencePersists(self):
        p = M.Person('Joe', 'Bloggs')
        pmt = M.PaymentWithOtherEvidence(date(2000, 1, 1), Decimal('123.45'), "Example payment")
        p.payments.append(pmt)
        self.session.add(p)
        resetSession()
        self.session.add(p)
        pmt = self.session.query(M.Payment).first()
        self.assertNotEqual(None, pmt)
        self.assertEqual(p, pmt.personFrom)
        self.assertEqual(date(2000, 1, 1), pmt.paymentDate)
        self.assertEqual(Decimal('123.45'), pmt.amount)
        self.assertEqual("Example payment", pmt.explanation)

class PaymentWithStatementEvidenceTest(DatabaseTestCase):
    def testPaymentWithStatementEvidencePersists(self):
        p = M.Person('Joe', 'Bloggs')
        t = M.Transaction(date(2000, 6, 1), Decimal('456.78'), 'FITID1', 'Example Transaction', 'Memo')
        pmt = M.PaymentWithStatementEvidence(t)
        p.payments.append(pmt)
        self.session.add(p)
        self.session.add(t)
        resetSession()
        self.session.add(p)
        self.session.add(t)
        pmt = self.session.query(M.Payment).first()
        self.assertNotEqual(None, pmt)
        self.assertEqual(p, pmt.personFrom)
        self.assertEqual(date(2000, 6, 1), pmt.paymentDate)
        self.assertEqual(Decimal('456.78'), pmt.amount)
        self.assertEqual(t, pmt.transaction)
