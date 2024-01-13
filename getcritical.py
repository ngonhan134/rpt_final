#!/usr/bin/python
# Author : Taesik Na
# Affiliation : Georgia Institute of Technology
# This script helps to extract critical path including dummy loading

import sys
import re
import copy
import time
import datetime
import os

Verbose = True
timenow = re.split("[\s\-\:\.]", str(datetime.datetime.now()))
postfix = ''.join(timenow)

########################################
#                Setup                 # 
########################################

if len(sys.argv) < 4:
	#print 
	print ("Usage : getcritical.py <timing-report-file> <verilog-netlist-file> <stdcell-library-file> numCriticals <spf-file>")
	print ("Input : <timing-report-file> - timing report file generated by Synopsys IC Compiler")
	print ("Input : <verilog-netlist-file> - flatten gate-level verilog netlist file generated by Synopsys IC Compiler")
	#print "Input : <stdcell-library-file> - standard cell .lib file"
	#print "Input : numCriticals - Optional, positive number, number of critical paths you want to extract"
	#print "Input : <spf-file> - Optional, spice compatible spf file"
	#print "Output: <gate-level-critical-path-verilog-files>"
	#print 
	sys.exit(-1)

timingFile = sys.argv[1]
verilogFile = sys.argv[2]
libFile = sys.argv[3]
numCriticals = 2
if len(sys.argv) >= 5:
	numCriticals = int(sys.argv[4]) + 1
endKeyword = "^Path " + str(numCriticals) + ":"

spfFlag = False
if len(sys.argv) >= 6:
	spfFile = sys.argv[5]
	spfFlag = True

fname = re.split("\.", verilogFile)
outtestFile = fname[0] + ".test.v"
outFile = fname[0] + ".crit.v"
outFile2 = fname[0] + ".crit.rc.v"
outFile3 = fname[0] + ".crit.spf.v"
spfoutFile = fname[0] + ".crit.spf.parasitics.ckt"
hspiceFile = fname[0] + ".force.ckt"
hspicebackFile = fname[0] + ".force.ckt." + postfix
libreportFile = "lib.report"
criticalnetreportFile = "criticalpath.net.report"

########################################
#        Primary data structure        #
########################################

class stdcell:
	def __init__(self):
		self.mastername = ""
		self.pinlists = list()

	def getOutcritpin(self):
		for mypin in self.pinlists:
			if mypin.netname != "" and mypin.direction.lower() == "output":
				return mypin
		return mypin
	
	def getOutpin(self):
		for mypin in self.pinlists:
			if mypin.direction.lower() == "output":
				return mypin
	
	def setNetname(self, pinname, netname):
		for mypin in self.pinlists:
			if mypin.pinname == pinname:
				mypin.netname = netname
				break

class inst(stdcell):
	def __init__(self, mastername=None):
		stdcell.__init__(self)
		self.instname = ""
		if mastername is not None:
			for mystdcell in allStdcells:
				if mystdcell.mastername == mastername:
					self.mastername = mastername
					self.pinlists = copy.deepcopy(mystdcell.pinlists)
					break

class pin:
	def __init__(self, pinname=None, direction=None, netname=None, instname=None, function=None):
		if pinname is None:
			self.pinname = ""
		else:
			self.pinname = pinname
		if direction is None:
			self.direction = ""
		else:
			self.direction = direction
		if netname is None:
			self.netname = ""
		else:
			self.netname = netname
		if instname is None:
			self.instname = ""
		else:
			self.instname = instname
		if function is None:
			self.function = ""
		else:
			self.function = function

class net:
	def __init__(self, netname=None):
		if netname is None:
			self.netname = ""
		else:
			self.netname = netname
		self.pinlists = list()
	
	def getPin(self, instname, pinname):
		for mypin in self.pinlists:
			if mypin.pinname is pinname and mypin.instname is instname:
				return mypin
		
########################################
#	Initialize lists	#
########################################
		
allStdcells = list()
criticalInsts = list()
criticalNets = list()
forcenets = list()
forcelevels = list()
filePos = list()

########################################
#   Library building   #
########################################
isFirstCell = True
isFirstPin = True
p = re.compile('([\w\)])\s([\w\(])')
lfile = open(libFile)
for line in lfile:
	res = re.search("^\s*cell\s*\((\S+)\)", line)
	if res:
		newStdcell = stdcell()
		newStdcell.mastername = re.sub("\"", "", res.group(1))
		allStdcells.append(newStdcell)
		continue
	res = re.search("^\s*pin\s*\((\S+)\)", line)
	if res:
		newPin = pin(re.sub("\"", "", res.group(1)))
		newStdcell.pinlists.append(newPin)
		continue
	res = re.search("^\s*direction : (\S+);", line)
	if res:
		newPin.direction = re.sub("\"", "", res.group(1))
		continue
	res = re.search("^\s*function : \"(.+)\";", line)
	if res:
		tempfunc = p.sub(r'\1*\2', res.group(1))
		newPin.function = tempfunc

lfile.close()

lrfile = open(libreportFile, 'w')
for mystdcell in allStdcells:
	line = mystdcell.mastername + "\n"
	lrfile.write(line)
	for mypin in mystdcell.pinlists:
		line = mypin.pinname + "\t" + mypin.direction + "\t" +  mypin.function + "\n"
		lrfile.write(line)

lrfile.close()
print ("Writing %s is done" %(libreportFile))

########################################
#   read timing file and construct criticalNets and criticalInsts   #
########################################
noInsts = 0
isPath = False
tfile = open(timingFile)

isCadence = False
for i, line in enumerate(tfile):
	if i < 2:
		m = re.search("Cadence Encounter", line)
		if m:
			isCadence = True
			break
tfile.close()

tfile = open(timingFile)
if isCadence:
	isdoubleline = False
	for line in tfile:
		if isPath:
			m = re.search(endKeyword, line)
			if m:
				isPath = False
				break
			if isdoubleline:
				res = re.search("^\s+\|\s+(\w*)\/\w+\s+\|", line)
				instname += res.group(1)
				isalready = False
				for mycriticalinst in criticalInsts:
					if mycriticalinst.instname == instname:
						isalready = True
						break
				if not isalready:
					newInst = inst(mastername)
					newInst.instname = instname
					noInsts = noInsts+1
					criticalInsts.append(newInst)
					if Verbose:
						print ("Instance name :", newInst.instname)
						print ("Master name :", newInst.mastername)
				isdoubleline = False
			else:
				netname = ""
				res = re.search("^\s+\|\s+(\w+)/\w*\s+\|\s+[\^v]\s+\|\s+(\w+)\s+\|\s+(\w+)\s+", line)
				if res:
					instname = res.group(1)
					netname = res.group(2)
					mastername = res.group(3)
					isalready = False
					for mycriticalinst in criticalInsts:
						if mycriticalinst.instname == instname:
							isalready = True
							break
					if not isalready:
						newInst = inst(mastername)
						newInst.instname = instname
						noInsts = noInsts+1
						criticalInsts.append(newInst)
						if Verbose:
							print ("Instance name :", newInst.instname)
							print ("Master name :", newInst.mastername)
				else:
					res = re.search("^\s+\|\s+(\w+)\s+\|\s+[\^v]\s+\|\s+(\w+)\s+\|\s+(\w+)\s+", line)
					if res:
						instname = res.group(1)
						netname = res.group(2)
						mastername = res.group(3)
						isdoubleline = True
				# critical path nets save
				if netname:
					isalready = False
					for mynet in criticalNets:
						if mynet.netname == netname:
							isalready = True
							break
					if not isalready:
						newNet = net(netname)
						criticalNets.append(newNet)
						if Verbose:
							print ("Net name :", netname)

		else:
			m = re.search("Timing Path:", line)
			if m:
				isPath = True
else:
	for line in tfile:
		if isPath:
			m = re.search("^\s*slack\s*\(", line)
			if m:
				isPath = False
				break
	
			m = re.search("^\s*(\S+)\/(\S+)\s*\((\S+)\)", line)	# Instance/Pin (Master)
			if m:
				instname = m.group(1)
				mastername = m.group(3)
				isalready = False
				for mycriticalinst in criticalInsts:
					if mycriticalinst.instname == instname:
						isalready = True
						break
				if not isalready:
					newInst = inst(mastername)
					newInst.instname = instname
					noInsts = noInsts+1
					criticalInsts.append(newInst)
					if Verbose:
						print ("Instance name :", newInst.instname)
						print ("Master name :", newInst.mastername)

			# critical path nets save
			m = re.search("^\s*(\S+)\s*\(net\)", line)	# critical netname (net)
			if m:
				netname = m.group(1)
				isalready = False
				for mynet in criticalNets:
					if mynet.netname == netname:
						isalready = True
						break
				if not isalready:
					newNet = net(netname)
					criticalNets.append(newNet)
					if Verbose:
						print ("Net name :", netname)

		else:
			m = re.search("^\s*Point\s+", line)
			if m:
				isPath = True
tfile.close()

# remove the last item
#del criticalInsts[len(criticalInsts)-1]
print ("Read %d insts from %s\n" %(noInsts, timingFile))

########################################
# Getting netnames of the critical path #
########################################
vfile = open(verilogFile)
templine = ""
isCriticalInst = False
for line in vfile:
	res = re.search("^\s*(\S+)\s+(\S+)\s*\(", line)
	if res:
		for myInst in criticalInsts:
			if myInst.instname == res.group(2):
				isCriticalInst = True
				break
	if isCriticalInst:
		templine += line.strip()
		m = re.search(";", line)
		if m:
			if Verbose:
				print (templine)
			res = re.search("^\s*(\S+)\s+(\S+)\s*\(", templine)
			if res:
				for myInst in criticalInsts:
					if myInst.instname == res.group(2):
						break
			for mynet in criticalNets:
				res = re.search("\.(\S+)\s*\(\s*" + mynet.netname + "\s*\)", templine) # . (Pin) ((netname))
				if res:
					myInst.setNetname(res.group(1), mynet.netname)
					if Verbose:
						print (myInst.instname, res.group(1), mynet.netname)

			isCriticalInst = False
			templine = ""

vfile.close()
print ("Setting netname for criticalInsts done\n")

########################################
# Outputting critical path net names   #
########################################
cfile = open(criticalnetreportFile, 'w')
for mynet in criticalNets:
	line = mynet.netname.lower() + "\n"
	cfile.write(line)
cfile.write("\n\n\n")
for mynet in criticalNets:
	line = mynet.netname + "\n"
	cfile.write(line)
cfile.write("\n\n\n")
for mycriticalInst in criticalInsts:
	myoutpin = mycriticalInst.getOutcritpin()
	line = mycriticalInst.instname + ":" + myoutpin.pinname + "\n"
	cfile.write(line)

cfile.write("\n\n\n")
for mycriticalInst in criticalInsts:
	myoutpin = mycriticalInst.getOutcritpin()
	line = "v(" + mycriticalInst.instname + ":" + myoutpin.pinname + ")" + "\n"
	cfile.write(line)

cfile.close()
print ("Writing %s is done" %(criticalnetreportFile))


########################################
# Outputting all instances connected with critical path #
########################################
if os.path.isfile(hspiceFile):
	cmd = "\cp %s %s"%(hspiceFile, hspicebackFile)
	os.system(cmd)
	print ("Backup hspice force file from %s to %s"%(hspiceFile, hspicebackFile))
vfile = open(verilogFile)
ofile = open(outFile,'w')
ofile2 = open(outFile2,'w')
ofile3 = open(outFile3,'w')
sfile = open(hspiceFile,'w')
printNow = False
findStart = False
ofile.write("module critical (clk);\n")
ofile2.write("module critical (clk);\n")
ofile3.write("module critical (clk);\n")

for line in iter(vfile.readline, ''):
	pos = vfile.tell();
	filePos.append(pos)
	if findStart:
		if printNow:
			templine += line.strip()
			ofile.write(line)
			templine2 = line
			templine3 = line
			# critical path instance check
			res = re.search("^\s*([^\.]\S+)\s+([^\.]\S+)\s*\(", line)
			if res: # if first line
				mymastername = res.group(1)
				myinstname = res.group(2)
				isCriticalInst = False
				for myInst in criticalInsts:
					if myInst.instname == myinstname:
						isCriticalInst = True
						break
			if isCriticalInst: # if critical path instance, both input and output nets are critical path
				currentoutpin = myInst.getOutcritpin()
				if currentoutpin.netname:
					res = re.search(currentoutpin.netname, line)
					if res:
						templine2 = re.sub(currentoutpin.netname, currentoutpin.netname + "_start", line)
						ofile2.write("//" + line)

			for myNet in criticalNets:
				res = re.search("\.(\S+)\s*\(\s*" + myNet.netname + "\s*\)" , line)
				if res:
					temppin = res.group(1)
					templine3 = re.sub(myNet.netname + "\s*\)", myinstname + "unexpectedcolon" + temppin + ")", templine3)
					ofile3.write("//" + line)

			ofile2.write(templine2)
			ofile3.write(templine3)

			m = re.search(";", line)
			if m:
				res = re.search("^\s*([^\.]\S+)\s+([^\.]\S+)\s*\(", templine)
				if res:
					mymastername = res.group(1)
					myinstname = res.group(2)
					isCriticalInst = False
					for myInst in criticalInsts:
						if myInst.instname == myinstname:
							isCriticalInst = True
							break
					myforcelevel = "0"
					res = re.search("AND", mymastername)
					if res and isCriticalInst:
						myforcelevel = "evc"
					if myforcelevel == "evc":
						print (templine)
					for mystdcell in allStdcells:
						if mystdcell.mastername == mymastername:
							break
					for mypin in mystdcell.pinlists:
						if mypin.direction == "input":
							res = re.search("\." + mypin.pinname + "\s*\(\s*(\w+)\s*\)" , templine)
							if res:
								tempnet = res.group(1)
								if tempnet != mynet.netname:
									if myforcelevel == "evc":
										print (tempnet)
									isalready = False
									for i, myforcenet in enumerate(forcenets):
										if myforcenet == tempnet:
											isalready = True
											if myforcelevel == "evc":
												forcelevels[i] = "evc"
											break
									if not isalready:
										forcenets.append(tempnet)
										forcelevels.append(myforcelevel)
				printNow = False
		else:
			for mynet in criticalNets:
				m = re.search("\(\s*" + mynet.netname + "\s*\)", line)
				if m:
					filePos.pop()
					filePos.pop()
					vfile.seek(filePos.pop())
					line = vfile.readline()
					while not re.search(";", line):
						vfile.seek(filePos.pop())
						line = vfile.readline()
					pos = vfile.tell();
					filePos.append(pos)
					templine = ""
					printNow = True
					isCriticalInst = False
					break
	else:
		m = re.search("\S+\s+\S+\s+\(\s*\.", line)
		if m:
			findStart = True
		else:
			continue

ofile.write("endmodule")
ofile2.write("endmodule")
ofile3.write("endmodule")
for i, myforcenet in enumerate(forcenets):
	isinput = False
	for j, mycriticalnet in enumerate(criticalNets):
		if myforcenet.lower() == mycriticalnet.netname.lower():
			isinput = True
			break
	if isinput:
		sfile.write("*v"+ myforcenet + " " + myforcenet + " 0 " + forcelevels[i] + "\n")
	else:
		sfile.write("v"+ myforcenet + " " + myforcenet + " 0 " + forcelevels[i] + "\n")
vfile.close()
ofile.close()
ofile2.close()
ofile3.close()
sfile.close()

print ("Writing %s"%outFile)
print ("Writing %s"%outFile2)
print ("Writing %s"%outFile3)
print ("Writing %s"%hspiceFile)

########################################
# Parasitics - Optional
########################################

if spfFlag:
	spffile = open(spfFile)
	spfofile = open(spfoutFile,'w')
	printNow = False
	for line in iter(spffile.readline, ''):
		# critical net check
		res = re.search("^\*\|NET\s+(\S+)\s+", line)
		if res:
			printNow = False
			tempnet = res.group(1)
			for myNet in criticalNets:
				if tempnet == myNet.netname:
					printNow = True
					break
		if printNow:
			spfofile.write(line)

	spffile.close()
	spfofile.close()
	print ("Writing %s"%spfoutFile)

