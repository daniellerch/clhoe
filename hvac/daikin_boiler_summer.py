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
import datetime
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
COMFORT_TEMPERATURE_SLEEPING_ZONE1=16
COMFORT_TEMPERATURE_SLEEPING_ZONE2=16
COMFORT_TEMPERATURE_AWAKE_ZONE1=20
COMFORT_TEMPERATURE_AWAKE_ZONE2=20
COMFORT_TEMPERATURE_ZONE1=COMFORT_TEMPERATURE_AWAKE_ZONE1
COMFORT_TEMPERATURE_ZONE2=COMFORT_TEMPERATURE_AWAKE_ZONE2
SLEEPING_TIME_BEGINS_AT = 20
SLEEPING_TIME_ENDS_AT = 5

UNDERFLOR_COLD_MIN_TEMPERATURE=5
UNDERFLOR_COLD_ACCEPTED_TO_START_INERTIA_TEMPERATURE=25
UNDERFLOR_COLD_ACCEPTED_INERTIA_TEMPERATURE=25
UNDERFLOR_COLD_WATER_PUMP_WAITING_TIME=120
DAIKIN_RUNNING_TIME=1800

# state machines
DAIKIN_STATE="on"
DAIKIN_STATE_T0=int(time.time())
UNDERFLOR_COLD_WATER_PUMP_C1_STATE="waiting"
UNDERFLOR_COLD_WATER_PUMP_C1_STATE_T0=int(time.time())
UNDERFLOR_COLD_WATER_PUMP_C2_STATE="waiting"
UNDERFLOR_COLD_WATER_PUMP_C2_STATE_T0=int(time.time())

def ith(T, H):
    return 0.8 * T + ((H/100)*(T - 14.3)) + 46.4

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
            return round(unpack('f', pack('<HH', r[1], r[0]))[0], 2)

        # ---------------------------------------------------------------------
        #   TEMPERATURE SENSOR 2
        # ---------------------------------------------------------------------
        addr, fn, l = 10, 4, 2
        if dev=="HOME_TEMP_2":
            reg=7002
            #mb.execute(247, 6, 4001, output_value=addr) # change mb address
            r=mb.execute(addr, 4, 7002, 2) 
            return round(unpack('f', pack('<HH', r[1], r[0]))[0], 2)


        # ---------------------------------------------------------------------
        #   RELATIVE HUMIDITY SENSOR 1
        # ---------------------------------------------------------------------
        addr, fn, l = 9, 4, 2
        if dev=="HOME_RHUM_1":
            reg=7004
            #mb.execute(247, 6, 4001, output_value=addr) # change mb address
            r=mb.execute(addr, 4, reg, 2) 
            return round(unpack('f', pack('<HH', r[1], r[0]))[0], 2)

        # ---------------------------------------------------------------------
        #   RELATIVE HUMIDITY SENSOR 2
        # ---------------------------------------------------------------------
        addr, fn, l = 10, 4, 2
        if dev=="HOME_RHUM_2":
            reg=7004
            #mb.execute(247, 6, 4001, output_value=addr) # change mb address
            r=mb.execute(addr, 4, reg, 2) 
            return round(unpack('f', pack('<HH', r[1], r[0]))[0], 2)




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

def set_output_by_name(dev, value):
    
    if value.lower()=="on":
        value=1
    else:
        value=0

    try:
        addr, fn = 3, 5

        if dev=="PumpCircUp":
            output=2 # conn=2, output=1

        elif dev=="PumpCircDown":
            output=3 # conn=3, output=2

        elif dev=="PumpACS":
            output=4 # conn=4, output=3

        elif dev=="EStank":
            output=5 # conn=5, output=4

        elif dev=="ESburner":
            output=6 # conn=6, output=5

        elif dev=="turbine":
            output=7 # conn=7, output=6

        elif dev=="PumpBoiler":
            output=8 # conn=8, output=7

        elif dev=="termo":
            output=9 # conn=9, output=8

        else:
            return False

        for i in range(3):
            try:
                mb.execute(addr, fn, output-2, output_value=value)
                return True
            except:
                time.sleep(1)
                pass

        mb.execute(addr, fn, output-1, output_value=value)
        return True

    except:
        #print "ERROR:", traceback.format_exc()
        #return None
        raise

    return None


def get_output_by_name(dev):

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


def set_value(name, value):
    #debug("set "+name+" to "+value)
    #if value not in ["ON", "OFF"]:
    #    print "set() unknown value"
    #    sys.exit(0)

    # is_modbus = set_output_by_name(name, value)
    is_modbus = False

    # try with ODC
    if not is_modbus:
        request = urllib2.Request("http://192.168.1.77:81/set+"+name+'+'+value)
        base64string = base64.b64encode('%s:%s' % (ODC_USERNAME, ODC_PASSWORD))
        request.add_header("Authorization", "Basic %s" % base64string)   
        result = urllib2.urlopen(request, timeout=5)
        data=result.read().split('\n')
        if data[0]!="DONE":
            print "Warning! set_value() failed!"
            sys.stdout.flush()



def get_value(name):

    # mb_res = get_output_by_name(name)
    mb_res = None
    if mb_res==None:
        request = urllib2.Request("http://192.168.1.77:81/lsc+"+name)
        base64string = base64.b64encode('%s:%s' % (ODC_USERNAME, ODC_PASSWORD))
        request.add_header("Authorization", "Basic %s" % base64string)   
        result = urllib2.urlopen(request, timeout=5)
        data=result.read().split('\n')
        field=data[0].split(':')
        return field[2]
    else:
        return mb_res

def debug(string):
    s="["+strftime("%Y-%m-%d %H:%M:%S")+"]"
    name=inspect.stack()[1][3]
    print s+" : "+name+" - "+string
    sys.stdout.flush()
    return


class TimedOutExc(Exception):
   def __str__(self):
       return "TimedOutExc"

def deadline(timeout, *args):
    def decorate(f):
        def handler(signum, frame):
            raise TimedOutExc()

        def new_f(*args):
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(timeout)
            return f(*args)

        new_f.__name__ = f.__name__
        return new_f
    return decorate






ser, mb = init_mb_serial()



# HVAC SYSTEM

def set_state(state_machine, state):

    if state_machine=="UNDERFLOR_COLD_WATER_PUMP_C1_STATE":
        global UNDERFLOR_COLD_WATER_PUMP_C1_STATE
        global UNDERFLOR_COLD_WATER_PUMP_C1_STATE_T0
        debug("UNDERFLOR_COLD_WATER_PUMP_C1_STATE: "+\
               UNDERFLOR_COLD_WATER_PUMP_C1_STATE +" -> "+state)
        UNDERFLOR_COLD_WATER_PUMP_C1_STATE=state
        UNDERFLOR_COLD_WATER_PUMP_C1_STATE_T0=int(time.time())
        
    if state_machine=="UNDERFLOR_COLD_WATER_PUMP_C2_STATE":
        global UNDERFLOR_COLD_WATER_PUMP_C2_STATE
        global UNDERFLOR_COLD_WATER_PUMP_C2_STATE_T0
        debug("UNDERFLOR_COLD_WATER_PUMP_C2_STATE: "+\
               UNDERFLOR_COLD_WATER_PUMP_C2_STATE +" -> "+state)
        UNDERFLOR_COLD_WATER_PUMP_C2_STATE=state
        UNDERFLOR_COLD_WATER_PUMP_C2_STATE_T0=int(time.time())

    if state_machine=="DAIKIN_STATE":
        global DAIKIN_STATE
        global DAIKIN_STATE_T0
        debug("DAIKIN_STATE: "+DAIKIN_STATE +" -> "+state)
        DAIKIN_STATE=state
        DAIKIN_STATE_T0=int(time.time())




def stop_all(signum, frame):
    print 'exit ...' 
    #set_value("TERMO", "OFF"); print "TERMO:", get_value("TERMO")
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
    #print "- HOME_TEMP_1:", read_temperature("HOME_TEMP_1")
    #print "- HOME_TEMP_2:", read_temperature("HOME_TEMP_2")
    print 
    print "MODBUS GATEWAY:"
    #print "- C1_PROBE:", read_temperature("C1_PROBE")
    #print "- C2_PROBE:", read_temperature("C2_PROBE")
    #print "- BOILER_PROBE:", read_temperature("BOILER_PROBE")
    #print "- INERCIA_PROBE:", read_temperature("INERCIA_PROBE")
    print "- ACS:", read_temperature("ACS")
    print "- TERMO:", read_temperature("TERMO")
    print "- NONE_11:", read_temperature("NONE_11")
    print "- NONE_12:", read_temperature("NONE_12")
    print
    sys.stdout.flush()

def query_ports():
    """
    print "Modbus ports:"
    print "- PumpCircUp:", get_value("PumpCircUp")
    print "- PumpCircDown:", get_value("PumpCircDown")
    print "- PumpCircACS:", get_value("PumpACS")
    print "- EStank:", get_value("EStank")
    print "- ESburner:", get_value("ESburner")
    print "- turbine:", get_value("turbine")
    print "- PumpBoiler:", get_value("PumpBoiler")
    print "- termo:", get_value("termo")
    """

    print "ODControl ports:"
    print "- TERMO:", get_value("TERMO")
    print "- BmC01:", get_value("BmC01")
    print "- BmC02:", get_value("BmC02")
    print "- BmACS:", get_value("BmACS")
    print "- SFdep:", get_value("SFdep")
    print "- SFqum:", get_value("SFqum")
    print "- VENTL:", get_value("VENTL")
    print "- BmCAL:", get_value("BmCAL")
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


@deadline(10)
def process_underfloor_cold_water_pump_C1():
    t0=UNDERFLOR_COLD_WATER_PUMP_C1_STATE_T0
    t1=int(time.time())

    if t1-t0 > UNDERFLOR_COLD_WATER_PUMP_WAITING_TIME:

        temp_inercia=read_temperature("INERCIA_PROBE")
        temp_probe=read_temperature("C1_PROBE")
        temp_home=read_temperature("HOME_TEMP_1")
        rhum_home=read_temperature("HOME_RHUM_1")

        debug("Inercia temperature: "+str(temp_inercia))
        debug("Circuit temperature: "+str(temp_probe))
        debug("Home temperature (zone 1): "+str(temp_home))
        debug("Home relative humidity (zone 1): "+str(rhum_home))
        debug("T/HR: "+str(round(temp_home/rhum_home, 2)))

        if temp_probe<UNDERFLOR_COLD_MIN_TEMPERATURE:
            debug("Temperature is too low! Turn off pump.")
            set_value("BmC01", "OFF")
        elif temp_home<=COMFORT_TEMPERATURE_ZONE1:
            debug("Comfort temperature reached! Turn off pump.")
            set_value("BmC01", "OFF")
        elif temp_inercia<UNDERFLOR_COLD_ACCEPTED_TO_START_INERTIA_TEMPERATURE:
            debug("Turn on pump")
            set_value("BmC01", "ON")
            #set_value("Dkn01", "ON")
        elif temp_inercia<UNDERFLOR_COLD_ACCEPTED_INERTIA_TEMPERATURE:
            debug("Inercia temperature is not enough. Turn off pump.")
            set_value("BmC01", "OFF")
            #set_value("Dkn01", "ON")
            set_state("DAIKIN_STATE", "on") 
        elif temp_inercia<UNDERFLOR_COLD_ACCEPTED_INERTIA_TEMPERATURE:
            debug("Inercia temperature is not enough.")
            debug("BmC01:"+get_value("BmC01")+", BmC02:"+get_value("BmC02"))
            #set_value("Dkn01", "ON")
            set_state("DAIKIN_STATE", "on") 
            
        set_state("UNDERFLOR_COLD_WATER_PUMP_C1_STATE", "waiting") 

@deadline(10)
def process_underfloor_cold_water_pump_C2():
    t0=UNDERFLOR_COLD_WATER_PUMP_C2_STATE_T0
    t1=int(time.time())

    if t1-t0 > UNDERFLOR_COLD_WATER_PUMP_WAITING_TIME:

        temp_inercia=read_temperature("INERCIA_PROBE")
        temp_probe=read_temperature("C2_PROBE")
        temp_home=read_temperature("HOME_TEMP_2")
        rhum_home=read_temperature("HOME_RHUM_1")

        debug("Inercia temperature: "+str(temp_inercia))
        debug("Circuit temperature: "+str(temp_probe))
        debug("Home temperature (zone 2): "+str(temp_home))
        debug("Home relative humidity (zone 2): "+str(rhum_home))
        debug("T/HR: "+str(round(temp_home/rhum_home, 2)))

        if temp_probe<UNDERFLOR_COLD_MIN_TEMPERATURE:
            debug("Temperature is too low! Turn off pump.")
            set_value("BmC02", "OFF")
        elif temp_home<=COMFORT_TEMPERATURE_ZONE2:
            debug("Comfort temperature reached! Turn off pump.")
            set_value("BmC02", "OFF")
        elif temp_inercia<UNDERFLOR_COLD_ACCEPTED_TO_START_INERTIA_TEMPERATURE:
            debug("Turn on pump.")
            set_value("BmC02", "ON")
            #set_value("Dkn01", "ON")
            set_state("DAIKIN_STATE", "on") 
        elif temp_inercia<UNDERFLOR_COLD_ACCEPTED_INERTIA_TEMPERATURE:
            debug("Inercia temperature is not enough. Turn off pump.")
            set_value("BmC02", "OFF")
            #set_value("Dkn01", "ON")
            set_state("DAIKIN_STATE", "on") 
        elif temp_inercia<UNDERFLOR_COLD_ACCEPTED_INERTIA_TEMPERATURE:
            debug("Inercia temperature is not enough.")
            debug("BmC01:"+get_value("BmC01")+", BmC02:"+get_value("BmC02"))
            #set_value("Dkn01", "ON")
            set_state("DAIKIN_STATE", "on") 
            
        set_state("UNDERFLOR_COLD_WATER_PUMP_C2_STATE", "waiting") 

@deadline(10)
def process_daikin():
    t0=DAIKIN_STATE_T0
    t1=int(time.time())

    if DAIKIN_STATE=="on":
        if t1-t0 > DAIKIN_RUNNING_TIME:
            debug("Turn off daikin")
            set_state("DAIKIN_STATE", "off") 
            set_value("Dkn01", "OFF")
            return







if __name__ == "__main__":

    if len(sys.argv)==2 and sys.argv[1]=="show-temps":
        query_temperatures()
        sys.exit(0)

    if len(sys.argv)==2 and sys.argv[1]=="show-ports":
        query_ports()
        sys.exit(0)

    if len(sys.argv)==2 and sys.argv[1]=="copy-temps":
        copy_temperatures_to_odc()
        sys.exit(0)

    if len(sys.argv)==4 and sys.argv[1]=="cmd-set":
        name=sys.argv[2]
        value=sys.argv[3]
        set_value(name, value)
        print get_value(name)
        sys.exit(0)

    if len(sys.argv)==3 and sys.argv[1]=="cmd-get":
        name=sys.argv[2]
        print get_value(name)
        sys.exit(0)


    elif len(sys.argv)==2 and sys.argv[1]=="run":

        signal.signal(signal.SIGINT, stop_all)

        print "-- START --"

        # Main loop
        while True:
            try:
                sys.stdout.flush()
                time.sleep(1)

                now = datetime.datetime.now()
                if (now.hour >= SLEEPING_TIME_BEGINS_AT or
                    now.hour < SLEEPING_TIME_ENDS_AT):
                    COMFORT_TEMPERATURE_ZONE1 = COMFORT_TEMPERATURE_SLEEPING_ZONE1
                    COMFORT_TEMPERATURE_ZONE2 = COMFORT_TEMPERATURE_SLEEPING_ZONE2
                else:
                    COMFORT_TEMPERATURE_ZONE1 = COMFORT_TEMPERATURE_AWAKE_ZONE1
                    COMFORT_TEMPERATURE_ZONE2 = COMFORT_TEMPERATURE_AWAKE_ZONE2

                process_underfloor_cold_water_pump_C1()
                process_underfloor_cold_water_pump_C2()
                process_daikin()
            except Exception,e:
                print "Error in main loop: "+str(e)
                time.sleep(1)

    else:
        print "Usage:", sys.argv[0], "<run|show-temps|show-ports|copy-temps|cmd-set|cmd-get>"
        print 



