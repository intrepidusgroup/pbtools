#!/usr/bin/python

import httplib
import urllib2
import re
import sys
from optparse import OptionParser

URL = "playbook.websl.blackberry.com"
URI = "/cs/cs"
PIN = "500eabcd"
BILLINGID = "0123456789"
ENCRYPTIONID = "OiD9k6NFBeTtWGFKH4NfRCaHBpbl77rk3HMcn5LWEa4=" # Encryption ID for a misfit playbook... 
HEADERS = {"Accept-Encoding": "deflate, gzip", "Accept": "text/xml, application/xml, application/xhtml+xml, text/html;q=0.9, text/plain;q=0.8, text/css, image/png, image/jpeg, image/gif;q=0.8, application/x-shockwave-flash, video/mp4;q=0.9, flv-application/octet-stream;q=0.8, video/x-flv;q=0.7, audio/mp4, application/futuresplash, */*;q=0.5", "User-Agent": "Mozilla/5.0 (X11; U; Linux i686; undefined) AppleWebKit/531.9 (KHTML, like Gecko) AdobeAIR/2.5", "x-flash-version": "10,1,94,181", "Referer": "app:/firstlaunch.swf?debug=true", "Content-Type": "text/xml"}

def pollAvailableUpdates():
	postxml =  "<bundleVersionRequest version=\"3.0\">\n"
	postxml += "  <hwid>0x06001a06</hwid>\n"
	postxml += "  <vendorid>504</vendorid>\n"
	postxml += "  <pin>0x" + PIN + "</pin>\n"
	postxml += "  <billingID>1057455534</billingID>\n"
	postxml += "  <langid>0</langid>\n"
	postxml += "  <bundle platform-ver=\"1.0.0.1439\" apps-ver=\"1.0.0.1439\"/>\n"
	postxml += "</bundleVersionRequest>"
	conn = httplib.HTTPSConnection(URL)
	conn.request("POST", URI, postxml, HEADERS)
	response = conn.getresponse()
	if response.status != 200:
		sys.exit("Bad response code: " + response.status + " - " + response.reason + "; I'm not sure what to do.")
	rawresponse = response.read()
	conn.close()
	return rawresponse

def parseRecentVersion(rawAvailableUpdatesResponse):
	return re.findall(r"platform-ver=\"(\d\.\d\.\d\.\d{4})\"", rawAvailableUpdatesResponse)

def pollPackages(platformVer,reportError=True):
	postxml =  "<bundleUpgradeRequest version=\"3.0\">\n"
	postxml += "  <hwid>0x06001a06</hwid>\n"
	postxml += "  <pin>0x" + PIN + "</pin>\n"
	postxml += "  <billingID>" + BILLINGID + "</billingID>\n"
	postxml += "  <vendorid>504</vendorid>\n"
	postxml += "  <bundle scm-ver=\"" + platformVer + "\"/>\n"
	postxml += "  <mode>upgrade</mode>\n"
	postxml += "  <isolocale>en_US</isolocale>\n"
	postxml += "</bundleUpgradeRequest>\n"
	conn = httplib.HTTPSConnection(URL)
	conn.request("POST", URI, postxml, HEADERS)
	response = conn.getresponse()
	if response.status != 200:
		sys.exit("Bad response code: " + response.status + " - " + response.reason + "; I'm not sure what to do.")
	fileList = response.read()
	if re.search(r"<errorResponse>", fileList):
		if reportError:
			sys.exit("Problems retrieving package specified: " + re.search(r"<code error=\"([0-9]*)\"/>", fileList).group(1))
		else:
			return None, None
	urlBase = re.search(r"url=\"([a-zA-Z0-9\.:/_]*)\"", fileList).group(1)
	urlFiles = re.findall(r"name=\"([a-zA-Z0-9\._]*)\"",fileList)
	conn.close
	return urlBase, urlFiles

def listFiles(urlBase, urlFiles):
	urlList = []
	for urlfile in urlFiles:
		urlList.append(urlBase + urlfile)
	return urlList

def urlretrieve(urlfile, fpath):
	chunk = 4096
	f = open(fpath, "w")
	size = 0
	while 1:
		data = urlfile.read(chunk)
		if not data:
			print "Downloaded " + str(size) + " bytes."
			break
		size += len(data)
		f.write(data)

def downloadFiles(urlBase, urlFiles):
	for urlfile in urlFiles:
		request = urllib2.Request(urlBase + urlfile)
		request.add_header('X-Encryption-Id', ENCRYPTIONID)
		print "Downloading " + urlBase + urlfile + "..."
		f = urlretrieve(urllib2.urlopen(request), urlfile)

def bruteVersions(bundleBase):
	versionsExist = []
	for i in range(10000):
		version = "%s.%04d" % (bundleBase,i)
		print "Version %s..." % version,
		urlBase, urlFiles = pollPackages(version,reportError=False)
		if urlFiles:
			print "exists!"
			versionsExist.append(version)
		else:
			print "doesn't exist."
	return versionsExist


parser = OptionParser()
parser.add_option("-l", "--list", action="store_true", dest="listBundles", default=False, help="List available package bundles")
parser.add_option("-b", "--bundle", action="store", dest="bundleVersion", help="Specify the bundle version that you wish to download")
parser.add_option("-d", "--download", action="store_true", dest="downloadFiles", default=False, help="Download available bundle files")
parser.add_option("-B", "--brute", action="store_true", dest="bruteForce", default=False, help="Brute-force available un-public bundle versions")
parser.add_option("-a", "--base", action="store", dest="bundleBase",  help="Bundle version base (required for -b option). Ex: -B 2.0.0 will check for versions between 2.0.0.0000 and 2.0.0.9999")
(options, args) = parser.parse_args()

if not options.bundleVersion and not options.listBundles and not options.bruteForce:
	parser.print_help()
	parser.error("No arguments given.")
elif options.bundleVersion and options.listBundles and options.bruteForce:
	parser.error("These options are mutually exclusive.")

elif options.listBundles:
	print "Bundle versions available for download:"
	for ver in parseRecentVersion(pollAvailableUpdates()):
		print ver

elif options.bundleVersion:
	urlBase, urlFiles = pollPackages(options.bundleVersion)
	if options.downloadFiles:
		downloadFiles(urlBase, urlFiles)
	else:
		for url in listFiles(urlBase, urlFiles):
			print url

elif options.bruteForce:
	if not options.bundleBase:
		parser.print_help()
		parser.error("No arguments given.")
	else:
		versions = bruteVersions(options.bundleBase)
		print "The following versions exist:"
		for version in versions:
			print version


