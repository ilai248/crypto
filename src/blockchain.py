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
        print("Type brolist", type(brolist))
        print("Type public_key", type(public_key))
        self.brolist: List[bytes] = brolist
        self.pos: int = pos
        self.money: int = money
        self.public_key: bytes = public_key
        self.data = shash(public_key, money)
        print("Type data", type(self.data))

    def to_dict(self):
        print("DEBUG: Entering BalanceInfo.to_dict")
        return {
            "brolist": [bytes_to_string(b) for b in self.brolist],
            "pos": self.pos,
            "money": self.money,
            "public_key": self.public_key,
            "data": bytes_to_string(self.data)
        }

    @staticmethod
    def from_dict(data):
        print("Type data['brolist']", type(data["brolist"]))
        print("Type data['public_key']", type(data["public_key"]))
        return BalanceInfo(
            brolist=[base64.b64decode(b.encode("ascii")) for b in data["brolist"]],
            pos=data["pos"],
            money=data["money"],
            public_key=base64.b64decode(data["public_key"].encode("ascii"))
        )

    def __hash__(self):
        return int.from_bytes(shash(self.public_key, self.money), 'big')


class Transaction:
    def __init__(self, amount, sender_balance, receiver_balance, curr_block_index, blocks_till_expire=TRANSACTION_EXPIRATION):
        print("Type sender_balance", type(sender_balance))
        print("Type receiver_balance", type(receiver_balance))
        self.amount = amount
        self.expiration = curr_block_index + blocks_till_expire
        self.sender_balance: BalanceInfo = sender_balance
        self.receiver_balance: BalanceInfo = receiver_balance
        self.signature = sign(self.compute_hash())
        print("Type signature", type(self.signature))

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
        print("DEBUG: Entering Transaction.to_dict")
        return {
            "amount": self.amount,
            "expiration": self.expiration,
            "sender_balance": self.sender_balance.to_dict(),
            "receiver_balance": self.receiver_balance.to_dict(),
            "signature": bytes_to_string(self.signature)
        }

    @staticmethod
    def from_dict(data):
        print("DEBUG: Entering Transaction.from_dict")
        print("Type data['sender_balance']", type(data["sender_balance"]))
        print("Type data['receiver_balance']", type(data["receiver_balance"]))
        print("Type data['signature']", type(data["signature"]))
        transaction = Transaction(
            amount=data["amount"],
            sender_balance=BalanceInfo.from_dict(data["sender_balance"]),
            receiver_balance=BalanceInfo.from_dict(data["receiver_balance"]),
            curr_block_index=data["expiration"] - TRANSACTION_EXPIRATION
        )
        transaction.signature = base64.b64decode(data["signature"].encode("ascii"))
        return transaction

    def __hash__(self):
        return int.from_bytes(self.compute_hash(), 'big')


class Block:
    def __init__(self, index, prev_hash, balance_info, transactions, new_users, timestamp=None, pow_pub_key=None):
        print("Type prev_hash", type(prev_hash))
        print("Type balance_info", type(balance_info))
        print("Type transactions", type(transactions))
        print("Type new_users", type(new_users))
        print("Type timestamp", type(timestamp))
        print("Type pow_pub_key", type(pow_pub_key))
        self.index = index
        self.prev_hash = prev_hash
        self.balance_info: BalanceInfo = balance_info
        self.transactions = transactions  # list of Transaction
        self.new_users = new_users  # List of public keys (bytes)
        self.timestamp = int(time.time()) if timestamp is None else timestamp
        self.med_hash = self.compute_med_hash()
        self.pow_key = pow_pub_key
        self.hash = self.compute_hash()
        print("Type pow_pub_key", type(pow_pub_key))
        print("Type med_hash", type(self.med_hash))
        print("Type hash", type(self.hash))

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
        print("DEBUG: Entering Block.to_dict")
        return {
            "index": self.index,
            "prev_hash": bytes_to_string(self.prev_hash),
            "balance_info": self.balance_info.to_dict(),
            "transactions": [tx.to_dict() for tx in self.transactions],
            "new_users": [pk for pk in self.new_users],
            "timestamp": self.timestamp,
            "pow_key": self.pow_key if self.pow_key else None,
            "hash": bytes_to_string(self.hash),
            "med_hash": bytes_to_string(self.med_hash)
        }

    @staticmethod
    def from_dict(data):
        print("DEBUG: Entering Block.from_dict")
        print("Type data['prev_hash']", type(data["prev_hash"]))
        print("Type data['balance_info']", type(data["balance_info"]))
        print("Type data['transactions']", type(data["transactions"]))
        print("Type data['new_users']", type(data["new_users"]))
        print("Type data['timestamp']", type(data["timestamp"]))
        print("Type data['pow_key']", type(data["pow_key"]))
        print("Type data['hash']", type(data["hash"]))
        print("Type data['med_hash']", type(data["med_hash"]))
        return Block(
            index=data["index"],
            prev_hash=base64.b64decode(data["prev_hash"].encode("ascii")),
            balance_info=BalanceInfo.from_dict(data["balance_info"]),
            transactions=[Transaction.from_dict(tx) for tx in data["transactions"]],
            new_users=[base64.b64decode(pk.encode("ascii")) for pk in data["new_users"]],
            timestamp=data["timestamp"],
            pow_pub_key=base64.b64decode(data["pow_key"].encode("ascii")) if data["pow_key"] else None
        )

    def __hash__(self):
        return int.from_bytes(self.hash, 'big')


class BlockRequest_heart:
    def __init__(self, timestamp: int, public_key: bytes):
        print("Type public_key", type(public_key))
        self.timestamp: int = timestamp
        self.public_key: bytes = public_key
        self.hash = self.compute_hash()
        print("Type hash", type(self.hash))

    def compute_hash(self):
        return hashlib.sha256(f"{self.timestamp}|{self.public_key}".encode()).digest()

    def int_hash(self):
        return int.from_bytes(self.hash, 'big')

    def to_dict(self):
        print("DEBUG: Entering BlockRequest_heart.to_dict")
        return {
            "timestamp": self.timestamp,
            "public_key": self.public_key,
            "hash": bytes_to_string(self.hash)
        }

    @staticmethod
    def from_dict(data):
        print("DEBUG: Entering BlockRequest_heart.from_dict")
        print("Type data['public_key']", type(data["public_key"]))
        print("Type data['hash']", type(data["hash"]))
        obj = BlockRequest_heart(
            timestamp=data["timestamp"],
            public_key=base64.b64decode(data["public_key"].encode("ascii"))
        )
        obj.hash = base64.b64decode(data["hash"].encode("ascii"))
        return obj

    def __hash__(self):
        return int.from_bytes(self.hash, 'big')


class BlockRequest:
    def __init__(self, heart: BlockRequest_heart, difficulty_factor: int, roots, n, block: Block):
        print("Type heart", type(heart))
        print("Type roots", type(roots))
        print("Type block", type(block))
        self.heart: BlockRequest_heart = heart
        self.difficulty_factor = difficulty_factor
        self.roots = roots
        self.n = n
        self.block = block

    def to_dict(self):
        print("DEBUG: Entering BlockRequest.to_dict")
        return {
            "heart": self.heart.to_dict(),
            "difficulty_factor": self.difficulty_factor,
            "roots": [bytes_to_string(r) if isinstance(r, bytes) else r for r in self.roots],
            "n": self.n,
            "block": self.block.to_dict()
        }

    @staticmethod
    def from_dict(data):
        print("DEBUG: Entering BlockRequest.from_dict")
        print("Type data['heart']", type(data["heart"]))
        print("Type data['roots']", type(data["roots"]))
        print("Type data['block']", type(data["block"]))
        return BlockRequest(
            heart=BlockRequest_heart.from_dict(data["heart"]),
            difficulty_factor=data["difficulty_factor"],
            roots=[base64.b64decode(r.encode("ascii")) if isinstance(r, str) else r for r in data["roots"]],
            n=data["n"],
            block=Block.from_dict(data["block"])
        )

    def __hash__(self):
        return int.from_bytes(shash(self.heart.hash, self.block.hash, self.difficulty_factor, self.n), 'big')
