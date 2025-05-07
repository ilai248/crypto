import sys, time, threading
from blockchain import Block, Transaction
from gossip import GossipNode

class LocalInfo:
    def __init__(self, balance_root_hash):
        self.balance_root_hash: bytes = balance_root_hash

PEER_PORTS = {
    "1": [("127.0.0.1", 5001)],
    "2": [("127.0.0.1", 5000)]
}

BLOCKCHAIN = []

TIME_INTERVAL_MS = 1000
curr_max_time = TIME_INTERVAL_MS # The first round will end in exactly 1 second from the launch.
local_info: LocalInfo = LocalInfo()

def get_block(block_hash: bytes) -> Block:
    # TODO: ...

def validate_transaction(transaction: Transaction) -> bool:
    return True

def validate_block(max_time: int, block: Block) -> bool:
    parent_ok = len(BLOCKCHAIN) == 0 or block.prev_hash == BLOCKCHAIN[-1].hash
    transactions_ok = all(validate_transaction(t) for t in block.transactions)
    timestamp_ok = get_block(block.prev_hash).timestamp <= block.timestamp <= max_time
    #heart_ok = ...
    #key_ok = ...
    return parent_ok

def on_block_received(block):
    if validate_block(block):
        BLOCKCHAIN.append(block)
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
        BLOCKCHAIN.append(genesis)

    # Block proposer simulation
    def proposer_loop():
        while True:
            time.sleep(10)
            tx = Transaction("node" + node_id, "receiver", 1.0)
            new_block = Block(
                index=len(BLOCKCHAIN),
                prev_hash=BLOCKCHAIN[-1].hash,
                proposer=f"node{node_id}",
                transactions=[tx]
            )
            BLOCKCHAIN.append(new_block)
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
