# Copyright (C) 2022 Mohamed El Mouctar HAIDARA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os
from typing import Dict, Optional

from ansible.utils.display import Display
from graphviz import Digraph

from ansibleplaybookgrapher.graph import (
    PlaybookNode,
    EdgeNode,
    PlayNode,
    RoleNode,
    BlockNode,
    Node,
)
from ansibleplaybookgrapher.utils import get_play_colors

display = Display()

# The supported protocol handlers to open roles and tasks from the viewer
OPEN_PROTOCOL_HANDLERS = {
    "default": {"folder": "{path}", "file": "{path}"},
    # https://code.visualstudio.com/docs/editor/command-line#_opening-vs-code-with-urls
    "vscode": {
        "folder": "vscode://file/{path}",
        "file": "vscode://file/{path}:{line}:{column}",
    },
    # For custom, the formats need to be provided
    "custom": {},
}


class GraphvizRenderer:
    """
    Render the graph with graphviz
    """

    DEFAULT_EDGE_ATTR = {"sep": "10", "esep": "5"}
    DEFAULT_GRAPH_ATTR = {
        "ratio": "fill",
        "rankdir": "LR",
        "concentrate": "true",
        "ordering": "in",
    }

    def __init__(
        self,
        playbook_node: "PlaybookNode",
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str] = None,
        graph_format: str = "svg",
        graph_attr: Dict = None,
        edge_attr: Dict = None,
    ):
        """

        :param playbook_node: Playbook parsed node
        :param open_protocol_handler: The protocol handler name to use
        :param open_protocol_custom_formats: The custom formats to use when the protocol handler is set to custom
        :param graph_format: the graph format to render. See https://graphviz.org/docs/outputs/
        :param graph_attr: Default graph attributes
        :param edge_attr: Default edge attributes
        """
        self.playbook_node = playbook_node
        self.open_protocol_handler = open_protocol_handler
        # Merge the two dicts
        formats = {**OPEN_PROTOCOL_HANDLERS, **{"custom": open_protocol_custom_formats}}
        self.open_protocol_formats = formats[self.open_protocol_handler]
        self.digraph = Digraph(
            format=graph_format,
            graph_attr=graph_attr or GraphvizRenderer.DEFAULT_GRAPH_ATTR,
            edge_attr=edge_attr or GraphvizRenderer.DEFAULT_EDGE_ATTR,
        )

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

        display.display("Rendering the graph...")
        rendered_file_path = self.digraph.render(
            cleanup=not save_dot_file, format="svg", filename=output_filename, view=view
        )

        if save_dot_file:
            # add .dot extension. The render doesn't add an extension
            final_name = output_filename + ".dot"
            os.rename(output_filename, final_name)
            display.display(f"Graphviz dot file has been exported to {final_name}")

        return rendered_file_path

    def render_node(
        self,
        graph: Digraph,
        edge_counter: int,
        edge: EdgeNode,
        color: str,
        shape: str = "octagon",
        **kwargs,
    ):
        """
        Render a generic node in the graph
        :param graph: The graph to render the node to
        :param edge: The edge from a node to the Node
        :param color: The color to apply
        :param edge_counter: The counter for this node
        :param shape: the default shape of the node
        :return:
        """
        destination_node = edge.destination
        source_node = edge.source
        node_label_prefix = kwargs.get("node_label_prefix", "")

        if isinstance(destination_node, BlockNode):
            self.render_block(graph, edge_counter, edge, color)
        elif isinstance(destination_node, RoleNode):
            self.render_role(graph, edge_counter, edge, color)
        else:
            # Here we have a TaskNode
            edge_label = f"{edge_counter} {edge.name}"
            # Task node
            graph.node(
                destination_node.id,
                label=node_label_prefix + destination_node.name,
                shape=shape,
                id=destination_node.id,
                tooltip=destination_node.name,
                color=color,
                URL=self.get_node_url(destination_node, "file"),
            )
            # Edge from parent to task
            graph.edge(
                source_node.id,
                destination_node.id,
                label=edge_label,
                color=color,
                fontcolor=color,
                id=edge.id,
                tooltip=edge_label,
                labeltooltip=edge_label,
            )

    def render_block(
        self,
        graph: Digraph,
        edge_counter: int,
        edge: EdgeNode,
        color: str,
        **kwargs,
    ):
        """
        Render a block in the graph.
        A BlockNode is a special node: a cluster is created instead of a normal node.
        :param graph: The graph to render the block into
        :param edge_counter: The counter for this edge in the graph
        :param edge: The edge from a node to the BlockNode
        :param color: The color to apply
        :param kwargs:
        :return:
        """
        # noinspection PyTypeChecker
        destination_node = edge.destination  # type: BlockNode
        edge_label = f"{edge_counter}"

        # Edge from parent to the block node inside the cluster
        graph.edge(
            edge.source.id,
            destination_node.id,
            label=edge_label,
            color=color,
            fontcolor=color,
            tooltip=edge_label,
            id=edge.id,
            labeltooltip=edge_label,
        )

        # BlockNode is a special node: a cluster is created instead of a normal node
        with graph.subgraph(
            name=f"cluster_{destination_node.id}"
        ) as cluster_block_subgraph:
            # block node
            cluster_block_subgraph.node(
                destination_node.id,
                label=f"[block] {destination_node.name}",
                shape="box",
                id=destination_node.id,
                tooltip=destination_node.name,
                color=color,
                labeltooltip=destination_node.name,
                URL=self.get_node_url(destination_node, "file"),
            )

            # The reverse here is a little hack due to how graphviz render nodes inside a cluster by reversing them.
            #  Don't really know why for the moment neither if there is an attribute to change that.
            for b_counter, task_edge_node in enumerate(
                reversed(destination_node.tasks)
            ):
                self.render_node(
                    cluster_block_subgraph,
                    edge_counter=len(destination_node.tasks) - b_counter,
                    edge=task_edge_node,
                    color=color,
                )

    def render_role(
        self, graph: Digraph, edge_counter: int, edge: EdgeNode, color: str, **kwargs
    ):
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

        if role.include_role:  # For include_role, we point to a file
            url = self.get_node_url(role, "file")
        else:  # For normal role invocation, we point to the folder
            url = self.get_node_url(role, "folder")

        # from parent to the role node
        graph.edge(
            edge.source.id,
            role.id,
            label=role_edge_label,
            color=color,
            fontcolor=color,
            id=edge.id,
            tooltip=role_edge_label,
            labeltooltip=role_edge_label,
        )

        with graph.subgraph(name=role.name, node_attr={}) as role_subgraph:
            role_subgraph.node(
                role.id,
                id=role.id,
                label=f"[role] {role.name}",
                tooltip=role.name,
                color=color,
                URL=url,
            )
            # role tasks
            for role_task_counter, role_task_edge in enumerate(role.tasks, 1):
                self.render_node(
                    role_subgraph,
                    edge_counter=role_task_counter,
                    edge=role_task_edge,
                    color=color,
                )

    def _convert_to_graphviz(self):
        """
        Convert the PlaybookNode to the graphviz dot format
        :return:
        """
        display.vvv(f"Converting the graph to the dot format for graphviz")
        # root node
        self.digraph.node(
            self.playbook_node.name,
            style="dotted",
            id=self.playbook_node.id,
            URL=self.get_node_url(self.playbook_node, "file"),
        )

        for play_counter, play_edge in enumerate(self.playbook_node.plays, 1):
            # noinspection PyTypeChecker
            play = play_edge.destination  # type: PlayNode
            with self.digraph.subgraph(name=play.name) as play_subgraph:
                color, play_font_color = get_play_colors(play)
                play_tooltip = (
                    ",".join(play.hosts) if len(play.hosts) > 0 else play.name
                )
                # play node
                play_subgraph.node(
                    play.id,
                    id=play.id,
                    label=play.name,
                    style="filled",
                    shape="box",
                    color=color,
                    fontcolor=play_font_color,
                    tooltip=play_tooltip,
                    URL=self.get_node_url(play, "file"),
                )
                # edge from root node to play
                playbook_to_play_label = f"{play_counter} {play_edge.name}"
                self.digraph.edge(
                    self.playbook_node.name,
                    play.id,
                    id=play_edge.id,
                    label=playbook_to_play_label,
                    color=color,
                    fontcolor=color,
                    tooltip=playbook_to_play_label,
                    labeltooltip=playbook_to_play_label,
                )

                # pre_tasks
                for pre_task_counter, pre_task_edge in enumerate(play.pre_tasks, 1):
                    self.render_node(
                        play_subgraph,
                        edge_counter=pre_task_counter,
                        edge=pre_task_edge,
                        color=color,
                        node_label_prefix="[pre_task] ",
                    )

                # roles
                for role_counter, role_edge in enumerate(play.roles, 1):
                    self.render_role(
                        play_subgraph,
                        edge_counter=role_counter + len(play.pre_tasks),
                        edge=role_edge,
                        color=color,
                    )

                # tasks
                for task_counter, task_edge in enumerate(play.tasks, 1):
                    self.render_node(
                        play_subgraph,
                        edge_counter=len(play.pre_tasks)
                        + len(play.roles)
                        + task_counter,
                        edge=task_edge,
                        color=color,
                        node_label_prefix="[task] ",
                    )

                # post_tasks
                for post_task_counter, post_task_edge in enumerate(play.post_tasks, 1):
                    self.render_node(
                        play_subgraph,
                        edge_counter=len(play.pre_tasks)
                        + len(play.roles)
                        + len(play.tasks)
                        + post_task_counter,
                        edge=post_task_edge,
                        color=color,
                        node_label_prefix="[post_task] ",
                    )

    def get_node_url(self, node: Node, node_type: str) -> Optional[str]:
        """
        Get the node url based on the chosen protocol
        :param node_type: task or role
        :param node: the node to get the url for
        :return:
        """
        if node.path:
            url = self.open_protocol_formats[node_type].format(
                path=node.path, line=node.line, column=node.column
            )
            display.vvvv(f"Open protocol URL for node {node}: {url}")
            return url

        return None
