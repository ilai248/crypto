from blockchain import Block, Transaction, BlockRequest, BlockRequest_heart, BalanceInfo
from gossip import GossipNode
from bin_heap import virt_bin_heap
from security import get_public_key_str
from utils import do_periodic
import time

DEBUG = True

TRANSACTIONS_PER_BLOCK = 2 if DEBUG else 1000
NEW_USERS_PER_BLOCK = 2 if DEBUG else 1000
TIME_INTERVAL_SECONDS = 1
USER_ADD_BROADCAST_PERIOD = 5
POW_PAY = 1

genesis_block = Block(
    index=0,
    prev_hash=b"\x00"*16,
    balance_info=BalanceInfo([], 0, 0, b"\x00"*16),
    transactions=[],
    new_users=[]
)
empty_money_bin = virt_bin_heap(0, [])

class BlockchainUser:
    def __init__(self, port: int, node_id: str, curr_max_time: int=TIME_INTERVAL_SECONDS, money_heap: virt_bin_heap=empty_money_bin, last_block: Block=genesis_block):
        self.money_heap: virt_bin_heap = money_heap
        self.transactions = []
        self.new_users = [get_public_key_str()]
        self.blockchain = {last_block.hash: last_block}
        self.last_hash = last_block.hash
        self.curr_max_time = curr_max_time
        self.curr_best_block_req: BlockRequest = None
        self.valid = False
        self.gossip: GossipNode = GossipNode("0.0.0.0", port, get_public_key_str(), node_id, self)
        do_periodic(self.request_add, [], USER_ADD_BROADCAST_PERIOD)

    def request_add(self) -> bool:
        if self.valid:
            return True
        self.gossip.broadcast_requestAdd()
        return False

    def can_create(self):
        return len(self.new_users) >= NEW_USERS_PER_BLOCK or len(self.transactions) >= TRANSACTIONS_PER_BLOCK and self.valid

    def get_interval(self, timestamp):
        return timestamp//TIME_INTERVAL_SECONDS
    
    def curr_interval(self):
        return self.get_interval(time.time())

    def interval_time(self, interval):
        return interval*TIME_INTERVAL_SECONDS

    def get_balance_info(self):
        return BalanceInfo(self.money_heap.brolist, self.money_heap.pos, self.money_heap.money, get_public_key_str())

    def on_add_user(self, public_key):
        self.new_users.append(public_key)

    def on_transact_verified(self, transact: Transaction):
        if self.validate_transaction(transact):
            self.transactions.append(transact)

    def get_last_block(self):
        return self.blockchain[self.last_hash]

    def get_block(self, block_hash: bytes):
        if block_hash in self.blockchain:
            return self.blockchain[block_hash]
        else:
            return self.gossip.get_block(block_hash)

    def validate_balance(self, balance: BalanceInfo):
        return self.money_heap.valid(balance.data, balance.pos, balance.brolist)

    def validate_transaction(self, transaction: Transaction) -> bool:
        balance_ok = self.validate_balance(transaction.sender_balance) and self.validate_balance(transaction.receiver_balance)
        money_ok = 0 < transaction.money <= transaction.sender_balance.money
        signature_ok = transaction.validate_signature()
        return balance_ok and money_ok and signature_ok

    def is_pow_transaction(self, block, t):
        return t.receiver_balance.public_key == block.pow_key and \
               t.sender_balance.public_key == block.balance_info.public_key and \
               t.amount == POW_PAY

    def pow_correct(self, block): # TODO: Calculate goal based on timestamp
        return block.hash[:self.pow_goal()] == "00"*self.pow_goal()

    # TODO: Check that goal is correct based on timestamp.
    def validate_block(self, block_request: BlockRequest) -> bool:
        block = block_request.block
        transactions_ok = all(self.validate_transaction(t) and t.expiration <= block.index for t in block.transactions)
        # TODO: Maybe add better check and maybe check timestamp.
        index_ok = block.index == 0 or block.index - 1 == self.get_block(block.prev_hash).index
        pow_ok = self.pow_correct(block) and any(self.is_pow_transaction(block, t) for t in block.transactions)
        heart_ok = block_request.heart.int_hash() < block.balance_info.money * self.calc_difficulty_factor()
        return transactions_ok and index_ok and pow_ok and heart_ok

    def calc_difficulty_factor(self):
        return 1  # PLACEHOLDER
    
    def pow_goal(self):
        return 0  # PLACEHOLDER

    def create_blockrequest(self, min_time: int, max_time: int):
        difficulty_factor = self.calc_difficulty_factor()
        new_index = self.blockchain[self.last_hash].index + 1
        prev_hash = self.last_hash
        balance_info = self.get_balance_info()
        block_transactions = self.transactions[:TRANSACTIONS_PER_BLOCK]
        block_users = self.new_users[:NEW_USERS_PER_BLOCK]
        block: Block = Block(new_index, prev_hash, balance_info, block_transactions, block_users, pow_pub_key=get_public_key_str())

        min_hash_int = None
        min_hash_req = None
        min_target_hash = balance_info.money * difficulty_factor
        for timestamp in range(min_time, max_time):
            heart: BlockRequest_heart = BlockRequest_heart(timestamp, get_public_key_str())
            heart_hash_int = heart.int_hash()
            if min_hash_int is None or heart_hash_int < min(min_hash_int, min_target_hash):
                min_hash_int = heart_hash_int
                block_request: BlockRequest = BlockRequest(heart, difficulty_factor, self.money_heap.roots, self.money_heap.n, block)
                min_hash_req = block_request

        if min_hash_int is not None:
            # TODO: If pow isn't correct broadcast request for pow.
            if not self.pow_correct(min_hash_req.block):
                min_hash_req.block.pow = None
                min_hash_req.block.hash = min_hash_req.block.compute_hash()
            else:
                # Block is fully correct so we are valid!
                self.valid = True
            self.gossip.broadcast_BlockRequest(min_hash_req)
            self.transactions = self.transactions[TRANSACTIONS_PER_BLOCK:]
            self.new_users = self.new_users[NEW_USERS_PER_BLOCK:]
            self.last_hash = min_hash_req.block.hash
            self.blockchain[self.last_hash] = min_hash_req.block
            return min_hash_req
        return None

    def on_block_create_req(self, block_req: BlockRequest):
        if self.validate_block(block_req):
            block = block_req.block
            if block.hash in self.blockchain and block.transactions != self.blockchain[block.hash].transactions:
                print("Bad Actor! Sending the ninjas...")
                return

            if len(self.blockchain) == 0 or block.prev_hash == self.last_hash:
                if self.curr_best_block_req is None or block_req.heart.int_hash() < self.curr_best_block_req.heart.int_hash():
                    self.curr_best_block_req = block_req
            else:
                original_block = block
                stake = blockchain_stake = 0

                while block.hash not in self.blockchain:
                    stake += block.balance_info.money
                    block = self.get_block(block.prev_hash)

                curr_block = self.blockchain[self.last_hash]
                while curr_block.hash != block.hash:
                    blockchain_stake += curr_block.balance_info.money
                    curr_block = self.blockchain[curr_block.prev_hash]

                if stake > blockchain_stake:
                    block_to_del = self.blockchain[self.last_hash]
                    while block_to_del.hash != block.hash:
                        del self.blockchain[block_to_del.hash]
                        block_to_del = self.blockchain[block_to_del.prev_hash]

                    while original_block.hash != block.hash:
                        self.blockchain[original_block.hash] = original_block
                        original_block = self.get_block(original_block.prev_hash)

            print(f"[CHAIN LENGTH] {len(self.blockchain)}")
        else:
            print("[FORK or STALE BLOCK] Ignored")

    def add_block_to_heap(self, block):
        for public_key in block.new_users:
            self.money_heap.insert(public_key)
        for transact in block.transactions:
            self.money_heap.change_data(
                transact.sender_balance.money - transact.amount,
                transact.sender,
                transact.sender_balance.brolist
            )
            self.money_heap.change_data(
                transact.receiver_balance.money + transact.amount,
                transact.receiver,
                transact.receiver_balance.brolist
            )
