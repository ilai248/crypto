import base64
import time
import hashlib
import json
from typing import List
from security import sign, verify_signed

TRANSACTION_EXPIRATION = 100
LOCAL_CHAIN_SIZE = TRANSACTION_EXPIRATION * 2


def shash(*args) -> bytes:
    result = hashlib.sha256("|".join(str(arg) for arg in args).encode()).digest()
    assert isinstance(result, bytes), f"shash result must be bytes, got {type(result)}"
    return result


def bytes_to_string(string: bytes):
    assert isinstance(string, bytes), f"bytes_to_string input must be bytes, got {type(string)}"
    result = base64.b64encode(string).decode("ascii")
    assert isinstance(result, str), f"bytes_to_string result must be str, got {type(result)}"
    return result


class BalanceInfo:
    def __init__(self, brolist, pos, money, public_key):
        print("Type brolist", type(brolist))
        print("Type public_key", type(public_key))
        assert isinstance(brolist, list), f"brolist must be list, got {type(brolist)}"
        for b in brolist:
            assert isinstance(b, bytes), f"brolist elements must be bytes, got {type(b)}"
        assert isinstance(pos, int), f"pos must be int, got {type(pos)}"
        assert isinstance(money, int), f"money must be int, got {type(money)}"
        assert isinstance(public_key, str), f"public_key must be str, got {type(public_key)}"
        assert base64.b64encode(base64.b64decode(public_key.encode("ascii"))).decode("ascii") == public_key, f"public_key {public_key} is not valid base64"
        self.brolist: List[bytes] = brolist
        self.pos: int = pos
        self.money: int = money
        self.public_key: str = public_key
        self.data = shash(base64.b64decode(public_key.encode("ascii")), money)
        print("Type data", type(self.data))
        assert isinstance(self.data, bytes), f"data must be bytes, got {type(self.data)}"

    def to_dict(self):
        print("DEBUG: Entering BalanceInfo.to_dict")
        result = {
            "brolist": [bytes_to_string(b) for b in self.brolist],
            "pos": self.pos,
            "money": self.money,
            "public_key": self.public_key,
            "data": bytes_to_string(self.data)
        }
        assert isinstance(result["brolist"], list), f"to_dict brolist must be list, got {type(result['brolist'])}"
        for b in result["brolist"]:
            assert isinstance(b, str), f"to_dict brolist elements must be str, got {type(b)}"
            assert base64.b64encode(base64.b64decode(b.encode("ascii"))).decode("ascii") == b, f"to_dict brolist element {b} is not valid base64"
        assert isinstance(result["pos"], int), f"to_dict pos must be int, got {type(result['pos'])}"
        assert isinstance(result["money"], int), f"to_dict money must be int, got {type(result['money'])}"
        assert isinstance(result["public_key"], str), f"to_dict public_key must be str, got {type(result['public_key'])}"
        assert base64.b64encode(base64.b64decode(result["public_key"].encode("ascii"))).decode("ascii") == result["public_key"], f"to_dict public_key {result['public_key']} is not valid base64"
        assert isinstance(result["data"], str), f"to_dict data must be str, got {type(result['data'])}"
        assert base64.b64encode(base64.b64decode(result["data"].encode("ascii"))).decode("ascii") == result["data"], f"to_dict data {result['data']} is not valid base64"
        return result

    @staticmethod
    def from_dict(data):
        print("Type data['brolist']", type(data["brolist"]))
        print("Type data['public_key']", type(data["public_key"]))
        assert isinstance(data, dict), f"from_dict data must be dict, got {type(data)}"
        assert isinstance(data["brolist"], list), f"data['brolist'] must be list, got {type(data['brolist'])}"
        for b in data["brolist"]:
            assert isinstance(b, str), f"data['brolist'] elements must be str, got {type(b)}"
            assert base64.b64encode(base64.b64decode(b.encode("ascii"))).decode("ascii") == b, f"data['brolist'] element {b} is not valid base64"
        assert isinstance(data["pos"], int), f"data['pos'] must be int, got {type(data['pos'])}"
        assert isinstance(data["money"], int), f"data['money'] must be int, got {type(data['money'])}"
        assert isinstance(data["public_key"], str), f"data['public_key'] must be str, got {type(data['public_key'])}"
        assert base64.b64encode(base64.b64decode(data["public_key"].encode("ascii"))).decode("ascii") == data["public_key"], f"data['public_key'] {data['public_key']} is not valid base64"
        return BalanceInfo(
            brolist=[base64.b64decode(b.encode("ascii")) for b in data["brolist"]],
            pos=data["pos"],
            money=data["money"],
            public_key=data["public_key"]
        )

    def __hash__(self):
        result = int.from_bytes(shash(base64.b64decode(self.public_key.encode("ascii")), self.money), 'big')
        assert isinstance(result, int), f"__hash__ result must be int, got {type(result)}"
        return result


class Transaction:
    def __init__(self, amount, sender_balance, receiver_balance, curr_block_index,
                 blocks_till_expire=TRANSACTION_EXPIRATION):
        print("Type sender_balance", type(sender_balance))
        print("Type receiver_balance", type(receiver_balance))
        assert isinstance(amount, int), f"amount must be int, got {type(amount)}"
        assert isinstance(sender_balance, BalanceInfo), f"sender_balance must be BalanceInfo, got {type(sender_balance)}"
        assert isinstance(receiver_balance, BalanceInfo), f"receiver_balance must be BalanceInfo, got {type(receiver_balance)}"
        assert isinstance(curr_block_index, int), f"curr_block_index must be int, got {type(curr_block_index)}"
        assert isinstance(blocks_till_expire, int), f"blocks_till_expire must be int, got {type(blocks_till_expire)}"
        self.amount = amount
        self.expiration = curr_block_index + blocks_till_expire
        self.sender_balance: BalanceInfo = sender_balance
        self.receiver_balance: BalanceInfo = receiver_balance
        self.signature = sign(self.compute_hash())
        print("Type signature", type(self.signature))
        assert isinstance(self.signature, bytes), f"signature must be bytes, got {type(self.signature)}"

    def validate_signature(self):
        result = verify_signed(self.compute_hash(), self.signature, base64.b64decode(self.receiver_balance.public_key.encode("ascii")))
        assert isinstance(result, bool), f"validate_signature result must be bool, got {type(result)}"
        return result

    def compute_hash(self):
        result = shash(
            self.amount,
            self.expiration,
            self.sender_balance.data,
            self.receiver_balance.data
        )
        assert isinstance(result, bytes), f"compute_hash result must be bytes, got {type(result)}"
        return result

    def to_dict(self):
        print("DEBUG: Entering Transaction.to_dict")
        result = {
            "amount": self.amount,
            "expiration": self.expiration,
            "sender_balance": self.sender_balance.to_dict(),
            "receiver_balance": self.receiver_balance.to_dict(),
            "signature": bytes_to_string(self.signature)
        }
        assert isinstance(result["amount"], int), f"to_dict amount must be int, got {type(result['amount'])}"
        assert isinstance(result["expiration"], int), f"to_dict expiration must be int, got {type(result['expiration'])}"
        assert isinstance(result["sender_balance"], dict), f"to_dict sender_balance must be dict, got {type(result['sender_balance'])}"
        assert isinstance(result["receiver_balance"], dict), f"to_dict receiver_balance must be dict, got {type(result['receiver_balance'])}"
        assert isinstance(result["signature"], str), f"to_dict signature must be str, got {type(result['signature'])}"
        assert base64.b64encode(base64.b64decode(result["signature"].encode("ascii"))).decode("ascii") == result["signature"], f"to_dict signature {result['signature']} is not valid base64"
        return result

    @staticmethod
    def from_dict(data):
        print("DEBUG: Entering Transaction.from_dict")
        print("Type data['sender_balance']", type(data["sender_balance"]))
        print("Type data['receiver_balance']", type(data["receiver_balance"]))
        print("Type data['signature']", type(data["signature"]))
        assert isinstance(data, dict), f"from_dict data must be dict, got {type(data)}"
        assert isinstance(data["amount"], int), f"data['amount'] must be int, got {type(data['amount'])}"
        assert isinstance(data["expiration"], int), f"data['expiration'] must be int, got {type(data['expiration'])}"
        assert isinstance(data["sender_balance"], dict), f"data['sender_balance'] must be dict, got {type(data['sender_balance'])}"
        assert isinstance(data["receiver_balance"], dict), f"data['receiver_balance'] must be dict, got {type(data['receiver_balance'])}"
        assert isinstance(data["signature"], str), f"data['signature'] must be str, got {type(data['signature'])}"
        assert base64.b64encode(base64.b64decode(data["signature"].encode("ascii"))).decode("ascii") == data["signature"], f"data['signature'] {data['signature']} is not valid base64"
        transaction = Transaction(
            amount=data["amount"],
            sender_balance=BalanceInfo.from_dict(data["sender_balance"]),
            receiver_balance=BalanceInfo.from_dict(data["receiver_balance"]),
            curr_block_index=data["expiration"] - TRANSACTION_EXPIRATION
        )
        transaction.signature = base64.b64decode(data["signature"].encode("ascii"))
        return transaction

    def __hash__(self):
        result = int.from_bytes(self.compute_hash(), 'big')
        assert isinstance(result, int), f"__hash__ result must be int, got {type(result)}"
        return result


class Block:
    def __init__(self, index, prev_hash, balance_info, transactions, new_users, timestamp=None, pow_pub_key=None):
        print("Type prev_hash", type(prev_hash))
        print("Type balance_info", type(balance_info))
        print("Type transactions", type(transactions))
        print("Type new_users", type(new_users))
        print("Type timestamp", type(timestamp))
        print("Type pow_pub_key", type(pow_pub_key))
        assert isinstance(index, int), f"index must be int, got {type(index)}"
        assert isinstance(prev_hash, bytes), f"prev_hash must be bytes, got {type(prev_hash)}"
        assert isinstance(balance_info, BalanceInfo), f"balance_info must be BalanceInfo, got {type(balance_info)}"
        assert isinstance(transactions, list), f"transactions must be list, got {type(transactions)}"
        for tx in transactions:
            assert isinstance(tx, Transaction), f"transactions elements must be Transaction, got {type(tx)}"
        assert isinstance(new_users, list), f"new_users must be list, got {type(new_users)}"
        for u in new_users:
            assert isinstance(u, str), f"new_users elements must be str, got {type(u)}"
            assert base64.b64encode(base64.b64decode(u.encode("ascii"))).decode("ascii") == u, f"new_users element {u} is not valid base64"
        assert isinstance(timestamp, (int, type(None))), f"timestamp must be int or None, got {type(timestamp)}"
        assert isinstance(pow_pub_key, (bytes, type(None))), f"pow_pub_key must be bytes or None, got {type(pow_pub_key)}"
        self.index = index
        self.prev_hash = prev_hash
        self.balance_info: BalanceInfo = balance_info
        self.transactions = transactions  # list of Transaction
        self.new_users = new_users  # List of public keys (str)
        self.timestamp = int(time.time()) if timestamp is None else timestamp
        self.med_hash = self.compute_med_hash()
        self.pow_key = pow_pub_key
        self.hash = self.compute_hash()
        print("Type pow_pub_key", type(self.pow_key))
        print("Type med_hash", type(self.med_hash))
        print("Type hash", type(self.hash))
        assert isinstance(self.med_hash, bytes), f"med_hash must be bytes, got {type(self.med_hash)}"
        assert isinstance(self.hash, bytes), f"hash must be bytes, got {type(self.hash)}"

    def compute_med_hash(self):
        result = shash(
            self.index,
            self.prev_hash,
            self.timestamp,
            [tx.compute_hash() for tx in self.transactions]
        )
        assert isinstance(result, bytes), f"compute_med_hash result must be bytes, got {type(result)}"
        return result

    def compute_hash(self):
        result = shash(self.med_hash, self.pow_key if self.pow_key else "")
        assert isinstance(result, bytes), f"compute_hash result must be bytes, got {type(result)}"
        return result

    def to_dict(self):
        print("DEBUG: Entering Block.to_dict")
        result = {
            "index": self.index,
            "prev_hash": bytes_to_string(self.prev_hash),
            "balance_info": self.balance_info.to_dict(),
            "transactions": [tx.to_dict() for tx in self.transactions],
            "new_users": self.new_users,
            "timestamp": self.timestamp,
            "pow_key": bytes_to_string(self.pow_key) if self.pow_key else None,
            "hash": bytes_to_string(self.hash),
            "med_hash": bytes_to_string(self.med_hash)
        }
        assert isinstance(result["index"], int), f"to_dict index must be int, got {type(result['index'])}"
        assert isinstance(result["prev_hash"], str), f"to_dict prev_hash must be str, got {type(result['prev_hash'])}"
        assert base64.b64encode(base64.b64decode(result["prev_hash"].encode("ascii"))).decode("ascii") == result["prev_hash"], f"to_dict prev_hash {result['prev_hash']} is not valid base64"
        assert isinstance(result["balance_info"], dict), f"to_dict balance_info must be dict, got {type(result['balance_info'])}"
        assert isinstance(result["transactions"], list), f"to_dict transactions must be list, got {type(result['transactions'])}"
        for tx in result["transactions"]:
            assert isinstance(tx, dict), f"to_dict transactions elements must be dict, got {type(tx)}"
        assert isinstance(result["new_users"], list), f"to_dict new_users must be list, got {type(result['new_users'])}"
        for u in result["new_users"]:
            assert isinstance(u, str), f"to_dict new_users elements must be str, got {type(u)}"
            assert base64.b64encode(base64.b64decode(u.encode("ascii"))).decode("ascii") == u, f"to_dict new_users element {u} is not valid base64"
        assert isinstance(result["timestamp"], int), f"to_dict timestamp must be int, got {type(result['timestamp'])}"
        assert isinstance(result["pow_key"], (str, type(None))), f"to_dict pow_key must be str or None, got {type(result['pow_key'])}"
        if result["pow_key"] is not None:
            assert base64.b64encode(base64.b64decode(result["pow_key"].encode("ascii"))).decode("ascii") == result["pow_key"], f"to_dict pow_key {result['pow_key']} is not valid base64"
        assert isinstance(result["hash"], str), f"to_dict hash must be str, got {type(result['hash'])}"
        assert base64.b64encode(base64.b64decode(result["hash"].encode("ascii"))).decode("ascii") == result["hash"], f"to_dict hash {result['hash']} is not valid base64"
        assert isinstance(result["med_hash"], str), f"to_dict med_hash must be str, got {type(result['med_hash'])}"
        assert base64.b64encode(base64.b64decode(result["med_hash"].encode("ascii"))).decode("ascii") == result["med_hash"], f"to_dict med_hash {result['med_hash']} is not valid base64"
        return result

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
        assert isinstance(data, dict), f"from_dict data must be dict, got {type(data)}"
        assert isinstance(data["index"], int), f"data['index'] must be int, got {type(data['index'])}"
        assert isinstance(data["prev_hash"], str), f"data['prev_hash'] must be str, got {type(data['prev_hash'])}"
        assert base64.b64encode(base64.b64decode(data["prev_hash"].encode("ascii"))).decode("ascii") == data["prev_hash"], f"data['prev_hash'] {data['prev_hash']} is not valid base64"
        assert isinstance(data["balance_info"], dict), f"data['balance_info'] must be dict, got {type(data['balance_info'])}"
        assert isinstance(data["transactions"], list), f"data['transactions'] must be list, got {type(data['transactions'])}"
        for tx in data["transactions"]:
            assert isinstance(tx, dict), f"data['transactions'] elements must be dict, got {type(tx)}"
        assert isinstance(data["new_users"], list), f"data['new_users'] must be list, got {type(data['new_users'])}"
        for u in data["new_users"]:
            assert isinstance(u, str), f"data['new_users'] elements must be str, got {type(u)}"
            assert base64.b64encode(base64.b64decode(u.encode("ascii"))).decode("ascii") == u, f"data['new_users'] element {u} is not valid base64"
        assert isinstance(data["timestamp"], int), f"data['timestamp'] must be int, got {type(data['timestamp'])}"
        assert isinstance(data["pow_key"], (str, type(None))), f"data['pow_key'] must be str or None, got {type(data['pow_key'])}"
        if data["pow_key"] is not None:
            assert base64.b64encode(base64.b64decode(data["pow_key"].encode("ascii"))).decode("ascii") == data["pow_key"], f"data['pow_key'] {data['pow_key']} is not valid base64"
        assert isinstance(data["hash"], str), f"data['hash'] must be str, got {type(data['hash'])}"
        assert base64.b64encode(base64.b64decode(data["hash"].encode("ascii"))).decode("ascii") == data["hash"], f"data['hash'] {data['hash']} is not valid base64"
        assert isinstance(data["med_hash"], str), f"data['med_hash'] must be str, got {type(data['med_hash'])}"
        assert base64.b64encode(base64.b64decode(data["med_hash"].encode("ascii"))).decode("ascii") == data["med_hash"], f"data['med_hash'] {data['med_hash']} is not valid base64"
        return Block(
            index=data["index"],
            prev_hash=base64.b64decode(data["prev_hash"].encode("ascii")),
            balance_info=BalanceInfo.from_dict(data["balance_info"]),
            transactions=[Transaction.from_dict(tx) for tx in data["transactions"]],
            new_users=data["new_users"],
            timestamp=data["timestamp"],
            pow_pub_key=base64.b64decode(data["pow_key"].encode("ascii")) if data["pow_key"] else None
        )

    def __hash__(self):
        result = int.from_bytes(self.hash, 'big')
        assert isinstance(result, int), f"__hash__ result must be int, got {type(result)}"
        return result


class BlockRequest_heart:
    def __init__(self, timestamp: int, public_key: str):
        print("Type public_key", type(public_key))
        assert isinstance(timestamp, int), f"timestamp must be int, got {type(timestamp)}"
        assert isinstance(public_key, str), f"public_key must be str, got {type(public_key)}"
        assert base64.b64encode(base64.b64decode(public_key.encode("ascii"))).decode("ascii") == public_key, f"public_key {public_key} is not valid base64"
        self.timestamp: int = timestamp
        self.public_key: str = public_key
        self.hash = self.compute_hash()
        print("Type hash", type(self.hash))
        assert isinstance(self.hash, bytes), f"hash must be bytes, got {type(self.hash)}"

    def compute_hash(self):
        result = hashlib.sha256(f"{self.timestamp}|{base64.b64decode(self.public_key.encode('ascii'))}".encode()).digest()
        assert isinstance(result, bytes), f"compute_hash result must be bytes, got {type(result)}"
        return result

    def int_hash(self):
        result = int.from_bytes(self.hash, 'big')
        assert isinstance(result, int), f"int_hash result must be int, got {type(result)}"
        return result

    def to_dict(self):
        print("DEBUG: Entering BlockRequest_heart.to_dict")
        result = {
            "timestamp": self.timestamp,
            "public_key": self.public_key,
            "hash": bytes_to_string(self.hash)
        }
        assert isinstance(result["timestamp"], int), f"to_dict timestamp must be int, got {type(result['timestamp'])}"
        assert isinstance(result["public_key"], str), f"to_dict public_key must be str, got {type(result['public_key'])}"
        assert base64.b64encode(base64.b64decode(result["public_key"].encode("ascii"))).decode("ascii") == result["public_key"], f"to_dict public_key {result['public_key']} is not valid base64"
        assert isinstance(result["hash"], str), f"to_dict hash must be str, got {type(result['hash'])}"
        assert base64.b64encode(base64.b64decode(result["hash"].encode("ascii"))).decode("ascii") == result["hash"], f"to_dict hash {result['hash']} is not valid base64"
        return result

    @staticmethod
    def from_dict(data):
        print("DEBUG: Entering BlockRequest_heart.from_dict")
        print("Type data['public_key']", type(data["public_key"]))
        print("Type data['hash']", type(data["hash"]))
        assert isinstance(data, dict), f"from_dict data must be dict, got {type(data)}"
        assert isinstance(data["timestamp"], int), f"data['timestamp'] must be int, got {type(data['timestamp'])}"
        assert isinstance(data["public_key"], str), f"data['public_key'] must be str, got {type(data['public_key'])}"
        assert base64.b64encode(base64.b64decode(data["public_key"].encode("ascii"))).decode("ascii") == data["public_key"], f"data['public_key'] {data['public_key']} is not valid base64"
        assert isinstance(data["hash"], str), f"data['hash'] must be str, got {type(data['hash'])}"
        assert base64.b64encode(base64.b64decode(data["hash"].encode("ascii"))).decode("ascii") == data["hash"], f"data['hash'] {data['hash']} is not valid base64"
        obj = BlockRequest_heart(
            timestamp=data["timestamp"],
            public_key=data["public_key"]
        )
        obj.hash = base64.b64decode(data["hash"].encode("ascii"))
        return obj

    def __hash__(self):
        result = int.from_bytes(self.hash, 'big')
        assert isinstance(result, int), f"__hash__ result must be int, got {type(result)}"
        return result


class BlockRequest:
    def __init__(self, heart: BlockRequest_heart, difficulty_factor: int, roots, n, block: Block):
        print("Type heart", type(heart))
        print("Type roots", type(roots))
        print("Type block", type(block))
        assert isinstance(heart, BlockRequest_heart), f"heart must be BlockRequest_heart, got {type(heart)}"
        assert isinstance(difficulty_factor, int), f"difficulty_factor must be int, got {type(difficulty_factor)}"
        assert isinstance(roots, list), f"roots must be list, got {type(roots)}"
        for r in roots:
            assert isinstance(r, bytes), f"roots elements must be bytes, got {type(r)}"
        assert isinstance(n, int), f"n must be int, got {type(n)}"
        assert isinstance(block, Block), f"block must be Block, got {type(block)}"
        self.heart: BlockRequest_heart = heart
        self.difficulty_factor = difficulty_factor
        self.roots = roots
        self.n = n
        self.block = block

    def to_dict(self):
        print("DEBUG: Entering BlockRequest.to_dict")
        result = {
            "heart": self.heart.to_dict(),
            "difficulty_factor": self.difficulty_factor,
            "roots": [bytes_to_string(r) if isinstance(r, bytes) else r for r in self.roots],
            "n": self.n,
            "block": self.block.to_dict()
        }
        assert isinstance(result["heart"], dict), f"to_dict heart must be dict, got {type(result['heart'])}"
        assert isinstance(result["difficulty_factor"], int), f"to_dict difficulty_factor must be int, got {type(result['difficulty_factor'])}"
        assert isinstance(result["roots"], list), f"to_dict roots must be list, got {type(result['roots'])}"
        for r in result["roots"]:
            assert isinstance(r, str), f"to_dict roots elements must be str, got {type(r)}"
            assert base64.b64encode(base64.b64decode(r.encode("ascii"))).decode("ascii") == r, f"to_dict roots element {r} is not valid base64"
        assert isinstance(result["n"], int), f"to_dict n must be int, got {type(result['n'])}"
        assert isinstance(result["block"], dict), f"to_dict block must be dict, got {type(result['block'])}"
        return result

    @staticmethod
    def from_dict(data):
        print("DEBUG: Entering BlockRequest.from_dict")
        print("Type data['heart']", type(data["heart"]))
        print("Type data['roots']", type(data["roots"]))
        print("Type data['block']", type(data["block"]))
        assert isinstance(data, dict), f"from_dict data must be dict, got {type(data)}"
        assert isinstance(data["heart"], dict), f"data['heart'] must be dict, got {type(data['heart'])}"
        assert isinstance(data["difficulty_factor"], int), f"data['difficulty_factor'] must be int, got {type(data['difficulty_factor'])}"
        assert isinstance(data["roots"], list), f"data['roots'] must be list, got {type(data['roots'])}"
        for r in data["roots"]:
            assert isinstance(r, str), f"data['roots'] elements must be str, got {type(r)}"
            assert base64.b64encode(base64.b64decode(r.encode("ascii"))).decode("ascii") == r, f"data['roots'] element {r} is not valid base64"
        assert isinstance(data["n"], int), f"data['n'] must be int, got {type(data['n'])}"
        assert isinstance(data["block"], dict), f"data['block'] must be dict, got {type(data['block'])}"
        return BlockRequest(
            heart=BlockRequest_heart.from_dict(data["heart"]),
            difficulty_factor=data["difficulty_factor"],
            roots=[base64.b64decode(r.encode("ascii")) if isinstance(r, str) else r for r in data["roots"]],
            n=data["n"],
            block=Block.from_dict(data["block"])
        )

    def __hash__(self):
        result = int.from_bytes(shash(self.heart.hash, self.block.hash, self.difficulty_factor, self.n), 'big')
        assert isinstance(result, int), f"__hash__ result must be int, got {type(result)}"
        return result