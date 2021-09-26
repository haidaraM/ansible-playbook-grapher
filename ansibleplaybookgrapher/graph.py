from collections import defaultdict
from typing import Dict, List

from ansibleplaybookgrapher.utils import generate_id


class Node:
    """
    A node in the graph. Everything of the final graph is a node: playbook, plays, edges, tasks and roles.
    """

    def __init__(self, node_name: str, node_id: str):
        self.name = node_name
        self.id = node_id

    def __str__(self):
        return f"{type(self).__name__}: name='{self.name}',id='{self.id}'"

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class CompositeNode(Node):
    """
    A node that composed of multiple of nodes.
    """

    def __init__(self, node_name: str, node_id: str, supported_compositions: List[str] = None):
        """

        :param node_name:
        :param node_id:
        """
        super().__init__(node_name, node_id)
        self._supported_compositions = supported_compositions or []
        # The dict will contain the different types of composition.
        self._compositions = defaultdict(list)  # type: Dict[str, List]

    @property
    def total_length(self) -> int:
        """
        Return the total length of elements in this composite node
        :return:
        """
        return sum([len(val) for val in self._compositions.values()])

    def add_node(self, target_composition: str, node: Node):
        """
        Add a node in the target composition
        :param target_composition: The name of the target composition
        :param node: The node to add in the given composition
        :return:
        """
        if target_composition not in self._supported_compositions:
            raise Exception(
                f"The target composition '{target_composition}' is unknown. Supported are: {self._supported_compositions}")
        self._compositions[target_composition].append(node)

    def links_structure(self) -> Dict[Node, List[Node]]:
        """
        Return a representation of the composite node where each key of the dictionary is the node ID and the values is
        a list of the linked nodes
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

    def __init__(self, node_name: str, plays: List['PlayNode'] = None, node_id: str = None):
        super().__init__(node_name, node_id or generate_id("playbook_"), ["plays"])
        self._compositions['plays'] = plays or []

    @property
    def plays(self) -> List['EdgeNode']:
        """
        Return the list of plays
        :return:
        """
        return self._compositions['plays']

    def add_play(self, play: 'PlayNode', edge_name: str, **kwargs) -> 'EdgeNode':
        """
        Add a play to the playbook
        :param play:
        :param edge_name:
        :return:
        """
        edge = EdgeNode(self, play, edge_name)
        self.add_node("plays", edge)
        return edge


class PlayNode(CompositeNode):
    """
    A play is a list of:
     - pre_tasks
     - roles
     - tasks
     - post_tasks
    """

    def __init__(self, node_name: str, hosts: List[str] = None, node_id: str = None):
        """
        :param node_name:
        :param node_id:
        :param hosts: List of hosts attached to the play
        """
        super().__init__(node_name, node_id or generate_id("play_"), ["pre_tasks", "roles", "tasks", "post_tasks"])
        self.hosts = hosts or []

    @property
    def roles(self) -> List['EdgeNode']:
        return self._compositions["roles"]

    @property
    def pre_tasks(self) -> List['EdgeNode']:
        return self._compositions["pre_tasks"]

    @property
    def post_tasks(self) -> List['EdgeNode']:
        return self._compositions["post_tasks"]

    @property
    def tasks(self) -> List['EdgeNode']:
        return self._compositions["tasks"]


class BlockNode(CompositeNode):
    """
    A block node: https://docs.ansible.com/ansible/latest/user_guide/playbooks_blocks.html
    """

    def __init__(self, node_name: str, node_id: str = None):
        super().__init__(node_name, node_id or generate_id("block_"), ["tasks"])

    @property
    def tasks(self) -> List['EdgeNode']:
        """
        The tasks attached to this block
        :return:
        """
        return self._compositions['tasks']


class EdgeNode(CompositeNode):
    """
    An edge between two nodes. It's a special case of composite node with only one composition with one element
    """

    def __init__(self, source: Node, destination: Node, node_name: str = "", node_id: str = None):
        """

        :param node_name: The edge name
        :param source: The edge source node
        :param destination: The edge destination node
        :param node_id: The edge id
        """
        super().__init__(node_name, node_id or generate_id("edge_"), ["destination"])
        self.source = source
        self.add_node("destination", destination)

    def add_node(self, target_composition: str, node: Node):
        """
        Override the add_node. An edge node should only have one linked node
        :param target_composition: 
        :param node: 
        :return: 
        """
        current_nodes = self._compositions[target_composition]
        if len(current_nodes) == 1:
            raise Exception("An EdgeNode should have at most one linked node")
        return super(EdgeNode, self).add_node(target_composition, node)

    @property
    def destination(self) -> Node:
        """
        Return the destination of the edge
        :return:
        """
        return self._compositions["destination"][0]


class TaskNode(Node):
    """
    A task node. Can be pre_task, task or post_task
    """

    def __init__(self, node_name: str, node_id: str = None):
        super().__init__(node_name, node_id or generate_id("task_"))


class RoleNode(CompositeNode):
    """
    A role node. A role is a composition of tasks
    """

    def __init__(self, node_name: str, node_id: str = None):
        super().__init__(node_name, node_id or generate_id("role_"), ["tasks"])

    @property
    def tasks(self):
        return self._compositions["tasks"]
