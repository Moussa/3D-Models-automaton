#!/usr/bin/python -OO
# -*- coding: utf-8 -*-
import os, wikiUpload, urllib2, hashlib

def fileURL(filename, siteaddress=r'http://wiki.teamfortress.com/w/images/'):
	filenamehash = hashlib.md5(filename.replace(' ', '_')).hexdigest()
	return siteaddress + filenamehash[:1] + '/' + filenamehash[:2] + '/' + filename.replace(' ', '_')	

def uploadFile(file, title, description, username, password, category='', wikiURL='http://wiki.tf2.com/w/', license='', fileprefix='', filesuffix='', overwrite=False):
	if username is None or password is None:
		return
	uploader = wikiUpload.wikiUploader(username, password, wikiURL)
	try:
		print 'Uploading', file, 'as', title, '...'
		try:
			uploader.upload(file, title, description + category, license, overwrite=overwrite)
		except:
			print 'Failed', file
			return None
	except KeyboardInterrupt:
		print 'Stopped.'