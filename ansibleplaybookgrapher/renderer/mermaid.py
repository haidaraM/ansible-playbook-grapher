from typing import Dict, Set, List

from ansible.utils.display import Display

from ansibleplaybookgrapher import BlockNode, RoleNode, TaskNode, PlayNode, PlaybookNode
from ansibleplaybookgrapher.renderer import PlaybookBuilder

display = Display()


class MermaidFlowChartRenderer:
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
        **kwargs,
    ) -> str:
        """

        :param open_protocol_handler:
        :param open_protocol_custom_formats:
        :param output_filename: without any extension
        :param kwargs:
        :return:
        """
        # TODO: Add support to customize this
        mermaid_code = "%%{ init: { 'flowchart': { 'curve': 'bumpX' } } }%%\n"
        mermaid_code += "flowchart LR\n"

        # Set of the roles that have been built so far for all the playbooks
        roles_built = set()
        for playbook_node in self.playbook_nodes:
            playbook_builder = MermaidFlowChartPlaybookBuilder(
                playbook_node=playbook_node,
                open_protocol_handler=open_protocol_handler,
                open_protocol_custom_formats=open_protocol_custom_formats,
                roles_usage=self.roles_usage,
                roles_built=roles_built,
            )
            mermaid_code += playbook_builder.build_playbook()
            roles_built.update(playbook_builder.roles_built)

        final_output_filename = f"{output_filename}.mmd"
        with open(final_output_filename, "w") as f:
            f.write(mermaid_code)

        display.display(
            f"Mermaid code written to {final_output_filename}", color="green"
        )
        return final_output_filename


class MermaidFlowChartPlaybookBuilder(PlaybookBuilder):
    def __init__(
        self,
        playbook_node: PlaybookNode,
        open_protocol_handler: str,
        open_protocol_custom_formats: Dict[str, str],
        roles_usage: Dict[RoleNode, Set[PlayNode]],
        roles_built: Set[RoleNode],
    ):
        super().__init__(
            playbook_node,
            open_protocol_handler,
            open_protocol_custom_formats,
            roles_usage,
            roles_built,
        )
        self.mermaid_code = ""

    def build_playbook(self, **kwargs):
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
        self.mermaid_code += f'\t{play_node.id}["{play_node.name}"]\n'

        # From playbook to play
        self.mermaid_code += (
            f"\t{self.playbook_node.id} --> |{play_node.index}| {play_node.id}\n"
        )

        # traverse the play
        self.traverse_play(play_node)

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
            f'\t{task_node.id}["{node_label_prefix}{task_node.name}"]\n'
        )
        # Replace double quotes with single quotes. Mermaid doesn't like double quotes
        when = task_node.when.replace('"', "'")
        # From parent to task
        self.mermaid_code += (
            f'\t{task_node.parent.id} --> |"{task_node.index} {when}"| {task_node.id}\n'
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
        self.mermaid_code += f'\t{role_node.id}("{role_node.name}")\n'
        # from parent to role
        self.mermaid_code += (
            f'\t{role_node.parent.id} --> |"{role_node.index}"| {role_node.id}\n'
        )

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
        self.mermaid_code += f'\t{block_node.id}["[block] {block_node.name}"]\n'
        # from parent to block
        self.mermaid_code += (
            f'\t{block_node.parent.id} --> |"{block_node.index}"| {block_node.id}\n'
        )

        for task in block_node.tasks:
            self.build_node(
                node=task,
                color=color,
                fontcolor=fontcolor,
            )
