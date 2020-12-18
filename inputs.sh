#!/bin/bash

tab="--tab"
## Triples of <port><id>
CONFS="0 1 2 3 4 5 6 7 8 9"

for conf in $CONFS; do
	## Get parameters
  node=$(echo $conf)
	run_cmd="python3 node.py ${node}"
	##$run_cmd &
	foo+=($tab -e "$run_cmd")


done

gnome-terminal "${foo[@]}"

exit 0
