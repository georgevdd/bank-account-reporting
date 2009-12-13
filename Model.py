import Schema
import MsMoney
from datetime import datetime
import sqlalchemy
import sqlalchemy.orm as orm
sqlfunc = sqlalchemy.func
# For Python 2.3, decimal is available from
# http://sourceforge.net/projects/sigefi
from decimal import Decimal

MAXIMUM_LIKELY_PAYMENT = Decimal('1000.00')

def requiredSession(obj):
    s = orm.session.object_session(obj)
    if not s:
        raise Exception("Object %s has no session" % obj)
    return s


class Event(object):
    '''Object representing an update to the database. All eventstamped
    objects that were created in the same event will have a reference
    to the same eventstamp.'''
    def __init__(self, eventTimestamp):
        self.eventTimestamp = eventTimestamp

    currentEvent = None

class EventStamped(object):
    '''Base class for all types where we need to know exactly when
    each instance was created.'''
    def __init__(self):
        if Event.currentEvent is None:
            Event.currentEvent = Event(datetime.utcnow())
        self.creationEvent = Event.currentEvent

class Transaction(MsMoney.Transaction, EventStamped):
    def __init__(self, *args, **kwargs):
        EventStamped.__init__(self)
        MsMoney.Transaction.__init__(self, *args, **kwargs)

class ImportedStatement(EventStamped):
    def __init__(self, beginDate, endDate):
        EventStamped.__init__(self)
        self.beginDate = beginDate
        self.endDate = endDate


class Person(object):
    def __init__(self, givenName, familyName):
        self.givenName = givenName
        self.familyName = familyName
    def __repr__(self):
        return object.__repr__(self) + ' (%s %s)' % (self.givenName, self.familyName)
    def _get_fullName(self):
        return '%s %s' % (self.givenName, self.familyName)
    fullName = property(_get_fullName)

class Tenancy(EventStamped):
    def __init__(self, dateMovedIn, dateMovedOut = None):
        EventStamped.__init__(self)
        self.dateMovedIn = dateMovedIn
        self.dateMovedOut = dateMovedOut
    def __repr__(self):
        return EventStamped.__repr__(self) + ' (%s - %s)' % \
            (self.dateMovedIn, self.dateMovedOut)

    def includes(personIdProperty, dateProperty):
        return ((Tenancy.personId == personIdProperty) &
            (Tenancy.dateMovedIn <= dateProperty) &
            ((Tenancy.dateMovedOut > dateProperty) |
             (Tenancy.dateMovedOut == None)))
    includes = staticmethod(includes)


class Payment(EventStamped):
    def __init__(self, paymentDate, amount):
        EventStamped.__init__(self)
        self.paymentDate = paymentDate
        self.amount = amount

class PaymentWithStatementEvidence(Payment):
    def __init__(self, transaction):
        Payment.__init__(self, transaction.date, transaction.amount)
        self.transaction = transaction

class PaymentWithOtherEvidence(Payment):
    def __init__(self, paymentDate, amount, explanation):
        Payment.__init__(self, paymentDate, amount)
        self.explanation = explanation


class InvoiceableItem(EventStamped):
    def __init__(self, transaction):
        EventStamped.__init__(self)
        self.transaction = transaction

    def _get_tenants(self):
        s = Schema
        return requiredSession(self) \
            .query(Person) \
            .filter( \
                (self.fitid == Transaction.fitid) &
                Tenancy.includes(Person.personId, Transaction.date)) \
            .order_by(Person.personId)
    tenants = property(_get_tenants)

    def _get_amountPerTenant(self):
        return self.transaction.amount / len(list(self.tenants))
    amountPerTenant = property(_get_amountPerTenant)

class Invoice(EventStamped):
    def __init__(self, invoiceDate, amount=None):
        EventStamped.__init__(self)
        self.invoiceDate = invoiceDate
        self.amount = amount

    def _get_computedAmount(self):
        prevInv = self.previousInvoice
        if prevInv is None:
            prevAmt = Decimal('0.00')
        else:
            prevAmt = prevInv.amount
        return self.total + prevAmt + self.totalPayments
    computedAmount = property(_get_computedAmount)

    def _get_previousInvoice(self):
        a = sqlalchemy
        session = requiredSession(self)
        
        result = session \
            .query(Invoice) \
            .filter(
                (Invoice.personId == self.personId) &
                self._hasNoEarlierEventIdThan(Invoice.eventId) &
                (Invoice.invoiceDate < self.invoiceDate)) \
            .order_by(Invoice.invoiceDate.desc()) \
            .first()
        return result
    previousInvoice = property(_get_previousInvoice)

    def _hasNoEarlierEventIdThan(self, eventIdProperty):
        if self.eventId is None:
            return True
        else:
            return eventIdProperty <= self.eventId

    def _noPreviousInvoiceSince(self, eventIdProperty, dateProperty):
        return ~sqlalchemy.exists([Invoice.invoiceId],
            (Invoice.personId == self.personId) &
            (eventIdProperty <= Invoice.eventId) &
            (dateProperty <= Invoice.invoiceDate) &
            (Invoice.invoiceDate < self.invoiceDate))

    def _get_items(self):
        return requiredSession(self) \
            .query(InvoiceableItem) \
            .filter(
                (InvoiceableItem.fitid == Transaction.fitid) &
                self._hasNoEarlierEventIdThan(InvoiceableItem.eventId) &
                (Transaction.date <= self.invoiceDate) &
                self._noPreviousInvoiceSince(
                    InvoiceableItem.eventId, Transaction.date) &
                Tenancy.includes(self.personId, Transaction.date))
    items = property(_get_items)
    
    def _get_payments(self):
        a = sqlalchemy
        s = Schema
        
        return requiredSession(self) \
            .query(Payment) \
            .filter(
                (Payment.personId == self.personId) &
                self._hasNoEarlierEventIdThan(Payment.eventId) &
                (Payment.paymentDate <= self.invoiceDate) &
                self._noPreviousInvoiceSince(Payment.eventId, Payment.paymentDate)) \
            .order_by([Payment.paymentDate])
    payments = property(_get_payments)
    
    def _get_total(self):
        return sum([x.amountPerTenant for x in self.items])
    total = property(_get_total)
    
    def _get_totalPayments(self):
        return sum([x.amount for x in self.payments])
    totalPayments = property(_get_totalPayments)

class LikelyInvoiceable(object):
    def __init__(self, pattern):
        self.pattern = pattern


def initMappings():
    a = sqlalchemy    
    s = Schema
    
    def eventstampedMapper(class_, local_table, **kwargs):
        props = kwargs.setdefault('properties', {})
        props['creationEvent'] = orm.relation(Event)
        props['eventId'] = local_table.c.event_id
        return orm.mapper(class_, local_table, **kwargs)
    
    orm.mapper(Event, s.event, properties={
        'eventId' : s.event.c.event_id,
        'eventTimestamp' : s.event.c.event_timestamp,
        })

    
    transactionMapper = eventstampedMapper(
        Transaction, s.statementItem, properties={
            'date' : s.statementItem.c.dtposted,
            'amount' : s.statementItem.c.trnamt,
            })

    isLikelyInvoiceable = a.exists([1],
        s.statementItem.c.name.ilike(s.likelyInvoiceable.c.pattern)) \
        .correlate(s.statementItem) \
        .label('isLikelyInvoiceable')
    isInvoiceable = a.exists([1],
        s.statementItem.c.fitid == s.invoiceableItem.c.fitid) \
        .label('isInvoiceable')
    isLikelyPayment = ((s.statementItem.c.trnamt > 0) &
        (s.statementItem.c.trnamt <= MAXIMUM_LIKELY_PAYMENT)) \
        .label('isLikelyPayment')
    isPayment = a.exists([1],
        s.statementItem.c.fitid == s.paymentStatementEvidence.c.fitid) \
        .label('isPayment')

    transactionListSelect = a.select([
        s.statementItem,
        isLikelyInvoiceable,
        isInvoiceable,
        isLikelyPayment,
        isPayment,
        ]).alias('transactionSelect')
    
    global transactionListMapper
    transactionListMapper = orm.mapper(Transaction,
        transactionListSelect, properties={
            'date' : s.statementItem.c.dtposted,
            'amount' : s.statementItem.c.trnamt,
            },
        non_primary=True)

    eventstampedMapper(ImportedStatement, s.importedStatement, properties={
        'beginDate' : s.importedStatement.c.begin_date,
        'endDate' : s.importedStatement.c.end_date,
        })


    orm.mapper(Person, s.person, properties={
        'personId' : s.person.c.person_id,
        'givenName' : s.person.c.given_name,
        'familyName' : s.person.c.family_name,
        'tenancies' : orm.relation(Tenancy, backref='person', cascade='all, delete-orphan'),
        'payments' : orm.relation(Payment, backref='personFrom', cascade='all, delete-orphan'),
        'invoices' : orm.relation(Invoice, backref='personTo', cascade='all, delete-orphan'),
        })

    eventstampedMapper(Tenancy, s.personTenancy, properties={
        'tenancyId' : s.personTenancy.c.tenancy_id,
        'personId' : s.personTenancy.c.person_id,
        'dateMovedIn' : s.personTenancy.c.date_moved_in,
        'dateMovedOut' : s.personTenancy.c.date_moved_out,
        })
    

    paymentJoin = orm.polymorphic_union(
        {
            'paymentWithStatementEvidence' : s.personPayment.join(s.paymentStatementEvidence),
            'paymentWithOtherEvidence' : s.personPayment.join(s.paymentOtherEvidence),
        }, None, 'paymentjoin')
    
    paymentMapper = eventstampedMapper(Payment, s.personPayment,
        polymorphic_on=s.personPayment.c.evidence_type,
        properties={
            'paymentId' : s.personPayment.c.payment_id,
            'personId' : s.personPayment.c.person_id,
            'paymentDate' : s.personPayment.c.payment_date,
            'evidenceType' : s.personPayment.c.evidence_type,
            })
    orm.mapper(PaymentWithStatementEvidence, s.paymentStatementEvidence,
         inherits=paymentMapper, polymorphic_identity='statement',
         properties={ 'transaction' : orm.relation(Transaction) })
    orm.mapper(PaymentWithOtherEvidence, s.paymentOtherEvidence,
         inherits=paymentMapper, polymorphic_identity='other')


    eventstampedMapper(InvoiceableItem, s.invoiceableItem, properties={
         'transaction' : orm.relation(Transaction),
         })

    eventstampedMapper(Invoice, s.personInvoice, properties={
        'invoiceId' : s.personInvoice.c.invoice_id,
        'personId' : s.personInvoice.c.person_id,
        'invoiceDate' : s.personInvoice.c.invoice_date,
        'amount' : s.personInvoice.c.amount,
        })

    orm.mapper(LikelyInvoiceable, s.likelyInvoiceable)

    orm.compile_mappers()

initMappings()
