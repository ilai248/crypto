import socket
import threading
import json
import time
from blockchain import Block, Transaction, BlockRequest
from main import get_balance_info, get_last_block

MIN_REQ_TIME = 3
MIN_REQ_ANS  = 10

def most_common(lst):
    """
    Return the most common item in lst, handling dictionaries by serializing to JSON.
    Returns None if lst is empty.
    """
    if not lst:
        return None
    hashable_lst = [json.dumps(item, sort_keys=True) if isinstance(item, dict) else item for item in lst]
    most_common_hash = max(hashable_lst, key=hashable_lst.count)
    for item in lst:
        if isinstance(item, dict) and json.dumps(item, sort_keys=True) == most_common_hash:
            return item
        elif item == most_common_hash:
            return item
    return None

class GossipNode:
    def __init__(self, host, port, peers, public_key, uid, on_block_create_req, on_add_user, on_transact_verified, blockchain=None):
        self.host = host
        self.port = port
        self.peers = peers  # list of (ip, port)
        self.public_key = public_key
        self.uid = uid
        self.on_block_create_req = on_block_create_req
        self.on_add_user = on_add_user
        self.on_transact_verified = on_transact_verified
        self.blockchain = blockchain  # Reference to blockchain for responding to requests
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
            try:
                data = conn.recv(65536).decode()
                message = json.loads(data)
                response_data = None
                msg_type, msg_data = message["type"], message["data"]
                if message["type"] == "request":
                    # Handle generic request by responding with requested data
                    req_type = message["data"]["type"]
                    req_data = message["data"]["data"]
                    if req_type == "get_block" and req_data in self.blockchain:
                        block = self.blockchain[req_data]
                        response_data = block.to_dict()
                    
                    # Send response
                    response = json.dumps({"type": "response", "data": response_data})
                    conn.sendall(response.encode())
                elif msg_type == "add_user":
                    self.on_add_user(msg_data)
                elif msg_type == "verify_transaction":
                    sender   = self.uid
                    receiver = msg_data.get("receiver_pos", None)
                    amount   = msg_data.get("amount", None)
                    if receiver is None or amount is None:
                        print("[*] DEBUG: Invalid Transaction To Verify")
                        return
                    pub_key  = self.public_key
                    balance  = get_balance_info()
                    curr_idx = get_last_block().index
                    transact = Transaction(sender, receiver, amount, pub_key, balance, curr_idx)
                    self.broadcast_data("transaction_verified", transact.to_dict())
                elif msg_type == "transaction_verified":
                    self.on_transact_verified(Transaction.from_dict(msg_data))
                elif msg_type == "create_block":
                    self.on_block_create_req(BlockRequest.from_dict(msg_data), self)
            except Exception as e:
                print(f"Error handling peer: {e}")

    def broadcast_request(self, type, data, min_ans, interval, listener):
        """
        Broadcast a request to all peers and collect responses.
        Calls listener with list of results when min_ans responses are received or interval elapses.
        Remaining threads run as daemons and complete in the background.
        """
        results = []
        results_lock = threading.Lock()
        response_count = 0
        stop_event = threading.Event()

        def request_from_peer(ip, port):
            nonlocal response_count
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(interval)
                    s.connect((ip, port))
                    message = json.dumps({"type": "request", "data": {"type": type, "data": data}})
                    s.sendall(message.encode())
                    response_data = s.recv(65536).decode()
                    response = json.loads(response_data)
                    if response["type"] == "response" and response["data"] is not None:
                        with results_lock:
                            results.append(response["data"])
                            response_count += 1
                            if response_count >= min_ans:
                                stop_event.set()
            except Exception as e:
                print(f"Error requesting from {ip}:{port} - {e}")

        # Start daemon threads for each peer
        for ip, port in self.peers:
            t = threading.Thread(target=request_from_peer, args=(ip, port), daemon=True)
            t.start()

        # Wait for min_ans responses or timeout
        stop_event.wait(timeout=interval)

        # Call listener immediately, let remaining threads finish in background
        listener(results)

    def request_most_likely(self, type, data, listener):
        def wrapper_listener(results):
            listener(most_common(results))
        self.broadcast_request(type, data, MIN_REQ_ANS, MIN_REQ_TIME, wrapper_listener)

    def sync_request_most_likely(self, type, data, timeout=30.0):
        """
        Synchronously broadcast a request and return the most common result.
        Blocks until a result is received or timeout elapses.

        Args:
            type (str): Type of request (e.g., "get_block").
            data (any): Data for the request (e.g., block hash).
            timeout (float): Maximum time to wait (seconds).

        Returns:
            The most common result (e.g., Block for type="get_block") or None if no result.
        """
        result = [None]  # Use a list for mutable, thread-safe storage
        result_event = threading.Event()
        def on_res(res):
            result[0] = res
            result_event.set()
        self.request_most_likely(type, data, on_res)
        result_event.wait(timeout=timeout)
        return result[0]

    def get_block(self, block_hash, listener):
        inner_listener = (lambda result: listener(Block.from_dict(result)) if result is not None else None)
        self.sync_request_most_likely("get_block", block_hash, inner_listener)

    def broadcast_data(self, type, data):
        def request_from_peer(ip, port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, port))
                    message = json.dumps({"type": type, "data": data})
                    s.sendall(message.encode())
            except Exception as e:
                print(f"Error requesting from {ip}:{port} - {e}")

        # Start daemon threads for each peer
        for ip, port in self.peers:
            t = threading.Thread(target=request_from_peer, args=(ip, port), daemon=True)
            t.start()

    def broadcast_BlockRequest(self, block_req):
        self.broadcast_data("create_block", block_req.to_dict())

    def broadcast_requestAdd(self, public_key):
        self.broadcast_data("add_user", public_key)
    
    def broadcast_verifyTransactionRequest(self, receiver_pos, amount):
        self.broadcast_data("verify_transaction", {"receiver_pos": receiver_pos, "amount": amount})
