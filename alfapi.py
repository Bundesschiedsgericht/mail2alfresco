# encoding: utf-8

import base64
import httplib
import json
import mimetypes
import requests
from xml.dom.minidom import parseString, getDOMImplementation

get_content_type = lambda n: mimetypes.guess_type(n)[0] or 'application/octet-stream'

def encode_multipart_formdata(fields, files):

	boundary = '----------ThIs_Is_tHe_bouNdaRY_$'
	crlf = '\r\n'

	lines = []
	for (key, filename, value) in files:
		lines.append('--' + boundary)
		lines.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
		lines.append('Content-Type: %s' % get_content_type(filename))
		lines.append('Content-Transfer-Encoding: base64')
		lines.append('')
		lines.append(base64.b64encode(value))
	for (key, value) in fields:
		lines.append('--' + boundary)
		lines.append('Content-Disposition: form-data; name="%s"' % key)
		lines.append('')
		lines.append(value)
	lines.append('--' + boundary + '--')
	lines.append('')
	body = crlf.join([x if type(x)==str else str(x) for x in lines])
	content_type = 'multipart/form-data; boundary=%s' % boundary
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

	def listFolders(self, path):
		lst = []
		res = self.request('GET', self.addUrlParams('/alfresco/s/slingshot/doclib/doclist/%7Btype%7D/site' + path, alf_ticket=self.ticket))
		content = json.loads(res.read())
		for item in content['items']:
			if item['nodeType'] == 'cm:folder':
				lst.append(item['fileName'])

	def fileUpload(self, filedata, siteid, containerid, uploaddirectory):
		url = self.addUrlParams('https://dms.savvy.ch/alfresco/service/api/upload', alf_ticket=self.ticket)
		files = {"filedata": filedata}
		data = {"siteid": siteid, "containerid": containerid, "uploaddirectory":uploaddirectory}
		r = requests.post(url, files=files, data=data)
		if r.status_code == 200:		
			print('File %s uploaded in %s/%s%s.' % (filedata.name, siteid, containerid, uploaddirectory))
			return json.loads(r.text)["nodeRef"].split("/")[-1]
		else:
			print('Error: ' + r.status_code)
			print(json.loads(r.text))

	def xfileUpload(self, filedata, siteid, containerid, uploaddirectory):

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

