from wise import Phrase, parse_phrase
import parse_command
import document
import urllib
import search

def interact(query, state):
	# query: String, state: Dictionary
	parsed = parse_command.parse_command(query)
	print parsed
	if 'BrowserState' in state:
		bstate = state['BrowserState']
	else:
		state['BrowserState'] = document.BrowserState()
		bstate = state['BrowserState']

	bstate.clean_up()

	if parsed.intent == 'url':
		bstate.navigate_to_url(parsed.get("*url", None))
		return bstate.get_n_messages(1)
	elif parsed.intent in ('more_text', 'previous_text'):
		return bstate.get_n_messages(min(7, int(parsed.get('*number', '1'))), backwards=(parsed.intent=='previous_text'))
	elif parsed.intent == 'back_to_top':
		bstate.frame_stack[-1].offset = 0
		return bstate.get_n_messages(1)
	elif parsed.intent == 'navigate' and parsed.get('*number', None):
		if parsed.get('on_last_page', False):
			bstate.back()
		url = bstate.frame_stack[-1].document.links[int(parsed.get('*number', '0'))-1]
		bstate.navigate_to_url(url)
		return bstate.get_n_messages(1)
	elif parsed.intent == 'help':
		return ['Try these: "Go to hackerschool.com", "search wikipedia for Azerbaijan". On a web page, type "2 more" to see more or text the # of a link to click it.']
	elif parsed.intent == 'back':
		bstate.back()
		return bstate.resend_current_place()
	elif parsed.intent == 'search':
		query = parsed.get("~query", "")
		if parsed.get('search_source/wikipedia', False):
			url = "http://en.wikipedia.org/w/index.php?search=" + urllib.quote_plus(query)
			bstate.navigate_to_url(url)
			return bstate.get_n_messages(1)
		else:
			bstate.frame_stack.append(document.Frame(search.document_from_query(query)))
			return bstate.get_n_messages(1)
	elif parsed.intent == 'whereami':
		if bstate.frame_stack == []:
			return ["You haven't loaded any page yet."]
		else:
			return [u'You\'re reading "{0}" ({1})'.format(bstate.frame_stack[-1].document.title, bstate.frame_stack[-1].document.url)]
	else:
		return ["What's that? I don't understand. Say 'help me' for help."]
