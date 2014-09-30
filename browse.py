from wise import Phrase, parse_phrase
import parse_command
import document

def interact(query, state):
	# query: String, state: Dictionary
	parsed = parse_command.parse_command(query)
	print parsed
	if 'BrowserState' in state:
		bstate = state['BrowserState']
	else:
		state['BrowserState'] = document.BrowserState()
		bstate = state['BrowserState']

	if parsed.intent == 'url':
		bstate.navigate_to_url(parsed.get("*url", None))
		return bstate.get_n_messages(1)
	elif parsed.intent == 'more_text':
		return bstate.get_n_messages(min(7, int(parsed.get('*number', '1'))))
	elif parsed.intent == 'navigate' and parsed.get('*number', None):
		url = bstate.frame_stack[-1].document.links[int(parsed.get('*number', '0'))]
		bstate.navigate_to_url(url)
		return bstate.get_n_messages(1)
	elif parsed.intent == 'help':
		return ['"Go to wsj.com", "search wikipedia for Azerbaijan". Text the # of a link to click it.']
	elif parsed.intent == 'back':
		bstate.back()
		return bstate.resend_current_place()
	else:
		return ["What's that? I don't understand. Say 'help me' for help."]
