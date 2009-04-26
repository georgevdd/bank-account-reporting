import BaseHTTPServer

import Action

class WebRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def do_GET(self):
    reload(Action)
    Action.doAction(self)

server = BaseHTTPServer.HTTPServer(('localhost',1337), WebRequestHandler)
server.serve_forever()
