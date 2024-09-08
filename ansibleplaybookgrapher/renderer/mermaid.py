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

import json
import webbrowser
import zlib
from base64 import urlsafe_b64encode
from pathlib import Path

from ansible.utils.display import Display

from ansibleplaybookgrapher.graph_model import (
    BlockNode,
    PlaybookNode,
    PlayNode,
    RoleNode,
    TaskNode,
)
from ansibleplaybookgrapher.renderer import PlaybookBuilder, Renderer

display = Display()

# Default directive when rendering the graph.
# More info at https://mermaid.js.org/config/directives.html
DEFAULT_DIRECTIVE = '%%{ init: { "flowchart": { "curve": "bumpX" } } }%%'
DEFAULT_ORIENTATION = "LR"  # Left to right


class MermaidFlowChartRenderer(Renderer):
    def render(
        self,
        open_protocol_handler: str,
        open_protocol_custom_formats: dict[str, str],
        output_filename: str,
        view: bool = False,
        hide_empty_plays: bool = False,
        hide_plays_without_roles: bool = False,
        directive: str = DEFAULT_DIRECTIVE,
        orientation: str = DEFAULT_ORIENTATION,
        **kwargs,
    ) -> str:
        """Render the graph to a Mermaid flow chart format.

        :param open_protocol_handler: Not supported for the moment
        :param open_protocol_custom_formats: Not supported for the moment
        :param output_filename: The output filename without any extension
        :param view: Not supported for the moment
        :param hide_empty_plays: Whether to hide empty plays or not when rendering the graph
        :param hide_plays_without_roles: Whether to hide plays without any roles or not
        :param directive: Mermaid directive
        :param orientation: Mermaid graph orientation
        :param kwargs:
        :return:
        """
        # TODO: Add support for protocol handler
        # TODO: Add support for hover

        mermaid_code = "---\n"
        mermaid_code += "title: Ansible Playbook Grapher\n"
        mermaid_code += "---\n"

        display.vvv(f"Using '{directive}' as directive for the mermaid chart")
        mermaid_code += f"{directive}\n"

        mermaid_code += f"flowchart {orientation}\n"

        # Mermaid only supports adding style to links by using the order of the link when it is created
        # https://mermaid.js.org/syntax/flowchart.html#styling-links
        link_order = 0

        # Set of the roles that have been built so far for all the playbooks
        roles_built = set()
        for playbook_node in self.playbook_nodes:
            playbook_builder = MermaidFlowChartPlaybookBuilder(
                playbook_node=playbook_node,
                open_protocol_handler=open_protocol_handler,
                open_protocol_custom_formats=open_protocol_custom_formats,
                roles_usage=self.roles_usage,
                roles_built=roles_built,
                link_order=link_order,
            )

            mermaid_code += playbook_builder.build_playbook(
                hide_empty_plays=hide_empty_plays,
                hide_plays_without_roles=hide_plays_without_roles,
            )
            link_order = playbook_builder.link_order
            roles_built.update(playbook_builder.roles_built)

        final_output_path_file = Path(f"{output_filename}.mmd")
        # Make the sure the parents directories exist
        final_output_path_file.parent.mkdir(exist_ok=True, parents=True)
        final_output_path_file.write_text(mermaid_code)

        display.display(
            f"Mermaid code written to {final_output_path_file}",
            color="green",
        )

        if view:
            MermaidFlowChartRenderer.view(mermaid_code)

        return str(final_output_path_file)

    @staticmethod
    def view(mermaid_code: str) -> None:
        """View the mermaid code in the browser using https://mermaid.live/.

        This is based on:
          - https://github.com/mermaid-js/mermaid-live-editor/blob/b5978e6faf7635e39452855fb4d062d1452ab71b/src/lib/util/serde.ts#L19-L29
          - https://github.com/mermaidjs/mermaid-live-editor/issues/41#issuecomment-1820242778

        :param mermaid_code:
        :return:
        """
        graph_state = {
            "code": mermaid_code,
            "mermaid": {"theme": "default"},
            "autoSync": True,
            "updateDiagram": True,
        }

        compressed = zlib.compress(json.dumps(graph_state).encode("utf-8"), level=9)

        url_path = f'pako:{urlsafe_b64encode(compressed).decode("utf-8")}'
        url = f"https://mermaid.live/edit#{url_path}"

        display.vvv(f"Mermaid live editor URL: {url}")

        # Open the url using the default browser in a new tab.
        webbrowser.open(url, new=2)


class MermaidFlowChartPlaybookBuilder(PlaybookBuilder):
    """ """

    def __init__(
        self,
        playbook_node: PlaybookNode,
        open_protocol_handler: str,
        open_protocol_custom_formats: dict[str, str],
        roles_usage: dict[RoleNode, set[PlayNode]],
        roles_built: set[RoleNode],
        link_order: int = 0,
    ) -> None:
        super().__init__(
            playbook_node,
            open_protocol_handler,
            open_protocol_custom_formats,
            roles_usage,
            roles_built,
        )

        self.mermaid_code = ""
        # Used as an identifier for the links
        self.link_order = link_order
        # The current depth level of the nodes. Used for indentation
        self._indentation_level = 1

    def build_playbook(
        self,
        hide_empty_plays: bool = False,
        hide_plays_without_roles: bool = False,
        **kwargs,
    ) -> str:
        """Build a playbook.

        :param hide_plays_without_roles: Whether to hide plays without any roles or not
        :param hide_empty_plays: Whether to hide empty plays or not
        :param hide_plays_without_roles: Whether to hide plays without any roles or not
        :param kwargs:
        :return:
        """
        display.vvv(
            f"Converting the playbook '{self.playbook_node.name}' to mermaid format",
        )

        # Playbook node
        self.add_comment(f"Start of the playbook '{self.playbook_node.name}'")
        self.add_text(f'{self.playbook_node.id}("{self.playbook_node.name}")')

        self._indentation_level += 1
        for play_node in self.playbook_node.plays(
            exclude_empty=hide_empty_plays,
            exclude_without_roles=hide_plays_without_roles,
        ):
            self.build_play(play_node)
        self._indentation_level -= 1

        self.add_comment(f"End of the playbook '{self.playbook_node.name}'\n")

        return self.mermaid_code

    def build_play(self, play_node: PlayNode, **kwargs) -> None:
        """Build a play.

        :param play_node:
        :param kwargs:
        :return:
        """
        # Play node
        color, play_font_color = play_node.colors
        self.add_comment(f"Start of the play '{play_node.name}'")

        self.add_text(f'{play_node.id}["{play_node.name}"]')
        self.add_text(f"style {play_node.id} fill:{color},color:{play_font_color}")

        # From playbook to play
        self.add_link(
            source_id=play_node.parent.id,
            text=f"{play_node.index}",
            dest_id=play_node.id,
            style=f"stroke:{color},color:{color}",
        )

        # traverse the play
        self._indentation_level += 1
        self.traverse_play(play_node)
        self._indentation_level -= 1

        self.add_comment(f"End of the play '{play_node.name}'")

    def build_task(
        self,
        task_node: TaskNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """Build a task.

        :param task_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
        node_label_prefix = kwargs.get("node_label_prefix", "")

        # Task node
        self.add_text(f'{task_node.id}["{node_label_prefix} {task_node.name}"]')
        self.add_text(f"style {task_node.id} stroke:{color},fill:{fontcolor}")

        # From parent to task
        self.add_link(
            source_id=task_node.parent.id,
            text=f"{task_node.index} {task_node.when}",
            dest_id=task_node.id,
            style=f"stroke:{color},color:{color}",
        )

    def build_role(
        self,
        role_node: RoleNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """Build a role.

        :param role_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
        self.add_comment(f"Start of the role '{role_node.name}'")

        plays_using_this_role = len(self.roles_usage[role_node])
        node_color = color
        if plays_using_this_role > 1:
            # If the role is used in multiple plays, we take black as the default color
            node_color = "#000000"  # black

        # From parent to role
        self.add_link(
            source_id=role_node.parent.id,
            text=f"{role_node.index} {role_node.when}",
            dest_id=role_node.id,
            style=f"stroke:{color},color:{node_color}",
        )

        # Check if we already built this role
        if role_node in self.roles_built:
            return

        self.roles_built.add(role_node)

        # Role node
        self.add_text(f'{role_node.id}("[role] {role_node.name}")')
        self.add_text(
            f"style {role_node.id} fill:{node_color},color:{fontcolor},stroke:{node_color}",
        )

        # Role tasks
        self._indentation_level += 1
        for role_task in role_node.tasks:
            self.build_node(
                node=role_task,
                color=node_color,
                fontcolor=fontcolor,
            )
        self._indentation_level -= 1

        self.add_comment(f"End of the role '{role_node.name}'")

    def build_block(
        self,
        block_node: BlockNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """Build a block.

        :param block_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
        # Block node
        self.add_comment(f"Start of the block '{block_node.name}'")
        self.add_text(f'{block_node.id}["[block] {block_node.name}"]')
        self.add_text(
            f"style {block_node.id} fill:{color},color:{fontcolor},stroke:{color}",
        )

        # from parent to block
        self.add_link(
            source_id=block_node.parent.id,
            text=f"{block_node.index} {block_node.when}",
            dest_id=block_node.id,
            style=f"stroke:{color},color:{color}",
        )

        self.add_text(f'subgraph subgraph_{block_node.id}["{block_node.name} "]')

        self._indentation_level += 1
        for task in block_node.tasks:
            self.build_node(
                node=task,
                color=color,
                fontcolor=fontcolor,
            )
        self._indentation_level -= 1

        self.add_text("end")  # End of the subgraph
        self.add_comment(f"End of the block '{block_node.name}'")

    def add_link(
        self,
        source_id: str,
        text: str,
        dest_id: str,
        style: str = "",
        link_type: str = "--",
    ) -> None:
        """Add link between two nodes.

        :param source_id: The link source
        :param text: The text on the link
        :param dest_id: The link destination
        :param style: The style to apply to the link
        :param link_type: Type of link to create. https://mermaid.js.org/syntax/flowchart.html#links-between-nodes
        :return:
        """
        # Replace double quotes with single quotes. Mermaid doesn't like double quotes
        text = text.replace('"', "'").strip()
        self.add_text(f'{source_id} {link_type}> |"{text}"| {dest_id}')

        if style != "" or style is not None:
            self.add_text(f"linkStyle {self.link_order} {style}")

        self.link_order += 1

    def add_comment(self, text: str) -> None:
        """Add a comment to the mermaid code.

        :param text: The text used as a comment
        :return:
        """
        self.mermaid_code += f"{self.indentation}%% {text}\n"

    def add_text(self, text: str) -> None:
        """Add a text to the mermaid diagram.

        :param text:
        :return:
        """
        self.mermaid_code += f"{self.indentation}{text.strip()}\n"

    @property
    def indentation(self) -> str:
        """Return the current indentation level as tabulations.

        :return:
        """
        return "\t" * self._indentation_level
