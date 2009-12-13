import TestSetup
import Model as M
from datetime import date, timedelta
# For Python 2.3, decimal is available from
# http://sourceforge.net/projects/sigefi
from decimal import Decimal
from TestSetup import resetSession, DatabaseTestCase
from TestData import exampleTransaction
from sets import Set

DAWN_OF_TIME = date(2000, 1, 1)
PREVIOUS_INVOICE_DATE = date(2005, 12, 12)
TENANCY_BEGIN = date(2006, 1, 1)
TENANCY_END = date(2006, 2, 2)
TENANCY_MIDDLE = TENANCY_BEGIN + (TENANCY_END - TENANCY_BEGIN)/2
INVOICE_DATE = date(2006, 4, 4)
    
class InvoiceTest(DatabaseTestCase):
    def setUp(self):
        DatabaseTestCase.setUp(self)
        self.exTenant = M.Person('Joe', 'Bloggs')
        self.exTenant.tenancies.append(M.Tenancy(TENANCY_BEGIN, TENANCY_END))
        self.session.add(self.exTenant)
        
        self.currentTenant = M.Person('John', 'Smith')
        self.currentTenant.tenancies.append(M.Tenancy(DAWN_OF_TIME))
        self.session.add(self.currentTenant)

class BasicInvoiceTest(InvoiceTest):
    def testPersonInitiallyHasNoInvoices(self):
        p = self.exTenant
        self.assert_(hasattr(p, 'invoices'))
        self.assertEqual(0, len(p.invoices))
        
    def testInvoiceCanBeAssignedToPerson(self):
        p = self.exTenant
        i = M.Invoice(INVOICE_DATE, Decimal('123.45'))
        p.invoices.append(i)
        self.assert_(i in p.invoices)
        self.assertEqual(p, i.personTo)
    
    def testInvoicePersists(self):
        p = self.exTenant
        i = M.Invoice(INVOICE_DATE, Decimal('123.45'))
        p.invoices.append(i)
        self.session.add(p)
        resetSession()
        self.session.add(p)
        i = self.session.query(M.Invoice).first()
        self.assertNotEqual(None, i)
        self.assertEqual(p, i.personTo)
        self.assertEqual(INVOICE_DATE, i.invoiceDate)
        self.assertEqual(Decimal('123.45'), i.amount)
    
class InvoiceItemsTest(InvoiceTest):
    def assertInvoiceItemPresence(self, tenant, itemDate, expectedPresent):
        t = exampleTransaction(itemDate)
        ii = M.InvoiceableItem(t)
        self.session.add(ii)
        
        p = tenant
        i0 = M.Invoice(PREVIOUS_INVOICE_DATE, Decimal('0.00'))
        i = M.Invoice(INVOICE_DATE, Decimal('1.11'))
        p.invoices.append(i0)
        p.invoices.append(i)
        self.session.add(p)
        resetSession()

        self.session.add(i)
        self.session.add(ii)
        items = list(i.items)
        
        if expectedPresent:
            self.assertEqual(1, len(items))
            self.assertEqual(ii, items[0])
        else:
            self.assertEqual(0, len(items))

    def testInvoiceExcludesItemsBeforeTenancy(self):
        self.assertInvoiceItemPresence(self.exTenant,
            TENANCY_BEGIN - timedelta(1), False)

    def testInvoiceIncludesItemsDuringTenancy(self):
        self.assertInvoiceItemPresence(self.exTenant,
            TENANCY_MIDDLE, True)

    def testInvoiceExcludesItemsAfterTenancy(self):
        self.assertInvoiceItemPresence(self.exTenant,
            TENANCY_END + timedelta(1), False)

    def testInvoiceExcludesItemsAfterInvoiceDate(self):
        self.assertInvoiceItemPresence(self.currentTenant,
            INVOICE_DATE + timedelta(1), False)

    def testInvoiceExcludesItemsBeforePreviousInvoiceDate(self):
        self.assertInvoiceItemPresence(self.currentTenant,
            PREVIOUS_INVOICE_DATE - timedelta(1), False)

    def testInvoiceExcludesItemsWithMoreRecentEventStamp(self):
        iiEarlier = M.InvoiceableItem(exampleTransaction(TENANCY_MIDDLE))
        self.session.add(iiEarlier)
        
        p = self.currentTenant
        i = M.Invoice(INVOICE_DATE, Decimal('1.11'))
        p.invoices.append(i)
        self.session.add(p)
        resetSession()
        
        iiLater = M.InvoiceableItem(exampleTransaction(TENANCY_MIDDLE))
        self.session.add(iiLater)
        resetSession()
        
        self.session.add(i)
        self.session.add(iiEarlier)
        self.session.add(iiLater)
        items = list(i.items)
        
        self.assertEqual(1, len(items))
        self.assertEqual(iiEarlier, items[0])

    def testInvoiceIncludesItemsBeforePreviousInvoiceDateButWithMoreRecentEventStamp(self):
        p = self.currentTenant

        i0 = M.Invoice(PREVIOUS_INVOICE_DATE, Decimal('0.00'))
        p.invoices.append(i0)
        self.session.add(p)
        resetSession()

        ii = M.InvoiceableItem(exampleTransaction(PREVIOUS_INVOICE_DATE - timedelta(1)))
        self.session.add(ii)
        
        i = M.Invoice(INVOICE_DATE, Decimal('1.11'))
        p.invoices.append(i)
        self.session.add(p)
        resetSession()

        self.session.add(i)
        self.session.add(ii)
        items = list(i.items)

        self.assertEqual(1, len(items))
        self.assertEqual(ii, items[0])

    def testInvoiceItemsHaveCorrectTenantLists(self):
        p = self.currentTenant
        
        iiBeforeOtherTenancy = M.InvoiceableItem(exampleTransaction(TENANCY_BEGIN - timedelta(1)))
        iiDuringOtherTenancy = M.InvoiceableItem(exampleTransaction(TENANCY_MIDDLE))
        iiAfterOtherTenancy = M.InvoiceableItem(exampleTransaction(TENANCY_END + timedelta(1)))
        iiList = [iiBeforeOtherTenancy, iiDuringOtherTenancy, iiAfterOtherTenancy]
        for x in iiList:
            self.session.add(x)
        
        i = M.Invoice(INVOICE_DATE, Decimal('1.11'))        
        p.invoices.append(i)
        self.session.add(p)
        resetSession()
        
        for x in iiList:
            self.session.add(x)
        for x in self.currentTenant, self.exTenant:
            self.session.add(x)
        self.session.add(i)
        
        self.assertEqual(iiList, list(i.items))
        self.assertEqual(Set([self.currentTenant]), Set(iiBeforeOtherTenancy.tenants))
        self.assertEqual(Set([self.exTenant, self.currentTenant]), Set(iiDuringOtherTenancy.tenants))
        self.assertEqual(Set([self.currentTenant]), Set(iiAfterOtherTenancy.tenants))


class InvoicePaymentsTest(InvoiceTest):
    def assertInvoicePaymentPresence(self, tenant, paymentDate, expectedPresent):
        t = exampleTransaction(paymentDate)
        pmt = M.PaymentWithStatementEvidence(t)
        
        p = tenant
        self.session.add(p)
        i0 = M.Invoice(PREVIOUS_INVOICE_DATE, Decimal('0.00'))
        i = M.Invoice(INVOICE_DATE, Decimal('1.11'))
        p.invoices.append(i0)
        p.invoices.append(i)
        p.payments.append(pmt)
        self.session.add(p)
        resetSession()

        self.session.add(i)
        self.session.add(pmt)
        payments = list(i.payments)
        
        if expectedPresent:
            self.assertEqual(1, len(payments))
            self.assertEqual(pmt, payments[0])
        else:
            self.assertEqual(0, len(payments))
    
    def testBug577WorkaroundDoesNotCauseIncorrectPaymentsQuery(self):
        t0 = exampleTransaction(TENANCY_BEGIN + timedelta(1))
        pmt0 = M.PaymentWithStatementEvidence(t0)
        i0 = M.Invoice(t0.date + timedelta(1), Decimal('0.00'))
        
        t = exampleTransaction(i0.invoiceDate + timedelta(1))
        pmt = M.PaymentWithStatementEvidence(t)
        i = M.Invoice(t.date + timedelta(1), Decimal('1.11'))
        
        p = self.currentTenant
        p.invoices.extend([i0, i])
        p.payments.extend([pmt0, pmt])
        self.session.add(p)
        resetSession()
        
        for x in pmt0, i0, pmt, i:
            self.session.add(x)
        
        payments0 = list(i0.payments)
        self.assertEqual(1, len(payments0))
        self.assertEqual(pmt0, payments0[0])

        payments = list(i.payments)
        self.assertEqual(1, len(payments))
        self.assertEqual(pmt, payments[0])

    def testInvoiceIncludesPaymentsBeforeTenancy(self):
        self.assertInvoicePaymentPresence(self.exTenant,
            TENANCY_BEGIN - timedelta(1), True)

    def testInvoiceIncludesPaymentsDuringTenancy(self):
        self.assertInvoicePaymentPresence(self.exTenant,
            TENANCY_MIDDLE, True)

    def testInvoiceIncludesPaymentsAfterTenancy(self):
        self.assertInvoicePaymentPresence(self.exTenant,
            TENANCY_END + timedelta(1), True)

    def testInvoiceExcludesPaymentsAfterInvoiceDate(self):
        self.assertInvoicePaymentPresence(self.currentTenant,
            INVOICE_DATE + timedelta(1), False)

    def testInvoiceExcludesPaymentsBeforePreviousInvoiceDate(self):
        self.assertInvoicePaymentPresence(self.currentTenant,
            PREVIOUS_INVOICE_DATE - timedelta(1), False)

    def testInvoiceExcludesPaymentsWithMoreRecentEventStamp(self):
        pmtEarlier = M.PaymentWithStatementEvidence(exampleTransaction(TENANCY_MIDDLE))
        
        p = self.currentTenant
        self.session.add(p)
        i = M.Invoice(INVOICE_DATE, Decimal('1.11'))
        p.invoices.append(i)
        p.payments.append(pmtEarlier)
        self.session.add(p)
        resetSession()
        
        pmtLater = M.PaymentWithStatementEvidence(exampleTransaction(TENANCY_MIDDLE))
        p.payments.append(pmtLater)
        self.session.add(p)
        resetSession()
        
        self.session.add(i)
        self.session.add(pmtEarlier)
        self.session.add(pmtLater)
        payments = list(i.payments)
        
        self.assertEqual(1, len(payments))
        self.assertEqual(pmtEarlier, payments[0])

    def testInvoiceIncludesPaymentsBeforePreviousInvoiceDateButWithMoreRecentEventStamp(self):
        p = self.currentTenant

        i0 = M.Invoice(PREVIOUS_INVOICE_DATE, Decimal('0.00'))
        p.invoices.append(i0)
        self.session.add(p)
        resetSession()

        self.session.add(p)

        pmt = M.PaymentWithStatementEvidence(exampleTransaction(PREVIOUS_INVOICE_DATE - timedelta(1)))
        p.payments.append(pmt)
        
        i = M.Invoice(INVOICE_DATE, Decimal('1.11'))
        p.invoices.append(i)
        self.session.add(p)
        resetSession()

        self.session.add(i)
        self.session.add(pmt)
        payments = list(i.payments)

        self.assertEqual(1, len(payments))
        self.assertEqual(pmt, payments[0])
    
    def testInvoiceExcludesPaymentsFromOtherTenants(self):
        pmtFromOneTenant = M.PaymentWithStatementEvidence(exampleTransaction(TENANCY_MIDDLE))
        pmtFromOtherTenant = M.PaymentWithStatementEvidence(exampleTransaction(TENANCY_MIDDLE))
        
        p = self.currentTenant
        p.payments.append(pmtFromOneTenant)
        
        p2 = self.exTenant
        p2.payments.append(pmtFromOtherTenant)
        
        i = M.Invoice(INVOICE_DATE, Decimal('1.11'))
        p.invoices.append(i)
        
        self.session.add(p)
        self.session.add(p2)
        
        resetSession()
        
        self.session.add(p)

        self.session.add(i)
        self.session.add(pmtFromOneTenant)
        self.session.add(pmtFromOtherTenant)
        payments = list(i.payments)
        
        self.assertEqual(1, len(payments))
        self.assertEqual(pmtFromOneTenant, payments[0])

   
class PreviousInvoiceTest(DatabaseTestCase):
    def setUp(self):
        DatabaseTestCase.setUp(self)
        self.tenant1 = M.Person('Joe', 'Bloggs')
        self.tenant1.tenancies.append(M.Tenancy(DAWN_OF_TIME))
        
        self.earliestInvoice = M.Invoice(PREVIOUS_INVOICE_DATE - timedelta(1), Decimal('876.54'))
        self.tenant1.invoices.append(self.earliestInvoice)
        self.earlierInvoice = M.Invoice(PREVIOUS_INVOICE_DATE, Decimal('123.45'))
        self.tenant1.invoices.append(self.earlierInvoice)
        self.session.add(self.tenant1)
        
        self.tenant2 = M.Person('John', 'Smith')
        self.tenant2.tenancies.append(M.Tenancy(DAWN_OF_TIME))
        self.session.add(self.tenant2)
    
    def testPreviousInvoiceReturnsEarlierInvoice(self):
        invoice = M.Invoice(INVOICE_DATE, Decimal('456.78'))
        self.tenant1.invoices.append(invoice)
        resetSession()

        self.session.add(invoice)
        self.session.add(self.earlierInvoice)
        self.assertEqual(self.earlierInvoice, invoice.previousInvoice)

    def testPreviousInvoiceIsNoneIfNoEarlierInvoiceForSameTenantExists(self):
        invoice = M.Invoice(INVOICE_DATE, Decimal('456.78'))
        self.tenant2.invoices.append(invoice)
        resetSession()
        self.session.add(self.tenant1)
        self.session.add(invoice)
        self.assertEqual(None, invoice.previousInvoice)

class InvoiceAmountTest(InvoiceTest):
    def testComputedAmountIsPreviousAmountPlusItemsPlusPayments(self):        
        previousInvoice = M.Invoice(PREVIOUS_INVOICE_DATE, Decimal('-100001.00'))
        item1 = M.InvoiceableItem(exampleTransaction(
            PREVIOUS_INVOICE_DATE + timedelta(1), Decimal('-020000.00')))
        item2 = M.InvoiceableItem(exampleTransaction(
            INVOICE_DATE - timedelta(1), Decimal('-003000.00')))
        
        pmt1 = M.PaymentWithOtherEvidence(PREVIOUS_INVOICE_DATE + timedelta(1),
            Decimal('000000.01'), 'pmt1 explanation')
        pmt2 = M.PaymentWithStatementEvidence(
            exampleTransaction(INVOICE_DATE - timedelta(1), Decimal('000000.20')))
        invoice = M.Invoice(INVOICE_DATE, Decimal('00.11'))
        
        self.session.add(item1)
        self.session.add(item2)
        
        p = self.currentTenant
        p.invoices.append(previousInvoice)
        p.invoices.append(invoice)
        p.payments.append(pmt1)
        p.payments.append(pmt2)
        self.session.add(p)
        
        resetSession()
        self.session.add(invoice)
        
        self.assertEqual(Decimal('-123000.79'), invoice.computedAmount)

class InvoiceableItemTest(DatabaseTestCase):
    def testInvoiceableItemPersists(self):
        t = exampleTransaction(date(2006, 1, 1))
        ii = M.InvoiceableItem(t)
        self.session.add(t)
        self.session.add(ii)
        resetSession()

        t = self.session.query(M.Transaction).first()
        ii = self.session.query(M.InvoiceableItem).first()
        self.assertEqual(t, ii.transaction)

if __name__ == '__main__':
    import TestSetup
    TestSetup.runOneTest(InvoiceAmountTest.testComputedAmountIsPreviousAmountPlusItemsLessPayments)
