import xml.dom.minidom as mdom
import os
import os.path
from datetime import date
# For Python 2.3, decimal is available from
# http://sourceforge.net/projects/sigefi
from decimal import Decimal

# Hacks to make access to child elements easier.
mdom.Document.__getitem__ = lambda s, x: mdom.Document.getElementsByTagName( s, x )[0]
mdom.Element.__getitem__ = lambda s, x: mdom.Element.getElementsByTagName( s, x )[0]

def parseDate( moneyDate ):
    return date( int( moneyDate[:4] ), int( moneyDate[4:6] ), int( moneyDate[6:8] ) )

class Transaction(object):
    def __init__( self, date, amount, fitid, name, memo ):
        self.date = date
        self.amount = amount
        self.fitid = fitid
        self.name = name
        self.memo = memo

class Statement:
    def __init__( self, file ):
        self.readHeader( file )
        self.readBody( file )
        
    def readHeader( self, file ):
        self.header = {}
        file.readline() # First line is blank.
        line = file.readline().strip()
        while line:
            k, v = tuple( line.split( ':' )[:2] )
            self.header[k] = v.strip()
            line = file.readline().strip()
    
    def readBody( self, file ):
        self.transactions = []
        dom = mdom.parse( file )
        tranListElem = dom['OFX']['BANKMSGSRSV1']['STMTTRNRS']['BANKTRANLIST']
        self.beginDate = parseDate(tranListElem['DTSTART'].firstChild.wholeText.strip())
        self.endDate = parseDate(tranListElem['DTEND'].firstChild.wholeText.strip())
        for tranElem in tranListElem.getElementsByTagName( 'STMTTRN' ):
            get = lambda elem: tranElem[elem].firstChild.wholeText.strip()
            rawTranType = get('TRNTYPE')
            rawDate = get('DTPOSTED')
            rawAmount = get('TRNAMT')
            name = get('NAME')
            memo = get('MEMO')
            fitid = get('FITID')
            t = Transaction( parseDate( rawDate ),
                             Decimal( rawAmount ),
                             fitid,
                             name,
                             memo )
            if not ((rawTranType == 'DEBIT' and t.amount < 0) or \
                    (rawTranType == 'CREDIT' and t.amount > 0)):
                raise Exception( 'Unexpected inconsistency between \
                    transaction type %s and amount %s' % (rawTranType, t.amount) )
            self.transactions.append( t )
