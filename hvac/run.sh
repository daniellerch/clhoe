#!/bin/bash
sudo ./biomass_boiler.py run >> /var/log/biomass_boiler.log &
disown
