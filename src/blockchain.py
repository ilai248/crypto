import time, hashlib, json
from typing import List

from main import encrypt

TRANSACTION_EXPIRATION = 100
LOCAL_CHAIN_SIZE = TRANSACTION_EXPIRATION*2

class BalanceInfo:
    def __init__(self, brolist, pos, money):
        self.brolist: List[bytes] = brolist
        self.pos: int = pos
        self.money: int = money

class Transaction:
    def __init__(self, sender, receiver, amount, public_key, balance, curr_block_index, blocks_till_expire=TRANSACTION_EXPIRATION):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.public_key = public_key
        self.expiration = curr_block_index + blocks_till_expire
        self.balance_info: BalanceInfo = balance
        self.signature = encrypt(self.compute_hash())

    def compute_hash(self):
        string = f"{self.sender}|{self.receiver}|{self.amount}|{self.public_key}|{self.expiration}|{self.balance_info}"
        return hashlib.sha256(string.encode()).hexdigest()

    def to_dict(self):
        return {"sender": self.sender, "receiver": self.receiver, "amount": self.amount}

class Block:
    def __init__(self, index, prev_hash, balance_info, transactions, new_users):
        self.index = index
        self.prev_hash = prev_hash
        self.balance_info: 'BalanceInfo' = balance_info
        self.new_users = new_users
        self.transactions = transactions  # list of Transaction
        self.hash = self.compute_hash()
        self.signature = encrypt(self.hash)

    def compute_hash(self):
        block_string = f"{self.index}|{self.prev_hash}|{self.proposer}|{self.timestamp}|{[tx.to_dict() for tx in self.transactions]}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    # TODO: Fix
    def to_dict(self):
        return {
            "prev_hash": self.prev_hash,
            "proposer": self.proposer,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "timestamp": self.timestamp,
            "hash": self.hash
        }

    @staticmethod
    def from_dict(data):
        txs = [Transaction(**tx) for tx in data["transactions"]]
        blk = Block(data["index"], data["prev_hash"], data["proposer"], txs, data["signature"], data["timestamp"])
        blk.hash = data["hash"]
        return blk

class BlockRequest_heart:
    def __init__(self, timestamp: int, public_key: bytes):
        self.timestamp: int = timestamp
        self.public_key: bytes = public_key

    def compute_hash(self):
        return hashlib.sha256(f"{self.timestamp}|{self.public_key}".encode()).hexdigest()
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "public_key": self.public_key
        }

class BlockRequest:
    def __init__(self, heart: BlockRequest_heart, difficulty_factor: int, roots, n, block: Block):
        self.heart: 'BlockRequest_heart' = heart
        self.difficulty_factor = difficulty_factor
        self.roots = roots
        self.n = n
        self.block = block
        
    def to_dict(self):
        return {
            'heart': self.heart.to_dict(),
            "difficulty_factor": self.difficulty_factor,
            "roots": self.roots,
            "n": self.n,
            'block': self.block.to_dict()
        }
