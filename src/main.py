import sys, time, threading
from blockchain import Block, Transaction
from gossip import GossipNode

PEER_PORTS = {
    "1": [("127.0.0.1", 5001)],
    "2": [("127.0.0.1", 5000)]
}

BLOCKCHAIN = []

def on_block_received(block):
    if len(BLOCKCHAIN) == 0 or block.prev_hash == BLOCKCHAIN[-1].hash:
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
