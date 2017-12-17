#!/bin/bash

BIN=biomass_boiler
#BIN=termo_boiler

if pgrep $BIN
then
	echo "running"
else
	cd /home/dlerch/clhoe/hvac
	echo "--AUTOSTART--" >> /var/log/biomass_boiler.log
	sudo ./$BIN.py run >> /var/log/biomass_boiler.log &
	disown

fi
