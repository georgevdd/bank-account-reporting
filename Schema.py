from sqlalchemy import *
import sqlalchemy.schema as schema
import sqlalchemy.types as types
# For Python 2.3, decimal is available from
# http://sourceforge.net/projects/sigefi
from decimal import Decimal as PythonDecimal

md = MetaData()

class Decimal(types.TypeDecorator):
    '''Column type that can handle Python Decimal instances.'''
    impl = types.Numeric
    def convert_bind_param(self, value, engine):
        return float(value)
    def convert_result_value(self, value, engine):
        return PythonDecimal(str(value))

event = Table('event', md,
    Column('event_id', Integer, primary_key=True),
    Column('event_timestamp', DateTime, nullable=False)
)

def eventstampColumn():
    '''Describes a column suitable for storing the eventstamp of an
    eventstamped object.'''
    return Column('event_id', Integer, ForeignKey('event.event_id'), nullable=False) 

statementItem = Table('stmtitem', md,
    Column('dtposted', Date, nullable=False),
    Column('trnamt', Decimal, nullable=False),
    Column('fitid', String, nullable=False, primary_key=True),
    Column('name', String(31), nullable=False),
    Column('memo', String, nullable=False),
    eventstampColumn(),
)

importedStatement = Table('imported_statement', md,
    Column('begin_date', Date, nullable=False, primary_key=True),
    Column('end_date', Date, nullable=False, primary_key=True),
    eventstampColumn(),
)

person = Table('person', md,
    Column('person_id', Integer, primary_key=True),
    Column('given_name', String, nullable=False),
    Column('family_name', String, nullable=False)
)

personTenancy = Table('person_tenancy', md,
    Column('tenancy_id', Integer, primary_key=True),
    eventstampColumn(),
    Column('person_id', Integer, ForeignKey('person.person_id'), nullable=False),
    Column('date_moved_in', Date, nullable=False),
    Column('date_moved_out', Date, nullable=True)
)

personPayment = Table('person_payment', md,
    Column('payment_id', Integer, primary_key=True),
    eventstampColumn(),
    Column('person_id', Integer, ForeignKey('person.person_id'), nullable=False),
    Column('payment_date', Date, nullable=False),
    Column('amount', Decimal, nullable=False),
    Column('evidence_type', String(10), nullable=False)
)

paymentStatementEvidence = Table('payment_statement_evidence', md,
    Column('payment_id', Integer, ForeignKey('person_payment.payment_id'), primary_key=True),
    Column('fitid', String, ForeignKey('stmtitem.fitid'), nullable=False)
)

paymentOtherEvidence = Table('payment_other_evidence', md,
    Column('payment_id', Integer, ForeignKey('person_payment.payment_id'), primary_key=True),
    Column('explanation', String, nullable=False)
)

invoiceableItem = Table('invoiceable_item', md,
    Column('invoiceable_item_id', Integer, primary_key=True),
    eventstampColumn(),
    Column('fitid', String, ForeignKey('stmtitem.fitid'), nullable=False)
)

personInvoice = Table('person_invoice', md,
    Column('invoice_id', Integer, primary_key=True),
    eventstampColumn(),
    Column('person_id', Integer, ForeignKey('person.person_id'), nullable=False),
    Column('invoice_date', Date, nullable=False),
    Column('amount', Decimal, nullable=False)
)

likelyInvoiceable = Table('likely_invoiceable', md,
    Column('pattern', String, primary_key=True)
)

metadata = md
del md
