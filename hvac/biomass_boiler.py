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

# odcontrol conf
ODC_USERNAME='admin'
ODC_PASSWORD='opendomo'

# hvac conf
COMFORT_TEMPERATURE_ZONE1=18
COMFORT_TEMPERATURE_ZONE2=18
ENDLESS_SCREW_LOADING_TIME=5
ENDLESS_SCREW_DIFSTOP_TIME=2
ENDLESS_SCREW_WAITING_TIME=120
BOILER_WATER_PUMP_WAITING_TIME=60
UNDERFLOR_HEATING_MAX_TEMPERATURE=45
UNDERFLOR_HEATING_WATER_PUMP_WAITING_TIME=60
WATER_HEATING_CHECKING_TIME=60
BOILER_TEMP_MIN_DIFF=5

# state machines
ENDLESS_SCREW_STATE="waiting"
ENDLESS_SCREW_STATE_T0=int(time.time())
BOILER_WATER_PUMP_STATE="waiting"
BOILER_WATER_PUMP_STATE_T0=int(time.time())
UNDERFLOR_HEATING_WATER_PUMP_C1_STATE="waiting"
UNDERFLOR_HEATING_WATER_PUMP_C1_STATE_T0=int(time.time())
UNDERFLOR_HEATING_WATER_PUMP_C2_STATE="waiting"
UNDERFLOR_HEATING_WATER_PUMP_C2_STATE_T0=int(time.time())


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
        #print "ERROR:", traceback.format_exc()
        #return None
        raise

    return None

def read_temperature(dev):
    for i in range(3):
        try:
            temp=temperature=query_temperature_by_name(dev)
            #debug(dev+" temperature is "+str(temp))
            return temperature
        except:
            pass

    return query_temperature_by_name(dev)

def set_value(name, value):
    #debug("set "+name+" to "+value)
    #if value not in ["ON", "OFF"]:
    #    print "set() unknown value"
    #    sys.exit(0)

    request = urllib2.Request("http://192.168.1.77:81/set+"+name+'+'+value)
    base64string = base64.b64encode('%s:%s' % (ODC_USERNAME, ODC_PASSWORD))
    request.add_header("Authorization", "Basic %s" % base64string)   
    result = urllib2.urlopen(request)
    data=result.read().split('\n')
    if data[0]!="DONE":
        print "Warning! set_value() failed!"
        sys.stdout.flush()

def get_value(name):
    request = urllib2.Request("http://192.168.1.77:81/lsc+"+name)
    base64string = base64.b64encode('%s:%s' % (ODC_USERNAME, ODC_PASSWORD))
    request.add_header("Authorization", "Basic %s" % base64string)   
    result = urllib2.urlopen(request)
    data=result.read().split('\n')
    field=data[0].split(':')
    return field[2]

def debug(string):
    s="["+strftime("%Y-%m-%d %H:%M:%S")+"]"
    name=inspect.stack()[1][3]
    print s+" : "+name+" - "+string
    sys.stdout.flush()
    return




ser, mb = init_mb_serial()



# HVAC SYSTEM

def set_state(state_machine, state):
    if state_machine=="ENDLESS_SCREW_STATE":
        global ENDLESS_SCREW_STATE
        global ENDLESS_SCREW_STATE_T0
        debug("ENDLESS_SCREW_STATE: "+ENDLESS_SCREW_STATE +" -> "+state)
        ENDLESS_SCREW_STATE=state
        ENDLESS_SCREW_STATE_T0=int(time.time())

    if state_machine=="BOILER_WATER_PUMP_STATE":
        global BOILER_WATER_PUMP_STATE
        global BOILER_WATER_PUMP_STATE_T0
        debug("BOILER_WATER_PUMP_STATE: "+BOILER_WATER_PUMP_STATE +" -> "+state)
        BOILER_WATER_PUMP_STATE=state
        BOILER_WATER_PUMP_STATE_T0=int(time.time())
 
    if state_machine=="UNDERFLOR_HEATING_WATER_PUMP_C1_STATE":
        global UNDERFLOR_HEATING_WATER_PUMP_C1_STATE
        global UNDERFLOR_HEATING_WATER_PUMP_C1_STATE_T0
        debug("UNDERFLOR_HEATING_WATER_PUMP_C1_STATE: "+\
               UNDERFLOR_HEATING_WATER_PUMP_C1_STATE +" -> "+state)
        UNDERFLOR_HEATING_WATER_PUMP_C1_STATE=state
        UNDERFLOR_HEATING_WATER_PUMP_C1_STATE_T0=int(time.time())
        
    if state_machine=="UNDERFLOR_HEATING_WATER_PUMP_C2_STATE":
        global UNDERFLOR_HEATING_WATER_PUMP_C2_STATE
        global UNDERFLOR_HEATING_WATER_PUMP_C2_STATE_T0
        debug("UNDERFLOR_HEATING_WATER_PUMP_C2_STATE: "+\
               UNDERFLOR_HEATING_WATER_PUMP_C2_STATE +" -> "+state)
        UNDERFLOR_HEATING_WATER_PUMP_C2_STATE=state
        UNDERFLOR_HEATING_WATER_PUMP_C2_STATE_T0=int(time.time())

def stop_all(signum, frame):
    print 'exit ...' 
    set_value("TERMO", "OFF"); print "TERMO:", get_value("TERMO")
    set_value("BmC01", "OFF"); print "BmC01:", get_value("BmC01")
    set_value("BmC02", "OFF"); print "BmC02:", get_value("BmC02")
    set_value("BmACS", "OFF"); print "BmACS:", get_value("BmACS")
    set_value("SFdep", "OFF"); print "SFdep:", get_value("SFdep")
    set_value("SFqum", "OFF"); print "SFqum:", get_value("SFqum")
    set_value("VENTL", "OFF"); print "VENTL:", get_value("VENTL")
    set_value("BmCAL", "OFF"); print "BmCAL:", get_value("BmCAL")
    sys.stdout.flush()
    sys.exit(0)

def query_temperatures():
    print
    print "MODBUS DIRECT:"
    print "- HOME_TEMP_1:", read_temperature("HOME_TEMP_1")
    print "- HOME_TEMP_2:", read_temperature("HOME_TEMP_2")
    print 
    print "MODBUS GATEWAY:"
    print "- C1_PROBE:", read_temperature("C1_PROBE")
    print "- C2_PROBE:", read_temperature("C2_PROBE")
    print "- BOILER_PROBE:", read_temperature("BOILER_PROBE")
    print "- INERCIA_PROBE:", read_temperature("INERCIA_PROBE")
    print "- ACS:", read_temperature("ACS")
    print "- TERMO:", read_temperature("TERMO")
    print "- NONE_11:", read_temperature("NONE_11")
    print "- NONE_12:", read_temperature("NONE_12")
    print
    sys.stdout.flush()

def copy_temperatures_to_odc():
    set_value("Tdown", str(read_temperature("HOME_TEMP_1")*10000))
    set_value("Tupst", str(read_temperature("HOME_TEMP_2")*10000)) 
    set_value("TCdwn", str(read_temperature("C1_PROBE")*10000))
    set_value("TCups", str(read_temperature("C2_PROBE")*10000)) 
    set_value("Tboil", str(read_temperature("BOILER_PROBE")*10000)) 
    set_value("TtACS", str(read_temperature("ACS")*10000)) 
    set_value("Termo", str(read_temperature("TERMO")*10000)) 
    set_value("Tiner", str(read_temperature("INERCIA_PROBE")*10000)) 


def process_endless_screw():
    t0=ENDLESS_SCREW_STATE_T0
    t1=int(time.time())

    if ENDLESS_SCREW_STATE=="waiting":
        if t1-t0 > ENDLESS_SCREW_WAITING_TIME:
            debug("Turn on endless screws")
            set_value("SFqum", "ON"); 
            set_value("SFdep", "ON");
            set_state("ENDLESS_SCREW_STATE", "loading") 
            return

    if ENDLESS_SCREW_STATE=="loading":
        if t1-t0 > ENDLESS_SCREW_LOADING_TIME:
            debug("Turn off tank endless screw")
            set_value("SFdep", "OFF"); 
            set_state("ENDLESS_SCREW_STATE", "stopping") 
            return

    if ENDLESS_SCREW_STATE=="stopping":
        if t1-t0 > ENDLESS_SCREW_DIFSTOP_TIME:
            debug("Turn off burner endless screw")
            set_value("SFqum", "OFF"); 
            set_state("ENDLESS_SCREW_STATE", "waiting") 
            return

def process_boiler_water_pump():
    t0=BOILER_WATER_PUMP_STATE_T0
    t1=int(time.time())

    if t1-t0 > BOILER_WATER_PUMP_WAITING_TIME:

        temp_inercia=read_temperature("INERCIA_PROBE")
        temp_probe=read_temperature("BOILER_PROBE")
        debug("Inercia temperature: "+str(temp_inercia))
        debug("Boiler temperature: "+str(temp_probe))

        if temp_probe>temp_inercia+BOILER_TEMP_MIN_DIFF:
            debug("Boiler is hot! Turn on boiler pump")
            set_value("BmCAL", "ON")
        else:
            debug("Boiler is cold. Turn off boiler pump")
            set_value("BmCAL", "OFF")
            
        set_state("BOILER_WATER_PUMP_STATE", "waiting") 

def process_underfloor_heating_water_pump_C1():
    t0=UNDERFLOR_HEATING_WATER_PUMP_C1_STATE_T0
    t1=int(time.time())

    if t1-t0 > UNDERFLOR_HEATING_WATER_PUMP_WAITING_TIME:

        temp_inercia=read_temperature("INERCIA_PROBE")
        temp_probe=read_temperature("C1_PROBE")
        temp_home=read_temperature("HOME_TEMP_1")

        debug("Inercia temperature: "+str(temp_inercia))
        debug("Circuit temperature: "+str(temp_probe))
        debug("Home temperature (zone 1): "+str(temp_probe))

        if temp_probe>UNDERFLOR_HEATING_MAX_TEMPERATURE:
            debug("Temperature is too high! Turn of pump.")
            set_value("BmC01", "OFF")
        elif temp_home>=COMFORT_TEMPERATURE_ZONE1:
            debug("Comfort temperature reached! Turn of pump.")
            set_value("BmC01", "OFF")
        elif temp_inercia>temp_probe:
            debug("Turn on pump")
            set_value("BmC01", "ON")
        else:
            debug("Inercia temperature is not enough. Turn off pump.")
            set_value("BmC01", "OFF")
            
        set_state("UNDERFLOR_HEATING_WATER_PUMP_C1_STATE", "waiting") 

def process_underfloor_heating_water_pump_C2():
    t0=UNDERFLOR_HEATING_WATER_PUMP_C2_STATE_T0
    t1=int(time.time())

    if t1-t0 > UNDERFLOR_HEATING_WATER_PUMP_WAITING_TIME:

        temp_inercia=read_temperature("INERCIA_PROBE")
        temp_probe=read_temperature("C2_PROBE")
        temp_home=read_temperature("HOME_TEMP_2")

        debug("Inercia temperature: "+str(temp_inercia))
        debug("Circuit temperature: "+str(temp_probe))
        debug("Home temperature (zone 2): "+str(temp_probe))

        if temp_probe>UNDERFLOR_HEATING_MAX_TEMPERATURE:
            debug("Temperature is too high! Turn of pump.")
            set_value("BmC02", "OFF")
        elif temp_home>=COMFORT_TEMPERATURE_ZONE2:
            debug("Comfort temperature reached! Turn of pump.")
            set_value("BmC02", "OFF")
        elif temp_inercia>temp_probe:
            debug("Turn on pump.")
            set_value("BmC02", "ON")
        else:
            debug("Inercia temperature is not enough. Turn off pump.")
            set_value("BmC02", "OFF")
            
        set_state("UNDERFLOR_HEATING_WATER_PUMP_C2_STATE", "waiting") 

def water_heating():
    # TODO: turn on water heating only if confort temperature is reached
    pass



if __name__ == "__main__":

    if len(sys.argv)==2 and sys.argv[1]=="show-temps":
        query_temperatures()

    if len(sys.argv)==2 and sys.argv[1]=="copy-temps":
        copy_temperatures_to_odc()

    if len(sys.argv)==4 and sys.argv[1]=="cmd":
        name=sys.argv[2]
        value=sys.argv[3]
        set_value(name, value)
        print get_value(name)

    elif len(sys.argv)==2 and sys.argv[1]=="run":

        signal.signal(signal.SIGINT, stop_all)

        debug("turn on turbine")
        set_value("VENTL", "ON")

        # Main loop
        while True:
            sys.stdout.flush()
            time.sleep(0.5)
            process_endless_screw()
            process_boiler_water_pump()
            process_underfloor_heating_water_pump_C1()
            process_underfloor_heating_water_pump_C2()

    else:
        print "Usage:", sys.argv[0], "<run|show-temps>"
        print 

