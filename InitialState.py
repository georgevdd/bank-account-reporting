#!/usr/bin/env python

import Model as M
from Database import ensureSession, resetSession, rebuildSchema
from ImportStatements import importAll
from datetime import date
# For Python 2.3, decimal is available from
# http://sourceforge.net/projects/sigefi
from decimal import Decimal

LIKELY_INVOICEABLE_PATTERNS = [
    '%gas%', 
    '%elec%', 
    '%water%', 
    '%edf%', 
    '%council%', 
    '%energy%', 
]

def createInitialState():
    rebuildSchema()
    
    session = ensureSession()

    for pattern in LIKELY_INVOICEABLE_PATTERNS:
        session.add(M.LikelyInvoiceable(pattern))
    
    importAll()

    whenWeAllMovedIn = date(2003, 5, 4)
    whenAnnaReplacedEd = date(2005, 3, 3)
    whenBobbyReplacedAnna = date(2005, 12, 1)
    whenAlexaMovedIn = date(2006, 5, 1)
    whenAlexaMovedOut = date(2006, 7, 1)
    whenSimonReplacedBobby = date(2006, 7, 1)

    george = M.Person('George', 'van den Driessche')
    george.tenancies.append(M.Tenancy(whenWeAllMovedIn))

    dude = M.Person('David', 'Rosel')
    dude.tenancies.append(M.Tenancy(whenWeAllMovedIn))
    dude.invoices.append(M.Invoice(date(2005, 12, 1), Decimal('550.52')))
    dude.invoices.append(M.Invoice(date(2006, 1, 30), Decimal('99.38')))
    dude.payments.append(M.PaymentWithOtherEvidence(date(2006, 4, 6), Decimal('649.90'),
            'Payment to 20-23-97 00177504'))

    joe = M.Person('Joseph', 'Hamed')
    joe.tenancies.append(M.Tenancy(whenWeAllMovedIn))
    joe.invoices.append(M.Invoice(date(2005, 12, 1), Decimal('550.52')))
    joe.invoices.append(M.Invoice(date(2006, 1, 30), Decimal('99.38')))

    ed = M.Person('Edward', 'Parcell')
    ed.tenancies.append(M.Tenancy(whenWeAllMovedIn, whenAnnaReplacedEd))

    anna = M.Person('Anna', 'Tozer')
    anna.tenancies.append(M.Tenancy(whenAnnaReplacedEd, whenBobbyReplacedAnna))

    bobby = M.Person('Bobby', 'Wong')
    bobby.tenancies.append(M.Tenancy(whenBobbyReplacedAnna, whenSimonReplacedBobby))
    bobby.invoices.append(M.Invoice(date(2006, 1, 30), Decimal('99.38')))
    bobby.invoices.append(M.Invoice(date(2006, 6, 9), Decimal('303.55')))

    alexa = M.Person('Alexa', 'Sale')
    alexa.tenancies.append(M.Tenancy(whenAlexaMovedIn, whenAlexaMovedOut))

    simon = M.Person('Simon', 'Hill')
    simon.tenancies.append(M.Tenancy(whenSimonReplacedBobby))

    mayuko = M.Person('Mayuko', 'Hill')
    mayuko.tenancies.append(M.Tenancy(date(2006, 10, 1), date(2007, 1, 16)))

    for person in [george, dude, joe, ed, anna, bobby, alexa, simon, mayuko]:
        session.add(person)
    resetSession()

if __name__ == '__main__':
    createInitialState()
