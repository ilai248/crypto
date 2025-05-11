import hashlib
import sys, time, threading
from blockchain import Block, Transaction, BlockRequest, BlockRequest_heart, BalanceInfo
from gossip import GossipNode
from bin_heap import virt_bin_heap

PEER_PORTS = {
    "1": [("127.0.0.1", 5001)],
    "2": [("127.0.0.1", 5000)]
}

# TODO: Add option to send transaction packets.
transactions = []
TRANSACTIONS_PER_BLOCK = 1000

BLOCKCHAIN = {}
last_hash: bytes
money_heap: virt_bin_heap = virt_bin_heap # TODO Initialize

TIME_INTERVAL_MS = 1000
curr_max_time = TIME_INTERVAL_MS # The first round will end in exactly 1 second from the launch.

def get_block(block_hash: bytes, gossip: GossipNode):
    if block_hash in BLOCKCHAIN:
        return BLOCKCHAIN[block_hash]
    else:
        return gossip.get_block(block_hash)

def validate_transaction(transaction: Transaction) -> bool:
    balance = transaction.balance_info
    state = hashlib.sha256(transaction.public_key + transaction.sender.money).digest()
    for salt in balance.verify_hashes:
        state = hashlib.sha256(state + salt).digest()
    return state == local_info.balance_root_hash and 0 <= balance.coin_amount <= transaction.sender.money

def validate_block(max_time: int, block_request: BlockRequest, gossip: GossipNode) -> bool:
    transactions_ok = all(validate_transaction(t) and t.expiration <= block_request.block.index for t in block_request.block.transactions)
    timestamp_ok = get_block(block_request.block.prev_hash, gossip).timestamp <= block_request.block.timestamp <= max_time
    #heart_ok = hashlib.sha256(block_request.heart)
    key_ok = ...
    #return parent_ok

def calc_difficulty_factor():
    return 1 # PLACEHOLDER

def encrypt(data):
    return data # PLACEHOLDER

def get_public_key():
    return b'0'*64 # PLACEHOLDER

def create_blockrequest(index: int, min_time: int, max_time: int, gossip: GossipNode):
    difficulty_factor = calc_difficulty_factor()
    new_index = BLOCKCHAIN[last_hash].block.index + 1
    prev_hash = last_hash
    proposer = money_heap.pos
    balance_info = BalanceInfo(money_heap.brolist, money_heap.pos, money_heap.coin_amount)
    block_transactions = transactions[:TRANSACTIONS_PER_BLOCK]
    block: Block = Block(new_index, prev_hash, proposer, balance_info, block_transactions)
    for timestamp in range(min_time, max_time + 1):
        heart: BlockRequest_heart = BlockRequest_heart(timestamp, get_public_key())
        block_request: BlockRequest = BlockRequest(heart, difficulty_factor, money_heap.roots, block)
        gossip.broadcast_BlockRequest(block_request)
    # TOOD: Check if block is accepted.

def on_block_received(block: 'BlockRequest', gossip: GossipNode):
    if validate_block(curr_max_time, block):
        block = block.block
        if block.hash in BLOCKCHAIN and block.transactions != BLOCKCHAIN[block.hash].transactions:
            print("Bad Actor! Sending the ninjas...")
            # TODO: Send "Liar!" request
            # TODO: Send the ninjas.
            return

        if len(BLOCKCHAIN) == 0 or block.prev_hash == BLOCKCHAIN[-1].hash:
            BLOCKCHAIN[block.hash] = block
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


def start_node(node_id):
    port = 5000 if node_id == "1" else 5001
    peers = PEER_PORTS[node_id]

    gossip = GossipNode("0.0.0.0", port, peers, on_block_received)

    # Genesis block
    if not BLOCKCHAIN:
        genesis = Block(0, "0", "genesis", [])
        BLOCKCHAIN[genesis.hash] = genesis
        last_hash = genesis.hash

    # TODO: Add logic.

    # Keep running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <node_id>")
        sys.exit(1)
    start_node(sys.argv[1])
