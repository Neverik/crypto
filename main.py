import rsa
import hashlib
import json
from time import time
from rsa import PublicKey,PrivateKey
import pickle
import codecs
from miner import encode,decode

def hashate (i):
    return hashlib.sha256(i.encode('utf8')).hexdigest()

class block (object):

    def __init__(self, sender, to, amount, priv, phash="no one", n=0):
        self.data = {
            'from': to_str(sender),
            'to': to,
            'amount': amount
        }
        self.prev_hash = phash
        self.n = n
        self.nonce = 0
        self.time = time()
        self.miner = sender
        self.hash()
        self.sign = rsa.sign((json.dumps(self.data) + str(self.time)).encode('utf8'),priv,'SHA-256')

    def hash(self):
        self.h = hashate(self.prev_hash + json.dumps(self.data) + str(self.n)+str(self.nonce)+str(self.time)+encode(self.miner))

    def verify(self,diff):
        try:
            (rsa.verify((json.dumps(self.data) + str(self.time)).encode('utf8'), self.sign, from_str(self.data['from'])))
        except rsa.VerificationError:
            print("Wrong key")
            return False
        if not (self.h[:diff] == "0" * diff):
            return False
        if int(self.data["amount"]) < 0 or int(self.data["amount"]) == 0:
            return False
        return True

    def mine(self, diff):
        while not self.verify(diff):
            self.nonce += 1
            self.hash()

    def __str__(self):
        return encode(self)

    @staticmethod
    def from_str(s):
        return decode(s)


class blockchain (object):
    def __init__(self,difficulty=4):
        self.blocks = []
        self.diff = difficulty
        self.lastmined = 0
        self.miners = []

    def add(self,b):
        if isinstance(b,block):
            self.blocks.append(b)
            b.n = len(self.blocks)-1
            if len(self.blocks) > 1:
                b.prev_hash = self.blocks[-2].h
            b.hash()
        else:
            try:
                self.blocks.append(block(b["from"],b["to"],b["amount"],self.blocks[-1].h,n=len(self.blocks)))
            except IndexError:
                self.blocks.append(block(b["from"],b["to"],b["amount"],"no one", n=len(self.blocks)))
        if len(self.blocks) > 0:
            self.blocks[-1].mine(self.diff)

    def verify(self):
        balance = {}
        for i, e in enumerate(self.blocks):
            if e.n != i:
                return False
            if e.prev_hash != self.blocks[i-1].h and i > 0:
                return False
            if not e.verify(self.diff):
                return False
            try:
                balance[e.data["from"]] -= int(e.data["amount"])
            except KeyError:
                if int(e.data["amount"]) != 0:
                    return False
            try:
                balance[e.data["to"]] += int(e.data["amount"])
            except KeyError:
                balance[e.data["to"]] = int(e.data["amount"])
            try:
                reward = int(e.data["amount"]) * 0.001 + 1/len(self.blocks)
            except ZeroDivisionError:
                reward = int(e.data["amount"]) * 0.001 + 2
            try:
                balance[to_str(e.miner)] += reward
            except KeyError:
                balance[to_str(e.miner)] = reward
            for i in balance.values():
                if int(i) < 0:
                    print("Not enough funds (<0)")
                    return False
        m = 0
        for i in [p.time for p in self.blocks]:
            if i > m:
                m = i
            else:
                print("Wrong time")
                return False
        return True


def from_str(a):
    a = a.split("_")
    return PublicKey(int(a[0]),int(a[1]))

def to_str(a):
    return str(a.n) + "_" + str(a.e)

def from_strp(a):
    a = a.split("_")
    return PrivateKey(int(a[0]),int(a[1]),int(a[2]),int(a[3]),int(a[4]))

def to_strp(a):
    return str(a.n) + "_" + str(a.e) + "_" + str(a.d) + "_" + str(a.p) + "_" + str(a.q)

