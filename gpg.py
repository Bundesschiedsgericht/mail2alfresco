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

gpg = gnupg.GPG()
print(gpg.list_keys())
