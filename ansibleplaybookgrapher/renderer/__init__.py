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
from abc import ABC, abstractmethod
from typing import Dict, Optional, Set

from ansible.utils.display import Display

from ansibleplaybookgrapher.graph import (
    PlaybookNode,
    PlayNode,
    RoleNode,
    Node,
    BlockNode,
    TaskNode,
)

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


class PlaybookBuilder(ABC):
    def __init__(
        self,
        playbook_node: PlaybookNode,
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str] = None,
        roles_usage: Dict[RoleNode, Set[PlayNode]] = None,
        roles_built: Set = None,
    ):
        """

        :param playbook_node: Playbook parsed node
        :param open_protocol_handler: The protocol handler name to use
        :param open_protocol_custom_formats: The custom formats to use when the protocol handler is set to custom
        :param roles_usage: The usage of the roles in the whole playbook
        :param roles_built: The roles that have been "built" so far
        """
        self.playbook_node = playbook_node
        self.roles_usage = roles_usage or playbook_node.roles_usage()
        # A map containing the roles that have been built so far
        self.roles_built = roles_built or set()

        self.open_protocol_handler = open_protocol_handler
        # Merge the two dicts
        formats = {**OPEN_PROTOCOL_HANDLERS, **{"custom": open_protocol_custom_formats}}
        self.open_protocol_formats = formats[self.open_protocol_handler]

    def build_node(self, node: Node, color: str, fontcolor: str, **kwargs):
        """
        Build a generic node.
        :param node: The RoleNode to render
        :param color: The color to apply
        :param fontcolor: The font color to apply
        :return:
        """

        if isinstance(node, BlockNode):
            self.build_block(
                block_node=node, color=color, fontcolor=fontcolor, **kwargs
            )
        elif isinstance(node, RoleNode):
            self.build_role(role_node=node, color=color, fontcolor=fontcolor, **kwargs)
        else:  # This is necessarily a TaskNode
            self.build_task(
                task_node=node,
                color=color,
                fontcolor=fontcolor,
                node_label_prefix=kwargs.pop("node_label_prefix", ""),
                **kwargs,
            )

    @abstractmethod
    def build_playbook(self, **kwargs):
        pass

    @abstractmethod
    def build_play(self, play_node: PlayNode, **kwargs):
        pass

    @abstractmethod
    def build_task(self, task_node: TaskNode, color: str, fontcolor: str, **kwargs):
        """
        Build a single task to be rendered
        :param task_node: The task
        :param fontcolor: The font color to apply
        :param color: Color from the play
        :param kwargs:
        :return:
        """
        pass

    @abstractmethod
    def build_role(self, role_node: RoleNode, color: str, fontcolor: str, **kwargs):
        """
        Render a role in the graph
        :param role_node: The RoleNode to render
        :param color: The color to apply
        :param fontcolor: The font color to apply
        :return:
        """
        pass

    @abstractmethod
    def build_block(self, block_node: BlockNode, color: str, fontcolor: str, **kwargs):
        """
        Build a block to be rendered.
        A BlockNode is a special node: a cluster is created instead of a normal node.
        :param block_node: The BlockNode to build
        :param color: The color from the play to apply
        :param fontcolor: The font color to apply
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
