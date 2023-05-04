import os
from typing import Dict, List, Tuple

from ansible.utils.display import Display
from graphviz import Digraph

from ansibleplaybookgrapher import GraphVizPostProcessor
from ansibleplaybookgrapher.graph import (
    PlaybookNode,
    PlayNode,
    RoleNode,
    Node,
    BlockNode,
    TaskNode,
)
from ansibleplaybookgrapher.renderer import Builder

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
        plays_colors: Dict[PlayNode, Tuple[str, str]],
        roles_usage: Dict["RoleNode", List[Node]],
    ):
        self.plays_colors = plays_colors
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
        # Map of the roles that have been built so far for all playbooks
        roles_built = {}
        digraph = Digraph(
            format="svg",
            graph_attr=DEFAULT_GRAPH_ATTR,
            edge_attr=DEFAULT_EDGE_ATTR,
        )
        for p in self.playbook_nodes:
            builder = GraphvizGraphBuilder(
                p,
                play_colors=self.plays_colors,
                open_protocol_handler=open_protocol_handler,
                open_protocol_custom_formats=open_protocol_custom_formats,
                roles_usage=self.roles_usage,
                roles_built=roles_built,
                digraph=digraph,
            )
            builder.build()
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


class GraphvizGraphBuilder(Builder):
    """
    Build the graphviz graph
    """

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

    def build_task(self, counter, source: Node, destination: TaskNode, color:str, **kwargs):
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

    def build(self, **kwargs):
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
