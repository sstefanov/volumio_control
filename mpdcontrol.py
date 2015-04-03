#!/usr/bin/python
# -*- coding: utf-8 -*-
 
from serial import Serial
import os
from subprocess import Popen, PIPE
import time
import threading
import string
from daemon import runner
import commands
ips = commands.getoutput("/sbin/ifconfig | grep -i \"inet\" | grep -iv \"inet6\" | " +
                         "awk {'print $2'} | sed -ne 's/addr\:/ /p'")
print ips
# This class provides the functionality we want. You only need to look at
# this if you want to know how this works. It only needs to be defined
# once, no need to muck around with its internals.
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False
    
    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration
    
    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False

connected = False
poweroff = False
t1=0
serial_port = Serial('/dev/ttyAMA0', 115200, timeout=0)

def handle_data(x):
	global poweroff
#	print(x.strip())
	cmd2=''
	for case in switch(x.strip()):
	    if case('RPC_PLAY'):
        	cmd='play'
	        break
	    if case('RPC_STOP'):
        	cmd='stop'
	        break
	    if case('RPC_PAUSE'):
        	cmd='toggle'
	        break
	    if case('RPC_NEXT'):
        	cmd='next'
	        break
	    if case('RPC_PREV'):
        	cmd='prev'
	        break
	    if case('RPC_POWEROFF'):
        	cmd='RPC_POWEROFF'
	        break
	    if case('RPC_POWERON'):
        	cmd=''
	        break
	    if case('RPC_VOLUP'):
        	cmd='volume'
        	cmd2='+1'
	        break
	    if case('RPC_VOLDOWN'):
        	cmd='volume'
        	cmd2='-1'
	        break
	    if case('RPC_STATUS'):
        	cmd='STATUS'
#        	if poweroff:
#        		print("Power off...")
#			else:
#	        	print("Status OK")
		ips = commands.getoutput("/sbin/ifconfig | grep -i \"inet\" | grep -iv \"inet6\" | grep -v '127.0.0.1' | awk {'print $2'} | sed -ne 's/addr\:/ /p'")
#		serial_port.write("OK\n")
		serial_port.write(ips)
		serial_port.write("\n")
		time.sleep(0.1)
	        break
	    if case(): # default
        	cmd=''
        	cmd2=''
        	break
	if cmd:
	    if cmd=="RPC_POWEROFF":
	    	print("Going to power off...")
	    	cmd=""
	    	poweroff=True;	# set flag to power off PC
	    else:
	    	if cmd!="STATUS":
		    	print("NO power off!")
	    		poweroff=False;
	if cmd:
		print(cmd)
		if cmd=="STATUS":
			process = Popen(["mpc"], stdout=PIPE)	
		else:
			if cmd2=='':
				process = Popen(["mpc", cmd], stdout=PIPE)
			else:
				process = Popen(["mpc", cmd, cmd2], stdout=PIPE)
		(output, err) = process.communicate()
		exit_code = process.wait()
#		print ("Exit code")
#		print (exit_code)
		print ("Output")
		print(output)
		serstat=0
		for line in string.split(output, '\n'):
			if line.startswith('volume:'):
				if line.find("%"):
					vol=line[line.find(" ")+1:line.find("%")]
					if vol:
						serial_port.write("v"+vol+"\n")
						print("v"+vol+"\n")
						serstat=1
#		print ("line = " + line)


def read_from_port(ser):
	global connected
	while not connected:
	#serin = ser.read()
		connected = True

		while True:
#			print("test")
			reading = ser.readline().decode()
			handle_data(reading)

# if threaded
#thread = threading.Thread(target=read_from_port, args=(serial_port,))
#thread.start()

def mainloop():
	#t1=time()
	while True:
	#	x=ser.readline()
	#ser.write('1')
	#if not threaded
		x=serial_port.readline()
		handle_data(x)
		if poweroff:
			if (time.time()-t2>1):
				print(".")
				t2=time.time()
			if t1>0:
				if (time.time()-t1>10):	# 30 seconds timeout without commands
					print ("Bye bye!")
					serial_port.write("PWROFF")
					os.system("mpc stop && poweroff");
			else:
				t1=time.time()	# start counting
		else:
			t1=0
			t2=0
	#	t2=time()
	#	if t2-t1>10:
	#		print(t2-t1)
	#		t1=t2
	#		process = Popen(["mpc"], stdout=PIPE)
	#		(output, err) = process.communicate()
	#		exit_code = process.wait()
			#				print ("Exit code")
			#				print (exit_code)
	#		print ("Output")
	#		print(output)
		time.sleep(0.1)

class MPDControl():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path =  '/tmp/mpdcontrol.pid'
        self.pidfile_timeout = 5
    def run(self):
		serial_port = Serial('/dev/ttyAMA0', 115200, timeout=0)
		mainloop()


app = MPDControl()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.do_action()
