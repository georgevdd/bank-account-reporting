#!/usr/bin/env python

import Model as M
from Database import ensureSession, resetSession, rebuildSchema
from ImportStatements import importAll
from datetime import date
# For Python 2.3, decimal is available from
# http://sourceforge.net/projects/sigefi
from decimal import Decimal

LIKELY_INVOICEABLE_PATTERNS = [
    '%se gas%', 
    '%southern electric%', 
    '%thames water%', 
#    '%edf%', 
#   '%council%', 
    '%wandsworth b.c.%',
    '%wandsworth council%',
    '%virgin media%',
#'%energy%', 
]

def createInitialState():
    rebuildSchema()
    
    session = ensureSession()

    for pattern in LIKELY_INVOICEABLE_PATTERNS:
        session.add(M.LikelyInvoiceable(pattern))
    
    importAll()

    mike = M.Person('Mike', 'Sackur')
    mike.tenancies.append(M.Tenancy(date(2012, 6, 1), None))

    for person in [mike]:
        session.add(person)
    resetSession()

if __name__ == '__main__':
    createInitialState()
