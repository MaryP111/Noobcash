
import os,sys
import json
import datetime
import requests
import hashlib
from random import seed, randint
from subprocess import Popen
from signal import SIGTERM
from Crypto.Hash import SHA
import blockchain
## capacity of blocks
BLOCK_CAPACITY = 5
DIFFICULTY = 5

def compute_block_hash(nonce,block_dict,previous_hash,dictTransactions,timestamp):
	block_dict['nonce'] = nonce
	block_string = json.dumps(dict(
		previous_hash = previous_hash,
		listOfTransactions = dictTransactions,
		nonce = nonce,
		timestamp = timestamp,
	),sort_keys=True)
	return SHA.new(block_string.encode('utf8')).hexdigest()

def proof_of_work(stop_mine,dictTransactions, previous_hash):
	if (not(stop_mine.isSet())):
		block_dict = {} 
		block_dict['listOfTransactions'] = dictTransactions
		block_dict['previous_hash'] = previous_hash
		d_start = datetime.datetime.now()
		timestamp = str(d_start - datetime.timedelta(microseconds = d_start.microsecond))
		block_dict['timestamp'] = timestamp
		#nonce = 0
		nonce = (randint(0, 4294967295) * 5) % 4294967295
		block_hash = compute_block_hash(nonce,block_dict,previous_hash,dictTransactions,timestamp)
		while not block_hash.startswith('0' * DIFFICULTY):
			#nonce += 1
			nonce = (nonce + 1) % 4294967295
			block_hash = compute_block_hash(nonce,block_dict,previous_hash,dictTransactions,timestamp)
		d_end = datetime.datetime.now()
		d = d_end - d_start
		block_dict['mine_time'] = str(d)
		return block_dict
	else:
		return None
	# blockchain.create_block(nonce, timestamp, dictTransactions)
