#!/usr/bin/python
from struct import unpack
from sys import exit
from sys import argv
import os

def parseHeader(handle,offset,seekRel=1):
	handle.seek(offset,seekRel)
	magic = handle.read(4)
	handle.seek(8, 1)
	records = unpack('<L', handle.read(4))[0]
	block = unpack('<L', handle.read(4))[0]
	return magic,records,block

def parseEachQcfp(handle,offset=0):
	handle.seek(offset,1)
	qcfpHeader = parseHeader(handle,offset)
	if qcfpHeader[0] != "qcfp":
		exit("Something went wrong... encountered a non-qcfp record: " + qcfpHeader[0])
	elif qcfpHeader[2] != 65536:
		exit("Something went wrong... encountered an unexpected block size: " + qcfpHeader[2])
	else:
		handle.seek(20,1)
		qcfpRecs = []
		for record in range(qcfpHeader[1]):
			blockPos = unpack('<L', handle.read(4))[0]
			blockCount = unpack('<L', handle.read(4))[0]
			if blockCount:
				qcfpRecs.append((blockPos,blockCount))
	return qcfpRecs

def parseQcfps(handle,qcfpCount,seekPos=32,seekRel=0):
	handle.seek(seekPos,seekRel)
	qcfpRecs = []
	for qcfp in range(qcfpCount):
		qcfpRecs.append((parseEachQcfp(handle)))
	return qcfpRecs

def writeDummy(file, size):
	if file.write("\x00"*size):
		return True
	else:
		return False

def writeNewRecord(qcfpTuple,origHan,newHan,seekPos=0,seekRel=1,bs=65536):
	origHan.seek(seekPos,seekRel)
	blockOffset = qcfpTuple[0][0]
	for q in qcfpTuple:
		newHan.seek((q[0]-blockOffset)*bs)
		newHan.write(origHan.read(q[1]*bs))

def decompress(handle,qcfpList,bs=65536):
	handle.seek(bs)
	i=0
	for q in qcfpList:
		newFileName = handle.name + "_qcfp_" + str(i) + ".bin"
		bc = 0
		for r in q:
			bc += r[1]
		newFileSize =  bc * bs
		if os.path.isfile(newFileName):
			exit(newFileName + " exists! Quitting...")
		outputFile = open(newFileName, 'w')
		writeDummy(outputFile,newFileSize)
		writeNewRecord(q,handle,outputFile)
		outputFile.close()
		print "wrote out: " + newFileName
		i+=1


file = argv[1]
if file is None:
	exit("No file to parse...")
f = open(file, 'rb')
qcfmHeader = parseHeader(f,0)
if qcfmHeader[0] != "mfcq":
	exit("Something went wrong... incorrect qcfm magic #: " + qcfmHeader[0])

qcfpList = parseQcfps(f,qcfmHeader[1])

decompress(f,qcfpList)

f.close()
