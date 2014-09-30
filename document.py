import urllib, urllib2
import bs4
from txtfy import txtfy

SMS_LEN = 160

def normalize_url(url):
	scheme = url.split("://")[0]
	if scheme not in ['http', 'https']:
		url = 'http://' + url
	return url

def get_content(url):
	url = "http://instapaper.com/m?u=" + urllib.quote_plus(url)
	html = urllib2.urlopen(url).read()
	soup = bs4.BeautifulSoup(html)
	story = soup.find(id='story')
	return unicode(story), soup.title.get_text()

NO_URL = ""

class Document(object):
	def __init__(self, url=None, html=None):
		self.url = url
		if url:
			html, self.title = get_content(normalize_url(url))
		soup = bs4.BeautifulSoup(html)
		self.text = u""
		self.links = []
		self.headers = []
		def break_line():
			if len(self.text) > 0 and self.text[-1] != '\n':
				self.text += '\n'
		def break_word():
			if len(self.text) > 0 and self.text[-1] not in " \n":
				self.text += " "
		def emit_text(t):
			break_word()
			self.text += txtfy(t)
		def traverse(tag):
			if tag.name == 'a' and tag.has_attr('href'):
				self.links.append(tag['href'])
				emit_text(u'[{0}]({1}) '.format(tag.get_text(), len(self.links)))
			elif tag.name in ['h1', 'h2', 'h3', 'h4']:
				break_line()
				self.headers.append((tag.get_text(), len(self.text)))
				process_contents(tag)
				break_line()
			elif tag.name in ['li', 'p']:
				break_line()
				process_contents(tag)
				break_line()
			else:
				process_contents(tag)
		def process_contents(tag):
			for child in tag.contents:
				if isinstance(child, bs4.NavigableString):
					emit_text(unicode(child))
				elif hasattr(child, 'name'):
					traverse(child)
		traverse(soup)
		break_line()
		emit_text("<end of page>")

class Frame(object):
	def __init__(self, doc):
		self.document = doc
		self.offset = 0

class BrowserState(object):
	def __init__(self):
		self.frame_stack = []

	def clean_up(self):
		while len(self.frame_stack) > 5:
			self.frame_stack = self.frame_stack[1:]

	def navigate_to_url(self, url):
		self.frame_stack.append(Frame(Document(url)))

	def back(self):
		if len(self.frame_stack):
			self.frame_stack = self.frame_stack[:-1]

	def resend_current_place(self):
		self.frame_stack[-1].offset = max(0, self.frame_stack[-1].offset - SMS_LEN)
		return self.get_n_messages(1)

	def get_n_messages(self, n):
		if self.frame_stack[-1].offset >= len(self.frame_stack[-1].document.text):
			return ["<end of page>"]
		else:
			messages = []
			for i in xrange(n):
				start_offset = self.frame_stack[-1].offset
				end_offset = min(len(self.frame_stack[-1].document.text), start_offset + SMS_LEN)
				if end_offset - start_offset == 0:
					break
				messages.append(self.frame_stack[-1].document.text[start_offset : end_offset])
				self.frame_stack[-1].offset = end_offset
			return messages

