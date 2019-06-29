#!/bin/bash

BIN=daikin_boiler
#BIN=biomass_boiler
#BIN=termo_boiler

if pgrep $BIN
then
	echo "running"
else
	cd /home/dlerch/clhoe/hvac
	echo "--AUTOSTART--" >> /var/log/daikin_boiler.log
	sudo ./$BIN.py run >> /var/log/daikin_boiler.log &
	disown

fi
