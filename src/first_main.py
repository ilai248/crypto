from blockchain__impl import BlockchainUser
from bin_heap import virt_bin_heap
import time

def start_node():
    money_heap = virt_bin_heap(0, [])
    money_heap.create([], money=50)
    user = BlockchainUser(5000, 0, money_heap=money_heap)
    
    # Create genesis block
    while True:
        user.create_blockrequest(user.interval_time(0), user.interval_time(1))
        time.sleep(5)

if __name__ == "__main__":
    start_node()
