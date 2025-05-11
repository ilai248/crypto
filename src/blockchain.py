import time, hashlib, json
from typing import List

from main import encrypt

TRANSACTION_EXPIRATION = 100
LOCAL_CHAIN_SIZE = TRANSACTION_EXPIRATION*2

class BalanceInfo:
    def __init__(self, verify_hashes, balance_addr, coin_amount):
        self.verify_hashes: List[bytes] = verify_hashes
        self.balance_addr: int = balance_addr
        self.coin_amount: int = coin_amount

class Transaction:
    def __init__(self, sender, receiver, amount, public_key, signature, balance, curr_block_index, blocks_till_expire=TRANSACTION_EXPIRATION):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.public_key = public_key
        self.expiration = curr_block_index + blocks_till_expire
        self.balance_info: BalanceInfo = balance
        self.signature = signature

    def to_dict(self):
        return {"sender": self.sender, "receiver": self.receiver, "amount": self.amount}

# TODO: Add balance_info
class Block:
    def __init__(self, index, prev_hash, proposer, balance_info, transactions):
        self.index = index
        self.prev_hash = prev_hash
        self.balance_info: 'BalanceInfo' = balance_info
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
