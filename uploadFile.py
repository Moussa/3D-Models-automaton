#!/usr/bin/python -OO
# -*- coding: utf-8 -*-
import os, wikitools, urllib2, hashlib

def fileURL(filename, siteaddress=r'http://wiki.teamfortress.com/w/images/'):
	filenamehash = hashlib.md5(filename.replace(' ', '_')).hexdigest()
	return siteaddress + filenamehash[:1] + '/' + filenamehash[:2] + '/' + filename.replace(' ', '_')	

def uploadFile(file, title, description, username, password, category='', wikiURL='http://wiki.tf2.com/w/api.php', license='', fileprefix='', filesuffix='', overwrite=False):
	if username is None or password is None:
		return
	wiki = wikitools.wiki.Wiki(wikiURL)
	wiki.login(username, password)
	uploader = wikitools.wikifile.File(wiki=wiki, title=u'File:' + title)
	try:
		print 'Uploading', file, 'as', title, '...'
		try:
			uploader.upload(fileobj=open(file, "rb"), ignorewarnings=True, comment=description)
			wikitools.page.Page(wiki, u'File:' + title).edit(description + category, summary=u'', minor=True, bot=False, skipmd5=True)
		except Exception as e:
			print 'Failed for file: ', file
			print e
			return None
	except KeyboardInterrupt:
		print 'Stopped.'
