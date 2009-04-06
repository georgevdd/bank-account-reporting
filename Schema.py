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

metadata = md
del md
