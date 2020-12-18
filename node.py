import json
import requests
import sys

node_number = int(sys.argv[1])
f = open("./transactions{}.txt".format(node_number+1),  newline = '\n')
port = "500{}".format(node_number)
base_url = "http://127.0.0.1:"+port+"/"
headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
for i in f:
	id, receiver, amount  = i.split(" ",3)
	print(id, receiver, amount)
	url = base_url+"create_transaction"
	recepient_address = receiver
	amount = amount
	payload = {'recepient_address':recepient_address,'amount':amount}
	payload = json.dumps(payload)
	response = requests.post(url,data=payload,headers=headers)
print("eleni1")
