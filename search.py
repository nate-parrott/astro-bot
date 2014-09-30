import document
from urllib import urlencode
from httplib2 import Http
import json
from base64 import b64encode

BING_API_KEY = "<YOUR KEY HERE>"

def document_from_query(query):
	query_dict = {"$format": "json", "Query": "'{0}'".format(query)}
	url = "https://api.datamarket.azure.com/Bing/Search/Web?" + urlencode(query_dict)
	print url
	auth_string = b64encode("{0}:{0}".format(BING_API_KEY))
	headers = {"Authorization": "Basic " + auth_string}
	response, content = Http().request(url, "GET", headers=headers)
	print content, response
	results = json.loads(content)['d']['results']
	html = u" ".join([u"<a href='{0}'>{1} ({2})</a>".format(r['Url'], r['Title'], r['DisplayUrl']) for r in results])
	doc = document.Document(html = html)
	return doc
