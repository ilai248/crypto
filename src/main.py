import hashlib
import sys, time, threading
from blockchain import Block, Transaction, BlockRequest, BlockRequest_heart
from gossip import GossipNode

class LocalInfo:
    def __init__(self, balance_root_hash):
        self.balance_root_hash: bytes = balance_root_hash

PEER_PORTS = {
    "1": [("127.0.0.1", 5001)],
    "2": [("127.0.0.1", 5000)]
}

BLOCKCHAIN = {}
last_hash  = b""

TIME_INTERVAL_MS = 1000
curr_max_time = TIME_INTERVAL_MS # The first round will end in exactly 1 second from the launch.
local_info: LocalInfo = LocalInfo()

def get_block(block_hash: bytes) -> Block:
    # TODO: implement
    raise NotImplementedError()

def validate_transaction(transaction: Transaction) -> bool:
    balance = transaction.balance_info
    state = hashlib.sha256(transaction.sender.signature + transaction.sender.money).digest()
    for salt in balance.verify_hashes:
        state = hashlib.sha256(state + salt).digest()
    return state == local_info.balance_root_hash and balance.coin_amount <= transaction.sender.money

def validate_block(max_time: int, block_request: BlockRequest) -> bool:
    transactions_ok = all(validate_transaction(t) for t in block_request.transactions)
    timestamp_ok = get_block(block_request.prev_hash).timestamp <= block_request.timestamp <= max_time
    #heart_ok = ...
    #key_ok = ...
    #return parent_ok

def on_block_received(block: 'BlockRequest'):
    if validate_block(curr_max_time, block):
        block = Block(block.index, block.prev_hash, block.proposer, block.balance_info, block.transactions, block.timestamp)
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
                block = get_block(block.prev_hash) # TODO: Make sure it exists.

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

    # Block proposer simulation (TODO: Change).
    def proposer_loop():
        while True:
            time.sleep(10)
            tx = Transaction("node" + node_id, "receiver", 1.0)
            new_block = Block(
                index=BLOCKCHAIN[last_hash].index + 1,
                prev_hash=last_hash,
                proposer=f"node{node_id}",
                transactions=[tx]
            )
            BLOCKCHAIN[new_block.hash] = new_block
            last_hash = new_block.hash
            gossip.broadcast_block(new_block)
            print(f"[SENT BLOCK] {new_block.hash[:10]}")

    threading.Thread(target=proposer_loop, daemon=True).start()

    # Keep running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <node_id>")
        sys.exit(1)
    start_node(sys.argv[1])
