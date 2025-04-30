from datetime import date as curr_date
from typing import List, Tuple
from hashlib import sha256

# TODO: Save verfifiers and add cryptographic system to verify the transaction and the money exists.
# * Maybe utilize account-based model or UTXO.
class Transaction:
    from_uid: int
    to_uid: int
    amount: int
    date: any
    def __init__(self, from_uid: int, to_uid: int, amount: int):
        self.from_uid = from_uid
        self.to_uid = to_uid
        self.amount = amount
        self.date = curr_date.today()

    def __str__(self) -> str:
        return f"Transaction({self.from_uid}, {self.to_uid}, {self.amount}, {self.date})"


class Block:
    transactions: List[Transaction]
    prev_hash: bytes
    def __init__(self, prev_hash: bytes=b'\x00' * 32):
        self.transactions = []
        self.prev_hash = prev_hash
    
    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

    def to_bytes(self) -> bytes:
        return (str(self.transactions) + str(self.prev_hash)).encode()

    def hash(self) -> bytes:
        return sha256(self.to_bytes()).digest()
    
    def __str__(self):
        transactions_str = ', '.join(str(tx) for tx in self.transactions)
        return f"Block([{transactions_str}], prev_hash={self.prev_hash})"

# TODO: Remember the longst chaing or something like the chain with the highest stake.
# * Maybe try to add strong-finality.
class BlockNode:
    block: Block
    nexts: List['BlockNode']
    height: int
    def __init__(self, block: Block):
        self.block = block
        self.nexts = []
        self.height = 0

    def add_next(self, block_node: 'BlockNode'):
        self.nexts.append(block_node)
        self.calc_height()
    
    def calc_height(self):
        self.height = 1 + max(node.height for node in self.nexts) if len(self.nexts) else 0
    
    def remove_shorter_nexts(self, min_diff_to_remove: int):
        max_height = max(node.height for node in self.nexts)
        self.nexts = [node for node in self.nexts if max_height - node.height < min_diff_to_remove]

    def __str__(self):
        return str(self.block)

class BlockChain:
    """
    A class representing a blockchain, which is a narrow tree of blocks.
    We assume we have a linear number of blocks in the tree, when 'n' is the longest chain length.
    At the end of each time interval we clean the tree of blocks in shorter branches.
    """
    head: BlockNode
    def __init__(self):
        self.head = self.gen_starting_block()

    def gen_starting_block(self) -> Block:
        return BlockNode(Block())
    
    def add_block_helper(self, block: Block, starting_node: BlockNode) -> bool:
        if block.prev_hash == starting_node.block.hash():
            starting_node.add_next(BlockNode(block))
            return True
        for next_node in starting_node.nexts:
            if self.add_block_helper(block, next_node):
                starting_node.calc_height()
                return True
        return False

    def add_block(self, block: Block):
        self.add_block_helper(block, self.head)
