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

from ansibleplaybookgrapher.graph import (
    PlaybookNode,
    PlayNode,
    RoleNode,
    Node,
    BlockNode,
    TaskNode,
)
from ansibleplaybookgrapher.renderer import PlaybookBuilder
from ansibleplaybookgrapher.renderer.graphviz.postprocessor import GraphVizPostProcessor

display = Display()

DEFAULT_EDGE_ATTR = {"sep": "10", "esep": "5"}
DEFAULT_GRAPH_ATTR = {
    "ratio": "fill",
    "rankdir": "LR",
    "concentrate": "true",
    "ordering": "in",
}


class GraphvizRenderer:
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
        save_dot_file: bool,
        output_filename: str,
        view: bool,
        **kwargs,
    ) -> str:
        """
        :return: The filename where the playbooks where rendered
        """
        # Set of the roles that have been built so far for all the playbooks
        roles_built = set()
        digraph = Digraph(
            format="svg",
            graph_attr=DEFAULT_GRAPH_ATTR,
            edge_attr=DEFAULT_EDGE_ATTR,
        )
        for playbook_node in self.playbook_nodes:
            builder = GraphvizGraphBuilder(
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

        post_processor = GraphVizPostProcessor(svg_path=svg_path)
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


class GraphvizGraphBuilder(PlaybookBuilder):
    """
    Build the graphviz graph
    """

    def __init__(
        self,
        playbook_node: PlaybookNode,
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str],
        roles_usage: Dict[RoleNode, Set[PlayNode]],
        roles_built: Set,
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

    def build_task(
        self,
        counter: int,
        source: Node,
        destination: TaskNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ):
        """
        Build a task
        :param counter:
        :param source:
        :param destination:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
        # Here we have a TaskNode
        digraph = kwargs["digraph"]
        node_label_prefix = kwargs["node_label_prefix"]
        edge_label = f"{counter} {destination.when}"

        digraph.node(
            destination.id,
            label=node_label_prefix + destination.name,
            shape="octagon",
            id=destination.id,
            tooltip=destination.name,
            color=color,
            URL=self.get_node_url(destination, "file"),
        )

        # Edge from parent to task
        digraph.edge(
            source.id,
            destination.id,
            label=edge_label,
            color=color,
            fontcolor=color,
            id=f"edge_{counter}_{source.id}_{destination.id}",
            tooltip=edge_label,
            labeltooltip=edge_label,
        )

    def build_block(
        self,
        counter: int,
        source: Node,
        destination: BlockNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ):
        """

        :return:
        """
        edge_label = f"{counter}"
        digraph = kwargs["digraph"]

        # Edge from parent to the block node inside the cluster
        digraph.edge(
            source.id,
            destination.id,
            label=edge_label,
            color=color,
            fontcolor=color,
            tooltip=edge_label,
            id=f"edge_{counter}_{source.id}_{destination.id}",
            labeltooltip=edge_label,
        )

        # BlockNode is a special node: a cluster is created instead of a normal node
        with digraph.subgraph(
            name=f"cluster_{destination.id}"
        ) as cluster_block_subgraph:
            # block node
            cluster_block_subgraph.node(
                destination.id,
                label=f"[block] {destination.name}",
                shape="box",
                style="filled",
                id=destination.id,
                tooltip=destination.name,
                color=color,
                fontcolor=fontcolor,
                labeltooltip=destination.name,
                URL=self.get_node_url(destination, "file"),
            )

            # The reverse here is a little hack due to how graphviz render nodes inside a cluster by reversing them.
            #  Don't really know why for the moment neither if there is an attribute to change that.
            for b_counter, task in enumerate(reversed(destination.tasks)):
                self.build_node(
                    counter=len(destination.tasks) - b_counter,
                    source=destination,
                    destination=task,
                    fontcolor=fontcolor,
                    color=color,
                    digraph=cluster_block_subgraph,
                )

    def build_role(
        self,
        counter: int,
        source: Node,
        destination: RoleNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ):
        """
        Render a role in the graph
        :return:
        """
        digraph = kwargs["digraph"]

        if destination.include_role:  # For include_role, we point to a file
            url = self.get_node_url(destination, "file")
        else:  # For normal role invocation, we point to the folder
            url = self.get_node_url(destination, "folder")

        role_edge_label = f"{counter} {destination.when}"

        # from parent to the role node
        digraph.edge(
            source.id,
            destination.id,
            label=role_edge_label,
            color=color,
            fontcolor=color,
            id=f"edge_{counter}_{source.id}_{destination.id}",
            tooltip=role_edge_label,
            labeltooltip=role_edge_label,
        )

        # check if we already built this role
        if destination in self.roles_built:
            return

        self.roles_built.add(destination)

        plays_using_this_role = self.roles_usage[destination]
        if len(plays_using_this_role) > 1:
            # If the role is used in multiple plays, we take black as the default color
            role_color = "black"
            fontcolor = "#ffffff"
        else:
            role_color, fontcolor = list(plays_using_this_role)[0].colors

        with digraph.subgraph(name=destination.name, node_attr={}) as role_subgraph:
            role_subgraph.node(
                destination.id,
                id=destination.id,
                label=f"[role] {destination.name}",
                style="filled",
                tooltip=destination.name,
                fontcolor=fontcolor,
                color=color,
                URL=url,
            )
            # role tasks
            for role_task_counter, role_task in enumerate(destination.tasks, 1):
                self.build_node(
                    counter=role_task_counter,
                    source=destination,
                    destination=role_task,
                    color=role_color,
                    fontcolor=fontcolor,
                    digraph=role_subgraph,
                )

    def build_playbook(self, **kwargs):
        """
        Convert the PlaybookNode to the graphviz dot format
        :return:
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

        for play_counter, play in enumerate(self.playbook_node.plays, 1):
            self.build_play(play_counter, play, **kwargs)

    def build_play(self, counter: int, destination: PlayNode, **kwargs):
        """

        :param counter:
        :param destination:
        :param kwargs:
        :return:
        """
        with self.digraph.subgraph(name=destination.name) as play_subgraph:
            color, play_font_color = destination.colors
            play_tooltip = (
                ",".join(destination.hosts)
                if len(destination.hosts) > 0
                else destination.name
            )

            # play node
            play_subgraph.node(
                destination.id,
                id=destination.id,
                label=destination.name,
                style="filled",
                shape="box",
                color=color,
                fontcolor=play_font_color,
                tooltip=play_tooltip,
                URL=self.get_node_url(destination, "file"),
            )

            # edge from root node to play
            playbook_to_play_label = f"{counter} {destination.name}"
            self.digraph.edge(
                self.playbook_node.id,
                destination.id,
                id=f"edge_{self.playbook_node.id}_{destination.id}",
                label=playbook_to_play_label,
                color=color,
                fontcolor=color,
                tooltip=playbook_to_play_label,
                labeltooltip=playbook_to_play_label,
            )

            # pre_tasks
            for pre_task_counter, pre_task in enumerate(destination.pre_tasks, 1):
                self.build_node(
                    counter=pre_task_counter,
                    source=destination,
                    destination=pre_task,
                    color=color,
                    fontcolor=play_font_color,
                    digraph=play_subgraph,
                    node_label_prefix="[pre_task] ",
                    **kwargs,
                )

            # roles
            for role_counter, role in enumerate(destination.roles, 1):
                self.build_role(
                    counter=role_counter + len(destination.pre_tasks),
                    source=destination,
                    destination=role,
                    color=color,
                    fontcolor=play_font_color,
                    digraph=play_subgraph,
                    **kwargs,
                )

            # tasks
            for task_counter, task in enumerate(destination.tasks, 1):
                self.build_node(
                    counter=len(destination.pre_tasks)
                    + len(destination.roles)
                    + task_counter,
                    source=destination,
                    destination=task,
                    fontcolor=play_font_color,
                    color=color,
                    digraph=play_subgraph,
                    node_label_prefix="[task] ",
                    **kwargs,
                )

            # post_tasks
            for post_task_counter, post_task in enumerate(destination.post_tasks, 1):
                self.build_node(
                    counter=len(destination.pre_tasks)
                    + len(destination.roles)
                    + len(destination.tasks)
                    + post_task_counter,
                    source=destination,
                    destination=post_task,
                    fontcolor=play_font_color,
                    color=color,
                    digraph=play_subgraph,
                    node_label_prefix="[post_task] ",
                    **kwargs,
                )