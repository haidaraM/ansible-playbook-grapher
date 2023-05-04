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
from typing import Dict, List

from ansible.utils.display import Display
from graphviz import Digraph

from ansibleplaybookgrapher import PlaybookParser
from ansibleplaybookgrapher.graph import (
    PlaybookNode,
    RoleNode,
    Node,
)
from ansibleplaybookgrapher.renderer.graphviz import GraphvizGraphBuilder
from ansibleplaybookgrapher.utils import get_play_colors, merge_dicts

display = Display()


class Grapher:
    def __init__(self, playbook_filenames: List[str]):
        """
        :param playbook_filenames: List of playbooks to graph
        """
        self.playbook_filenames = playbook_filenames
        # Colors assigned to plays
        self.plays_colors = {}

        # The usage of the roles in all playbooks
        self.roles_usage: Dict["RoleNode", List[Node]] = {}

    def parse(
        self,
        include_role_tasks: bool = False,
        tags: List[str] = None,
        skip_tags: List[str] = None,
        group_roles_by_name: bool = False,
    ) -> List[PlaybookNode]:
        """
        Parses all the provided playbooks
        :param include_role_tasks: Should we include the role tasks
        :param tags: Only add plays and tasks tagged with these values
        :param skip_tags: Only add plays and tasks whose tags do not match these values
        :param group_roles_by_name: Group roles by name instead of considering them as separate nodes with different IDs
        :return:
        """
        playbook_nodes = []
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
            playbook_nodes.append(playbook_node)

            # Setting colors for play
            for play in playbook_node.plays:
                # TODO: find a way to create visual distance between the generated colors
                # TODO: assign the color to the playnode directly instead of maintaining a separate dict
                #   https://stackoverflow.com/questions/9018016/how-to-compare-two-colors-for-similarity-difference
                self.plays_colors[play] = get_play_colors(play.id)

            # Update the usage of the roles
            self.roles_usage = merge_dicts(
                self.roles_usage, playbook_node.roles_usage()
            )

        return playbook_nodes

    def render(
        self,
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str] = None,
    ) -> Digraph:
        """
        Render the graph
        :param open_protocol_handler
        :param open_protocol_custom_formats
        :return:
        """
        digraph = Digraph(
            format="svg",
            graph_attr=GraphvizGraphBuilder.DEFAULT_GRAPH_ATTR,
            edge_attr=GraphvizGraphBuilder.DEFAULT_EDGE_ATTR,
        )
        # Map of the roles that have been built so far for all playbooks
        roles_built = {}
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

        return digraph
