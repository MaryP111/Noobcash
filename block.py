from collections import OrderedDict
from threading import RLock
import datetime
from Crypto.Hash import SHA
import binascii
import hashlib
import Crypto
import Crypto.Random
import json



class Block:
	def __init__(self, index, previous_hash, nonce, listOfTransactions=[], timestamp=None, current_hash=0,mine_time = None): #index = len(self.chain)
		##set

		self.lock = RLock()   #prosorinaaaaaaaaaaaa
		self.index = index  #index of block
		self.previous_hash = previous_hash
		self.current_hash = current_hash
		self.nonce = nonce
		self.listOfTransactions = listOfTransactions
		if timestamp is None:
			d=datetime.datetime.now()
			self.timestamp = str(d-datetime.timedelta(microseconds=d.microsecond))
		else:
			self.timestamp = timestamp
		self.mine_time = mine_time
	def to_dict(self):
		return dict(
		previous_hash = self.previous_hash,
		current_hash = self.current_hash,
		nonce = self.nonce,
		listOfTransactions = self.listOfTransactions,
		index = self.index,
		timestamp = self.timestamp,
		mine_time = self.mine_time
		)

	def calculate_hash(self):
		block_string = json.dumps(dict(
			previous_hash = self.previous_hash,
			listOfTransactions = self.listOfTransactions,
			nonce = self.nonce,
			timestamp = self.timestamp,
		),sort_keys=True)
		return SHA.new(block_string.encode('utf8'))

	def __eq__(self,other):
		if not isinstance(other,Block):
			return False
		return (json.dumps(self.to_dict(),sort_keys = True)==  json.dumps(other.to_dict(),sort_keys = True))



block = Block(34,2,43,234,[1,2,3])
