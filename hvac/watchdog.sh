#!/bin/bash

#BIN=daikin_boiler
BIN=daikin_boiler_summer
#BIN=biomass_boiler
#BIN=termo_boiler

if pgrep boiler
then
	echo "running"
else
	cd /home/dlerch/clhoe/hvac
	echo "--AUTOSTART--" >> /var/log/daikin_boiler.log
	sudo ./$BIN.py run >> /var/log/daikin_boiler.log &
	disown

fi
