# encoding: utf-8

import httplib
import json
import mimetypes
from xml.dom.minidom import parseString, getDOMImplementation

get_content_type = lambda n: mimetypes.guess_type(n)[0] or 'application/octet-stream'

def encode_multipart_formdata(fields, files):

	BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
	CRLF = '\r\n'

	L = []
	for (key, filename, value) in files:
		L.append('--' + BOUNDARY)
		L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
		L.append('Content-Type: %s' % get_content_type(filename))
		L.append('')
		L.append(value)
	for (key, value) in fields:
		L.append('--' + BOUNDARY)
		L.append('Content-Disposition: form-data; name="%s"' % key)
		L.append('')
		L.append(value)
	L.append('--' + BOUNDARY + '--')
	L.append('')
	body = CRLF.join([x if type(x)==str else str(x) for x in L])
	content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
	return content_type, body

class AlfApi:
	def __init__(self, host):
		self.host = host
		self.port = 443
		self.ticket = None

	def addUrlParams(self, url, **kwargs):
		paramList = []
		for param in kwargs:
			paramList.append(param + '=' + kwargs[param])
		
		if len(paramList) > 0:
			url = url + '?' + '&'.join(paramList)

		return url


	def request(self, method, url, body=None, headers=None):
		conn = httplib.HTTPSConnection(self.host, self.port, timeout=60)

		if body == None:
			conn.request(method, url)
		elif headers == None:
			conn.request(method, url, body)
		else:
			conn.request(method, url, body, headers)

	        try:
        	    res = conn.getresponse()
	        except socket.timeout:
        	    print('timeout')
	            return None

		if res.status/100 in (4, 5):
			print(res.reason)
			content = res.read()
			print(content)
		else:
			return res


	def login(self, username, password):
		jsonDict = dict(username=username, password=password)
		res = self.request('POST', '/alfresco/service/api/login', json.dumps(jsonDict))
		self.ticket = json.loads(res.read())['data']['ticket']

	def createFolder(self, path, name):
		jsonDict = dict(name=name)
		res = self.request('POST', self.addUrlParams('/alfresco/service/api/site/folder' + path, alf_ticket=self.ticket), json.dumps(jsonDict))

	def fileUpload(self, filedata, siteid, containerid, uploaddirectory):

		filename = filedata.name
		contenttype = 'cm:content'
		pars = dict(siteid = siteid,
		containerid = containerid,
		uploaddirectory = uploaddirectory,
		filename = filename,
		contenttype = contenttype)

		files = (("filedata", filename, filedata.read()),)

		content_type, body = encode_multipart_formdata(pars.items(), files)

		headers = {
			"User-Agent": "alfREST",
			"Host": "%s:%s" % (self.host, self.port),
			"Accept": "*/*",
			"Content-Length": str(len(body)),
			"Expect": "100-continue",
			"Content-Type": content_type,
		}

		res = self.request('POST', self.addUrlParams('/alfresco/service/api/upload', alf_ticket=self.ticket), body, headers)
		if res is not None:
			print('File %s uploaded in %s/%s%s.' % (filename, siteid, containerid, uploaddirectory))
			return eval(res.read())["nodeRef"].split("/")[-1]
		return False

