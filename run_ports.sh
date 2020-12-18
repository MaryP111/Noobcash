#!/bin/bash

tab="--tab"
## Triples of <port><id>
CONFS="5000_0 5001_1 5002_2 5003_3 5004_4"
# 5005_5 5006_6 5007_7 5008_3 5009_9

for conf in $CONFS; do
	## Get parameters
    	port=$(echo $conf | cut -d'_' -f1)
    	id=$(echo $conf | cut -d'_' -f2)   
	run_cmd="python3 blockchain.py -p ${port} -id ${id}"
	##$run_cmd &
	foo+=($tab -e "$run_cmd")

done

gnome-terminal "${foo[@]}"

exit 0
