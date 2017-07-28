#!/usr/bin/python

import sys
import json
import time
import socket
import random
import base64
import md5
import hmac
import serial
import unicodedata
import traceback
import modbus_tk.defines as mb_def
import modbus_tk.modbus_rtu as mb_rtu
import urllib2
import base64
import signal
from time import gmtime, strftime
from pprint import pprint
from struct import unpack, pack



# -- GLOBALS --

# modbus channel conf
MB_BAUDRATE=9600
MB_SERIAL="/dev/ttyUSB0"
MB_PARITY=serial.PARITY_NONE
MB_STOPBITS=serial.STOPBITS_ONE

# odcontrol conf
ODC_USERNAME='admin'
ODC_PASSWORD='opendomo'

# hvac donf
ENDLESS_SCREW_LOADING_TIME=10
ENDLESS_SCREW_WAITING_TIME=60


def init_mb_serial():
    ser = serial.Serial(
        port=MB_SERIAL,
        baudrate=MB_BAUDRATE,
        parity=MB_PARITY,
        stopbits=MB_STOPBITS
    )
    mb = mb_rtu.RtuMaster(ser)
    mb.set_timeout(1)

    return ser, mb

def query_temperature_by_name(dev):
    try:
        addr, fn, l = 2, 4, 2
        if dev=="HOME_UP":
            reg=7002
            #mb.execute(addr, 6, 4001, output_value=2) # change mb address
            r=mb.execute(addr, 4, 7010, 2) 
            print "temp min", unpack('f', pack('<HH', r[1], r[0]))[0]
            r=mb.execute(addr, 4, 7012, 2) 
            print "temp max", unpack('f', pack('<HH', r[1], r[0]))[0]

            r=mb.execute(addr, 4, 7002, 2) 
            return unpack('f', pack('<HH', r[1], r[0]))[0]


        # ---------------------------------------------------------------------
        #   SENECA GATEWAY 0
        # ---------------------------------------------------------------------
        addr=1
        conf_offset=34
        pt1000_flags=0b0000000011000010
        fn, wfn, l = 3, 6, 1

        # Channel 1
        if dev=="C1_1":
            reg=3
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 2
        if dev=="C2_1":
            reg=4
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 3
        if dev=="S1":
            reg=5
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 4
        if dev=="INERCIA":
            reg=6
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10


        # ---------------------------------------------------------------------
        #   SENECA GATEWAY 1
        # ---------------------------------------------------------------------
        addr=2
        conf_offset=34
        pt1000_flags=0b0000000011000010
        fn, wfn, l = 3, 6, 1

        # Channel 1
        if dev=="C1_2":
            reg=3
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 2
        if dev=="C2_2":
            reg=4
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 3
        if dev=="ACS":
            reg=5
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 4
        if dev=="S2":
            reg=6
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10



        addr, fn, l = 2, 3, 1
        if dev=="TERMO":
            reg=3
            mb.execute(addr, 6, 37-1, output_value=0b0000000000000010) # write PT100
            return float(mb.execute(addr, fn, reg-1, l)[0])/10


    except:
        #print "ERROR:", traceback.format_exc()
        #return None
        raise

    return None

def read_temperature(dev):
    for i in range(3):
        try:
            temperature=query_temperature_by_name(dev)
            return temperature
        except:
            pass

    return query_temperature_by_name(dev)

def set_value(name, value):
    if value not in ["ON", "OFF"]:
        print "set() unknown value"
        sys.exit(0)

    request = urllib2.Request("http://192.168.1.77:81/set+"+name+'+'+value)
    base64string = base64.b64encode('%s:%s' % (ODC_USERNAME, ODC_PASSWORD))
    request.add_header("Authorization", "Basic %s" % base64string)   
    result = urllib2.urlopen(request)
    data=result.read().split('\n')
    if data[0]!="DONE":
        print "Warning! set_value() failed!"

def get_value(name):
    request = urllib2.Request("http://192.168.1.77:81/lsc+"+name)
    base64string = base64.b64encode('%s:%s' % (ODC_USERNAME, ODC_PASSWORD))
    request.add_header("Authorization", "Basic %s" % base64string)   
    result = urllib2.urlopen(request)
    data=result.read().split('\n')
    field=data[0].split(':')
    return field[2]

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


# -- UTILS --

def tm():
    return "["+strftime("%Y-%m-%d %H:%M:%S")+"]"

def debug(string):
    print tm()+" "+string

ser, mb = init_mb_serial()

"""
#print read_temperature("HOME_UP")
#print read_temperature("TERMO")
#print "C1_1:", read_temperature("C1_1")
#print "C2_1:", read_temperature("C2_1")
print "S1:", read_temperature("S1")
print "INERCIA:", read_temperature("INERCIA")
#print "C1_2:", read_temperature("C1_2")
#print "C2_2:", read_temperature("C2_2")
print "ACS:", read_temperature("ACS")
print "S2:", read_temperature("S2")
print "--"
"""

# HVAC SYSTEM

def stop(signum, frame):
        print 'exit ...' 
        set_value("TERMO", "OFF"); print "TERMO:", get_value("TERMO")
        set_value("BmC01", "OFF"); print "BmC01:", get_value("BmC01")
        set_value("BmC02", "OFF"); print "BmC02:", get_value("BmC02")
        set_value("BmACS", "OFF"); print "BmACS:", get_value("BmACS")
        set_value("SFdep", "OFF"); print "SFdep:", get_value("SFdep")
        set_value("SFqum", "OFF"); print "SFqum:", get_value("SFqum")
        set_value("VENTL", "OFF"); print "VENTL:", get_value("VENTL")
        set_value("BmCAL", "OFF"); print "BmCAL:", get_value("BmCAL")
        sys.exit(0)

def endless_screw():
    debug("endless_screw(): set on")
    set_value("SFqum", "ON"); 
    set_value("SFdep", "ON"); 
    debug("endless_screw(): loading biomass")
    time.sleep(ENDLESS_SCREW_LOADING_TIME)
    debug("endless_screw(): set off")
    set_value("SFqum", "OFF"); 
    set_value("SFdep", "OFF"); 



signal.signal(signal.SIGINT, stop)

while True:
    time.sleep(0.5)
    t=int(time.time())
    #print t%ENDLESS_SCREW_WAITING_TIME

    if t%ENDLESS_SCREW_WAITING_TIME==0:
        endless_screw()


#set_value("BmC01", "ON")
#print get_value("BmC01")

#set_value("BmC01", "OFF")
#print get_value("BmC01")


#print "[1] ERR CH1 CH2:", mb.execute(1, 3, 25-1, 1)
#print "[2] ERR CH1 CH2:", mb.execute(2, 3, 25-1, 1)
#print "[1] CONF CH1:", mb.execute(1, 3, 37-1, 1)
#print "[2] CONF CH1:", mb.execute(2, 3, 37-1, 1)
#print "--"

sys.exit(0)




