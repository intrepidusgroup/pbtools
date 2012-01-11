#!/usr/bin/python

from sys import argv
import re
import os
import sys

def ifsFileList(ifsfile):
	command = "dumpifs " + ifsfile
	return os.popen(command)

def parseIfsOutput(ifsinput):
	flist=[]
	llist=[]
	findex = 0
	for line in ifsinput:
		if findex < 7:
			findex+=1
			continue
		elif not re.match("Checksums:", line):
			findex+=1
			path = re.search(r"(\s*[a-zA-Z0-9\-]*\s*\w*\s*)(\w.*)", line).group(2)
			if re.search(r"\-\>", path):
				llist.append(path)
			elif re.search(r"\w",path):
				flist.append(path)
			else:
				sys.exit("Something went wrong. Regex error.")
	return flist,llist

def mkDirs(path,root):
	pathParts = path.split("/")
	pathParts.insert(0,root)
	pathString =  '/'.join(pathParts[:-1])
	if not os.path.exists(pathString):
		os.makedirs(pathString)
	return pathString,pathParts[len(pathParts)-1]

def dumpFile(ifsfile,path,filetoextract):
	command = "dumpifs -xbd " + path + " " + ifsfile + " " + filetoextract
	return os.system(command)

def parsePaths(flist,ifsfile="foo",root="ifs"):
	for path in flist:
		print root + "/" + path
		pathList =mkDirs(path,root)
		dumpFile(ifsfile,pathList[0],pathList[1])

def parseLinks(llists,handle):
	linkcount = 0;
	for line in llists:
		pathPieces = line.split()
		handle.write("ln -s " + pathPieces[2] + " " + pathPieces[0] + "\n")
		linkcount+=1
	print "Writing symlink list: " + handle.name
	return linkcount
		
		
ROOT = 'ifs'
ifsfile = argv[1]
if ifsfile is None:
	exit("No file to parse...")

linkfile = argv[2]
if linkfile is None:
	linkfile = ROOT + "/links.txt"
f = open(linkfile, 'w')


flist,llist=parseIfsOutput(ifsFileList(ifsfile))

parsePaths(flist,ifsfile,ROOT)
parseLinks(llist,f)

f.close

