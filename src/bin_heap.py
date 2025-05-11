from hashlib import sha256

        
def lsb(n):
    if n == 0:
        return None  # No '1' in the binary representation of 0
    position = 0
    while n & 1 == 0:
        n >>= 1
        position += 1
    return position

# Assume n is not 0.
def msb(n):
    position = 0
    while n > 1:
        position += 1
        n >>= 1
    return position

class virt_bin_heap:
    @staticmethod
    def hashes(data):
        return sha256(data.encode()).hexdigest()

    """
    We need to account for a starting brolist because maybe we merged a lot in the start.
    """
    def __init__(self, n=0, roots=[]):
        self.n = n
        self.roots = roots
        self.created = False
        self.brolist = None
        self.curr_root = None
        self.pos = None
        self.my_money = None

    # If we want to get the root after a change we need to input n after the change to the function.
    def root_bit_by_pos(self, pos):
        nodes_accounted = 0
        mask = 1 << msb(self.n)
        while nodes_accounted <= pos:
            nodes_accounted |= (mask & self.n)
            mask >>= 1
        return mask

    def is_root(self, root_mask_bit, n):
        return root_mask_bit & n
    
    def get_root(self, root_idx):
        return self.roots[-root_idx - 1]
    
    def set_root(self, root_idx, new_hash):
        self.roots[-root_idx - 1] = new_hash

    def root_idx_by_bit(self, root_bit):
        mask = 1 << msb(self.n)
        root_mask = 1 << root_bit
        count = 0
        while mask > root_mask:
            count += self.is_root(mask)
            mask >>= 1
        return count

    def insert(self, data):
        """roots is sorted s.t. roots[0] represents the biggest tree"""
        if len(self.roots) is 0:
            self.roots = [virt_bin_heap.hashes(str(data) + str(self.n))]
            self.n = 1
            return 0, []
        
        if self.n % 2 == 0:
            # Even number of trees, add a new tree
            self.roots.append(virt_bin_heap.hashes(str(data) + str(self.n)))
            self.n += 1
            return self.n - 1, []

        h = virt_bin_heap.hashes(str(data) + str(self.n))
        prev_lsb = lsb(self.n)
        new_lsb = lsb(self.n + 1)
        bro_lst = []

        linked = False
        for i in range(new_lsb - prev_lsb):
            # Merge with the root corrosponding to 'i'.
            if linked:
                self.bro_lst.append(self.roots[-1])
                self.curr_root += 1
            elif self.created and self.curr_root == i:
                self.bro_lst.append(h)
                linked = True
            h = virt_bin_heap.hashes(str(h) + str(self.roots[-1]))
            bro_lst.append(self.roots[-1])
            self.roots.pop()

        self.roots.append(h)
        self.n += 1
        return self.n - 1, bro_lst

    # Creates the *current* user. Assumes the created user is the last one inserted.
    def create(self, brolist, money):
        self.pos = self.n - 1
        self.brolist = brolist
        self.my_money = money
        self.curr_root = lsb(self.n)
        self.created = True

    def is_power_of2(self, num: int):
        return num == (1 << self.msb(num))

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
        root_idx = self.root_idx_by_bit(self.root_bit_by_pos(pos))
        root_hash = self.calc_hash(data, pos, bro_list)
        if self.created:
            if pos == self.pos:
                self.my_money = data
            if self.get_root(root_idx) in self.brolist:
                self.brolist[self.brolist.index(root_idx)] = root_hash
        self.set_root(root_idx, root_hash)

    def get_brolist(self):
        return self.brolist
