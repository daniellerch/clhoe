#!/bin/bash

if pgrep biomass_boiler
then
	echo "running"
else
	cd /home/dlerch/clhoe/hvac
	echo "--AUTOSTART--" >> /var/log/biomass_boiler.log
	./run.sh
fi
