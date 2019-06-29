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
import inspect
from time import gmtime, strftime
from pprint import pprint
from struct import unpack, pack



# -- GLOBALS --

# modbus channel conf
MB_BAUDRATE=9600
MB_SERIAL="/dev/ttyUSB0"
MB_PARITY=serial.PARITY_NONE
MB_STOPBITS=serial.STOPBITS_ONE

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


def check_modbus_outputs(dev):
    addr, fn = 3, 2

    res=None
    for i in range(3):
        try:
            res=mb.execute(addr, fn, 0, 10)
        except:
            time.sleep(1)
            pass
      
    if res==None:
        res=mb.execute(addr, fn, 0, 10)

    #print res

    if dev=="PumpCircUp":
        return res[2-2] # conn=2, output=1

    elif dev=="PumpCircDown":
        return res[3-2] # conn=3, output=2

    elif dev=="PumpACS":
        return res[4-2] # conn=4, output=3

    elif dev=="EStank":
        return res[5-2] # conn=5, output=4

    elif dev=="ESburner":
        return res[6-2] # conn=6, output=5

    elif dev=="turbine":
        return res[7-2] # conn=7, output=6

    elif dev=="PumpBoiler":
        return res[8-2] # conn=8, output=7

    elif dev=="termo":
        return res[9-2] # conn=9, output=8

    return None



def check_modbus_sensors(dev):
    try:

        # ---------------------------------------------------------------------
        #   TEMPERATURE SENSOR 1
        # ---------------------------------------------------------------------
        addr, fn, l = 9, 4, 2
        if dev=="HOME_TEMP_1":
            reg=7002
            #mb.execute(247, 6, 4001, output_value=addr) # change mb address
            r=mb.execute(addr, 4, 7002, 2) 
            return unpack('f', pack('<HH', r[1], r[0]))[0]

        # ---------------------------------------------------------------------
        #   TEMPERATURE SENSOR 2
        # ---------------------------------------------------------------------
        addr, fn, l = 10, 4, 2
        if dev=="HOME_TEMP_2":
            reg=7002
            #mb.execute(247, 6, 4001, output_value=addr) # change mb address
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
        if dev=="TERMO":
            reg=3
            #mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 2
        if dev=="ACS":
            reg=4
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 3
        if dev=="C1_PROBE":
            reg=5
            #mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 4
        if dev=="INERCIA_PROBE":
            reg=6
            #mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10


        # ---------------------------------------------------------------------
        #   SENECA GATEWAY 1
        # ---------------------------------------------------------------------
        addr=2
        conf_offset=34
        pt1000_flags=0b0000000011000010
        fn, wfn, l = 3, 6, 1

        # Channel 1
        if dev=="NONE_11":
            reg=3
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 2
        if dev=="NONE_12":
            reg=4
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 3
        if dev=="BOILER_PROBE":
            reg=5
             #mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 4
        if dev=="C2_PROBE":
            reg=6
            #mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

    except:
        print "ERROR:", traceback.format_exc()
        return None

    return None




if __name__ == "__main__":

    ser, mb = init_mb_serial()

    print "***** SENSORS *****"
    for dev in ["HOME_TEMP_1", "HOME_TEMP_2", "TERMO", "ACS", "C1_PROBE", 
                "INERCIA_PROBE", "NONE_11", "NONE_12", "BOILER_PROBE", "C2_PROBE"]:
        print "--", dev, "--"
        print check_modbus_sensors(dev)
        time.sleep(0.5)


    print "***** OUTPUTS *****"
    for dev in ["PumpCircUp", "PumpCircDown", "PumpACS", "EStank", "ESburner",
                "turbine", "PumpBoiler", "termo"]:
        print "--", dev, "--"
        print check_modbus_outputs(dev)
        time.sleep(0.5)


 

