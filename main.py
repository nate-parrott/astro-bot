#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import uuid
import os
import base64
import pickle
from google.appengine.ext import ndb
import browse
from xml.sax import saxutils
import json

class State(ndb.Model):
	pickled = ndb.BlobProperty(compressed=True)

def interact(query, stateid):
	state = State.get_or_insert(stateid)
	unpickled_state = pickle.loads(state.pickled) if state.pickled else {}
	messages = browse.interact(query, unpickled_state)
	print "MESSAGES", messages
	state.pickled = pickle.dumps(unpickled_state)
	state.put()
	return messages

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(open('page.html').read())

class Interact(webapp2.RequestHandler):
	def post(self):
		query = self.request.get('query')
		stateid = self.request.cookies.get('stateid', None)
		if stateid == None:
			stateid = base64.b64encode(uuid.uuid4().bytes + os.urandom(64))
			self.response.set_cookie('stateid', stateid, max_age=3600*20)
		self.response.write(json.dumps({"messages": interact(query, stateid)}))

class Twilio(webapp2.RequestHandler):
	def post(self):
		from_phone = self.request.get('From')
		query = self.request.get('Body')
		messages = []
		try:
			messages = interact(query, 'phone:'+from_phone)
		except Exception:
			messages.append("Oops, something went wrong.")
		self.response.content_type = 'text/xml'
		self.response.write('<?xml version="1.0" encoding="UTF-8" ?><Response>')
		for msg in messages:
			self.response.write(u"<Message>{0}</Message>".format(saxutils.escape(msg)))
		self.response.write("</Response>")


class InstructionsHandler(webapp2.RequestHandler):
	def get(self):
		self.response.write(open('instructions.html').read()) 

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/instructions', InstructionsHandler),
    ('/interact', Interact),
    ('/twilio', Twilio)
], debug=True)
