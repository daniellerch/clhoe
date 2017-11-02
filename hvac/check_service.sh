#!/bin/bash
ID="HVAC"
MAIL_TO="dlerch@gmail.com"

# {{{ alert_if_GT()
alert_if_GT()
{
   R=$(echo "$1>$2" | bc)
   if [ "$R" == "1" ]
   then
      echo "sending '$3'"
      mail -s "$3" $MAIL_TO << EOF
$4
EOF
   fi
}
# }}}

# {{{ alert_if_LT()
alert_if_LT()
{
   R=$(echo "$1<$2" | bc)
   if [ "$R" == "1" ]
   then
      echo "sending '$3'"
      mail -s "$3" $MAIL_TO << EOF
$4
EOF
   fi
}
# }}}




# {{{ alert_if_NE()
alert_if_NE()
{
   if [ "$1" != "$2" ]
   then
      echo "sending '$3'"
      mail -s "$3" $MAIL_TO << EOF
$4
EOF
   fi
}
# }}}



R=$(df / | grep / | awk '{ print $5}' | sed 's/%//g')
alert_if_GT $R 95 "[$ID] Root Disk $$% " ""

R=$(/home/dlerch/clhoe/hvac/biomass_boiler.py cmd-get Tboil|tr [+] 0)
alert_if_LT $R 30 "[$ID] Boiler temperature $R% " ""

R=$(pgrep biomass_boiler|wc -l)
alert_if_LT $R 1 "[$ID] Alert: Main process down" ""





