import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional
import sys

from ansible.utils.display import Display

from ansibleplaybookgrapher.graph_model import (
    BlockNode,
    RoleNode,
    TaskNode,
    PlayNode,
    PlaybookNode,
)
from ansibleplaybookgrapher.renderer import PlaybookBuilder, Renderer

display = Display()


class JSONRenderer(Renderer):
    def render(
        self,
        open_protocol_handler: Optional[str],
        open_protocol_custom_formats: Optional[Dict[str, str]],
        output_filename: str,
        view: bool,
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

        display.display(f"JSON written to {final_output_path_file}", color="green")

        if view:
            if sys.platform == "win32":
                os.startfile(str(final_output_path_file))
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, str(final_output_path_file)])

        return str(final_output_path_file)


class JSONPlaybookBuilder(PlaybookBuilder):
    def __init__(self, playbook_node: PlaybookNode, open_protocol_handler: str):
        super().__init__(playbook_node, open_protocol_handler)

        self.json_output = {}

    def build_playbook(
        self,
        hide_empty_plays: bool = False,
        hide_plays_without_roles: bool = False,
        **kwargs,
    ) -> str:
        """

        :param hide_empty_plays:
        :param hide_plays_without_roles:
        :param kwargs:
        :return:
        """
        display.vvv(
            f"Converting the playbook '{self.playbook_node.name}' to JSON format"
        )

        self.json_output = self.playbook_node.to_dict(
            hide_empty_plays=hide_empty_plays,
            hide_plays_without_roles=hide_plays_without_roles,
        )

        return json.dumps(self.json_output)

    def build_play(self, play_node: PlayNode, **kwargs):
        """
        Not needed
        :param play_node:
        :param kwargs:
        :return:
        """
        pass

    def build_task(self, task_node: TaskNode, color: str, fontcolor: str, **kwargs):
        """
        Not needed
        :param task_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
        pass

    def build_role(self, role_node: RoleNode, color: str, fontcolor: str, **kwargs):
        """
        Not needed
        :param role_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
        pass

    def build_block(self, block_node: BlockNode, color: str, fontcolor: str, **kwargs):
        """
        Not needed
        :param block_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
        pass
