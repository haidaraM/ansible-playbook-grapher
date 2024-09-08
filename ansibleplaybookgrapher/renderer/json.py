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
import os
import subprocess
import sys
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


class JSONRenderer(Renderer):
    """A renderer that writes the graph to a JSON file."""

    def render(
        self,
        open_protocol_handler: str | None,
        open_protocol_custom_formats: dict[str, str] | None,
        output_filename: str,
        view: bool = False,
        hide_empty_plays: bool = False,
        hide_plays_without_roles: bool = False,
        **kwargs,
    ) -> str:
        playbooks = []

        for playbook_node in self.playbook_nodes:
            json_builder = JSONPlaybookBuilder(playbook_node, open_protocol_handler)
            json_builder.build_playbook(
                hide_empty_plays=hide_empty_plays,
                hide_plays_without_roles=hide_plays_without_roles,
            )

            playbooks.append(json_builder.json_output)

        output = {
            "version": 1,
            "playbooks": playbooks,
        }

        final_output_path_file = Path(f"{output_filename}.json")
        # Make the sure the parents directories exist
        final_output_path_file.parent.mkdir(exist_ok=True, parents=True)
        dump_str = json.dumps(output, indent=2)
        final_output_path_file.write_text(dump_str)

        display.display(f"JSON file written to {final_output_path_file}", color="green")

        if view:
            if sys.platform == "win32":
                os.startfile(str(final_output_path_file))
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, str(final_output_path_file)])

        return str(final_output_path_file)


class JSONPlaybookBuilder(PlaybookBuilder):
    def __init__(self, playbook_node: PlaybookNode, open_protocol_handler: str) -> None:
        super().__init__(playbook_node, open_protocol_handler)

        self.json_output = {}

    def build_playbook(
        self,
        hide_empty_plays: bool = False,
        hide_plays_without_roles: bool = False,
        **kwargs,
    ) -> str:
        """Build a playbook.

        :param hide_empty_plays:
        :param hide_plays_without_roles:
        :param kwargs:
        :return:
        """
        display.vvv(
            f"Converting the playbook '{self.playbook_node.name}' to JSON format",
        )

        self.json_output = self.playbook_node.to_dict(
            exclude_empty_plays=hide_empty_plays,
            exclude_plays_without_roles=hide_plays_without_roles,
        )

        return json.dumps(self.json_output)

    def build_play(self, play_node: PlayNode, **kwargs) -> None:
        """Not needed.

        :param play_node:
        :param kwargs:
        :return:
        """

    def build_task(
        self,
        task_node: TaskNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """Not needed.

        :param task_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """

    def build_role(
        self,
        role_node: RoleNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """Not needed.

        :param role_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """

    def build_block(
        self,
        block_node: BlockNode,
        color: str,
        fontcolor: str,
        **kwargs,
    ) -> None:
        """Not needed.

        :param block_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
