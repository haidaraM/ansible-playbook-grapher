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
        # TODO: Add support to customize this
        # TODO: Add support for protocol handler
        # TODO: Add support for hover
        mermaid_code = "---\n"
        mermaid_code += "title: Ansible Playbook Grapher\n"
        mermaid_code += "---\n"

        mermaid_code = "%%{ init: { 'flowchart': { 'curve': 'bumpX' } } }%%\n"
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
        self.link_order = link_order

    def build_playbook(self, **kwargs):
        """
        Build the playbook
        :param kwargs:
        :return:
        """
        display.vvv(f"Converting the graph to the dot format for graphviz")

        # Playbook node
        playbook = f'\t{self.playbook_node.id}("{self.playbook_node.name}")\n'
        self.mermaid_code += playbook

        for play_node in self.playbook_node.plays:
            self.build_play(play_node)

        return self.mermaid_code

    def build_play(self, play_node: PlayNode, **kwargs):
        """

        :param play_node:
        :param kwargs:
        :return:
        """
        # Play node
        color, play_font_color = play_node.colors
        self.mermaid_code += f"\t%% Start of play {play_node.name}\n"
        self.mermaid_code += f'\t{play_node.id}["{play_node.name}"]\n'
        self.mermaid_code += (
            f"\tstyle {play_node.id} fill:{color},color:{play_font_color}\n"
        )

        # From playbook to play
        self.mermaid_code += (
            f'\t{self.playbook_node.id} --> |"{play_node.index}"| {play_node.id}\n'
        )
        self.mermaid_code += (
            f"\tlinkStyle {self.link_order} stroke:{color},color:{color}\n"
        )
        self.link_order += 1

        # traverse the play
        self.traverse_play(play_node)

        self.mermaid_code += f"\t%% End of play {play_node.name}\n"
        self.mermaid_code += "\n\n"

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
            f'\t\t{task_node.id}["{node_label_prefix}{task_node.name}"]\n'
        )
        self.mermaid_code += (
            f"\t\tstyle {task_node.id} stroke:{color},fill:{fontcolor}\n"
        )

        # Replace double quotes with single quotes. Mermaid doesn't like double quotes
        when = task_node.when.replace('"', "'")
        link_label = f"{task_node.index} {when}".strip()
        # From parent to task
        self.mermaid_code += (
            f'\t\t{task_node.parent.id} --> |"{link_label}"| {task_node.id}\n'
        )
        self.mermaid_code += (
            f"\t\tlinkStyle {self.link_order} stroke:{color},color:{color}\n"
        )
        self.link_order += 1

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
        self.mermaid_code += f'\t\t{role_node.id}("[role] {role_node.name}")\n'
        self.mermaid_code += (
            f"\t\tstyle {role_node.id} fill:{color},color:{fontcolor},stroke:{color}\n"
        )
        # from parent to role
        when = role_node.when.replace('"', "'")
        link_label = f"{role_node.index} {when}".strip()
        self.mermaid_code += (
            f'\t{role_node.parent.id} --> |"{link_label}"| {role_node.id}\n'
        )
        self.mermaid_code += (
            f"\t\tlinkStyle {self.link_order} stroke:{color},color:{color}\n"
        )
        self.link_order += 1

        # role tasks
        for role_task in role_node.tasks:
            self.build_node(
                node=role_task,
                color=color,
                fontcolor=fontcolor,
            )

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
        self.mermaid_code += f'\t\t{block_node.id}["[block] {block_node.name}"]\n'
        self.mermaid_code += (
            f"\t\tstyle {block_node.id} fill:{color},color:{fontcolor},stroke:{color}\n"
        )
        # from parent to block
        when = block_node.when.replace('"', "'")
        link_label = f"{block_node.index} {when}".strip()
        self.mermaid_code += (
            f'\t\t{block_node.parent.id} --> |"{link_label}"| {block_node.id}\n'
        )
        self.mermaid_code += (
            f"\t\tlinkStyle {self.link_order} stroke:{color},color:{color}\n"
        )
        self.link_order += 1

        for task in block_node.tasks:
            self.build_node(
                node=task,
                color=color,
                fontcolor=fontcolor,
            )
