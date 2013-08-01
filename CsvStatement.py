import csv
from datetime import date, datetime
from decimal import Decimal

def parseDate( csvDate ):
    return datetime.strptime(csvDate, '%d/%m/%Y').date()

class Transaction(object):
    def __init__(self, csvDict):
        try:
            self.date = parseDate(csvDict['Transaction Date'])
            self.type = csvDict['Transaction Type']
            self.description = csvDict['Transaction Description']
            self.creditAmount = (Decimal(csvDict['Credit Amount'] or '0') -
                                 Decimal(csvDict['Debit Amount' ] or '0'))
        except:
            print csvDict
            raise

# This doesn't really work because the CSV files contain quote characters that
# aren't at the beginning of a value and DictReader doesn't spot them.

class CsvStatement(object):
    def __init__(self, csvFile):
        entries = csv.DictReader(csvFile)
        self.transactions = [Transaction(entry) for entry in entries]
        self.beginDate = max([t.date for t in self.transactions])
        self.endDate = min([t.date for t in self.transactions])
