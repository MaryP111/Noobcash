import sys
import requests

participants = int(sys.argv[1])
port=5001
for p in range(participants-1):
    base_url = "http://127.0.0.1:{}".format(port)
    url = base_url+"/register_node"
    response = requests.get(url)
    port+=1

response = requests.get("http://127.0.0.1:5000/bootstrap")
response = requests.get("http://127.0.0.1:5000/give_money")


