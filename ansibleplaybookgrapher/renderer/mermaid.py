from pathlib import Path
from typing import Dict, Set, List

from ansible.utils.display import Display

from ansibleplaybookgrapher import BlockNode, RoleNode, TaskNode, PlayNode, PlaybookNode
from ansibleplaybookgrapher.renderer import PlaybookBuilder, Renderer

display = Display()


class MermaidFlowChartRenderer(Renderer):
    def __init__(
        self,
        playbook_nodes: List[PlaybookNode],
        roles_usage: Dict["RoleNode", Set[PlayNode]],
    ):
        self.playbook_nodes = playbook_nodes
        self.roles_usage = roles_usage

    def render(
        self,
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str],
        output_filename: str,
        view: bool,
        **kwargs,
    ) -> str:
        """

        :param open_protocol_handler:
        :param open_protocol_custom_formats:
        :param output_filename: without any extension
        :param view:
        :param kwargs:
        :return:
        """
        # TODO: Add support for protocol handler
        # TODO: Add support for hover
        mermaid_code = "---\n"
        mermaid_code += "title: Ansible Playbook Grapher\n"
        mermaid_code += "---\n"

        # TODO: Add support to customize this
        mermaid_code += "%%{ init: { 'flowchart': { 'curve': 'bumpX' } } }%%\n"
        mermaid_code += "flowchart LR\n"

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

            mermaid_code += playbook_builder.build_playbook()
            link_order += playbook_builder.link_order
            roles_built.update(playbook_builder.roles_built)

        final_output_path_file = Path(f"{output_filename}.mmd")
        # Make the sure the parents directories exist
        final_output_path_file.parent.mkdir(exist_ok=True, parents=True)
        final_output_path_file.write_text(mermaid_code)

        display.display(
            f"Mermaid code written to {final_output_path_file}", color="green"
        )
        # TODO: implement the view option
        #  https://github.com/mermaidjs/mermaid-live-editor/issues/41
        #  https://mermaid.ink/
        return final_output_path_file


class MermaidFlowChartPlaybookBuilder(PlaybookBuilder):
    def __init__(
        self,
        playbook_node: PlaybookNode,
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str],
        roles_usage: Dict[RoleNode, Set[PlayNode]],
        roles_built: Set[RoleNode],
        link_order: int = 0,
    ):
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
        self.depth_level = 1

    def build_playbook(self, **kwargs) -> str:
        """
        Build the playbook
        :param kwargs:
        :return:
        """
        display.vvv(f"Converting the playbook to mermaid format")

        # Playbook node
        self.add_comment(f"Start of playbook {self.playbook_node.name}")
        playbook = f'\t{self.playbook_node.id}("{self.playbook_node.name}")\n'
        self.mermaid_code += playbook

        self.depth_level += 1
        for play_node in self.playbook_node.plays:
            self.build_play(play_node)
        self.depth_level -= 1
        self.add_comment(f"End of playbook {self.playbook_node.name}")

        return self.mermaid_code

    def build_play(self, play_node: PlayNode, **kwargs):
        """

        :param play_node:
        :param kwargs:
        :return:
        """
        # Play node
        color, play_font_color = play_node.colors
        self.add_comment(f"Start of play {play_node.name}")

        self.mermaid_code += f'{self.indentation}{play_node.id}["{play_node.name}"]\n'
        self.mermaid_code += f"{self.indentation}style {play_node.id} fill:{color},color:{play_font_color}\n"

        # From playbook to play
        self.add_link(
            source_id=self.playbook_node.id,
            text=f"{play_node.index}",
            dest_id=play_node.id,
            style=f"stroke:{color},color:{color}",
        )

        # traverse the play
        self.depth_level += 1
        self.traverse_play(play_node)
        self.depth_level -= 1

        self.add_comment(f"End of play {play_node.name}")
        self.mermaid_code += "\n"

    def build_task(self, task_node: TaskNode, color: str, fontcolor: str, **kwargs):
        """

        :param task_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
        node_label_prefix = kwargs.get("node_label_prefix", "")
        # Task node
        self.mermaid_code += (
            f'{self.indentation}{task_node.id}["{node_label_prefix}{task_node.name}"]\n'
        )
        self.mermaid_code += (
            f"{self.indentation}style {task_node.id} stroke:{color},fill:{fontcolor}\n"
        )

        # From parent to task
        self.add_link(
            source_id=task_node.parent.id,
            text=f"{task_node.index} {task_node.when}",
            dest_id=task_node.id,
            style=f"stroke:{color},color:{color}",
        )

    def build_role(self, role_node: RoleNode, color: str, fontcolor: str, **kwargs):
        """

        :param role_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """

        # check if we already built this role
        if role_node in self.roles_built:
            return
        self.roles_built.add(role_node)

        # Role node
        self.mermaid_code += (
            f'{self.indentation}{role_node.id}("[role] {role_node.name}")\n'
        )
        self.mermaid_code += f"{self.indentation}style {role_node.id} fill:{color},color:{fontcolor},stroke:{color}\n"
        # from parent to role
        self.add_link(
            source_id=role_node.parent.id,
            text=f"{role_node.index} {role_node.when}",
            dest_id=role_node.id,
            style=f"stroke:{color},color:{color}",
        )

        # role tasks
        self.depth_level += 1
        for role_task in role_node.tasks:
            self.build_node(
                node=role_task,
                color=color,
                fontcolor=fontcolor,
            )
        self.depth_level -= 1

    def build_block(self, block_node: BlockNode, color: str, fontcolor: str, **kwargs):
        """

        :param block_node:
        :param color:
        :param fontcolor:
        :param kwargs:
        :return:
        """
        # TODO: add support for subgraph for blocks
        # Block node
        self.mermaid_code += (
            f'{self.indentation}{block_node.id}["[block] {block_node.name}"]\n'
        )
        self.mermaid_code += f"{self.indentation}style {block_node.id} fill:{color},color:{fontcolor},stroke:{color}\n"
        # from parent to block
        self.add_link(
            source_id=block_node.parent.id,
            text=f"{block_node.index} {block_node.when}",
            dest_id=block_node.id,
            style=f"stroke:{color},color:{color}",
        )

        self.depth_level += 1
        for task in block_node.tasks:
            self.build_node(
                node=task,
                color=color,
                fontcolor=fontcolor,
            )
        self.depth_level -= 1

    def add_link(
        self,
        source_id: str,
        text: str,
        dest_id: str,
        style: str = "",
        link_type: str = "--",
    ):
        """
        Add link between two nodes
        :param source_id: The link source
        :param text: The text on the link
        :param dest_id: The link destination
        :param style: The style to apply to the link
        :param link_type: Type of link to create. https://mermaid.js.org/syntax/flowchart.html#links-between-nodes
        :return:
        """
        # Replace double quotes with single quotes. Mermaid doesn't like double quotes
        text = text.replace('"', "'").strip()
        self.mermaid_code += (
            f'{self.indentation}{source_id} {link_type}> |"{text}"| {dest_id}\n'
        )

        if style != "" or style is not None:
            self.mermaid_code += (
                f"{self.indentation}linkStyle {self.link_order} {style}\n"
            )

        self.link_order += 1

    def add_comment(self, text: str):
        """
        Add a comment to the mermaid code
        :param text: The text used as a comment
        :return:
        """
        self.mermaid_code += f"{self.indentation}%% {text}\n"

    @property
    def indentation(self):
        """
        Return the current indentation level
        :return:
        """
        return "\t" * self.depth_level
