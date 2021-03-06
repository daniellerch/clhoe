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
from time import gmtime, strftime
from pprint import pprint
from struct import unpack, pack



BAUDRATE=9600
SERIALPORT="/dev/ttyUSB0"


# -- MODBUS --

# {{{ init_mb_serial()
def init_mb_serial():

    # Initialize Modbus RTU
    ser = serial.Serial(
        port=SERIALPORT,
        baudrate=BAUDRATE,
        parity=serial.PARITY_NONE,
        #stopbits=serial.STOPBITS_TWO
        stopbits=serial.STOPBITS_ONE
    )

    mb = mb_rtu.RtuMaster(ser)
    mb.set_timeout(1)

    return ser, mb
# }}}

# {{{ read_temperature()
def read_temperature(dev):

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
        if dev=="C3_1":
            reg=5
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10

        # Channel 4
        if dev=="C4_1":
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
        if dev=="C4_2":
            reg=6
            mb.execute(addr, wfn, conf_offset+reg-1, output_value=pt1000_flags) 
            return float(mb.execute(addr, fn, reg-1, l)[0])/10





        addr, fn, l = 2, 3, 1
        if dev=="TERMO":
            reg=3
            mb.execute(addr, 6, 37-1, output_value=0b0000000000000010) # write PT100
            return float(mb.execute(addr, fn, reg-1, l)[0])/10


    except:
        print "ERROR:", traceback.format_exc()
        return None

    return None
# }}}

# -- UTILS --

# {{{ tm()
def tm():
    return "["+strftime("%Y-%m-%d %H:%M:%S")+"]"
# }}}

ser, mb = init_mb_serial()

"""
#print read_temperature("HOME_UP")
#print read_temperature("TERMO")
print "C1_1:", read_temperature("C1_1")
print "C2_1:", read_temperature("C2_1")
print "C3_1:", read_temperature("C3_1")
print "C4_1:", read_temperature("C4_1")
print "C1_2:", read_temperature("C1_2")
print "C2_2:", read_temperature("C2_2")
print "ACS:", read_temperature("ACS")
print "C4_2:", read_temperature("C4_2")
print "--"


print "[1] ERR CH1 CH2:", mb.execute(1, 3, 25-1, 1)
print "[2] ERR CH1 CH2:", mb.execute(2, 3, 25-1, 1)
#print "[1] CONF CH1:", mb.execute(1, 3, 37-1, 1)
#print "[2] CONF CH1:", mb.execute(2, 3, 37-1, 1)
#print "--"

sys.exit(0)


try:
    print "-- ALL 1 --"
    print mb.execute(1, 3, 0, 16)
    print mb.execute(1, 3, 16, 16)
    print mb.execute(1, 3, 32, 13)
    print "-- ALL 2 --"
    print mb.execute(2, 3, 0, 16)
    print mb.execute(2, 3, 16, 16)
    print mb.execute(2, 3, 32, 13)
except:
    print "ERROR:", traceback.format_exc()

print "[1] ERR CH1 CH2:", mb.execute(1, 3, 25-1, 1)
print "[1] ERR CH1 CH2:", mb.execute(1, 3, 25-1, 1)
print "[1] ERR CH1 CH2:", mb.execute(1, 3, 25-1, 1)
sys.stdout.flush()
ser.close()
"""

print "values:", mb.execute(3, 2, 0, 10)
time.sleep(1)


for i in range(1, 11):
    output=i; value=1
    print mb.execute(3, 5, output-1, output_value=value)
    time.sleep(1)

print "values:", mb.execute(3, 2, 0, 10)





