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

from typing import Dict, List, Set, Tuple

from ansible.utils.display import Display

from ansibleplaybookgrapher.graph_model import (
    PlaybookNode,
    RoleNode,
    PlayNode,
)
from ansibleplaybookgrapher.parser import PlaybookParser
from ansibleplaybookgrapher.utils import merge_dicts
from .graph_model import PlaybookNode, PlayNode, TaskNode, RoleNode, BlockNode
from .parser import PlaybookParser

__version__ = "2.1.2"
__prog__ = "ansible-playbook-grapher"

display = Display()


class Grapher:
    def __init__(self, playbook_filenames: List[str]):
        """
        :param playbook_filenames: List of playbooks to graph
        """
        self.playbook_filenames = playbook_filenames

    def parse(
        self,
        include_role_tasks: bool = False,
        tags: List[str] = None,
        skip_tags: List[str] = None,
        group_roles_by_name: bool = False,
    ) -> Tuple[List[PlaybookNode], Dict[RoleNode, Set[PlayNode]]]:
        """
        Parses all the provided playbooks
        :param include_role_tasks: Should we include the role tasks
        :param tags: Only add plays and tasks tagged with these values
        :param skip_tags: Only add plays and tasks whose tags do not match these values
        :param group_roles_by_name: Group roles by name instead of considering them as separate nodes with different IDs
        :return:
        """
        playbook_nodes = []
        roles_usage: Dict[RoleNode, Set[PlayNode]] = {}

        for playbook_file in self.playbook_filenames:
            display.display(f"Parsing playbook {playbook_file}")
            playbook_parser = PlaybookParser(
                playbook_filename=playbook_file,
                tags=tags,
                skip_tags=skip_tags,
                include_role_tasks=include_role_tasks,
                group_roles_by_name=group_roles_by_name,
            )
            playbook_node = playbook_parser.parse()
            playbook_nodes.append(playbook_node)

            # Update the usage of the roles
            roles_usage = merge_dicts(roles_usage, playbook_node.roles_usage())

        return playbook_nodes, roles_usage
