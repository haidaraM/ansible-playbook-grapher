# Copyright (C) 2024 Mohamed El Mouctar HAIDARA
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
from pathlib import Path

from ansible.utils.display import Display
from graphviz import Digraph

from ansibleplaybookgrapher.graph_model import (
    BlockNode,
    PlaybookNode,
    PlayNode,
    RoleNode,
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
        playbook_nodes: list[PlaybookNode],
        roles_usage: dict["RoleNode", set[PlayNode]],
    ) -> None:
        super().__init__(playbook_nodes, roles_usage)

    def render(
        self,
        open_protocol_handler: str,
        open_protocol_custom_formats: dict[str, str],
        output_filename: str,
        title: str,
        include_role_tasks: bool = False,
        view: bool = False,
        show_handlers: bool = False,
        **kwargs,
    ) -> str:
        """Render the playbooks to a file.

        :param open_protocol_handler: The protocol handler name to use.
        :param open_protocol_custom_formats: The custom formats to use when the protocol handler is set to custom
        :param output_filename: The output filename without any extension
        :param title: The title of the graph.
        :param include_role_tasks: Whether to include the tasks of the roles in the graph or not.
        :param view: Whether to open the rendered file in the default viewer
        :param show_handlers: Whether to show the handlers or not.
        :param kwargs:
        :return: The path of the rendered file.
        """
        save_dot_file = kwargs.get("save_dot_file", False)

        # Set of the roles that have been built so far for all the playbooks
        roles_built = set()
        digraph = Digraph(
            format="svg",
            graph_attr=DEFAULT_GRAPH_ATTR,
            edge_attr=DEFAULT_EDGE_ATTR,
        )
        digraph.attr(label=title, labelloc="t")

        for playbook_node in self.playbook_nodes:
            builder = GraphvizPlaybookBuilder(
                playbook_node,
                open_protocol_handler=open_protocol_handler,
                open_protocol_custom_formats=open_protocol_custom_formats,
                roles_usage=self.roles_usage,
                roles_built=roles_built,
                digraph=digraph,
                include_role_tasks=include_role_tasks,
            )

            builder.build_playbook(
                show_handlers=show_handlers,
            )
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
            # Add .dot extension. The render doesn't add an extension
            final_name = output_filename + ".dot"
            Path(output_filename).rename(final_name)
            display.display(f"Graphviz dot file has been exported to {final_name}")

        return svg_path


class GraphvizPlaybookBuilder(PlaybookBuilder):
    """Build the graphviz graph."""

    def __init__(
        self,
        playbook_node: PlaybookNode,
        open_protocol_handler: str,
        open_protocol_custom_formats: dict[str, str],
        roles_usage: dict[RoleNode, set[PlayNode]],
        roles_built: set[RoleNode],
        include_role_tasks: bool,
        digraph: Digraph,
    ) -> None:
        """

        :param digraph: The Graphviz graph object into which to build the nodes and edges.
        """
        super().__init__(
            playbook_node,
            open_protocol_handler=open_protocol_handler,
            open_protocol_custom_formats=open_protocol_custom_formats,
            roles_usage=roles_usage,
            roles_built=roles_built,
            include_role_tasks=include_role_tasks,
        )
        self.digraph = digraph

    def build_task(
        self,
        task_node: TaskNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """Build a task
        :param task_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
        # Here we have a TaskNode
        digraph = kwargs["digraph"]
        edge_label = f"{task_node.index} {task_node.when}"

        edge_style = "solid"
        node_shape = "rectangle"
        node_style = "solid"

        if task_node.is_handler():
            edge_style = "dotted"
            node_shape = "hexagon"
            node_style = "dotted"

        digraph.node(
            task_node.id,
            label=task_node.display_name(),
            shape=node_shape,
            id=task_node.id,
            tooltip=task_node.name,
            color=color,
            style=node_style,
            URL=self.get_node_url(task_node),
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
            style=edge_style,
        )

    def build_block(
        self,
        block_node: BlockNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """:return:"""
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
            name=f"cluster_{block_node.id}",
        ) as cluster_block_subgraph:
            # Prevents the cluster from having the root graph label (not needed)
            cluster_block_subgraph.attr(label="")

            # block node
            cluster_block_subgraph.node(
                block_node.id,
                label=block_node.display_name(),
                shape="box",
                style="filled",
                id=block_node.id,
                tooltip=block_node.name,
                color=color,
                fontcolor=fontcolor,
                labeltooltip=block_node.name,
                URL=self.get_node_url(block_node),
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

    def build_role(
        self,
        role_node: RoleNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """Render a role in the graph

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

        url = self.get_node_url(role_node)

        plays_using_this_role = self.roles_usage[role_node]
        if len(plays_using_this_role) > 1:
            # If the role is used in multiple plays, we take black as the default color
            role_color = "black"
            fontcolor = "#ffffff"
        else:
            role_color, fontcolor = next(iter(plays_using_this_role)).colors

        with digraph.subgraph(name=role_node.name, node_attr={}) as role_subgraph:
            role_subgraph.node(
                role_node.id,
                id=role_node.id,
                label=role_node.display_name(),
                style="filled",
                tooltip=role_node.name,
                fontcolor=fontcolor,
                color=color,
                URL=url,
            )

            if self.include_role_tasks:
                # role tasks
                for role_task in role_node.tasks:
                    self.build_node(
                        node=role_task,
                        color=role_color,
                        fontcolor=fontcolor,
                        digraph=role_subgraph,
                    )

    def build_playbook(
        self,
        show_handlers: bool,
        **kwargs,
    ) -> str:
        """Convert the PlaybookNode to the graphviz dot format.

        :param show_handlers: Whether to show the handlers or not.
        :return: The text representation of the graphviz dot format for the playbook.
        """
        display.vvv("Converting the graph to the dot format for graphviz")
        # root node
        self.digraph.node(
            self.playbook_node.id,
            label=self.playbook_node.name,
            style="dotted",
            id=self.playbook_node.id,
            URL=self.get_node_url(self.playbook_node),
        )

        for play in self.playbook_node.plays:
            if not play.is_hidden:
                with self.digraph.subgraph(name=play.name) as play_subgraph:
                    self.build_play(
                        play,
                        digraph=play_subgraph,
                        show_handlers=show_handlers,
                        **kwargs,
                    )

        return self.digraph.source

    def build_play(
        self, play_node: PlayNode, show_handlers: bool = False, **kwargs
    ) -> None:
        """

        :param show_handlers:
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
            label=play_node.display_name(),
            style="filled",
            shape="box",
            color=color,
            fontcolor=play_font_color,
            tooltip=play_tooltip,
            URL=self.get_node_url(play_node),
        )

        # from playbook to play
        playbook_to_play_label = f"{play_node.index}"
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
        self.traverse_play(play_node, show_handlers=show_handlers, **kwargs)
