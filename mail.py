# encoding: utf-8

# script takes one mail at a time via pipe (stdin) and uploads the contents to alfresco

from StringIO import StringIO
from alfapi import AlfApi
import email
import email.header
import sys
import gnupg
import os
import re
import datetime

host = os.environ['ALF_HOST']
username = os.environ['ALF_USER']
password = os.environ['ALF_PASS']
alf_site = os.environ['ALF_SITE']
alf_library = os.environ['ALF_LIBRARY']
alf_cases = os.environ['ALF_CASES']
alf_messages = os.environ['ALF_MESSAGES']

alf = AlfApi(host)
alf.login(username, password)

gpg = gnupg.GPG()

def upload_file(alf, body, name, msgpath):
	sio = StringIO()
	sio.write(body)
	sio.seek(0)
	sio.name = name
	alf.fileUpload(sio, alf_site, alf_library, msgpath)

def handle_message(alf, msg, msgpath, msgtext):
	if msg.is_multipart():
		for item in msg.get_payload():
			handle_message(alf, item, msgpath, msgtext)
	elif msg.get_filename() != None and msg.get_filename().endswith('.asc'):
		encrypted = msg.get_payload()

		if encrypted.lstrip().startswith('-----BEGIN PGP MESSAGE-----'):
			decrypted = gpg.decrypt(encrypted)

			if decrypted.ok:
				plain = email.message_from_string(str(decrypted))
				handle_message(alf, plain, msgpath, msgtext)
			else:
				print('decryption error: ' + decrypted.status)
		else:
			upload_file(alf, encrypted, msg.get_filename(), msgpath)
	elif msg.get_filename() != None and msg.get_filename().endswith('.pgp'):
		encrypted = msg.get_payload(decode=True)
		decrypted = gpg.decrypt(encrypted)

		if decrypted.ok:
			upload_file(alf, decrypted.data, msg.get_filename()[:-4], msgpath)
		else:
			print('decryption error: ' + decrypted.status)
	elif msg.get_filename() != None:
		upload_file(alf, msg.get_payload(decode=True), msg.get_filename(), msgpath)
	elif msg.get_content_type() == 'text/plain':
		content = msg.get_payload(decode=True)
		
		if content.lstrip().startswith('-----BEGIN PGP MESSAGE-----'):
			decrypted = gpg.decrypt(content)

			if decrypted.ok:
				plaintext = decrypted.data.decode('utf8')
				msgtext += plaintext
				upload_file(alf, msgtext, 'message.txt', msgpath)
			else:
				print('decryption error: ' + decrypted.status)
		else:
			msgtext += content.decode('utf8') 
			upload_file(alf, msgtext, 'message.txt', msgpath)
	elif msg.get_content_type() == 'application/pgp-encrypted':
		#do nothing
		dummy = 0
	else:
		content = msg.get_payload(decode=True)
		
		if content.lstrip().startswith('-----BEGIN PGP MESSAGE-----'):
			decrypted = gpg.decrypt(content)

			if decrypted.ok:
				plaintext = decrypted.data.decode('utf8')
				upload_file(alf, plaintext, 'other.txt', msgpath)
			else:
				print('decryption error: ' + decrypted.status)
		else:
			upload_file(alf, content, 'other.txt', msgpath)

def decode_value(value):
	text = None
	for item in email.header.decode_header(value):
		if text == None:
			text = item[0]
		else:
			text += ' ' + item[0]
	return text.decode('utf-8')



text = '';
for line in sys.stdin.readlines():
	text = text + line

msg = email.message_from_string(text)

alf = AlfApi(host)
alf.login(username, password)

casespath = '/' + alf_site + '/' + alf_library + '/' + alf_cases + '/'
messagespath = '/' + alf_site + '/' + alf_library + '/' + alf_messages + '/'

cases = alf.listFolders(casespath)

regex = re.compile('^.*\[(.+)\].*$')
match = regex.match(msg['subject'])
msgname = 'Nachricht {:%Y-%m-%d %H_%M_%S}'.format(datetime.datetime.now())
msgpath = None

if match != None:
	for number in match.groups():
		if number in cases:
			alf.createFolder(casespath + number + '/', msgname)
			msgpath = '/' + alf_cases + '/' + number + '/' + msgname + '/'

if msgpath == None:
	alf.createFolder(messagespath, msgname)
	msgpath = '/' + alf_messages + '/' + msgname + '/'

msgtext = u'From: ' + decode_value(msg['from']) + u'\n'
msgtext += u'To: ' + decode_value(msg['to']) + u'\n'
msgtext += u'Date: ' + decode_value(msg['date']) + u'\n'
msgtext += u'Subject: ' + decode_value(msg['subject']) + u'\n\n'

upload_file(alf, text, 'raw.txt', msgpath)
handle_message(alf, msg, msgpath, msgtext)

