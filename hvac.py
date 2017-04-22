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

        addr, fn, l = 1, 3, 1
        if dev=="S2":
            reg=3
            mb.execute(addr, 6, 37-1, output_value=0b0000000011000010) # write PT1000
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

#print read_temperature("HOME_UP")
#print read_temperature("TERMO")
#print read_temperature("S2")
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

sys.stdout.flush()
ser.close()



