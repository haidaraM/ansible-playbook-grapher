import os
from typing import Dict

from ansible.utils.display import Display
from graphviz import Digraph

from ansibleplaybookgrapher.graph import PlaybookNode, EdgeNode, PlayNode, RoleNode, BlockNode
from ansibleplaybookgrapher.utils import get_play_colors


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
        self.digraph = Digraph(format=graph_format,
                               graph_attr=graph_attr or GraphvizRenderer.DEFAULT_GRAPH_ATTR,
                               edge_attr=edge_attr or GraphvizRenderer.DEFAULT_EDGE_ATTR)

    def render_node(self, graph: Digraph, edge: EdgeNode, color: str, node_counter: int,
                    shape: str = "octagon", **kwargs):
        """
        Render a generic node in the graph
        :param graph: The graph to render the node to
        :param edge: The edge from a node to the Node
        :param color: The color to apply
        :param node_counter: The counter for this node
        :param shape: the default shape of the node
        :return:
        """
        destination_node = edge.destination
        source_node = edge.source
        node_label_prefix = kwargs.get("node_label_prefix", "")

        if isinstance(destination_node, BlockNode):
            self.render_block(graph, node_counter, edge, color)
        elif isinstance(destination_node, RoleNode):
            self.render_role(graph, node_counter, edge, color)
        else:
            edge_label = f"{node_counter} {edge.name}"
            graph.node(destination_node.id, label=node_label_prefix + destination_node.name, shape=shape,
                       id=destination_node.id, tooltip=destination_node.name, color=color)
            graph.edge(source_node.id, destination_node.id, label=edge_label, color=color, fontcolor=color, id=edge.id,
                       tooltip=edge_label, labeltooltip=edge_label)

    def render_block(self, graph: Digraph, edge_counter: int, edge: EdgeNode, color: str, label_prefix="", **kwargs):
        """
        Render a block in the graph.
        A BlockNode is a special node: a cluster is created instead of a normal node.
        :param graph: The graph to render the block into
        :param edge_counter: The counter for this edge in the graph
        :param edge: The edge from a node to the BlockNode
        :param color: The color to apply
        :param kwargs:
        :param label_prefix: A prefix to add to the node label
        :return:
        """
        # noinspection PyTypeChecker
        destination_node = edge.destination  # type: BlockNode
        edge_label = f"{edge_counter}"

        # BlockNode is a special node: a cluster is created instead of a normal node
        with graph.subgraph(name=f"cluster_{destination_node.id}") as block_subgraph:
            block_subgraph.node(destination_node.id, label=f"[block] {destination_node.name}", shape="box",
                                id=destination_node.id, tooltip=destination_node.name, color=color,
                                labeltooltip=destination_node.name)
            graph.edge(edge.source.id, destination_node.id, label=edge_label, color=color, fontcolor=color,
                       tooltip=edge_label, id=edge.id, labeltooltip=edge_label)

            # The reverse here is a little hack due to how graphviz render nodes inside a cluster by reversing them.
            #  Don't really know why for the moment neither if there is an attribute to change that.
            for b_counter, task_edge_node in enumerate(reversed(destination_node.tasks)):
                self.render_node(block_subgraph, task_edge_node, color, len(destination_node.tasks) - b_counter)

    def render_role(self, graph: Digraph, edge_counter: int, edge: EdgeNode, color: str, **kwargs):
        """
        Render a role in the graph
        :param graph: The graph to render the role into
        :param edge_counter: The counter for this edge in the graph
        :param edge: The edge from a node to the RoleNode
        :param color: The color to apply
        :param kwargs:
        :return:
        """
        # noinspection PyTypeChecker
        role = edge.destination  # type: RoleNode
        role_edge_label = f"{edge_counter} {edge.name}"

        with self.digraph.subgraph(name=role.name, node_attr={}) as role_subgraph:
            role_subgraph.node(role.id, id=role.id, label=f"[role] {role.name}", tooltip=role.name, color=color)
            # from parent to role
            graph.edge(edge.source.id, role.id, label=role_edge_label, color=color, fontcolor=color, id=edge.id,
                       tooltip=role_edge_label, labeltooltip=role_edge_label)

            # role tasks
            for role_task_counter, role_task_edge in enumerate(role.tasks, 1):
                self.render_node(role_subgraph, role_task_edge, color, node_counter=role_task_counter)

    def _convert_to_graphviz(self):
        """
        Convert playbook to graph viz graph
        :return:
        """
        # root node
        self.digraph.node(self.playbook_node.name, style="dotted", id="root_node")

        for play_counter, play_edge in enumerate(self.playbook_node.plays, 1):
            # noinspection PyTypeChecker
            play = play_edge.destination  # type: PlayNode
            with self.digraph.subgraph(name=play.name) as play_subgraph:
                color, play_font_color = get_play_colors(play)
                # play node
                play_tooltip = ",".join(play.hosts) if len(play.hosts) > 0 else play.name
                self.digraph.node(play.id, id=play.id, label=play.name, style="filled", shape="box", color=color,
                                  fontcolor=play_font_color, tooltip=play_tooltip)
                # edge from root node to play
                playbook_to_play_label = f"{play_counter} {play_edge.name}"
                self.digraph.edge(self.playbook_node.name, play.id, id=play_edge.id, label=playbook_to_play_label,
                                  color=color, fontcolor=color, tooltip=playbook_to_play_label,
                                  labeltooltip=playbook_to_play_label)

                # pre_tasks
                for pre_task_counter, pre_task_edge in enumerate(play.pre_tasks, 1):
                    self.render_node(play_subgraph, pre_task_edge, color, node_counter=pre_task_counter,
                                     node_label_prefix="[pre_task] ")

                # roles
                for role_counter, role_edge in enumerate(play.roles, 1):
                    self.render_role(self.digraph, role_counter + len(play.pre_tasks), role_edge, color)

                # tasks
                for task_counter, task_edge in enumerate(play.tasks, 1):
                    self.render_node(play_subgraph, task_edge, color,
                                     node_counter=len(play.pre_tasks) + len(play.roles) + task_counter,
                                     node_label_prefix="[task] ")

                # post_tasks
                for post_task_counter, post_task_edge in enumerate(play.post_tasks, 1):
                    self.render_node(play_subgraph, post_task_edge, color,
                                     node_counter=len(play.pre_tasks) + len(play.roles) + len(
                                         play.tasks) + post_task_counter, node_label_prefix="[post_task] ")

    def render(self, output_filename: str, save_dot_file=False, view=False) -> str:
        """
        Render the graph
        :param output_filename: Output file name without '.svg' extension.
        :param save_dot_file: If true, the dot file will be saved when rendering the graph.
        :param view: If true, will automatically open the resulting (PDF, PNG, SVG, etc.) file with your system’s
            default viewer application for the file type
        :return: The rendered file path (output_filename.svg)
        """
        self._convert_to_graphviz()
        rendered_file_path = self.digraph.render(cleanup=not save_dot_file, format="svg", filename=output_filename,
                                                 view=view)

        if save_dot_file:
            # add .dot extension. The render doesn't add an extension
            final_name = output_filename + ".dot"
            os.rename(output_filename, final_name)
            self.display.display(f"Graphviz dot file has been exported to {final_name}")

        return rendered_file_path
