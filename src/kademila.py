import random
import hashlib


class Kademila:
    def __init__(self, k: int):
        self.k = k
        self.ID_BITS = 256

    @staticmethod
    def hash(value: str) -> int:
        return int(hashlib.sha1(value.encode()).hexdigest(), 16)

    @staticmethod
    def distance(a: int, b: int) -> int:
        return a ^ b


class Node(Kademila):
    def __init__(self, node_id: int, k: int):
        super().__init__(k)
        self.node_id = node_id
        self.routing_table = [[] for _ in range(self.ID_BITS)]

    def bucket_index(self, other_id: int) -> int:
        dist = self.distance(self.node_id, other_id)
        if dist == 0:
            return 0
        return dist.bit_length() - 1

    def add_contact(self, other_node):
        index = self.bucket_index(other_node.node_id)
        bucket = self.routing_table[index]
        if other_node not in bucket:
            if len(bucket) >= self.k:
                # TODO: decide if this is good
                bucket.pop(random.randrange(len(bucket)))
            bucket.append(other_node)

    def find_closest_nodes(self, target_id: int, count):
        nodes = []
        for bucket in self.routing_table:
            nodes.extend(bucket)

        nodes = list(set(nodes))
        nodes.sort(key=lambda node: self.distance(node.node_id, target_id))
        return nodes[:count]

    def lookup(self, target_id: int):
        nodes = self.routing_table[1]
        for bucket in self.routing_table[2:]:
            nodes.append(random.choice(bucket))

        return nodes
