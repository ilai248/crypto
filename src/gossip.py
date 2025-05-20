import socket
import threading
import json
import time
import struct
from blockchain import Block, Transaction, BlockRequest
# from main import get_balance_info, get_last_block

MIN_REQ_TIME = 3
MIN_REQ_ANS = 10
MULTICAST_GROUP = '224.0.0.1'
MULTICAST_PORT = 5002
DISCOVERY_INTERVAL = 5  # Seconds between multicast announcements


def most_common(lst):
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
    def __init__(self, host, port, public_key_str, uid, blockchain_user):
        self.host = host
        self.port = port
        self.peers = []  # Dynamic peer list
        self.public_key_str = public_key_str
        self.uid = uid
        self.user = blockchain_user
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        self.running = True

        # assigned later
        self.multicast_socket = None
        self.receiver_socket = None

        # Start peer discovery
        self.start_multicast_discovery()
        threading.Thread(target=self.accept_peers, daemon=True).start()

    def start_multicast_discovery(self):
        # Multicast sender
        self.multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        threading.Thread(target=self.send_multicast, daemon=True).start()

        # Multicast receiver
        self.receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.receiver_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receiver_socket.bind(('', MULTICAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
        self.receiver_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        threading.Thread(target=self.receive_multicast, daemon=True).start()

    def send_multicast(self):
        while self.running:
            try:
                message = json.dumps({'ip': self.host, 'port': self.port, 'uid': self.uid})
                self.multicast_socket.sendto(message.encode(), (MULTICAST_GROUP, MULTICAST_PORT))
                time.sleep(DISCOVERY_INTERVAL)
            except Exception as e:
                print(f"Error sending multicast: {e}")

    def receive_multicast(self):
        while self.running:
            try:
                data, addr = self.receiver_socket.recvfrom(1024)
                message = json.loads(data.decode())
                peer = (message['ip'], message['port'])
                if peer not in self.peers and message['uid'] != self.uid:
                    self.peers.append(peer)
                    print(f"Discovered peer: {peer}")
            except Exception as e:
                print(f"Error receiving multicast: {e}")

    def accept_peers(self):
        while self.running:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_peer, args=(conn,), daemon=True).start()

    def handle_peer(self, conn):
        with conn:
            try:
                data = conn.recv(65536).decode()
                message = json.loads(data)
                response_data = None
                msg_type, msg_data = message["type"], message["data"]
                print("[*] Received Request", msg_type, msg_data)
                if msg_type == "request":
                    req_type = message["data"]["type"]
                    req_data = message["data"]["data"]
                    if req_type == "get_block" and req_data in self.user.blockchain:
                        block = self.user.blockchain[req_data]
                        response_data = block.to_dict()
                    response = json.dumps({"type": "response", "data": response_data})
                    conn.sendall(response.encode())
                elif msg_type == "add_user":
                    self.user.on_add_user(msg_data)
                elif msg_type == "req_send_money":
                    sender = msg_data.get("sender", None)
                    sender_balance = msg_data.get("sender_balance", None)
                    receiver = msg_data.get("receiver", None)
                    amount = msg_data.get("amount", None)
                    if receiver == self.uid:
                        if receiver is None or amount is None:
                            print("[*] DEBUG: Invalid Transaction To Verify")
                            return
                        receiver_balance = self.user.get_balance_info()
                        curr_idx = self.user.get_last_block().index
                        #transact = Transaction(sender, receiver, amount, sender_balance, receiver_balance, curr_idx)
                        # make sure patch works
                        transact = Transaction(amount, sender_balance, receiver_balance, curr_idx)
                        self.broadcast_data("transaction_verified", transact.to_dict())
                elif msg_type == "req_get_money":
                    sender = msg_data.get("sender", None)
                    receiver = msg_data.get("receiver", None)
                    receiver_balance = msg_data.get("sender_balance", None)
                    amount = msg_data.get("amount", None)
                    if sender == self.uid:
                        if receiver is None or amount is None:
                            print("[*] DEBUG: Invalid Transaction To Verify")
                            return
                        sender_balance = self.user.get_balance_info()
                        curr_idx = self.user.get_last_block().index
                        #transact = Transaction(sender, receiver, amount, sender_balance, receiver_balance, curr_idx)
                        transact = Transaction(amount, sender_balance, receiver_balance, curr_idx)
                        self.broadcast_data("transaction_verified", transact.to_dict())
                elif msg_type == "transaction_verified":
                    self.user.on_transact_verified(Transaction.from_dict(msg_data))
                elif msg_type == "create_block":
                    print("Im right shut up")
                    self.user.on_block_create_req(BlockRequest.from_dict(msg_data))
                    print("8\n\n\n\n\n")
            except Exception as e:
                print(f"Error handling peer: {e}")

    def broadcast_request(self, message_type, data, min_ans, interval, listener):
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
                    message = json.dumps({"type": "request", "data": {"type": message_type, "data": data}})
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

        for ip, port in self.peers:
            t = threading.Thread(target=request_from_peer, args=(ip, port), daemon=True)
            t.start()

        stop_event.wait(timeout=interval)
        listener(results)

    def request_most_likely(self, type, data, listener):
        def wrapper_listener(results):
            listener(most_common(results))
        self.broadcast_request(type, data, MIN_REQ_ANS, MIN_REQ_TIME, wrapper_listener)

    def sync_request_most_likely(self, type, data, timeout=30.0):
        result = [None]
        result_event = threading.Event()

        def on_res(res):
            result[0] = res
            result_event.set()

        self.request_most_likely(type, data, on_res)
        result_event.wait(timeout=timeout)
        return result[0]

    def get_block(self, block_hash, listener=None):
        inner_listener = (lambda result: listener(Block.from_dict(result)) if result is not None else None)
        return self.sync_request_most_likely("get_block", block_hash)

    def broadcast_data(self, type, data):
        def request_from_peer(ip, port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, port))
                    message = json.dumps({"type": type, "data": data})
                    s.sendall(message.encode())
            except Exception as e:
                print(f"Error requesting from {ip}:{port} - {e}")

        for ip, port in self.peers:
            t = threading.Thread(target=request_from_peer, args=(ip, port), daemon=True)
            t.start()

    def broadcast_BlockRequest(self, block_req):
        self.broadcast_data("create_block", block_req.to_dict())

    def broadcast_requestAdd(self):
        print("Sending request add")
        self.broadcast_data("add_user", self.public_key_str)

    def broadcast_verifySendTransactionRequest(self, sender, sender_balance, receiver, amount):
        self.broadcast_data("req_send_money", {"sender": sender, "sender_balance": sender_balance.to_dict(), "receiver": receiver, "amount": amount})

    def broadcast_verifyGetTransactionRequest(self, receiver, receiver_balance, sender, amount):
        self.broadcast_data("req_get_money", {"receiver": receiver, "receiver_balance": receiver_balance.to_dict(), "sender": sender, "amount": amount})

    def stop(self):
        self.running = False
        self.server.close()
        self.multicast_socket.close()
        self.receiver_socket.close()
