# encoding: utf-8

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

alf = AlfApi(host)
alf.login(username, password)
#alf.createFolder('/bsg/documentlibrary/test', 'blubb')

gpg = gnupg.GPG()
#print(gpg.list_keys())

def upload_file(alf, body, name, msgpath):
	sio = StringIO()
	sio.write(body)
	sio.seek(0)
	sio.name = name
	alf.fileUpload(sio, 'bsg', 'documentlibrary', msgpath)

def handle_message(alf, msg, msgpath, msgtext):
	if msg.is_multipart():
		for item in msg.get_payload():
			handle_message(alf, item, msgpath, msgtext)
	elif msg.get_filename() != None and msg.get_filename().endswith('.asc'):
		encrypted = msg.get_payload()
		decrypted = gpg.decrypt(encrypted)

		if decrypted.ok:
			plain = email.message_from_string(str(decrypted))
			handle_message(alf, plain, msgpath, msgtext)
		else:
			print('decryption error: ' + decrypted.status)
	elif msg.get_filename() != None:
		upload_file(alf, msg.get_payload(decode=True), msg.get_filename(), msgpath)
	elif msg.get_content_type() == 'text/plain':
		msgtext += msg.get_payload(decode=True)
		upload_file(alf, msgtext, 'message.txt', msgpath)
	elif msg.get_content_type() == 'application/pgp-encrypted':
		#do nothing
		dummy = 0
	else:
		print(msg.get_content_type())
		print(msg.get_payload(decode=True))

def decode_subject(value):
	return email.header.decode_header(value)[0][0]

def decode_address(value):
	return email.header.decode_header(value)[0][0] + ' ' + email.header.decode_header(value)[1][0]


text = '';
for line in sys.stdin.readlines():
	text = text + line

msg = email.message_from_string(text)

alf = AlfApi(host)
alf.login(username, password)
#alf.createFolder('/bsg/documentlibrary/test', 'blubb')

cases = alf.listFolders('/bsg/documentlibrary/Verfahren/')

regex = re.compile('^.*\[(.+)\].*$')
match = regex.match(msg['subject'])
msgname = 'Nachricht {:%Y-%m-%d %H_%M_%S}'.format(datetime.datetime.now())
msgpath = None

if match != None:
	for number in match.groups():
		if number in cases:
			alf.createFolder('/bsg/documentlibrary/Verfahren/' + case + '/', msgname)
			msgpath = '/Verfahren/' + case + '/' + msgname + '/'

if msgpath == None:
	alf.createFolder('/bsg/documentlibrary/Nachrichten/', msgname)
	msgpath = '/Nachrichten/' + msgname + '/'

msgtext = 'From: ' + decode_address(msg['from']) + '\n'
msgtext += 'To: ' + decode_address(msg['to']) + '\n'
msgtext += 'Subject: ' + decode_subject(msg['subject']) + '\n\n'

upload_file(alf, text, 'raw.txt', msgpath)
handle_message(alf, msg, msgpath, msgtext)

