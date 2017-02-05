# encoding: utf-8

from alfapi import AlfApi
import os

host = os.environ['ALF_HOST']
username = os.environ['ALF_USER']
password = os.environ['ALF_PASS']

alf = AlfApi(host)
alf.login(username, password)
alf.createFolder('/bsg/documentlibrary/test', 'blubb')

from StringIO import StringIO
sio = StringIO()
sio.write("Well, that's all folks.")
sio.seek(0)
sio.name = "test.txt"

alf.fileUpload(sio, 'bsg', 'documentlibrary', '/test/blubb')
