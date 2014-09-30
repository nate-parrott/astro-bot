from wise import Phrase, parse_phrase
import bs4
import urllib, urllib2

def get_html(url):
	url = "http://instapaper.com/m?u=" + urllib.quote_plus(url)
	html = urllib2.urlopen(url).read()
	story = bs4.BeautifulSoup(html).find(id='story')
	return unicode(story)

def normalize_url(url):
	scheme = url.split("://")[0]
	if scheme not in ['http', 'https']:
		url = 'http://' + url
	return url
 
examples = [
	Phrase("url", [["*url", "google.com"]]),
	Phrase("url", ["load", ["*url", "google.com"]]),
	Phrase("url", ["open", ["*url", "google.com"]]),
	Phrase("url", ["fetch", ["*url", "google.com"]]),
	Phrase("url", ["go to", ["*url", "google.com"]]),
	Phrase("url", ["show", ["*url", "google.com"]]),
	Phrase("search", ["search", ["~query", "hacker school"]]),
	Phrase("search", ["google", ["~query", "weather 11215"]]),
	Phrase("search", ["search", ["search_source/wikipedia", "wikipedia"], "for", ["~query", "praying mantis"]]),
	Phrase("search", ["search", ["search_source/this_site", "this site"], "for", ["~query", "contact us"]]),
	Phrase("search", ["find", ["~query", "support"], "on", ["search_source/this_site", "this site"]]),
	Phrase("search", [["~query", "barack obama"]]),
	Phrase("more_text", ["more"]),
	Phrase("more_text", [["*number", "2"], "more pages"]),
	Phrase("more_text", [["*number", "3"], "more pages"]),
	Phrase("more_text", ["next"]),
	Phrase("more_text", ["next", ["*number", "4"]]),
	Phrase("navigate", ["click", ["*number", "6"]]),
	Phrase("navigate", [["*number", "7"]]),
	Phrase("navigate", ["click link", ["target", "hvuiehguo"]]),
	Phrase("navigate", ["click", ["target", "ihenigo"], ["on_last_page", "on last page"]]),
	Phrase("navigate", ["load", ["target", "jegotghr"], ["on_last_page", "from previous page"]]),
	Phrase("show_navigation", ["show navigation"]),
	Phrase("help", ["help me"]),
	Phrase("help", ["what are the options"]),
	Phrase("help", ["what can I say?"]),
	Phrase("summarize", ["summarize this page"]),
	Phrase("summarize", ["summarize", ["*number", "2"]]),
	Phrase("show summary for", ["*number", "3"]),
	Phrase("back", ["back"])
]
regexes = {
"url": r"[a-zA-Z0-9_\-\.]+\.[a-z]+(\/[^ ]*)?",
"number": r"\-?[0-9]+(\.[0-9]+)?"
}

def txtfy_word(w):
	maps = {
	"to": "2",
	"too": "2",
	"you": "u",
	"you'll": "u'll",
	"your": "ur",
	"for": "4",
	"and": "&",
	"at": "@",
	"with": "w/",
	"before": "b4",
	"one": "1",
	}
	if w.lower() in maps:
		return maps[w.lower()]
	return w

def txtfy(text):
	tokens = text.split(" ")
	return u" ".join(map(txtfy_word, tokens))

def get_document(html):
	soup = bs4.BeautifulSoup(html)
	doc = {"text": u"", "headers": [], "links": []}
	def break_line():
		if len(doc['text']) > 0 and doc['text'][-1] != '\n':
			doc['text'] += '\n'
	def break_word():
		if len(doc['text']) > 0 and doc['text'][-1] not in " \n":
			doc['text'] += " "
	def emit_text(t):
		break_word()
		doc['text'] += txtfy(t)
	def traverse(tag):
		if tag.name == 'a' and tag.has_attr('href'):
			doc['links'].append(tag['href'])
			emit_text(u'[{0}]({1}) '.format(tag.get_text(), len(doc['links'])))
		elif tag.name in ['h1', 'h2', 'h3', 'h4']:
			break_line()
			doc['headers'].append((tag.get_text(), len(doc['text'])))
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
	# print "DOC"
	# print doc
	# print "ENDDOC"
	return doc

# INTERACTIONS:

SMS_LEN = 160

print "RESTART BROWSE"

def get_url(url, state):
	url = normalize_url(url)
	if 'frame' in state:
		state['backstack'] = state.get('backstack', []) + [state['frame']]
		while len(state['backstack']) > 4:
			state['backstack'] = state['backstack'][1:]
	state['frame'] = {"doc": get_document(get_html(url)), "offset": 0}
	return n_more_messages(1, state)

def n_more_messages(n_more, state):
	n_more = min(7, n_more)
	messages = []
	for i in xrange(n_more):
		text = state['frame']['doc']['text']
		if state['frame']['offset'] < len(text):
			more_text = text[state['frame']['offset']:state['frame']['offset'] + min(len(text)-state['frame']['offset'], SMS_LEN)]
			messages.append(more_text)
			state['frame']['offset'] += len(more_text)
		else:
			if i == 0:
				messages.append("I couldn't find any more content on this page.")
			break
	return (messages, state)

def back(state):
	if len(state.get('backstack', [])) > 0:
		frame = state['backstack'][-1]
		state['backstack'] = state['backstack'][:-1]
		state['frame'] = frame
		state['frame']['offset'] = max(0, state['frame']['offset'])
		return n_more_messages(1, state)

def interact(query, state):
	parsed = parse_phrase(query, examples, regexes)
	print parsed
	if parsed.intent == 'url':
		return get_url(parsed.get('*url', None), state)
	elif parsed.intent == 'more_text':
		return n_more_messages(int(parsed.get('*number', '1')), state)
	elif parsed.intent == 'navigate' and parsed.get('*number', None):
		return get_url(state['document']['links'][int(parsed.get('*number', '0'))], state)
	elif parsed.intent == 'help':
		return (['"Go to wsj.com", "search wikipedia for Azerbaijan". Text the # of a link to click it.'], state)
	elif parsed.intent == 'back':
		return back(state)
	else:
		return (["What's that? I don't understand. Say 'help me' for help."], state)
