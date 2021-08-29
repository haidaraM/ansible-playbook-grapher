import os
from typing import Dict

from ansible.utils.display import Display
from graphviz import Digraph

from ansibleplaybookgrapher.graph import PlaybookNode, EdgeNode, Node, PlayNode, RoleNode
from ansibleplaybookgrapher.utils import clean_name, get_play_colors


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

    def __init__(self, playbook_node: 'PlaybookNode', display: Display, graph_format: str = "svg",
                 graph_attr: Dict = None, edge_attr: Dict = None):
        self.display = display
        self.playbook_node = playbook_node
        self.graphviz = GraphvizCustomDigraph(format=graph_format,
                                              graph_attr=graph_attr or GraphvizRenderer.DEFAULT_GRAPH_ATTR,
                                              edge_attr=edge_attr or GraphvizRenderer.DEFAULT_EDGE_ATTR)

    def _add_task(self, graph: GraphvizCustomDigraph, parent_node: Node, edge: EdgeNode, color: str,
                  shape: str = "octagon"):
        """
        Add a task in the given graph
        :param graph:
        :param edge:
        :param task:
        :return:
        """
        graph.node(edge.destination.id, label=edge.destination.label, shape=shape, id=edge.destination.id,
                   tooltip=edge.destination.label)
        graph.edge(parent_node.id, edge.destination.id, label=edge.label, color=color, fontcolor=color, style="bold",
                   id=edge.id)

    def _convert_to_graphviz(self):
        """
        Convert playbook to graph viz graph
        :return:
        """
        # root node
        self.graphviz.node(self.playbook_node.label, style="dotted", id="root_node")

        for play_edge in self.playbook_node.plays:
            # noinspection PyTypeChecker
            play = play_edge.destination  # type: PlayNode
            with self.graphviz.subgraph(name=play.label) as play_subgraph:
                color, play_font_color = get_play_colors(play)
                # play node
                play_tooltip = ",".join(play.hosts) if len(play.hosts) > 0 else play.label
                self.graphviz.node(play.id, id=play.id, label=play.label, style="filled", shape="box", color=color,
                                   fontcolor=play_font_color, tooltip=play_tooltip)
                # edge from root node to play
                self.graphviz.edge(self.playbook_node.label, play.id, id=play_edge.id, style="bold",
                                   label=play_edge.label, color=color, fontcolor=color)

                # pre_tasks
                for pre_task_edge in play.pre_tasks:
                    self._add_task(play_subgraph, play, pre_task_edge, color)

                # roles
                for role_edge in play.roles:
                    # noinspection PyTypeChecker
                    role = role_edge.destination  # type: RoleNode

                    with self.graphviz.subgraph(name=role.label, node_attr={}) as role_subgraph:
                        # from play to role
                        role_subgraph.node(role.id, id=role.id, label=role.label, tooltip=role.label)
                        play_subgraph.edge(play.id, role.id, label=role_edge.label, color=color, fontcolor=color,
                                           style="bold", id=role_edge.id)

                        # role tasks
                        for role_task_edge in role.tasks:
                            self._add_task(role_subgraph, role, role_task_edge, color)

                # tasks
                for task_edge in play.tasks:
                    self._add_task(play_subgraph, play, task_edge, color)

                # post_tasks
                for post_task_edge in play.post_tasks:
                    self._add_task(play_subgraph, play, post_task_edge, color)

    def render(self, output_filename: str, save_dot_file=False) -> str:
        """
        Render the graph
        :param output_filename: Output file name without '.svg' extension.
        :param save_dot_file: If true, the dot file will be saved when rendering the graph.
        :return: The rendered file path (output_filename.svg)
        """
        self._convert_to_graphviz()
        rendered_file_path = self.graphviz.render(cleanup=not save_dot_file, format="svg", filename=output_filename)

        if save_dot_file:
            # add .dot extension. The render doesn't add an extension
            final_name = output_filename + ".dot"
            os.rename(output_filename, final_name)
            self.display.display(f"Graphviz dot file has been exported to {final_name}")

        return rendered_file_path
