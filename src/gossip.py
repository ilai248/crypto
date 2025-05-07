import socket, threading, json
from blockchain import Block, Transaction

class GossipNode:
    def __init__(self, host, port, peers, on_block):
        self.host = host
        self.port = port
        self.peers = peers  # list of (ip, port)
        self.on_block = on_block
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()

        threading.Thread(target=self.accept_peers, daemon=True).start()

    def accept_peers(self):
        while True:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_peer, args=(conn,), daemon=True).start()

    def handle_peer(self, conn):
        with conn:
            data = conn.recv(65536).decode()
            try:
                message = json.loads(data)
                if message["type"] == "block":
                    block = Block.from_dict(message["data"])
                    print(f"[RECV BLOCK] from {block.proposer}: {block.hash[:10]}")
                    self.on_block(block)
            except Exception as e:
                print("Error handling peer:", e)

    def broadcast_block(self, block):
        message = json.dumps({"type": "block", "data": block.to_dict()})
        for ip, port in self.peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, port))
                    s.sendall(message.encode())
            except Exception as e:
                print(f"Failed to send to {ip}:{port} - {e}")
