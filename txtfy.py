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
	return u" ".join(map(txtfy_word, tokens)).strip()
