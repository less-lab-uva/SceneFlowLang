import networkx as nx
import re
import SG_Utils as utils
import typing
from functools import partial

from SymbolicEntity import Entity, ConcreteEntity, SymbolicEntity
from SymbolicProperty import UnboundEntityError

node_set_type = typing.Union[set, str, SymbolicEntity]


def parse_node_set(node_set: node_set_type, sg: nx.DiGraph,
                   entity_mapping: typing.Dict[SymbolicEntity, ConcreteEntity]) -> set:
    """ Parse node_set if it is a string.
    :param node_set: Set of nodes. It can be a set of networkx nodes
        or a string. The string must be either "Ego" (Set containing the Ego
        car node) or "G" (Set containing all nodes in Graph).
    :param sg: Networkx Directed Scene Graph.
    :param entity_mapping: Dictionary mapping the symbolic entities to concrete ones for evaluation
    :return: Set of nodes.
    """
    assert (isinstance(node_set, set) or isinstance(node_set, str) or
            isinstance(node_set, SymbolicEntity)), f"Invalid \
        node_set: {node_set}. It must be either a set of networkx nodes, a string, or an Entity."
    if isinstance(node_set, str):
        assert node_set in ["Ego", "G"], f"Invalid node_set string: {node_set}\
            . It must be either 'Ego' or 'G'."
        new_node_set = set()
        if node_set == "Ego":
            for node in sg.nodes:
                if node.name == "ego":
                    new_node_set.add(node)
                    break
        elif node_set == "G":
            for node in sg.nodes:
                new_node_set.add(node)
        return new_node_set
    elif isinstance(node_set, SymbolicEntity):
        return entity_mapping[node_set].get_node(sg)
    else:
        return node_set


def filterByAttr(
        node_set: node_set_type,
        attr: str,
        filter: typing.Union[str, typing.Callable[[float], bool]],
        sg: nx.DiGraph,
        entity_mapping: typing.Dict[SymbolicEntity, ConcreteEntity]) -> set:
    """ Filter a set of nodes by attribute value.
    :param node_set: Set of nodes to filter. It can be a set of networkx nodes
        or a string. The string must be either "Ego" (Set containing the Ego
        car node) or "G" (Set containing all nodes in Graph).
    :param attr: Attribute name to filter by. String representing the name of
        the attribute to filter by, e.g. "name".
    :param filter: Filter to apply to attribute values. It can be a string
        representing a regular expression that filters the node attribute,
        e.g. "Lane*". Or it can be a comparisson function for numeric
        attributes, e.g. greater_than(1.5).
    :param sg: Networkx Directed Scene Graph.
    :param entity_mapping: Dictionary mapping the symbolic entities to concrete ones for evaluation
    :return: Set of nodes with the given attribute values.
    """
    v = validate_sets(node_set)
    if v is not None:
        return v
    node_set = parse_node_set(node_set, sg, entity_mapping)
    assert isinstance(node_set, set) or isinstance(node_set, str), f"Invalid \
        node_set: {node_set}. It must be either a set of networkx nodes or a \
        string."
    assert isinstance(filter, str) or callable(filter), f"Invalid filter: \
        {filter}. It must be either a string or a function."
    new_node_set = set()
    for node in node_set:
        if attr != "name" and attr != "base_class":
            node_attr = node.attr[attr] if attr in node.attr else None
        else:
            node_attr = getattr(node, attr)
        if isinstance(filter, str):
            if re.search(filter, node_attr):
                new_node_set.add(node)
        else:
            if filter(node_attr):
                new_node_set.add(node)
    return new_node_set


def relSet(node_set: node_set_type, rel: str, sg: nx.DiGraph,
           entity_mapping: typing.Dict[SymbolicEntity, ConcreteEntity],
           edge_type: str = "outgoing",) -> set:
    """ Get the set of nodes with a given relationship
    :param node_set: Set of nodes to filter. It can be a set of networkx nodes
        or a string. The string must be either "Ego" (Set containing the Ego
        car node) or "G" (Set containing all nodes in Graph).
    :param rel: Relationship to filter by. String representing the name of
        the relationship to filter by, e.g. "isIn".
    :param edge_type: incoming or outgoing edges. Default: outgoing.
    :param sg: Networkx Directed Scene Graph.
    :param entity_mapping: Dictionary mapping the symbolic entities to concrete ones for evaluation
    :return: Set of nodes with the given relationship.
    """
    v = validate_sets(node_set)
    if v is not None:
        return v
    node_set = parse_node_set(node_set, sg, entity_mapping)
    assert edge_type in ["incoming", "outgoing"], f"Invalid edge_type: \
        {edge_type}. It must be either 'incoming' or 'outgoing'. Default: \
        outgoing."
    new_node_set = set()
    if edge_type == "outgoing":
        get_edges = partial(sg.out_edges, data="label")
    else:
        get_edges = partial(sg.in_edges, data="label")
    for node in node_set:
        for src, dst, edge in get_edges(node):
            if rel == edge:
                if edge_type == "outgoing":
                    new_node_set.add(dst)
                else:
                    new_node_set.add(src)
    return new_node_set


def validate_sets(s1, s2=None):
    unbounds = []
    for s in [s1, s2]:
        if type(s) == UnboundEntityError:
            unbounds.extend(s.entities)
        if type(s) == set:
            for node in s:
                if type(node) == UnboundEntityError:
                    unbounds.extend(node.entities)
    if len(unbounds) > 0:
        return UnboundEntityError(unbounds)
    else:
        return None

def union(s1: set, s2: set) -> set:
    v = validate_sets(s1, s2)
    if v is not None:
        return v
    return s1.union(s2)


def intersection(s1: set, s2: set) -> set:
    v = validate_sets(s1, s2)
    if v is not None:
        return v
    return s1.intersection(s2)


def symmetric_difference(s1: set, s2: set) -> set:
    v = validate_sets(s1, s2)
    if v is not None:
        return v
    return s1.symmetric_difference(s2)


def difference(s1: set, s2: set) -> set:
    v = validate_sets(s1, s2)
    if v is not None:
        return v
    return s1.difference(s2)


def size(s: set) -> int:
    v = validate_sets(s)
    if v is not None:
        return v
    return len(s)


def lt(a, b):
    v = validate_sets(a, b)
    if v is not None:
        return v
    return a < b


def gt(a, b):
    v = validate_sets(a, b)
    if v is not None:
        return v
    return a > b


def le(a, b):
    v = validate_sets(a, b)
    if v is not None:
        return v
    return a <= b


def ge(a, b):
    v = validate_sets(a, b)
    if v is not None:
        return v
    return a >= b


def eq(a, b):
    v = validate_sets(a, b)
    if v is not None:
        return v
    return a == b


def ne(a, b):
    v = validate_sets(a, b)
    if v is not None:
        return v
    return a != b


def logic_or(a, b):
    a_bad = validate_sets(a)
    b_bad = validate_sets(b)
    # if we have a value for a and b is bad, then try short-circuit around b
    # if a is True, then the and will be True anyway
    if a_bad is None and b_bad is not None:
        if a:
            return True
    # if we have a value for b and a is bad, then try short-circuit around a
    # if b is True, then the and will be True anyway
    if b_bad is None and a_bad is not None:
        if b:
            return True
    v = validate_sets(a, b)
    if v is not None:
        return v
    return a or b


def logic_and(a, b):
    a_bad = validate_sets(a)
    b_bad = validate_sets(b)
    # if we have a value for a and b is bad, then try short-circuit around b
    # if a is False, then the and will be false anyway
    if a_bad is None and b_bad is not None:
        if not a:
            return False
    # if we have a value for b and a is bad, then try short-circuit around a
    # if b is False, then the and will be false anyway
    if b_bad is None and a_bad is not None:
        if not b:
            return False
    v = validate_sets(a, b)
    if v is not None:
        return v
    return a and b

def logic_implies(a, b):
    # a -> b is equivalent to ~a | b
    return logic_or(logic_not(a), b)

def logic_xor(a, b):
    # v = validate_sets(a, b)
    # if v is not None:
    #     return v
    # return a ^ b
    # a ^ b is equivalent to (~a & b) | (a & ~b)
    return logic_or(logic_and(logic_not(a), b), logic_and(a, logic_not(b)))


def logic_not(a):
    v = validate_sets(a)
    if v is not None:
        return v
    return not a


def ite(a, b, c):
    v = validate_sets(a)
    if v is not None:
        return v
    return b if a else c


def defined(a):
    # this gets intercepted dynamically at runtime to compute if the variable is defined then
    return False


def boolean_equals(a, b):
    return logic_not(logic_xor(a, b))
    # return partial(logic_not, partial(logic_xor, a, b))


def main():
    # sg = utils.load_sg("./test_data/13_frame_381.rsv")
    # filterByAttr("Ego", "name", "Lane", sg)
    # filterByAttr("Ego", "name", partial(lt, b=5), sg)
    sg = utils.load_sg('./new_rsv/0.pkl')
    filterByAttr("Ego", "ego_control_carla_throttle", partial(lt, b=5), sg)
    # relSet("Ego", "isIn", sg)


if __name__ == '__main__':
    main()
