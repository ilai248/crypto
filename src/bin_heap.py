from hashlib import sha256

class virt_bin_heap:
    @staticmethod
    def hashes(data):
        return sha256(data.encode()).hexdigest()

    def __init__(self, uid, starting_brolist=[], n=0, roots=[]):
        self.n = n
        self.roots = roots
        self.brolist = starting_brolist
        self.diff = uid - len(starting_brolist)

    def insert(self, data):
        """roots is sorted s.t. roots[0] represents the biggest tree"""
        if len(self.roots) is 0:
            self.roots = [virt_bin_heap.hashes(str(data) + str(self.n))]
            n = 1
            return 0, []

        self.diff += 1
        if self.is_power_of2(self.diff):
            curr_root_power = self.first_pos(self.diff)
            while curr_root_power & n:  # curr root is in the heap.
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

    def valid(self, data, pos, bro_lst):
        h = virt_bin_heap.hashes(str(data) + str(pos))
        for b in bro_lst:
            h = virt_bin_heap.hashes(str(h) + str(b))
        
        return h in self.roots
