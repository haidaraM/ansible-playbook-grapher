# Copyright (C) 2023 Mohamed El Mouctar HAIDARA
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
from typing import Dict, List, Set

from ansible.utils.display import Display
from graphviz import Digraph

from ansibleplaybookgrapher.graph_model import (
    PlaybookNode,
    PlayNode,
    RoleNode,
    BlockNode,
    TaskNode,
)
from ansibleplaybookgrapher.renderer import PlaybookBuilder, Renderer
from ansibleplaybookgrapher.renderer.graphviz.postprocessor import GraphvizPostProcessor

display = Display()

DEFAULT_EDGE_ATTR = {"sep": "10", "esep": "5"}
DEFAULT_GRAPH_ATTR = {
    "ratio": "fill",
    "rankdir": "LR",
    "concentrate": "true",
    "ordering": "in",
}


class GraphvizRenderer(Renderer):
    def __init__(
        self,
        playbook_nodes: List[PlaybookNode],
        roles_usage: Dict["RoleNode", Set[PlayNode]],
    ):
        self.playbook_nodes = playbook_nodes
        self.roles_usage = roles_usage

    def render(
        self,
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str],
        output_filename: str,
        view: bool,
        **kwargs,
    ) -> str:
        """
        :return: The filename where the playbooks where rendered
        """
        save_dot_file = kwargs.get("save_dot_file", False)

        # Set of the roles that have been built so far for all the playbooks
        roles_built = set()
        digraph = Digraph(
            format="svg",
            graph_attr=DEFAULT_GRAPH_ATTR,
            edge_attr=DEFAULT_EDGE_ATTR,
        )
        for playbook_node in self.playbook_nodes:
            builder = GraphvizPlaybookBuilder(
                playbook_node,
                open_protocol_handler=open_protocol_handler,
                open_protocol_custom_formats=open_protocol_custom_formats,
                roles_usage=self.roles_usage,
                roles_built=roles_built,
                digraph=digraph,
            )
            builder.build_playbook()
            roles_built.update(builder.roles_built)

        display.display("Rendering the graph...")
        svg_path = digraph.render(
            cleanup=not save_dot_file,
            format="svg",
            filename=output_filename,
            view=view,
        )

        post_processor = GraphvizPostProcessor(svg_path=svg_path)
        display.v("Post processing the SVG...")
        post_processor.post_process(self.playbook_nodes)
        post_processor.write()

        display.display(f"The graph has been exported to {svg_path}", color="green")
        if save_dot_file:
            # add .dot extension. The render doesn't add an extension
            final_name = output_filename + ".dot"
            os.rename(output_filename, final_name)
            display.display(f"Graphviz dot file has been exported to {final_name}")

        return svg_path


class GraphvizPlaybookBuilder(PlaybookBuilder):
    """
    Build the graphviz graph
    """

    def __init__(
        self,
        playbook_node: PlaybookNode,
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str],
        roles_usage: Dict[RoleNode, Set[PlayNode]],
        roles_built: Set[RoleNode],
        digraph: Digraph,
    ):
        """

        :param digraph: Graphviz graph into which build the graph
        """
        super().__init__(
            playbook_node,
            open_protocol_handler,
            open_protocol_custom_formats,
            roles_usage,
            roles_built,
        )

        self.digraph = digraph

    def build_task(self, task_node: TaskNode, color: str, fontcolor: str, **kwargs):
        """
        Build a task
        :param task_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
        # Here we have a TaskNode
        digraph = kwargs["digraph"]
        node_label_prefix = kwargs["node_label_prefix"]
        edge_label = f"{task_node.index} {task_node.when}"

        digraph.node(
            task_node.id,
            label=node_label_prefix + task_node.name,
            shape="octagon",
            id=task_node.id,
            tooltip=task_node.name,
            color=color,
            URL=self.get_node_url(task_node, "file"),
        )

        # Edge from parent to task
        digraph.edge(
            task_node.parent.id,
            task_node.id,
            label=edge_label,
            color=color,
            fontcolor=color,
            id=f"edge_{task_node.index}_{task_node.parent.id}_{task_node.id}",
            tooltip=edge_label,
            labeltooltip=edge_label,
        )

    def build_block(self, block_node: BlockNode, color: str, fontcolor: str, **kwargs):
        """

        :return:
        """
        edge_label = f"{block_node.index}"
        digraph = kwargs["digraph"]

        # Edge from parent to the block node inside the cluster
        digraph.edge(
            block_node.parent.id,
            block_node.id,
            label=edge_label,
            color=color,
            fontcolor=color,
            tooltip=edge_label,
            id=f"edge_{block_node.index}_{block_node.parent.id}_{block_node.id}",
            labeltooltip=edge_label,
        )

        # BlockNode is a special node: a cluster is created instead of a normal node
        with digraph.subgraph(
            name=f"cluster_{block_node.id}"
        ) as cluster_block_subgraph:
            # block node
            cluster_block_subgraph.node(
                block_node.id,
                label=f"[block] {block_node.name}",
                shape="box",
                style="filled",
                id=block_node.id,
                tooltip=block_node.name,
                color=color,
                fontcolor=fontcolor,
                labeltooltip=block_node.name,
                URL=self.get_node_url(block_node, "file"),
            )

            # The reverse here is a little hack due to how graphviz render nodes inside a cluster by reversing them.
            #  Don't really know why for the moment neither if there is an attribute to change that.
            for task in reversed(block_node.tasks):
                self.build_node(
                    node=task,
                    color=color,
                    fontcolor=fontcolor,
                    digraph=cluster_block_subgraph,
                )

    def build_role(self, role_node: RoleNode, color: str, fontcolor: str, **kwargs):
        """
        Render a role in the graph
        :return:
        """

        digraph = kwargs["digraph"]

        role_edge_label = f"{role_node.index} {role_node.when}"
        # from parent to the role node
        digraph.edge(
            role_node.parent.id,
            role_node.id,
            label=role_edge_label,
            color=color,
            fontcolor=color,
            id=f"edge_{role_node.index}_{role_node.parent.id}_{role_node.id}",
            tooltip=role_edge_label,
            labeltooltip=role_edge_label,
        )

        # check if we already built this role
        if role_node in self.roles_built:
            return

        self.roles_built.add(role_node)

        if role_node.include_role:  # For include_role, we point to a file
            url = self.get_node_url(role_node, "file")
        else:  # For normal role invocation, we point to the folder
            url = self.get_node_url(role_node, "folder")

        plays_using_this_role = self.roles_usage[role_node]
        if len(plays_using_this_role) > 1:
            # If the role is used in multiple plays, we take black as the default color
            role_color = "black"
            fontcolor = "#ffffff"
        else:
            role_color, fontcolor = list(plays_using_this_role)[0].colors

        with digraph.subgraph(name=role_node.name, node_attr={}) as role_subgraph:
            role_subgraph.node(
                role_node.id,
                id=role_node.id,
                label=f"[role] {role_node.name}",
                style="filled",
                tooltip=role_node.name,
                fontcolor=fontcolor,
                color=color,
                URL=url,
            )
            # role tasks
            for role_task in role_node.tasks:
                self.build_node(
                    node=role_task,
                    color=role_color,
                    fontcolor=fontcolor,
                    digraph=role_subgraph,
                )

    def build_playbook(self, **kwargs) -> str:
        """
        Convert the PlaybookNode to the graphviz dot format
        :return: The text representation of the graphviz dot format for the playbook
        """
        display.vvv(f"Converting the graph to the dot format for graphviz")
        # root node
        self.digraph.node(
            self.playbook_node.id,
            label=self.playbook_node.name,
            style="dotted",
            id=self.playbook_node.id,
            URL=self.get_node_url(self.playbook_node, "file"),
        )

        for play in self.playbook_node.plays:
            with self.digraph.subgraph(name=play.name) as play_subgraph:
                self.build_play(play, digraph=play_subgraph, **kwargs)

        return self.digraph.source

    def build_play(self, play_node: PlayNode, **kwargs):
        """

        :param play_node:
        :param kwargs:
        :return:
        """
        digraph = kwargs["digraph"]

        color, play_font_color = play_node.colors
        play_tooltip = (
            ",".join(play_node.hosts) if len(play_node.hosts) > 0 else play_node.name
        )

        # play node
        digraph.node(
            play_node.id,
            id=play_node.id,
            label=play_node.name,
            style="filled",
            shape="box",
            color=color,
            fontcolor=play_font_color,
            tooltip=play_tooltip,
            URL=self.get_node_url(play_node, "file"),
        )

        # from playbook to play
        playbook_to_play_label = f"{play_node.index} {play_node.name}"
        self.digraph.edge(
            self.playbook_node.id,
            play_node.id,
            id=f"edge_{self.playbook_node.id}_{play_node.id}",
            label=playbook_to_play_label,
            color=color,
            fontcolor=color,
            tooltip=playbook_to_play_label,
            labeltooltip=playbook_to_play_label,
        )

        # traverse the play
        self.traverse_play(play_node, **kwargs)
