import os
from abc import ABC
from collections import defaultdict
from typing import Dict, List

from graphviz import Digraph

from ansibleplaybookgrapher.utils import clean_name, generate_id, get_play_colors


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


class GraphvizRenderer:
    """
    Render the graph with graphviz
    """
    DEFAULT_EDGE_ATTR = {"sep": "10", "esep": "5"}
    DEFAULT_GRAPH_ATTR = {"ratio": "fill", "rankdir": "LR", "concentrate": "true", "ordering": "in"}

    def __init__(self, playbook_node: 'PlaybookNode', graph_format: str = "svg", graph_attr: Dict = None,
                 edge_attr: Dict = None):
        self.playbook_node = playbook_node
        self.graphviz = GraphvizCustomDigraph(format=graph_format,
                                              graph_attr=graph_attr or GraphvizRenderer.DEFAULT_GRAPH_ATTR,
                                              edge_attr=edge_attr or GraphvizRenderer.DEFAULT_EDGE_ATTR)

    def convert_to_graphviz(self):
        """
        Convert playbook to graph viz graph
        :return:
        """
        # root node
        self.graphviz.node(self.playbook_node.label, style="dotted", id="root_node")
        for play_edge in self.playbook_node.plays:

            play = play_edge.destination
            with self.graphviz.subgraph(name=play.label) as play_subgraph:
                color, play_font_color = get_play_colors(play)
                # play node
                # TODO: add hosts as tooltip
                self.graphviz.node(play.id, id=play.id, label=play.label, style="filled", shape="box", color=color,
                                   fontcolor=play_font_color)
                # edge from root node to play
                self.graphviz.edge(self.playbook_node.label, play.id, id=play_edge.id, style="bold",
                                   label=play_edge.label, color=color, fontcolor=color)

                # pre_tasks
                for pre_task_edge in play.pre_tasks:  # type: EdgeNode
                    # noinspection PyTypeChecker
                    pre_task = pre_task_edge.destination  # type: TaskNode
                    play_subgraph.node(pre_task.id, label=pre_task.label, shape="octagon", id=pre_task.id,
                                       tooltip=pre_task.label)
                    play_subgraph.edge(play.id, pre_task.id, label=pre_task_edge.label, color=color, fontcolor=color,
                                       style="bold", id=pre_task_edge.id)

                # roles
                for role_edge in play.roles:  # type: EdgeNode
                    # noinspection PyTypeChecker
                    role = role_edge.destination  # type: RoleNode

                    with self.graphviz.subgraph(name=role.label, node_attr={}) as role_subgraph:
                        # from play to role
                        role_subgraph.node(role.id, id=role.id, label=role.label, tooltip=role.label)
                        play_subgraph.edge(play.id, role.id, label=role_edge.label, color=color,
                                           fontcolor=color)

                        # role tasks
                        for role_task_edge in role.tasks:
                            role_task = role_task_edge.destination
                            role_subgraph.node(role_task.id, label=role_task.label, shape="octagon", id=role_task.id,
                                               tooltip=role_task.label)
                            role_subgraph.edge(role.id, role_task.id, label=role_task_edge.label, color=color,
                                               fontcolor=color, style="bold", id=role_task_edge.id)

                # tasks
                for task_edge in play.tasks:  # type: EdgeNode
                    # noinspection PyTypeChecker
                    task = task_edge.destination  # type: TaskNode
                    play_subgraph.node(task.id, label=task.label, shape="octagon", id=task.id, tooltip=task.label)
                    play_subgraph.edge(play.id, task.id, label=task_edge.label, color=color, fontcolor=color,
                                       style="bold", id=task_edge.id)

                # post_tasks
                for post_task_edge in play.post_tasks:  # type: EdgeNode
                    # noinspection PyTypeChecker
                    post_task = post_task_edge.destination  # type: TaskNode
                    play_subgraph.node(post_task.id, label=post_task.label, shape="octagon", id=post_task.id,
                                       tooltip=post_task.label)
                    play_subgraph.edge(play.id, post_task.id, label=post_task_edge.label, color=color, fontcolor=color,
                                       style="bold", id=post_task_edge.id)

    def render(self, output_filename: str, save_dot_file=False) -> str:
        """
        Render the graph
        :param output_filename: Output file name without '.svg' extension.
        :param save_dot_file: If true, the dot file will be saved when rendering the graph.
        :return: The rendered file path (output_filename.svg)
        """
        rendered_file_path = self.graphviz.render(cleanup=not save_dot_file, format="svg",
                                                  filename=output_filename)
        if save_dot_file:
            # add .dot extension. The render doesn't add an extension
            final_name = output_filename + ".dot"
            os.rename(output_filename, final_name)
            self.display.display(f"Graphviz dot file has been exported to {final_name}")

        return rendered_file_path


class Node(ABC):
    """
    A node in the graph
    """

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
    def plays(self) -> List['EdgeNode']:
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

    def __init__(self, node_label: str, node_id: str = None, hosts: List[str] = None):
        """
        :param node_label:
        :param node_id:
        :param hosts: List of hosts attached to the play
        """
        play_id = node_id or generate_id("play_")
        super().__init__(node_label, play_id)
        self.hosts = hosts or []

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

    def __init__(self, node_label: str, source: Node, destination: Node):
        super().__init__(node_label, generate_id("edge_"))
        self.source = source
        self.add_node("nodes", destination)

    def add_node(self, target_composition: str, node: Node):
        """
        Override the add_node. An edge node should only one linked node
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
        return self._compositions["nodes"][0]


class TaskNode(Node):
    def __init__(self, node_label: str, node_id: str = None):
        super().__init__(node_label, node_id or generate_id("task_"))


class RoleNode(CompositeNode):
    def __init__(self, node_label: str, node_id: str = None):
        super().__init__(node_label, node_id or generate_id("role_"))

    @property
    def tasks(self):
        return self._compositions["tasks"]
