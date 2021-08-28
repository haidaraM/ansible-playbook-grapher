from abc import ABC
from collections import defaultdict
from typing import Dict, List

from graphviz import Digraph

from ansibleplaybookgrapher.utils import clean_name, generate_id


class GraphvizCustomDigraph(Digraph):
    """
    Custom digraph to avoid quoting issue with node names. Nothing special here except I put some double quotes around
    the node and edge names and override some methods.
    """
    _head = "digraph \"%s\"{"
    _edge = "\t\"%s\" -> \"%s\"%s"
    _node = "\t\"%s\"%s"
    _subgraph = "subgraph \"%s\"{"
    _quote = staticmethod(clean_name)
    _quote_edge = staticmethod(clean_name)


class Node(ABC):
    def __init__(self, node_name: str, node_id: str = None):
        self.name = node_name
        self.id = node_id or generate_id()

    def __str__(self):
        return f"{type(self)}: {self.name}:{self.id}"

    def __eq__(self, other: 'Node'):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class PlaybookNode(Node):
    def __init__(self, node_name: str):
        super().__init__(node_name)


class PlayNode(Node):
    def __init__(self, node_name: str, node_id: str = None):
        play_id = node_id or generate_id("play_")
        super().__init__(node_name, play_id)


class EdgeNode(Node):
    def __init__(self, node_name: str, node_id: str = None):
        edge_id = node_id or generate_id("edge_")
        super().__init__(node_name, edge_id)


class TaskNode(Node):
    def __init__(self, node_name: str, node_id: str = None):
        super().__init__(node_name, node_id)


class RoleNode(Node):
    def __init__(self, node_name: str, node_id: str = None):
        role_id = node_id or generate_id("role_")
        super().__init__(node_name, role_id)


class PlaybookGraph:
    """
    This a directed graph representing the parsed playbook
    """

    def __init__(self):
        self._graph = defaultdict(list)  # type: Dict[Node, List[Node]]

    def add_connection(self, source: Node, destination: Node, edge: EdgeNode = None):
        if edge is None:
            edge = EdgeNode("")
        self._graph[source].append(edge)
        self._graph[edge].append(destination)

    def items(self):
        return self._graph.items()
