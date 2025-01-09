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
from abc import ABC, abstractmethod

from ansible.utils.display import Display

from ansibleplaybookgrapher.graph_model import (
    BlockNode,
    Node,
    PlaybookNode,
    PlayNode,
    RoleNode,
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


class Renderer(ABC):
    def __init__(
        self,
        playbook_nodes: list[PlaybookNode],
        roles_usage: dict[RoleNode, set[PlayNode]],
    ) -> None:
        self.playbook_nodes = playbook_nodes
        self.roles_usage = roles_usage

    @abstractmethod
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
        :return:
        """


class PlaybookBuilder(ABC):
    """This is the base class to inherit from by the renderer to build a single Playbook in the target format.
    It provides some methods that MUST be implemented.
    """

    def __init__(
        self,
        playbook_node: PlaybookNode,
        open_protocol_handler: str | None,
        open_protocol_custom_formats: dict[str, str] | None = None,
        roles_usage: dict[RoleNode, set[PlayNode]] | None = None,
        roles_built: set[Node] | None = None,
        include_role_tasks: bool = False,
        show_handlers: bool = False,
    ) -> None:
        """The base class for all playbook builders.

        :param playbook_node: Playbook parsed node
        :param open_protocol_handler: The protocol handler name to use
        :param open_protocol_custom_formats: The custom formats to use when the protocol handler is set to custom
        :param roles_usage: The usage of the roles in the whole playbook
        :param roles_built: The roles that have been "built" so far.
        :param include_role_tasks: Whether to include the tasks of the roles in the graph or not.
        :param show_handlers: Whether to show the handlers or not.
        """
        self.playbook_node = playbook_node
        self.roles_usage = roles_usage or playbook_node.roles_usage()
        # A map containing the roles that have been built so far
        self.roles_built = roles_built or set()
        self.include_role_tasks = include_role_tasks
        self.show_handlers = show_handlers

        self.open_protocol_handler = open_protocol_handler
        self.open_protocol_formats = None
        # Merge the two dicts
        formats = {**OPEN_PROTOCOL_HANDLERS, "custom": open_protocol_custom_formats}
        if self.open_protocol_handler:
            self.open_protocol_formats = formats[self.open_protocol_handler]

    def build_node(
        self, play_node: PlayNode, node: Node, color: str, fontcolor: str, **kwargs
    ) -> None:
        """Build a generic node.

        :param play_node: The PlayNode to which the node belongs.
        :param node: The Node to render
        :param color: The color to apply.
        :param fontcolor: The font color to apply.
        :return:
        """

        if node.is_hidden:
            return

        if isinstance(node, BlockNode):
            # Only build the block if it is not empty or if it has a role node when we only want roles
            if not node.is_empty():
                self.build_block(
                    play_node=play_node,
                    block_node=node,
                    color=color,
                    fontcolor=fontcolor,
                    **kwargs,
                )
        elif isinstance(node, RoleNode):
            if not node.is_empty():
                self.build_role(
                    play_node=play_node,
                    role_node=node,
                    color=color,
                    fontcolor=fontcolor,
                    **kwargs,
                )
        elif isinstance(node, TaskNode):
            self.build_task(
                play_node=play_node,
                task_node=node,
                color=color,
                fontcolor=fontcolor,
                **kwargs,
            )
        else:
            msg = f"Unsupported node type: {type(node)}. This is likely a bug that should be reported"
            raise Exception(
                msg,
            )

    @abstractmethod
    def build_playbook(
        self,
        **kwargs,
    ) -> str:
        """Build the whole playbook

        :param kwargs:
        :return: The rendered playbook as a string.
        """

    @abstractmethod
    def build_play(self, play_node: PlayNode, **kwargs) -> None:
        """Build a single play to be rendered

        :param play_node: The play to render
        :param kwargs:
        :return:
        """

    def traverse_play(self, play_node: PlayNode, **kwargs) -> None:
        """Traverse a play to build the graph: pre_tasks, roles, tasks, post_tasks, handlers.

        :param play_node:
        :param kwargs:
        :return:
        """
        color, play_font_color = play_node.colors
        # pre_tasks
        for pre_task in play_node.pre_tasks:
            self.build_node(
                play_node=play_node,
                node=pre_task,
                color=color,
                fontcolor=play_font_color,
                **kwargs,
            )

        # roles
        for role in play_node.roles:
            if role.is_empty():
                continue

            self.build_role(
                play_node=play_node,
                color=color,
                fontcolor=play_font_color,
                role_node=role,
                **kwargs,
            )

        # tasks
        for task in play_node.tasks:
            self.build_node(
                play_node=play_node,
                node=task,
                color=color,
                fontcolor=play_font_color,
                **kwargs,
            )

        # post_tasks
        for post_task in play_node.post_tasks:
            self.build_node(
                play_node=play_node,
                node=post_task,
                color=color,
                fontcolor=play_font_color,
                **kwargs,
            )

        if self.show_handlers:
            # play handlers
            for p_handler in play_node.handlers:
                self.build_node(
                    play_node=play_node,
                    node=p_handler,
                    color=color,
                    fontcolor=play_font_color,
                    **kwargs,
                )

    @abstractmethod
    def build_task(
        self,
        play_node: PlayNode,
        task_node: TaskNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """Build a single task to be rendered.

        :param play_node: The play to which the task belongs
        :param task_node: The task
        :param fontcolor: The font color to apply
        :param color: Color from the play
        :param kwargs:
        :return:
        """

    @abstractmethod
    def build_role(
        self,
        play_node: PlayNode,
        role_node: RoleNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """Render a role in the graph

        :param play_node: The PlayNode to which the role belongs.
        :param role_node: The RoleNode to render
        :param color: The color to apply
        :param fontcolor: The font color to apply
        :return:
        """

    @abstractmethod
    def build_block(
        self,
        play_node: PlayNode,
        block_node: BlockNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """Build a block to be rendered.
        A BlockNode is a special node: a cluster is created instead of a normal node.

        :param play_node: The PlayNode to which the block belongs.
        :param block_node: The BlockNode to build
        :param color: The color from the play to apply
        :param fontcolor: The font color to apply
        :return:
        """

    def get_node_url(self, node: Node) -> str | None:
        """Get the node url based on the chosen open protocol.

        :param node: the node to get the url for
        :return:
        """
        if node.location and node.location.path:
            remove_from_path = self.open_protocol_formats.get("remove_from_path", "")
            path = node.location.path.replace(remove_from_path, "")

            url = self.open_protocol_formats[node.location.type].format(
                path=path,
                line=node.location.line,
                column=node.location.column,
            )
            display.vvvv(f"Open protocol URL for node {node}: {url}")
            return url

        return None


def log_handlers_not_found(
    play_node: PlayNode, task_node: TaskNode, handlers_not_found: list[str]
) -> None:
    """Log the handlers that have not been found.

    :param play_node: The play node
    :param task_node: The task node
    :param handlers_not_found: The handlers that have not been found.
    :return:
    """
    for handler in handlers_not_found:
        display.warning(
            f"The handler '{handler}' notified by the task '{task_node.display_name()}' has not been found in the play '{play_node.display_name()}'."
        )
