import pickle
import os
import warnings
from collections import defaultdict

from functools import lru_cache

from tqdm import tqdm

ID_ATTR = 'entity_id'

class Node:
    def __init__(self, name, base_class=None, attr=None):
        self.name = name
        self.base_class = base_class
        self.attr = {} if attr is None else dict(attr)

    def __repr__(self):
        return str(self.name)  # name should always be a string anyway, but just to be safe

    def repair(self):
        if self.base_class is None:
            replace = ['Lane', 'Road', 'Junction']
            for repl in replace:
                if repl in self.name:
                    self.base_class = repl.lower()
                    break

    def is_phantom(self):
        return 'PHANTOM' in self.attr and self.attr['PHANTOM']

    def get_id(self):
        id = None
        if ID_ATTR in self.attr:
            id = self.attr[ID_ATTR]
        return id if id is not None else self.name

    def is_road(self):
        for road_name in ['Lane', 'Road', 'Junction']:
            if road_name in self.name:
                return True


# class SGUnpickler(pickle.Unpickler):
#     def find_class(self, module, name):
#         if module == '__main__' and name == 'Node':
#             return Node
#         if module == 'carla_sgg.sgg_abstractor' and name == 'Node':
#             return Node
#         return super().find_class(module, name)


class SGUnpickler(pickle.Unpickler):
    def persistent_load(self, pid):
        if pid == 'please_ignore_me':
            return None
        else:
            return super().persistent_load(pid)

    def find_class(self, module, name):
        if module == '__main__' and name == 'Node':
            return Node
        if module == 'carla_sgg.sgg_abstractor' and name == 'Node':
            return Node
        return super().find_class(module, name)


class IgnoreWaypointPickler(pickle.Pickler):
    def reducer_override(self, obj):
        """Custom reducer for MyClass."""
        if getattr(obj, "__name__", None) == "Waypoint":
            return None
        else:
            # For any other object, fallback to usual reduction
            return NotImplemented

    def persistent_id(self, obj):
        # print(type(obj))
        if str(type(obj)) == "<class 'carla.libcarla.Waypoint'>":
            return 'please_ignore_me'
        else:
            return None  # default behavior


@lru_cache(maxsize=int(os.getenv('SG_CACHE_SIZE', default='128')))
def load_sg(sg_file):
    with open(sg_file, 'rb') as f:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sg = SGUnpickler(f).load()
            for node in sg.nodes:
                node.repair()
    return sg


def add_missing(sgs):
    node_map = defaultdict(list)
    # node_sets = []
    # for sg in sgs:
    #     node_set = set()
    #     for node in sg.nodes:
    #         node_set.add(node.get_id())
    #         node_map[node.get_id()].append(node)
    #     node_sets.append(node_set)
    # node_sets = [set([node.get_id() for node in sg.nodes]) for sg in sgs]
    # union = set.union(*node_sets)
    union = set()
    # make sure that all SGs that come later have isolated nodes for any entity that has been seen in the past.
    static_relationships = defaultdict(set)
    # for sg in tqdm(sgs, disabled=not print):
    for sg in sgs:
        node_set = set()
        for node in sg.nodes:
            node_map[node.get_id()].append(node)
            node_set.add(node.get_id())
        for (u, v, d) in sg.edges(data=True):
            if u.is_road() and v.is_road():
                uid = u.get_id()
                vid = v.get_id()
                static_relationships[uid].add((uid, vid, d['label']))
                static_relationships[vid].add((uid, vid, d['label']))
        need_to_add = union.difference(node_set)
        new_node_map = {}
        edges_to_add = set()
        for node_id in need_to_add:
            node = node_map[node_id][-1]
            new_node = Node(node.name, node.base_class, node.attr)
            # mark that this node doesn't actually exist
            new_node.attr['PHANTOM'] = True
            new_node_map[node_id] = new_node
            sg.add_node(new_node)
            edges_to_add.update(static_relationships[node_id])

        # for (u, v) in static_relationships:
        #     if u.get_id() in need_to_add or v.get_id() in need_to_add:
        for (uid, vid, data) in edges_to_add:
            # either get the new copy or the copy that is in the current graph
            u = new_node_map[uid] if uid in new_node_map else node_map[uid][-1]
            v = new_node_map[vid] if vid in new_node_map else node_map[vid][-1]
            sg.add_edge(u, v, label=data)
        union.update(node_set)

