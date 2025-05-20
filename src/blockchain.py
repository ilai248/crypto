import base64
import time, hashlib, json
from typing import List
from security import sign, verify_signed

TRANSACTION_EXPIRATION = 100
LOCAL_CHAIN_SIZE = TRANSACTION_EXPIRATION * 2


def shash(*args) -> bytes:
    return hashlib.sha256("|".join(str(arg) for arg in args).encode()).digest()


def bytes_to_string(string: bytes):
    return base64.b64encode(string).decode("ascii")


class BalanceInfo:
    def __init__(self, brolist, pos, money, public_key):
        self.brolist: List[bytes] = brolist
        self.pos: int = pos
        self.money: int = money
        self.public_key: bytes = public_key
        self.data = shash(public_key, money)

    def to_dict(self):
        return {
            "brolist": [b for b in self.brolist],
            "pos": self.pos,
            "money": self.money,
            "public_key": self.public_key
        }

    @staticmethod
    def from_dict(data):
        return BalanceInfo(
            brolist=[bytes.fromhex(b) for b in data["brolist"]],
            pos=data["pos"],
            money=data["money"],
            public_key=data["public_key"]
        )

    def __hash__(self):
        return int(shash(self.public_key, self.money), 16)


class Transaction:
    def __init__(self, amount, sender_balance, receiver_balance, curr_block_index, blocks_till_expire=TRANSACTION_EXPIRATION):
        self.amount = amount
        self.expiration = curr_block_index + blocks_till_expire
        self.sender_balance: BalanceInfo = sender_balance
        self.receiver_balance: BalanceInfo = receiver_balance
        self.signature = sign(self.compute_hash())

    def validate_signature(self):
        return verify_signed(self.compute_hash(), self.signature, self.receiver_balance.public_key)

    def compute_hash(self):
        return shash(
            self.amount,
            self.expiration,
            self.sender_balance.data,
            self.receiver_balance.data
        )

    def to_dict(self):
        return {
            "amount": self.amount,
            "expiration": self.expiration,
            "sender_balance": self.sender_balance.to_dict(),
            "receiver_balance": self.receiver_balance.to_dict(),
            "signature": self.signature
        }

    @staticmethod
    def from_dict(data):
        return Transaction(
            amount=data["amount"],
            sender_balance=BalanceInfo.from_dict(data["sender_balance"]),
            receiver_balance=BalanceInfo.from_dict(data["receiver_balance"]),
            curr_block_index=data["expiration"] - TRANSACTION_EXPIRATION
        )

    def __hash__(self):
        return int(self.compute_hash(), 16)


class Block:
    def __init__(self, index, prev_hash, balance_info, transactions, new_users, timestamp=None, pow_pub_key=None):
        self.index = index
        self.prev_hash = prev_hash
        self.balance_info: BalanceInfo = balance_info
        self.transactions = transactions  # list of Transaction
        self.new_users = new_users  # List of public keys (bytes)
        self.timestamp = int(time.time()) if timestamp is None else timestamp
        self.med_hash = self.compute_med_hash()
        self.pow_key = pow_pub_key
        self.hash = self.compute_hash()

    def compute_med_hash(self):
        return shash(
            self.index,
            self.prev_hash,
            self.timestamp,
            [tx.compute_hash() for tx in self.transactions]
        )

    def compute_hash(self):
        return shash(self.med_hash, self.pow_key if self.pow_key else "")

    def to_dict(self):
        return {
            "index": self.index,
            "prev_hash": self.prev_hash,
            "balance_info": self.balance_info.to_dict(),
            "transactions": [tx.to_dict() for tx in self.transactions],
            "new_users": [pk for pk in self.new_users],
            "timestamp": self.timestamp,
            "pow_key": self.pow_key if self.pow_key else None
        }

    @staticmethod
    def from_dict(data):
        return Block(
            index=data["index"],
            prev_hash=data["prev_hash"],
            balance_info=BalanceInfo.from_dict(data["balance_info"]),
            transactions=[Transaction.from_dict(tx) for tx in data["transactions"]],
            new_users=[pk for pk in data["new_users"]],
            timestamp=data["timestamp"],
            pow_pub_key=data["pow_key"] if data["pow_key"] else None
        )

    def __hash__(self):
        return int(self.hash, 16)


class BlockRequest_heart:
    def __init__(self, timestamp: int, public_key: bytes):
        self.timestamp: int = timestamp
        self.public_key: bytes = public_key
        self.hash = self.compute_hash()

    def compute_hash(self):
        return hashlib.sha256(f"{self.timestamp}|{self.public_key}".encode()).digest()

    def int_hash(self):
        return int.from_bytes(self.hash, 'little')

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "public_key": self.public_key,
            "hash": bytes_to_string(self.hash)
        }

    @staticmethod
    def from_dict(data):
        obj = BlockRequest_heart(
            timestamp=data["timestamp"],
            public_key=data["public_key"]
        )
        obj.hash = base64.b64decode(data["hash"].encode("ascii"))
        return obj

    def __hash__(self):
        return int(self.hash, 16)


class BlockRequest:
    def __init__(self, heart: BlockRequest_heart, difficulty_factor: int, roots, n, block: Block):
        self.heart: BlockRequest_heart = heart
        self.difficulty_factor = difficulty_factor
        self.roots = roots
        self.n = n
        self.block = block

    def to_dict(self):
        return {
            "heart": self.heart.to_dict(),
            "difficulty_factor": self.difficulty_factor,
            "roots": self.roots,
            "n": self.n,
            "block": self.block.to_dict()
        }

    @staticmethod
    def from_dict(data):
        return BlockRequest(
            heart=BlockRequest_heart.from_dict(data["heart"]),
            difficulty_factor=data["difficulty_factor"],
            roots=data["roots"],
            n=data["n"],
            block=Block.from_dict(data["block"])
        )

    def __hash__(self):
        return int(shash(self.heart.hash, self.block.hash, self.difficulty_factor, self.n), 16)
