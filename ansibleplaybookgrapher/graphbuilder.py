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
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, List

from ansible.utils.display import Display
from graphviz import Digraph

from ansibleplaybookgrapher import PlaybookParser
from ansibleplaybookgrapher.graph import (
    PlaybookNode,
    RoleNode,
    BlockNode,
    Node,
    PlayNode,
    TaskNode,
)
from ansibleplaybookgrapher.utils import get_play_colors, merge_dicts

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


class Grapher:
    def __init__(self, playbook_filenames: List[str]):
        """
        :param playbook_filenames: List of playbooks to graph
        """
        self.playbook_filenames = playbook_filenames
        # Colors assigned to plays

        self.plays_color = {}
        # The usage of the roles in all playbooks
        self.roles_usage: Dict["RoleNode", List[Node]] = {}

        # The parsed playbooks
        self.playbook_nodes: List[PlaybookNode] = []

    def parse(
        self,
        include_role_tasks: bool = False,
        tags: List[str] = None,
        skip_tags: List[str] = None,
        group_roles_by_name: bool = False,
    ):
        """
        Parses all the provided playbooks
        :param include_role_tasks: Should we include the role tasks
        :param tags: Only add plays and tasks tagged with these values
        :param skip_tags: Only add plays and tasks whose tags do not match these values
        :param group_roles_by_name: Group roles by name instead of considering them as separate nodes with different IDs
        :return:
        """

        for playbook_file in self.playbook_filenames:
            display.display(f"Parsing playbook {playbook_file}")
            parser = PlaybookParser(
                tags=tags,
                skip_tags=skip_tags,
                playbook_filename=playbook_file,
                include_role_tasks=include_role_tasks,
                group_roles_by_name=group_roles_by_name,
            )
            playbook_node = parser.parse()
            self.playbook_nodes.append(playbook_node)

            # Setting colors for play
            for play in playbook_node.plays:
                # TODO: find a way to create visual distance between the generated colors
                #   https://stackoverflow.com/questions/9018016/how-to-compare-two-colors-for-similarity-difference
                self.plays_color[play] = get_play_colors(play.id)

            # Update the usage of the roles
            self.roles_usage = merge_dicts(
                self.roles_usage, playbook_node.roles_usage()
            )

    def graph(
        self,
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str] = None,
    ) -> Digraph:
        """
        Generate the digraph graph
        :param open_protocol_handler
        :param open_protocol_custom_formats
        :return:
        """
        digraph = Digraph(
            format="svg",
            graph_attr=GraphvizGraphBuilder.DEFAULT_GRAPH_ATTR,
            edge_attr=GraphvizGraphBuilder.DEFAULT_EDGE_ATTR,
        )
        # Map of the rules that have been built so far for all playbooks
        roles_built = {}
        for p in self.playbook_nodes:
            builder = GraphvizGraphBuilder(
                p,
                play_colors=self.plays_color,
                open_protocol_handler=open_protocol_handler,
                open_protocol_custom_formats=open_protocol_custom_formats,
                roles_usage=self.roles_usage,
                roles_built=roles_built,
                digraph=digraph,
            )
            builder.build_graphviz_graph()
            roles_built.update(builder.roles_built)

        return digraph


class Builder(ABC):
    def __init__(
        self,
        playbook_node: PlaybookNode,
        play_colors: Dict[PlayNode, Tuple[str, str]],
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str] = None,
        roles_usage: Dict[RoleNode, List[Node]] = None,
        roles_built: Dict = None,
    ):
        """

        :param playbook_node: Playbook parsed node
        :param open_protocol_handler: The protocol handler name to use
        :param open_protocol_custom_formats: The custom formats to use when the protocol handler is set to custom
        :param play_colors: The colors associated to the play
        :param roles_usage: The usage of the roles in the whole playbook
        :param roles_built: The roles that have been "built" so far
        """
        self.playbook_node = playbook_node
        self.roles_usage = roles_usage or playbook_node.roles_usage()
        self.play_colors = play_colors
        # A map containing the roles that have been built so far
        self.roles_built = roles_built or {}

        self.open_protocol_handler = open_protocol_handler
        # Merge the two dicts
        formats = {**OPEN_PROTOCOL_HANDLERS, **{"custom": open_protocol_custom_formats}}
        self.open_protocol_formats = formats[self.open_protocol_handler]

    def build_node(
        self,
        counter: int,
        source: Node,
        destination: Node,
        color: str,
        **kwargs,
    ):
        """
        Render a generic node in the graph
        :param source: The source node
        :param destination: The RoleNode to render
        :param color: The color to apply
        :param counter: The counter for this node
        :return:
        """

        if isinstance(destination, BlockNode):
            self.build_block(
                counter=counter,
                source=source,
                destination=destination,
                color=color,
                **kwargs,
            )
        elif isinstance(destination, RoleNode):
            self.build_role(
                counter=counter,
                source=source,
                destination=destination,
                color=color,
                **kwargs,
            )
        else:  # This is necessarily a TaskNode
            self.build_task(
                counter=counter,
                source=source,
                destination=destination,
                color=color,
                node_label_prefix=kwargs.pop("node_label_prefix", ""),
                **kwargs,
            )

    @abstractmethod
    def build_task(
        self, counter: int, source: Node, destination: TaskNode, color: str, **kwargs
    ):
        """
        Build a single task to be rendered
        :param counter: The counter for the task
        :param source: The source node
        :param destination: The task
        :param color: Color from the play
        :param kwargs:
        :return:
        """
        pass

    @abstractmethod
    def build_role(
        self, counter: int, source: Node, destination: RoleNode, color: str, **kwargs
    ):
        """
        Render a role in the graph
        :param counter: The counter for this role in the graph
        :param source: The source node
        :param destination: The RoleNode to render
        :param color: The color to apply
        :return:
        """
        pass

    @abstractmethod
    def build_block(
        self, counter: int, source: Node, destination: BlockNode, color: str, **kwargs
    ):
        """
        Build a block to be rendered.
        A BlockNode is a special node: a cluster is created instead of a normal node.
        :param counter: The counter for this block in the graph
        :param source: The source node
        :param destination: The BlockNode to build
        :param color: The color from the play to apply
        :return:
        """
        pass

    def get_node_url(self, node: Node, node_type: str) -> Optional[str]:
        """
        Get the node url based on the chosen protocol
        :param node_type: task or role
        :param node: the node to get the url for
        :return:
        """
        if node.path:
            remove_from_path = self.open_protocol_formats.get("remove_from_path", "")
            path = node.path.replace(remove_from_path, "")

            url = self.open_protocol_formats[node_type].format(
                path=path, line=node.line, column=node.column
            )
            display.vvvv(f"Open protocol URL for node {node}: {url}")
            return url

        return None


class GraphvizGraphBuilder(Builder):
    """
    Build the graphviz graph
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
        playbook_node: PlaybookNode,
        play_colors: Dict[PlayNode, Tuple[str, str]],
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str],
        roles_usage: Dict[RoleNode, List[Node]],
        roles_built: Dict,
        digraph: Digraph,
    ):
        """

        :param digraph: Graphviz graph into which build the graph
        """
        super().__init__(
            playbook_node,
            play_colors,
            open_protocol_handler,
            open_protocol_custom_formats,
            roles_usage,
            roles_built,
        )

        self.digraph = digraph

    def build_task(self, counter, source: Node, destination: TaskNode, color, **kwargs):
        """
        Build a task
        :param counter:
        :param source:
        :param destination:
        :param color:
        :param kwargs:
        :return:
        """

        # Here we have a TaskNode
        digraph = kwargs["digraph"]
        node_label_prefix = kwargs["node_label_prefix"]
        edge_label = f"{counter} {destination.when}"
        # Task node
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
        self, counter: int, source: Node, destination: BlockNode, color: str, **kwargs
    ):
        """
        Build a block to be rendered.
        A BlockNode is a special node: a cluster is created instead of a normal node.
        :param counter: The counter for this block in the graph
        :param source: The source node
        :param destination: The BlockNode to build
        :param color: The color from the play to apply
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
                id=destination.id,
                tooltip=destination.name,
                color=color,
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
                    color=color,
                    digraph=cluster_block_subgraph,
                )

    def build_role(
        self, counter: int, source: Node, destination: RoleNode, color: str, **kwargs
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
        role_to_render = self.roles_built.get(destination.id, None)
        if role_to_render is None:
            # Merge the colors for each play where this role is used
            role_plays = self.roles_usage[destination]
            # Graphviz support providing multiple colors separated by :
            if len(role_plays) > 1:
                # If the role is used in multiple plays, we take black as the default color
                role_color = "black"
            else:
                colors = list(map(self.play_colors.get, role_plays))[0]
                role_color = colors[0]

            self.roles_built[destination.id] = destination

            with digraph.subgraph(name=destination.name, node_attr={}) as role_subgraph:
                role_subgraph.node(
                    destination.id,
                    id=destination.id,
                    label=f"[role] {destination.name}",
                    tooltip=destination.name,
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
                        digraph=role_subgraph,
                    )

    def build_graphviz_graph(self):
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

        for play_counter, play in enumerate(self.playbook_node.plays, 1):
            with self.digraph.subgraph(name=play.name) as play_subgraph:
                color, play_font_color = self.play_colors[play]
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
                playbook_to_play_label = f"{play_counter} {play.name}"
                self.digraph.edge(
                    self.playbook_node.name,
                    play.id,
                    id=f"edge_{self.playbook_node.id}_{play.id}",
                    label=playbook_to_play_label,
                    color=color,
                    fontcolor=color,
                    tooltip=playbook_to_play_label,
                    labeltooltip=playbook_to_play_label,
                )

                # pre_tasks
                for pre_task_counter, pre_task in enumerate(play.pre_tasks, 1):
                    self.build_node(
                        counter=pre_task_counter,
                        source=play,
                        destination=pre_task,
                        color=color,
                        digraph=play_subgraph,
                        node_label_prefix="[pre_task] ",
                    )

                # roles
                for role_counter, role in enumerate(play.roles, 1):
                    self.build_role(
                        counter=role_counter + len(play.pre_tasks),
                        source=play,
                        destination=role,
                        color=color,
                        digraph=play_subgraph,
                    )

                # tasks
                for task_counter, task in enumerate(play.tasks, 1):
                    self.build_node(
                        counter=len(play.pre_tasks) + len(play.roles) + task_counter,
                        source=play,
                        destination=task,
                        color=color,
                        digraph=play_subgraph,
                        node_label_prefix="[task] ",
                    )

                # post_tasks
                for post_task_counter, post_task in enumerate(play.post_tasks, 1):
                    self.build_node(
                        counter=len(play.pre_tasks)
                        + len(play.roles)
                        + len(play.tasks)
                        + post_task_counter,
                        source=play,
                        destination=post_task,
                        color=color,
                        digraph=play_subgraph,
                        node_label_prefix="[post_task] ",
                    )
