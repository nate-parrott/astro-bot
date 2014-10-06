import urllib, urllib2
import bs4
from txtfy import txtfy
from html2text import html2doc
import urlparse

SMS_LEN = 160

def normalize_url(url):
	scheme = url.split("://")[0]
	if scheme not in ['http', 'https']:
		url = 'http://' + url
	return url

# opera mini for dumbphones:
USER_AGENT = "Opera/9.80 (J2ME/MIDP; Opera Mini/4.2.13337/34.818; U; en) Presto/2.8.119 Version/11.10"

def get_content(url):
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', USER_AGENT)]
	html = opener.open(url).read()
	title = bs4.BeautifulSoup(html).title.get_text()
	return (html, title)

def get_content_ip(url):
	url = "http://instapaper.com/m?u=" + urllib.quote_plus(url)
	html = urllib2.urlopen(url).read()
	soup = bs4.BeautifulSoup(html)
	story = soup.find(id='story')
	return unicode(story), soup.title.get_text()

NO_URL = ""

class Document(object):
	url = None
	def __init__(self, url=None, html=None):
		if url:
			url = normalize_url(url)
			html, self.title = get_content(url)
			self.url = url
		if not isinstance(html, unicode):
			html = html.decode('utf-8')
		self.text, self.links, self.headers = html2doc(html, baseurl = url if url else "")
		print "HEADERS", self.headers

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
		parsed = urlparse.urlparse(url)
		if parsed.scheme == 'go-to-offset':
			self.back()
			self.frame_stack[-1].offset = int(parsed.netloc)
		else:
			self.frame_stack.append(Frame(Document(url)))

	def back(self):
		if len(self.frame_stack):
			self.frame_stack = self.frame_stack[:-1]

	def resend_current_place(self):
		self.frame_stack[-1].offset = max(0, self.frame_stack[-1].offset - SMS_LEN)
		return self.get_n_messages(1)

	def go_to_contents(self):
		current_page_title = self.frame_stack[-1].document.title
		html = "<title>Headings on {0}</title>".format(current_page_title) + u"<br/>".join([u"<a href='go-to-offset://{0}'>{1}</a>".format(offset, heading) for heading, offset in self.frame_stack[-1].document.headers])
		doc = Document(html = html)
		self.frame_stack.append(Frame(doc))

	def get_n_messages(self, n, backwards=False):
		if backwards:
			self.frame_stack[-1].offset = max(0, self.frame_stack[-1].offset - 160)

		if not backwards and self.frame_stack[-1].offset >= len(self.frame_stack[-1].document.text):
			return ["<end of page>"]
		else:
			messages = []
			for i in xrange(n):
				start_offset = self.frame_stack[-1].offset
				if backwards:
					start_offset = max(0, start_offset-160)
				end_offset = min(len(self.frame_stack[-1].document.text), start_offset + SMS_LEN)
				if end_offset - start_offset == 0:
					break
				messages.append(self.frame_stack[-1].document.text[start_offset : end_offset])
				self.frame_stack[-1].offset = start_offset if backwards else end_offset
				if self.frame_stack[-1].offset == 0:
					break
		if backwards:
			self.frame_stack[-1].offset = min(len(self.frame_stack[-1].document.text), self.frame_stack[-1].offset + 160)
		return messages

