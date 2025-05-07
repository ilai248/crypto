import time, hashlib, json

class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount

    def to_dict(self):
        return {"sender": self.sender, "receiver": self.receiver, "amount": self.amount}

class Block:
    def __init__(self, index, prev_hash, proposer, transactions, timestamp=None):
        self.index = index
        self.prev_hash = prev_hash
        self.proposer = proposer
        self.transactions = transactions  # list of Transaction
        self.timestamp = timestamp or time.time()
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = f"{self.index}{self.prev_hash}{self.proposer}{self.timestamp}{[tx.to_dict() for tx in self.transactions]}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
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
