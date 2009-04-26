import cgi
import datetime
import simplejson as json
import sys
import urlparse

import Database
import Model

def asDict(obj):
  return dict((k, v) for (k, v) in obj.__dict__.iteritems()
      if not k.startswith('_'))

TYPE_TO_JSON = {
  datetime.date : datetime.date.isoformat,
  datetime.datetime : datetime.datetime.isoformat,
  Model.Decimal : str
}

def toJson(obj):
  return TYPE_TO_JSON.get(type(obj), asDict)(obj)

def statements(self):
  result = list(Database.ensureSession()
      .query(Model.ImportedStatement)
      .order_by(Model.ImportedStatement.endDate))
  self.send_response(200)
  self.send_header("content-type", "text/html;charset=utf-8")
  self.end_headers()
  json.dump(result, self.wfile, default = toJson)

def transactions(self, startDate, endDate):
  startDate = datetime.date(*map(int, startDate[0].split('-')))
  endDate = datetime.date(*map(int, endDate[0].split('-')))
  result = list(Database.ensureSession()
      .query(Model.Transaction)
      .filter(Model.Transaction.date >= startDate)
      .filter(Model.Transaction.date <= endDate)
      .order_by(Model.Transaction.date))
  self.send_response(200)
  self.send_header("content-type", "text/html;charset=utf-8")
  self.end_headers()
  json.dump(result, self.wfile, default = toJson)

Action = sys.modules[__name__]

def doAction(self):
  url = urlparse.urlparse(self.path)
  actionName = url.path.split('/')[1]
  kwargs = cgi.parse_qs(url.query)
  print actionName, kwargs
  try:
    action = getattr(Action, actionName)
  except AttributeError:
    self.send_error(404)
    return
  action(self, **kwargs)

import Database
def noLogin():
  return Database.getBillsDbs('georgevdd', 'foo')
Database.getDbs = noLogin
