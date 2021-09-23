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
        """

        :param playbook_node: Playbook parsed node
        :param display: Display
        :param graph_format: the graph format to render. See https://graphviz.org/docs/outputs/
        :param graph_attr: Default graph attributes
        :param edge_attr: Default edge attributes
        """
        self.display = display
        self.playbook_node = playbook_node
        self.graphviz = GraphvizCustomDigraph(format=graph_format,
                                              graph_attr=graph_attr or GraphvizRenderer.DEFAULT_GRAPH_ATTR,
                                              edge_attr=edge_attr or GraphvizRenderer.DEFAULT_EDGE_ATTR)

    def _add_task(self, graph: GraphvizCustomDigraph, parent_node: Node, edge: EdgeNode, color: str, task_counter: int,
                  shape: str = "octagon"):
        """
        Add a task in the given graph
        :param graph:
        :param parent_node
        :param edge:
        :param color
        :param shape
        :return:
        """
        destination_node = edge.destination
        graph.node(destination_node.id, label=destination_node.name, shape=shape, id=destination_node.id,
                   tooltip=destination_node.name)
        edge_label = f"{task_counter} {edge.name}"
        graph.edge(parent_node.id, destination_node.id, label=edge_label, color=color, fontcolor=color, style="bold",
                   id=edge.id, tooltip=edge_label, labeltooltip=edge_label)

    def _convert_to_graphviz(self):
        """
        Convert playbook to graph viz graph
        :return:
        """
        # root node
        self.graphviz.node(self.playbook_node.name, style="dotted", id="root_node")

        for play_counter, play_edge in enumerate(self.playbook_node.plays, 1):
            # noinspection PyTypeChecker
            play = play_edge.destination  # type: PlayNode
            with self.graphviz.subgraph(name=play.name) as play_subgraph:
                color, play_font_color = get_play_colors(play)
                # play node
                play_tooltip = ",".join(play.hosts) if len(play.hosts) > 0 else play.name
                self.graphviz.node(play.id, id=play.id, label=play.name, style="filled", shape="box", color=color,
                                   fontcolor=play_font_color, tooltip=play_tooltip)
                # edge from root node to play
                playbook_to_play_label = f"{play_counter} {play_edge.name}"
                self.graphviz.edge(self.playbook_node.name, play.id, id=play_edge.id, style="bold",
                                   label=playbook_to_play_label, color=color, fontcolor=color,
                                   tooltip=playbook_to_play_label, labeltooltip=playbook_to_play_label)

                # pre_tasks
                for pre_task_counter, pre_task_edge in enumerate(play.pre_tasks, 1):
                    self._add_task(graph=play_subgraph, parent_node=play, edge=pre_task_edge, color=color,
                                   task_counter=pre_task_counter)

                # roles
                for role_counter, role_edge in enumerate(play.roles, 1):
                    # noinspection PyTypeChecker
                    role = role_edge.destination  # type: RoleNode
                    role_edge_label = f"{role_counter + len(play.pre_tasks)} {role_edge.name}"

                    with self.graphviz.subgraph(name=role.name, node_attr={}) as role_subgraph:
                        # from play to role
                        role_subgraph.node(role.id, id=role.id, label=f"[role] {role.name}", tooltip=role.name)

                        play_subgraph.edge(play.id, role.id, label=role_edge_label, color=color, fontcolor=color,
                                           style="bold", id=role_edge.id, tooltip=role_edge_label,
                                           labeltooltip=role_edge_label)

                        # role tasks
                        for role_task_counter, role_task_edge in enumerate(role.tasks, 1):
                            self._add_task(role_subgraph, role, role_task_edge, color, task_counter=role_task_counter)

                # tasks
                for task_counter, task_edge in enumerate(play.tasks, 1):
                    self._add_task(play_subgraph, play, task_edge, color,
                                   task_counter=len(play.pre_tasks) + len(play.roles) + task_counter)

                # post_tasks
                for post_task_counter, post_task_edge in enumerate(play.post_tasks, 1):
                    self._add_task(play_subgraph, play, post_task_edge, color,
                                   task_counter=len(play.pre_tasks) + len(play.roles) + len(
                                       play.tasks) + post_task_counter)

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
