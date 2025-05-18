from blockchain__impl import BlockchainUser
from bin_heap import virt_bin_heap
import time
from pprint import pprint

def start_node():
    money_heap = virt_bin_heap(0, [])
    money_heap.create([], money=50, pos=0)
    user = BlockchainUser(5000, 0, money_heap=money_heap)
    
    # Create genesis block
    block_req = user.create_blockrequest(user.interval_time(0), user.interval_time(1))
    if block_req == None:
        print("Failed to create starting block.")
        exit(1)
    print("Starting block created:")
    pprint(block_req.to_dict())
    while True:
        time.sleep(5)
        user.gossip.broadcast_BlockRequest(block_req)

if __name__ == "__main__":
    start_node()
