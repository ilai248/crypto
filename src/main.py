import hashlib
import sys, time, threading
from blockchain import Block, Transaction, BlockRequest, BlockRequest_heart, BalanceInfo
from gossip import GossipNode
from bin_heap import virt_bin_heap
import security

PEER_PORTS = {
    "1": [("127.0.0.1", 5001)],
    "2": [("127.0.0.1", 5000)]
}

money_heap: virt_bin_heap = None

# TODO: Add option to send transaction packets.
transactions = []
TRANSACTIONS_PER_BLOCK = 1000

new_users = []
NEW_USERS_PER_BLOCK = 1000

BLOCKCHAIN = {}
last_hash: bytes

TIME_INTERVAL_SECONDS = 1
curr_max_time = TIME_INTERVAL_SECONDS # The first round will end in exactly 1 second from the launch.

curr_best_block_req: BlockRequest = None
POW_GOAL = 20
POW_PAY  = 1

def get_balance_info():
    return BalanceInfo(money_heap.brolist, money_heap.pos, money_heap.money, security.get_public_key())

def on_add_user(public_key):
    new_users.append(public_key)

def on_transact_verified(transact: Transaction):
    if validate_transaction(transact):
        transactions.append(transact)

def get_last_block():
    return BLOCKCHAIN[last_hash]

def get_block(block_hash: bytes, gossip: GossipNode):
    if block_hash in BLOCKCHAIN:
        return BLOCKCHAIN[block_hash]
    else:
        return gossip.get_block(block_hash)

def validate_balance(balance: BalanceInfo):
    return money_heap.valid(balance.data, balance.pos, balance.brolist)

def validate_transaction(transaction: Transaction) -> bool:
    balance_ok = validate_balance(transaction.sender_balance) and validate_balance(transaction.receiver_balance)
    money_ok = 0 < transaction.money <= transaction.sender_balance.money
    return balance_ok and money_ok

def is_pow_transaction(block, t):
    return t.receiver_balance.public_key == block.pow_key and t.sender_balance.public_key == block.balance_info.public_key and t.amount == POW_PAY

def validate_block(max_time: int, block_request: BlockRequest, gossip: GossipNode) -> bool:
    block = block_request.block
    transactions_ok = all(validate_transaction(t) and t.expiration <= block.index for t in block.transactions)
    timestamp_ok = get_block(block.prev_hash, gossip).timestamp <= block.timestamp <= max_time
    pow_ok = set(block.hash[:POW_GOAL]) == b"\x00" and any(map(is_pow_transaction, block.transactions))
    heart_ok = block_request.heart.int_hash() < block.balance_info.money * calc_difficulty_factor()
    return transactions_ok and timestamp_ok and pow_ok and heart_ok

def calc_difficulty_factor():
    return 1 # PLACEHOLDER

def get_public_key():
    return b'0'*64 # PLACEHOLDER

def create_blockrequest(min_time: int, max_time: int, gossip: GossipNode):
    difficulty_factor = calc_difficulty_factor()
    new_index = BLOCKCHAIN[last_hash].block.index + 1
    prev_hash = last_hash
    proposer = money_heap.pos
    balance_info = get_balance_info()
    block_transactions = transactions[:TRANSACTIONS_PER_BLOCK]
    block_users = new_users[:TRANSACTIONS_PER_BLOCK]
    block: Block = Block(new_index, prev_hash, proposer, balance_info, block_transactions, block_users)

    min_hash_int = None
    min_hash_req = None
    min_target_hash = balance_info.money * difficulty_factor
    for timestamp in range(min_time, max_time + 1):
        heart: BlockRequest_heart = BlockRequest_heart(timestamp, get_public_key())
        heart_hash_int = heart.int_hash()
        if min_hash_int is None or heart_hash_int < min(min_hash_int, min_target_hash):
            min_hash_int = heart.hash()
            block_request: BlockRequest = BlockRequest(heart, difficulty_factor, money_heap.roots, block)
            min_hash_req = block_request
    
    if min_hash_int is not None:
        gossip.broadcast_BlockRequest(min_hash_req)
        transactions = transactions[TRANSACTIONS_PER_BLOCK:]
        new_users = new_users[TRANSACTIONS_PER_BLOCK:]
        last_hash = min_hash_req.block.hash
        BLOCKCHAIN[last_hash] = min_hash_req.block


def on_block_create_req(block_req: 'BlockRequest', gossip: GossipNode):
    if validate_block(curr_max_time, block_req):
        block = block_req.block
        if block.hash in BLOCKCHAIN and block.transactions != BLOCKCHAIN[block.hash].transactions:
            print("Bad Actor! Sending the ninjas...")
            # TODO: Send "Liar!" request
            # TODO: Send the ninjas.
            # TODO: Train an ai model to find the locations of everyone (for the ninjas).
            return

        if len(BLOCKCHAIN) == 0 or block.prev_hash == BLOCKCHAIN[-1].hash:
            if block_req.heart.int_hash() < curr_best_block_req.heart.int_hash():
                curr_best_block_req = block_req
        else:
            original_block = block
            stake = blockchain_stake = 0

            # Go up to forking point while collecting stake.
            while block.hash not in BLOCKCHAIN:
                stake += block.balance_info.coin_amount
                block = get_block(block.prev_hash, gossip) # TODO: Make sure it exists.

            # Collect the stake of our main chain up to the forking point.
            curr_block = BLOCKCHAIN[last_hash]
            while curr_block.hash != block.hash:
                blockchain_stake += curr_block.balance_info.coin_amount
                curr_block = BLOCKCHAIN[curr_block.prev_hash]
            
            if stake > blockchain_stake:
                # Delete the main chain up to the fork.
                block_to_del = BLOCKCHAIN[last_hash]
                while block_to_del.hash != block.hash:
                    del BLOCKCHAIN[block_to_del.hash]
                    block_to_del = BLOCKCHAIN[block_to_del.prev_hash]
                
                # Concat the suggested chain to our main chain.
                while original_block.hash != block.hash:
                    BLOCKCHAIN[original_block.hash] = original_block
                    original_block = BLOCKCHAIN[original_block.prev_hash]
        print(f"[CHAIN LENGTH] {len(BLOCKCHAIN)}")
    else:
        print("[FORK or STALE BLOCK] Ignored")


def add_block_to_heap(block):
    for public_key in block.new_users:
        money_heap.insert(public_key)
    for transact in block.transactions:
        money_heap.change_data(transact.sender_balance.money - transact.amount, transact.sender, transact.sender_balance.brolist)
        money_heap.change_data(transact.receiver_balance.money - transact.amount, transact.sender, transact.receiver_balance.brolist)


def start_node(node_id):
    global last_hash
    port = 5000 if node_id == "1" else 5001
    peers = PEER_PORTS[node_id]

    gossip = GossipNode("0.0.0.0", port, peers, security.get_public_key(), on_block_create_req, on_add_user, on_transact_verified)

    # Genesis block (TODO: Add way to buy the prev block's hash so that we could verify new blocks).
    if not BLOCKCHAIN:
        genesis = Block(0, "0", "genesis", [])
        BLOCKCHAIN[genesis.hash] = genesis
        last_hash = genesis.hash
    gossip.broadcast_requestAdd(security.get_public_key())

    # Keep running
    while True:
        time.sleep(TIME_INTERVAL_SECONDS)
        block = curr_best_block_req.block
        BLOCKCHAIN[block.hash] = block
        if money_heap is None:
            money_heap = virt_bin_heap(curr_best_block_req.n, curr_best_block_req.roots)
        add_block_to_heap(block)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <node_id>")
        sys.exit(1)
    start_node(sys.argv[1])
