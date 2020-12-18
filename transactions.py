from collections import OrderedDict

import binascii
import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import json
# import requests
# from flask import Flask, jsonify, request, render_template


class Transaction:

    def __init__(self, sender_address, recepient_address, amount, inputs,outputs =[], transaction_id = None, signature = None ):

        ##set

        self.sender_address = sender_address  #sender's public key
        self.recepient_address = recepient_address  #receiver's public key
        self.amount = amount #amount
        self.transaction_id = transaction_id
        self.inputs = inputs
        self.outputs = outputs
        self.signature = signature 
      

    def to_dict(self):
        return dict(
            sender_address = self.sender_address,
            recepient_address = self.recepient_address,
            amount = self.amount,
            inputs = self.inputs,
            outputs = self.outputs,
            transaction_id = self.transaction_id,
            signature = self.signature
        )
    def __eq__(self,other):
        if not isinstance(other,Transaction):
            return False
        return (json.dumps(self.to_dict(),sort_keys = True) ==  json.dumps(other.to_dict(),sort_keys = True))      

    def sign_transaction(self,private_key):
        """
        Sign transaction with private key
        """
        rsa_key = RSA.importKey(private_key)
        signer = PKCS1_v1_5.new(rsa_key)
        transaction_hash = self.calculate_hash()
        self.transaction_id = transaction_hash.hexdigest()
        self.signature = binascii.hexlify(signer.sign(transaction_hash)).decode('ascii')

    def calculate_hash(self):
        """
        Calculate transaction hash --SHA-256 hash
        """

        transaction_string = json.dumps(dict(
            sender_address = self.sender_address,
            recepient_address = self.recepient_address,
            amount = self.amount,
            inputs = self.inputs,
        ), sort_keys=True)
        return SHA.new(transaction_string.encode('utf8'))

    def verify_signature(self):
        """
        Check that the provided signature corresponds to transaction
        signed by the public key (sender_address)
        """
        public_key = RSA.importKey(self.sender_address.encode())
        verifier = PKCS1_v1_5.new(public_key)
        transaction_hash = self.calculate_hash()
        return verifier.verify(transaction_hash, binascii.unhexlify(self.signature))



#test functions
#generate a pair public private key

# rsa_keypair = RSA.generate(2048)
# private_key = rsa_keypair.exportKey('PEM').decode()
# public_key = rsa_keypair.publickey().exportKey('PEM').decode()

# rsa_keypair2 = RSA.generate(2048)
# private_key2 = rsa_keypair.exportKey('PEM').decode()
# public_key2 = rsa_keypair.publickey().exportKey('PEM').decode()
# inputs = []
# value = 5
# transaction = Transaction(public_key,public_key2,value,inputs)
# transaction.sign_transaction(private_key)

# print (transaction.transaction_id)
# print (transaction.signature)
# res = transaction.verify_signature()
# print(res)