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
import json
from google.appengine.ext import ndb
import browse
from xml.sax import saxutils

class State(ndb.Model):
	json = ndb.TextProperty()

def interact(query, stateid):
	state = State.get_or_insert(stateid, json="{}")
	messages, new_state = browse.interact(query, json.loads(state.json))
	state.json = json.dumps(new_state)
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


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/interact', Interact),
    ('/twilio', Twilio)
], debug=True)
