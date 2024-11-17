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


from ansibleplaybookgrapher.graph_model import (
    PlaybookNode,
    PlayNode,
    RoleNode,
)
from ansibleplaybookgrapher.parser import PlaybookParser
from ansibleplaybookgrapher.utils import merge_dicts


class Grapher:
    def __init__(self, playbooks_mapping: dict[str, str]) -> None:
        """

        :param playbooks_mapping: Mapping of playbook args to their paths.
        """
        self.playbooks_mapping = playbooks_mapping

    def parse(
        self,
        include_role_tasks: bool = False,
        tags: list[str] | None = None,
        skip_tags: list[str] | None = None,
        group_roles_by_name: bool = False,
    ) -> tuple[list[PlaybookNode], dict[RoleNode, set[PlayNode]]]:
        """Parses all the provided playbooks

        :param include_role_tasks: Should we include the role tasks
        :param tags: Only add plays and tasks tagged with these values
        :param skip_tags: Only add plays and tasks whose tags do not match these values
        :param group_roles_by_name: Group roles by name instead of considering them as separate nodes with different IDs
        :return: Tuple of the list of playbook nodes and the dictionary of the role usages: the key is the role and the
        value is the set of plays that use the role.
        """
        playbook_nodes = []
        roles_usage: dict[RoleNode, set[PlayNode]] = {}

        counter = 1
        for playbook_arg in self.playbooks_mapping:
            playbook_parser = PlaybookParser(
                playbook_path=self.playbooks_mapping[playbook_arg],
                tags=tags,
                skip_tags=skip_tags,
                include_role_tasks=include_role_tasks,
                group_roles_by_name=group_roles_by_name,
                playbook_name=playbook_arg,
            )
            playbook_node = playbook_parser.parse()
            playbook_node.index = counter
            playbook_nodes.append(playbook_node)

            # Update the usage of the roles
            roles_usage = merge_dicts(roles_usage, playbook_node.roles_usage())
            counter += 1

        return playbook_nodes, roles_usage
