from transactions import Transaction
from block import Block
from threading import RLock,Event
import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
import json
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import datetime
import miner
import threading
import copy
from random import seed, randint

BLOCK_CAPACITY = 5
DIFFICULTY = 4
headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}



def compute_block_hash(nonce,block_dict,previous_hash,dictTransactions,timestamp):
    block_dict['nonce'] = nonce
    block_string = json.dumps(dict(
        previous_hash = previous_hash,
        listOfTransactions = dictTransactions,
        nonce = nonce,
        timestamp = timestamp,
    ),sort_keys=True)
    return SHA.new(block_string.encode('utf8')).hexdigest()

def proof_of_work(dictTransactions, previous_hash):
    if (not(blockchain.stop_mine.isSet())):
        block_dict = {}  
        block_dict['listOfTransactions'] = dictTransactions
        block_dict['previous_hash'] = previous_hash
        d_start = datetime.datetime.now()
        timestamp = str(d_start - datetime.timedelta(microseconds = d_start.microsecond))
        block_dict['timestamp'] = timestamp
        #nonce = 0
        nonce = (randint(0, 4294967295) * 5) % 4294967295
        block_hash = compute_block_hash(nonce,block_dict,previous_hash,dictTransactions,timestamp)
        while not(block_hash.startswith('0' * DIFFICULTY)) and not(blockchain.stop_mine.isSet()):
            #nonce += 1
            nonce = (nonce + 1) % 4294967295
            block_hash = compute_block_hash(nonce,block_dict,previous_hash,dictTransactions,timestamp)
        d_end = datetime.datetime.now()
        d = d_end - d_start
        block_dict['mine_time'] = str(d)
        block_dict['current_hash'] = block_hash
        if (blockchain.stop_mine.isSet()):
            return None
        return block_dict
    else:
        return None
    # blockchain.create_block(nonce, timestamp, dictTransactions)

class Blockchain:

    def __init__(self):

        self.transactions = []
        self.chain = []
        # `utxos[public_key] = [{transaction_id, owner, amount}]`
        self.utxos = {}
        self.lock = RLock()
        self.minelock = RLock()
        self.stop_mine = Event()
        self.trans_set = set()
        #bootstrap node ip address is added beforehand
        #peers = [{id,ip_address:port,public_key}]
        self.peers = [{'id':0,'ip_address':'http://127.0.0.1:5000','public_key':None}]
        self.participants=1
        self.global_transactions = []
        #excellent design choice 
        self.copy_of_global = []

    def create_wallet(self):
        rsa_keypair = RSA.generate(2048)
        self.private_key = rsa_keypair.exportKey('PEM').decode()
        self.public_key = rsa_keypair.publickey().exportKey('PEM').decode()

    def mine(self):
        with self.minelock:
            exit_mine = False
            #this lock prevents miners from entering at the same time, we mine one block at a time
            with self.lock:
                #we cant validate a block and then mine a previous one, thus we enter here and we clear() / if after that a block is validated then we never mine the previous one
                #our transactions ar and chain are updated according to the block we validated, so we always are in consistent state 
                self.stop_mine.clear()
                if (len(self.transactions) < BLOCK_CAPACITY):
                    exit_mine = True
                if not(exit_mine):
                    dictTransactions = [json.dumps(t.to_dict(),sort_keys=True) for t in self.transactions[:BLOCK_CAPACITY]]
                    #del self.transactions[:BLOCK_CAPACITY]
                    current_hash = self.chain[-1].current_hash
                block_dict = None
            if not(exit_mine):
                block_dict = proof_of_work(dictTransactions, current_hash) #self.stop_mine #miner.
            if (block_dict):
                #del self.transactions[:BLOCK_CAPACITY]
                self.create_block(block_dict)

    def create_transaction(self,recepient_address, amount):
        """
        creates transaction and adds it to blockchain

        """
        sender_address = self.public_key
        amount=float(amount)
        inputs = [t['transaction_id'] for t in self.utxos[sender_address]]
        wallet = sum(t['amount'] for t in self.utxos[sender_address] if t['owner'] == sender_address)
        trans = Transaction(sender_address, recepient_address,amount,inputs)
        trans.sign_transaction(self.private_key)
        if (wallet<amount or sender_address == recepient_address):
            return None
        trans.outputs = [{
                'transaction_id': trans.transaction_id,
                'owner': trans.sender_address,
                'amount': wallet - amount
            }, {
                'transaction_id': trans.transaction_id,
                'owner': trans.recepient_address,
                'amount': amount
            }]
        with self.lock:
            self.utxos[sender_address] = [trans.outputs[0]]
            self.utxos[recepient_address].append(trans.outputs[1])
            self.transactions.append(trans)
            self.global_transactions.append(trans)
            length = len(self.transactions)
        # print(len(blockchain.transactions))
        if (length >= BLOCK_CAPACITY):
            miner = threading.Thread(name = 'miner', target = self.mine)
            miner.start()
        
        return trans


    def validate_transaction(self,transaction_string):
        """
        we verify that
        1) signature verification
        2) all inputs are unspent transactions
        3) sender's budget exceeds amount

        """
        with self.lock:
            trans = Transaction(**json.loads(transaction_string))
            if (trans.sender_address != self.peers[0]['public_key'] or trans.recepient_address != self.peers[0]['public_key']):
                sign_verification = trans.verify_signature()
                if (trans in self.transactions):
                    return trans
                if (not(sign_verification)):
                    return None
                if (trans.transaction_id in self.trans_set):
                    print('same old same old')
                    return None
                wallet = 0
                for t_id in trans.inputs:
                    found = False
                    for utxo in self.utxos[trans.sender_address]:
                        if (utxo['transaction_id'] == t_id and utxo['owner'] == trans.sender_address):
                            found = True
                            wallet += utxo['amount']
                            self.utxos[trans.sender_address].remove(utxo)
                            break
                    if not found:
                        raise Exception('missing transaction inputs')
                        return None
                    if wallet < trans.amount:
                        raise Exception('not enough money')
                        return None


                trans.outputs = [{
                    'transaction_id': trans.transaction_id,
                    'owner': trans.sender_address,
                    'amount': wallet - trans.amount
                    }, {
                    'transaction_id': trans.transaction_id,
                    'owner': trans.recepient_address,
                    'amount': trans.amount
                    }]
                self.utxos[trans.recepient_address].append(trans.outputs[1])
            self.utxos[trans.sender_address].append(trans.outputs[0])
            self.transactions.append(trans)
            self.global_transactions.append(trans)
            length = len(self.transactions)
        # print(len(self.transactions))
        if (length >= BLOCK_CAPACITY):
            self.mine()
        return trans

    def create_genesis_transaction(self):
        inputs = []
        amount = 100*self.participants
        sender_address = self.public_key
        trans = Transaction(sender_address,sender_address,amount,inputs)
        trans.sign_transaction(self.private_key)
        trans.outputs = [{
            'transaction_id': trans.transaction_id,
            'owner': trans.sender_address,
            'amount': trans.amount
        }]

        with self.lock:
            self.utxos[sender_address] = [trans.outputs[0]]
            self.transactions.append(trans)
            self.global_transactions.append(trans)

        self.broadcast_transaction(trans)

        return True

    def broadcast_transaction(self,trans):
        for peer in blockchain.peers:
            if (peer['public_key']!=self.public_key):
                url = "{}/add_transaction".format(peer['ip_address'])
                requests.post(url, data=json.dumps(trans.to_dict(), sort_keys=True),headers = headers)

# --------------------------------------------------------------------------------------------------------------------

    def create_genesis_block(self,trans): 
        previous_hash = 1
        nonce = 0
        listOfTransactions = trans
        index = 0
        d = datetime.datetime.now()
        timestamp = str(d - datetime.timedelta(microseconds = d.microsecond))
        genesis_block = Block(index, previous_hash, nonce, listOfTransactions, timestamp)
        genesis_block.current_hash = genesis_block.calculate_hash().hexdigest()
        with self.lock:
            self.chain.append(genesis_block)
        self.broadcast_block(genesis_block)

        return True

    def create_block(self, block_dict):

        block = Block(len(self.chain), block_dict['previous_hash'], block_dict['nonce'], block_dict['listOfTransactions'], block_dict['timestamp'],0,block_dict['mine_time'])
        #block.current_hash = block.calculate_hash().hexdigest()
        block.current_hash = block_dict['current_hash']
        #block_dict['current_hash'] = block.current_hash
        block_dict['index'] = len(self.chain)
        if ( isinstance(self.validate_block(json.dumps(block_dict),0),Block)):
            # del self.transactions[:BLOCK_CAPACITY]
            print('I mined this')
        self.broadcast_block(block)

        return block

    def broadcast_block(self,block):
        for peer in blockchain.peers:
            if (peer['public_key']!=self.public_key):
                url = "{}/add_block".format(peer['ip_address'])
                requests.post(url, data=json.dumps(block.to_dict(), sort_keys=True), headers = headers)

    def validate_block(self,block_string,is_consensus):
        with self.lock:
            block = Block(**json.loads(block_string))
            if block.index != 0:
                previous_block = self.chain[-1]
                exists = False
                if (previous_block.current_hash != block.previous_hash):
                    #if it does not increase chain length and can be dropped/if it is an unknown block we need to resolve conflicts
                    for my_block in self.chain[:-1]:
                        if (my_block.current_hash == block.previous_hash):
                            exists = True
                    if (exists):
                        print("dropped")
                        return('dropped')
                    else:
                        print("consensus")
                        self.resolve_conflicts()
                        return ('consensus')
                elif block.calculate_hash().hexdigest() != block.current_hash:
                    print("Current hash not valid")
                    raise Exception('current hash not valid')
                    return('Current hash not valid')
                elif not(block.current_hash.startswith('0' * DIFFICULTY)):
                    print("Invalid proof of work")
                    return('Invalid proof of work')
            self.chain.append(block)
            self.stop_mine.set()

             #my transactions have to be up to date with each block I validated
            #so I have to add blockchain transactions to a set and not accept them if they are late and remove transactions if they exist in the block
            if(not(is_consensus)):
                for transaction in block.listOfTransactions:
                    trans = Transaction(**json.loads(transaction))
                    if (trans in self.transactions):
                        self.transactions.remove(trans)
                    self.trans_set.add(json.loads(transaction)["transaction_id"])
            else:
                for transaction in block.listOfTransactions:
                    trans = Transaction(**json.loads(transaction))
                    if (trans in self.copy_of_global):
                        self.copy_of_global.remove(trans)
                    self.trans_set.add(json.loads(transaction)["transaction_id"])

                

        return block

    def add_and_validate_block(self,block_data):
        result = self.validate_block(block_data,0)


    def resolve_conflicts(self):

        """
        ask the other nodes for their chain and return the longest one
        if a longer valid chain is found, our chain is replaced with it
        """
        with self.lock:
            longest_chain = None
            current_length = len(blockchain.chain)
            for peer in self.peers:
                response = requests.get('{}/chain'.format(peer['ip_address']))
                length = response.json()['length']
                chain = response.json()['chain']
                if length > current_length:
                    current_length = length
                    longest_chain = chain
            if longest_chain:
                #self.chain = [Block(**json.loads(block_string)) for block_string in longest_chain]
                self.chain = []
                self.trans_set.clear()
                self.copy_of_global = copy.deepcopy(self.global_transactions)
                for block_string in longest_chain:
                    self.validate_block(block_string,1)
                    #edw tha ekxwrousame th global_transaction
                self.transactions = copy.deepcopy(self.copy_of_global)
                return True
            return False

    def add_transaction(self,transaction_data):
        self.validate_transaction(transaction_data)




app = Flask(__name__)
CORS(app)
blockchain = Blockchain()
blockchain.create_wallet()

@app.route('/block_transactions', methods=['GET'])
def show_transactions():
    transaction_list = []
    for block in blockchain.chain:
        for transaction in block.listOfTransactions:
            temp = json.loads(transaction)
            transaction_list.append(temp["transaction_id"])
    return json.dumps({"transaction_list": transaction_list})

@app.route('/show_times', methods=['GET'])
def show_times():
    total_time = datetime.timedelta()
    for block in blockchain.chain[1:]:
        mine_time = datetime.datetime.strptime(block.mine_time,'%H:%M:%S.%f').time()
        mine_time = datetime.timedelta(hours=mine_time.hour, minutes=mine_time.minute, seconds=mine_time.second, microseconds=mine_time.microsecond)
        total_time = mine_time + total_time
    return json.dumps({"mine_time": str(total_time)})


@app.route('/add_block', methods=['POST'])
def receive_block():
    block_data = request.get_json()
    #we create a thread that invokes add_and_validate_block
    receiver = threading.Thread(name = 'receiver', target = blockchain.add_and_validate_block, args = (json.dumps(block_data),))
    receiver.start()
    return 'Succesfully received',201

@app.route('/blocks/get', methods=['GET'])
def get_blocks():
    blocks = []
    for block in blockchain.chain:
        blocks.append(block.to_dict())
    #response = {'transactions': transactions}
    return json.dumps({"blocks": blocks})


@app.route('/chain', methods=['GET'])
#Returns the node copy of the chain
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(json.dumps(block.to_dict()))
    return json.dumps({"length": len(chain_data),
                "chain": chain_data})

@app.route('/bootstrap',methods = ['GET'])
def bootstrap():
    trans = []
    blockchain.create_genesis_block(trans)
    return 'Genesis block created',201


@app.route('/create_block', methods=['POST'])
def create_and_add_block():
    if (port!=5000):
        block_data = request.get_json() #<-- takes the input from the command line interface
        nonce = int(block_data["nonce"])
        block = blockchain.create_block(nonce)
    return "Block added to the chain", 201

@app.route('/')
def index():
    return "Welcome to the dark world of blockchain!"

@app.route('/transactions/get', methods=['GET'])
def get_transactions():
    transactions = []
    #Get transactions from transactions pool
    for transaction in blockchain.transactions:
        transactions.append(transaction.to_dict())
    #response = {'transactions': transactions}
    return json.dumps({"transactions": transactions})

@app.route('/nodes/get', methods=['GET'])
def get_nodes():
    nodes = []
    #Get participants
    for peer in blockchain.peers:
        nodes.append(peer)
    #response = {'transactions': transactions}
    return json.dumps({"nodes": nodes})

# responds to cli call t <recepient> <amount>
@app.route('/create_transaction', methods=['POST'])
def create_and_add_transaction():
    #if (port!=5000):
    transaction_data = request.get_json() #<-- takes the input from the command line interface
    recepient_id = int(transaction_data["recepient_address"])
    recepient = 0
    for peer in blockchain.peers:
        if (peer['id']==recepient_id):
            recepient = peer['public_key']
    trans = blockchain.create_transaction(recepient, transaction_data["amount"])
    if not trans:
        print("The transaction was discarded by the node")
    else:
        blockchain.broadcast_transaction(trans)
    return "Transaction added to transactions", 201

# responds to cli call view (view last transactions)
@app.route('/view_last_transactions', methods = ['GET'])
def view_transactions():
    trans_list = []
    view_block = blockchain.chain[-1]
    for tx in view_block.listOfTransactions:
            trans_list.append(json.loads(tx))
    return json.dumps({"trans_list": trans_list})

@app.route('/show_balance',methods = ['GET'])
def show_balance():
    my_address = blockchain.public_key
    my_wallet = sum(t['amount'] for t in blockchain.utxos[my_address] if t['owner'] == my_address)
    return json.dumps({"my_wallet": my_wallet})

@app.route('/add_transaction', methods=['POST'])
def receive_transaction():
    transaction_data = request.get_json()
    transaction_receive = threading.Thread(name = 'add', target = blockchain.add_transaction, args = (json.dumps(transaction_data),))
    transaction_receive.start()
    # blockchain.validate_transaction(json.dumps(transaction_data))
    # #if needed start miner in a different thread so that the caller does not block
    # print(len(blockchain.transactions))
    # if (len(blockchain.transactions) == 5):
    #     print("mpika sto if")
    #     miner = threading.Thread(name = 'miner', target = blockchain.mine)
    #     miner.start()
    return 'Succesfully received',201

@app.route('/register_node',methods = ['GET'])
def announce_node():
    ip = 'http://127.0.0.1:{}'.format(port)
    node_data ={'id':id,'public_key':blockchain.public_key,'ip_address':ip}
    url = 'http://127.0.0.1:5000/receive_node'
    requests.post(url, data=json.dumps(node_data, sort_keys=True),headers = headers)
    return 'Node announced',201

@app.route('/receive_node',methods = ['POST'])
def receive_node():
    #if we are the master
    if (port == 5000):
        node_data = request.get_json()
        blockchain.participants+=1
        blockchain.peers.append(node_data)
        blockchain.utxos[node_data['public_key']] = []
        blockchain.peers[0]['public_key'] = blockchain.public_key
        if (blockchain.participants == 5):
            blockchain.utxos[blockchain.peers[0]['public_key']] = []
            for peer in blockchain.peers:
                if (peer['id']!=0):
                    url = "{}/receive_node".format(peer['ip_address'])
                    requests.post(url, data=json.dumps(blockchain.peers, sort_keys=True),headers = headers )

    else:
        node_data = request.get_json()
        blockchain.peers = node_data
        for peer in blockchain.peers:
            blockchain.utxos[peer['public_key']] = []
    return 'Nodes received',201

@app.route('/give_money',methods = ['GET'])
def give_first_money():
    blockchain.create_genesis_transaction()
    #send everyone 100 nbc cause I can
    for peer in blockchain.peers:
        if (peer['id']!=0):
            trans = blockchain.create_transaction(peer['public_key'], 100)
            blockchain.broadcast_transaction(trans)
    return 'Everyone is rich',201


@app.route('/consensus', methods=['GET'])
def what():
    blockchain.resolve_conflicts()
    return "Everyone agrees then"

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-id', '--id', default=0, type=int, help='node id')
    args = parser.parse_args()
    port = args.port
    id = args.id

    app.run(host='127.0.0.1', port=port)
