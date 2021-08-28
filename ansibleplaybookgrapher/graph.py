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
    def __init__(self, node_label: str, node_id: str):
        self.label = node_label
        self.id = node_id

    def __str__(self):
        return f"{type(self).__name__}: {self.label} => {self.id}"

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class CompositeNode(Node):
    """
    A node that composed of multiple of nodes.
    """

    def __init__(self, node_label: str, node_id: str):
        super().__init__(node_label, node_id)
        # The dict will contain the different types of composition
        self._compositions = defaultdict(list)  # type: Dict[str, List]

    def add_node(self, target_composition: str, node: Node):
        """
        Add a node in the target composition
        :param target_composition: The name of the target composition
        :param node: The node to add in the given composition
        :return:
        """
        self._compositions[target_composition].append(node)

    def links_structure(self) -> Dict[Node, List[Node]]:
        """
        Return a representation of the composite node where each key of a dictionary is the node ID and the values is a
        list of linked nodes
        :return:
        """
        links = defaultdict(list)
        self._get_all_links(links)
        return links

    def _get_all_links(self, links: Dict[Node, List[Node]]):
        """
        Recursively get the node links
        :return:
        """

        for target, nodes in self._compositions.items():
            for node in nodes:
                if isinstance(node, CompositeNode):
                    node._get_all_links(links)
                links[self].append(node)


class PlaybookNode(CompositeNode):
    """
    A playbook is a list of play
    """

    def __init__(self, node_label: str, plays: List['PlayNode'] = None):
        super().__init__(node_label, generate_id())
        self._compositions['plays'] = plays or []

    @property
    def plays(self) -> List['PlayNode']:
        """
        Return the list of plays
        :return:
        """
        return self._compositions['plays']

    def add_play(self, play: 'PlayNode', edge_label: str, **kwargs) -> 'EdgeNode':
        """
        Add a play to the playbook
        :param play:
        :param edge_label:
        :return:
        """
        edge = EdgeNode(edge_label, self, play, **kwargs)
        self._compositions['plays'].append(edge)
        return edge


class PlayNode(CompositeNode):
    """
    A play is a list of:
     - pre_tasks
     - roles
     - tasks
     - post_tasks
    """

    def __init__(self, node_label: str, node_id: str = None):
        play_id = node_id or generate_id("play_")
        super().__init__(node_label, play_id)

    @property
    def roles(self):
        return self._compositions["roles"]

    @property
    def pre_tasks(self):
        return self._compositions["pre_tasks"]

    @property
    def post_tasks(self):
        return self._compositions["post_tasks"]

    @property
    def tasks(self):
        return self._compositions["tasks"]


class EdgeNode(CompositeNode):
    """
    An edge between two nodes. It's a special case of composite node with only one composition with one element
    """

    def __init__(self, node_label: str, source: Node, destination: Node, **kwargs):
        super().__init__(node_label, generate_id("edge_"))
        self.source = source
        self.add_node("nodes", destination)

    @property
    def nodes(self):
        return self._compositions["nodes"]


class TaskNode(Node):
    def __init__(self, node_label: str, node_id: str = None):
        super().__init__(node_label, node_id or generate_id("task_"))


class RoleNode(CompositeNode):
    def __init__(self, node_label: str, node_id: str = None):
        super().__init__(node_label, node_id or generate_id("role_"))

    @property
    def tasks(self):
        return self._compositions["tasks"]
