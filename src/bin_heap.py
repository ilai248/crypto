from hashlib import sha256

class virt_bin_heap:
    @staticmethod
    def hashes(data):
        return sha256(data.encode()).hexdigest()

    """
    We need to account for a starting brolist because maybe we merged a lot in the start.
    """
    def __init__(self, uid, start_money, starting_brolist=[], n=0, roots=[]):
        self.n = n
        self.roots = roots
        self.brolist = starting_brolist
        self.diff = uid - len(starting_brolist) # TODO: Fix
        self.pos = 
        self.my_money = start_money

    # If we want to get the root after a change we need to input n after the change to the function.
    def get_root_of_pos(self, pos, n):
        return self.first_pos(n - pos)
    
    def root_in_n(self, root_idx, n):
        return root_idx & n
    
    def get_root(self, root_idx):
        return self.roots[-root_idx - 1]
    
    def set_root(self, root_idx, new_hash):
        self.roots[-root_idx - 1] = new_hash

    def insert(self, data):
        """roots is sorted s.t. roots[0] represents the biggest tree"""
        if len(self.roots) is 0:
            self.roots = [virt_bin_heap.hashes(str(data) + str(self.n))]
            n = 1
            return 0, []

        """
        If the diff will become a power of 2, that means we will be linked.
        Basically, it means that the first link will be with a tree created by the given node
        and the rest with the roots (at the index that corrosponds to the power of 2 we'll become).
        TODO: FIX.
        """
        self.diff += 1
        if self.is_power_of2(self.diff):
            curr_root_power = self.get_root_of_pos(self.diff)
            while self.root_in_n(curr_root_power, n):  # curr root is in the heap. TODO: Maybe should be n+1?
                self.brolist.append(self.roots[curr_root_power])
                self.diff <<= 1
        
        if self.n % 2 == 0:
            # Even number of trees, add a new tree
            self.roots.append(virt_bin_heap.hashes(str(data) + str(self.n)))
            self.n += 1
            return self.n - 1, []

        h = virt_bin_heap.hashes(str(data) + str(self.n))
        p1 = self.first_pos(self.n)
        p2 = self.first_pos(self.n + 1)
        bro_lst = []

        for i in range(p2 - p1):
            h = virt_bin_heap.hashes(str(h) + str(self.roots[-1]))
            bro_lst.append(self.roots[-1])
            self.roots.pop()

        self.roots.append(h)
        self.n += 1
        return self.n - 1, bro_lst
        
    def first_pos(self, n):
        if n == 0:
            return None  # No '1' in the binary representation of 0
        position = 0
        while n & 1 == 0:
            n >>= 1
            position += 1
        return position

    def is_power_of2(self, num: int):
        return num == (1 << self.first_pos(num))

    def calc_hash(self, data, pos, bro_list):
        h = virt_bin_heap.hashes(str(data) + str(pos))
        for b in bro_list:
            h = virt_bin_heap.hashes(str(h) + str(b))
        return h

    def valid(self, data, pos, bro_lst):
        h = virt_bin_heap.hashes(str(data) + str(pos))
        for b in bro_lst:
            h = virt_bin_heap.hashes(str(h) + str(b))
        return h in self.roots
    
    def change_data(self, data, pos, bro_list):
        if pos == self.
        root_idx = self.get_root_of_pos(pos)
        self.set_root(root_idx, self.calc_hash(data, pos, bro_list))

    def get_brolist(self):
        return self.brolist
