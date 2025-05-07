import time, hashlib, json
from typing import List

TRANSACTION_EXPIRATION = 100
LOCAL_CHAIN_SIZE = TRANSACTION_EXPIRATION*2

class BalanceInfo:
    def __init__(self, verify_hashes, balance_addr, coin_amount):
        self.verify_hashes: List[bytes] = verify_hashes
        self.balance_addr: int = balance_addr
        self.coin_amount: int = coin_amount

class Transaction:
    def __init__(self, sender, receiver, amount, signature, balance, expiration=TRANSACTION_EXPIRATION):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.expiration = curr_block_index + blocks_till_expire
        self.signature = signature
        self.balance_info: BalanceInfo = balance

    def to_dict(self):
        return {"sender": self.sender, "receiver": self.receiver, "amount": self.amount}

# TODO: Add balance_info
class Block:
    def __init__(self, index, prev_hash, proposer, balance_info, transactions, timestamp=None):
        self.index = index
        self.prev_hash = prev_hash
        self.proposer = proposer
        self.balance_info: 'BalanceInfo' = balance_info
        self.transactions = transactions  # list of Transaction
        self.timestamp = timestamp or time.time()
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = f"{self.index}{self.prev_hash}{self.proposer}{self.timestamp}{[tx.to_dict() for tx in self.transactions]}"
        return hashlib.sha256(block_string.encode()).hexdigest()

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
        blk = Block(data["index"], data["prev_hash"], data["proposer"], txs, data["timestamp"])
        blk.hash = data["hash"]
        return blk

class BlockRequest_heart:
    def __init__(self, timestamp: int, public_key):
        self.timestamp: int = timestamp
        self.public_key: bytes = public_key

class BlockRequest:
    def __init__(self, heart, prev_hash, proposer, transactions, signature):
        self.heart: 'BlockRequest_heart' = heart
        self.prev_hash = prev_hash
        self.proposer = proposer
        self.transactions = transactions  # list of Transaction
        self.signature = signature
