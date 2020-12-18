#!/usr/bin/python

from termcolor import colored
import sys
import signal
import requests
import json
from flask import jsonify

def signal_handler(sig, frame):
    print()
    print(colored("Pleeaasee don't leave me",'cyan',attrs = ['bold']))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
flag = 0
# user should provide rest api's ports
if(len(sys.argv)==1):
    print("Usage is python3 client.py",colored("PORT",'grey',attrs = ['bold']))
    sys.exit(0)
port = sys.argv[1]
print(" ")
print("Welcome to the noobcash client")
base_url = "http://127.0.0.1:"+port+"/"
headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

while(1):

    print(" ")
    if(flag):
        flag = 0
        print("Invalid action")
        action = input()
    else:
        print('Select an action')
        action = input()



    if(action == 'help'):

        print(" ")
    
        print("Supported actions are")
        print("")
        #t <recipient_address> <amount>
        print(colored('t <recipient_address> <amount>','grey',attrs = ['bold']),"  creates a new transaction ")
        print("")
        # show balance
        print(colored('show balance','grey',attrs = ['bold']),"                    returns your account balance")
        print("")
        # view
        print(colored('view transactions','grey',attrs = ['bold']),"               displays the transactions contained in the last validated block")
        print("")

        #help
        print(colored('help','grey',attrs = ['bold']),"                            displays supported actions")
        print("")

        # fifth action is exit
        print(colored('exit','grey',attrs = ['bold']),"                            exits the system")
        print("")
    elif(not(action)):
        flag = 1
        continue

    elif(action[0]=='t'):

        print(" ")
        url = base_url+"create_transaction"
        inputs = action.split()
        recepient_address = inputs[1]
        amount = inputs[2]
        payload = {'recepient_address':recepient_address,'amount':amount}
        payload = json.dumps(payload)
        response = requests.post(url,data=payload,headers=headers)
        # print(response.json())

    elif(action=='show balance'):

        print(" ")
        url = base_url+"show_balance"
        response = requests.get(url)
        print(response.json())

    elif(action=='view transactions'):

        print(" ")
        url = base_url+"view_last_transactions"
        response = requests.get(url)
        print(response.json())

    elif(action=='exit' or action=='Exit' or action=='exit()' or action=='EXIT()' or action=='EXIT'):
        print(" ")
        print(colored("Pleeaasee don't leave me",'cyan',attrs = ['bold']))
        sys.exit(0)

    else:
        flag = 1