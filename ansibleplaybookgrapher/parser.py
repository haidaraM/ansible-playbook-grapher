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
from typing import Dict, Union, List

from ansible.cli import CLI
from ansible.errors import AnsibleParserError, AnsibleUndefinedVariable, AnsibleError
from ansible.parsing.yaml.objects import AnsibleUnicode
from ansible.playbook import Playbook
from ansible.playbook.block import Block
from ansible.playbook.helpers import load_list_of_blocks
from ansible.playbook.play import Play
from ansible.playbook.role import Role
from ansible.playbook.role_include import IncludeRole
from ansible.playbook.task import Task
from ansible.playbook.task_include import TaskInclude
from ansible.template import Templar
from ansible.utils.display import Display

from ansibleplaybookgrapher.graph_model import (
    TaskNode,
    PlaybookNode,
    RoleNode,
    PlayNode,
    CompositeNode,
    BlockNode,
)
from ansibleplaybookgrapher.utils import (
    clean_name,
    handle_include_path,
    has_role_parent,
    generate_id,
    convert_when_to_str,
    hash_value,
)

display = Display()


class BaseParser(ABC):
    """
    Base Parser of a playbook
    """

    def __init__(self, tags: List[str] = None, skip_tags: List[str] = None):
        """

        :param tags: Only add plays and tasks tagged with these values
        :param skip_tags: Only add plays and tasks whose tags do not match these values
        """
        loader, inventory, variable_manager = CLI._play_prereqs()
        self.data_loader = loader
        self.inventory_manager = inventory
        self.variable_manager = variable_manager

        self.tags = tags or ["all"]
        self.skip_tags = skip_tags or []

    @abstractmethod
    def parse(self, *args, **kwargs) -> PlaybookNode:
        pass

    def template(
        self, data: Union[str, AnsibleUnicode], variables: Dict, fail_on_undefined=False
    ) -> Union[str, AnsibleUnicode]:
        """
        Template the data using Jinja. Return data if an error occurs during the templating
        :param data:
        :param fail_on_undefined:
        :param variables:
        :return:
        """
        try:
            templar = Templar(loader=self.data_loader, variables=variables)
            return templar.template(data, fail_on_undefined=fail_on_undefined)
        except AnsibleError as ansible_error:
            # Sometimes we need to export
            if fail_on_undefined:
                raise
            display.warning(ansible_error)
            return data

    def _add_task(
        self, task: Task, task_vars: Dict, node_type: str, parent_node: CompositeNode
    ) -> bool:
        """
        Include the task in the graph.
        :return: True if the task has been included, false otherwise
        """

        # Ansible-core 2.11 added an implicit meta tasks at the end of the role. So wee skip it here.
        if task.action == "meta" and task.implicit:
            return False

        if not task.evaluate_tags(
            only_tags=self.tags, skip_tags=self.skip_tags, all_vars=task_vars
        ):
            display.vv(f"The task '{task.get_name()}' is skipped due to the tags.")
            return False

        display.vv(f"Adding {node_type} '{task.get_name()}' to the graph")

        task_name = clean_name(self.template(task.get_name(), task_vars))
        parent_node.add_node(
            target_composition=f"{node_type}s",
            node=TaskNode(
                task_name,
                generate_id(f"{node_type}_"),
                when=convert_when_to_str(task.when),
                raw_object=task,
                parent=parent_node,
            ),
        )

        return True


class PlaybookParser(BaseParser):
    """
    The playbook parser. This is the main entrypoint responsible to parser the playbook into a graph structure
    """

    def __init__(
        self,
        playbook_filename: str,
        include_role_tasks=False,
        tags: List[str] = None,
        skip_tags: List[str] = None,
        group_roles_by_name: bool = False,
    ):
        """
        :param playbook_filename: The filename of the playbook to parse
        :param include_role_tasks: If true, the tasks of the role will be included in the graph
        :param tags: Only add plays and tasks tagged with these values
        :param skip_tags: Only add plays and tasks whose tags do not match these values
        :param group_roles_by_name: Group roles by name instead of considering them as separate nodes with different IDs
        """

        super().__init__(tags=tags, skip_tags=skip_tags)
        self.group_roles_by_name = group_roles_by_name
        self.include_role_tasks = include_role_tasks
        self.playbook_filename = playbook_filename

    def parse(self, *args, **kwargs) -> PlaybookNode:
        """
        Loop through the playbook and generate the graph.

        The graph is drawn following this order (https://docs.ansible.com/ansible/2.4/playbooks_reuse_roles.html#using-roles)
        for each play:
            add pre_tasks
            add roles
                if  include_role_tasks
                    add role_tasks
            add tasks
            add post_tasks
        :return:
        """

        playbook = Playbook.load(
            self.playbook_filename,
            loader=self.data_loader,
            variable_manager=self.variable_manager,
        )
        # the root node
        playbook_root_node = PlaybookNode(self.playbook_filename, raw_object=playbook)
        # loop through the plays
        for play in playbook.get_plays():
            # the load basedir is relative to the playbook path
            if play._included_path is not None:
                self.data_loader.set_basedir(play._included_path)
            else:
                self.data_loader.set_basedir(playbook._basedir)
            display.vvv(f"Loader basedir set to {self.data_loader.get_basedir()}")

            play_vars = self.variable_manager.get_vars(play)
            play_hosts = [
                h.get_name()
                for h in self.inventory_manager.get_hosts(
                    self.template(play.hosts, play_vars)
                )
            ]
            play_name = f"Play: {clean_name(play.get_name())} ({len(play_hosts)})"
            play_name = self.template(play_name, play_vars)

            display.v(f"Parsing {play_name}")

            play_node = PlayNode(
                play_name, hosts=play_hosts, raw_object=play, parent=playbook_root_node
            )
            playbook_root_node.add_node("plays", play_node)

            # loop through the pre_tasks
            display.v("Parsing pre_tasks...")
            for pre_task_block in play.pre_tasks:
                self._include_tasks_in_blocks(
                    current_play=play,
                    parent_nodes=[play_node],
                    block=pre_task_block,
                    play_vars=play_vars,
                    node_type="pre_task",
                )

            # loop through the roles
            display.v("Parsing roles...")

            for role in play.get_roles():  # type: Role
                # Don't insert tasks from ``import/include_role``, preventing duplicate graphing
                if role.from_include:
                    continue

                # the role object doesn't inherit the tags from the play. So we add it manually.
                role.tags = role.tags + play.tags

                # More context on this line, see here: https://github.com/ansible/ansible/issues/82310
                # This seems to work for now.
                role._parent = None

                if not role.evaluate_tags(
                    only_tags=self.tags, skip_tags=self.skip_tags, all_vars=play_vars
                ):
                    display.vv(
                        f"The role '{role.get_name()}' is skipped due to the tags."
                    )
                    # Go to the next role
                    continue

                if self.group_roles_by_name:
                    # If we are grouping roles, we use the hash of role name as the node id
                    role_node_id = "role_" + hash_value(role.get_name())
                else:
                    # Otherwise, a random id is used
                    role_node_id = generate_id("role_")
                role_node = RoleNode(
                    clean_name(role.get_name()),
                    node_id=role_node_id,
                    raw_object=role,
                    parent=play_node,
                )
                # edge from play to role
                play_node.add_node("roles", role_node)

                if self.include_role_tasks:
                    # loop through the tasks of the roles
                    for block in role.compile(play):
                        self._include_tasks_in_blocks(
                            current_play=play,
                            parent_nodes=[role_node],
                            block=block,
                            play_vars=play_vars,
                            node_type="task",
                        )
                    # end of roles loop

            # loop through the tasks
            display.v("Parsing tasks...")
            for task_block in play.tasks:
                self._include_tasks_in_blocks(
                    current_play=play,
                    parent_nodes=[play_node],
                    block=task_block,
                    play_vars=play_vars,
                    node_type="task",
                )

            # loop through the post_tasks
            display.v("Parsing post_tasks...")
            for post_task_block in play.post_tasks:
                self._include_tasks_in_blocks(
                    current_play=play,
                    parent_nodes=[play_node],
                    block=post_task_block,
                    play_vars=play_vars,
                    node_type="post_task",
                )
            # Summary
            display.v(f"{len(play_node.pre_tasks)} pre_task(s) added to the graph.")
            display.v(f"{len(play_node.roles)} role(s) added to the play")
            display.v(f"{len(play_node.tasks)} task(s) added to the play")
            display.v(f"{len(play_node.post_tasks)} post_task(s) added to the play")
            # moving to the next play

        return playbook_root_node

    def _include_tasks_in_blocks(
        self,
        current_play: Play,
        parent_nodes: List[CompositeNode],
        block: Union[Block, TaskInclude],
        node_type: str,
        play_vars: Dict,
    ):
        """
        Recursively read all the tasks of the block and add it to the graph
        :param parent_nodes: This a list of parent nodes. Each time, we see an include_role, the corresponding node is
        added to this list
        :param current_play:
        :param block:
        :param play_vars:
        :param node_type:
        :return:
        """

        if not block._implicit and block._role is None:
            # Here we have an explicit block. Ansible internally converts all normal tasks to Block
            block_node = BlockNode(
                str(block.name),
                when=convert_when_to_str(block.when),
                raw_object=block,
                parent=parent_nodes[-1],
            )
            parent_nodes[-1].add_node(f"{node_type}s", block_node)
            parent_nodes.append(block_node)

        # loop through the tasks
        for task_or_block in block.block:
            if hasattr(task_or_block, "loop") and task_or_block.loop:
                display.warning(
                    "Looping on tasks or roles are not supported for the moment. Only the task having the loop argument will be added to the graph."
                )

            if isinstance(task_or_block, Block):
                self._include_tasks_in_blocks(
                    current_play=current_play,
                    parent_nodes=parent_nodes,
                    block=task_or_block,
                    node_type=node_type,
                    play_vars=play_vars,
                )
            elif isinstance(
                task_or_block, TaskInclude
            ):  # include, include_tasks, include_role are dynamic
                # So we need to process them explicitly because Ansible does it during the execution of the playbook

                task_vars = self.variable_manager.get_vars(
                    play=current_play, task=task_or_block
                )

                if isinstance(task_or_block, IncludeRole):
                    # Here we have an 'include_role'. The class IncludeRole is a subclass of TaskInclude.
                    # We do this because the management of an 'include_role' is different.
                    # See :func:`~ansible.playbook.included_file.IncludedFile.process_include_results` from line 155
                    display.v(f"An 'include_role' found: '{task_or_block.get_name()}'")

                    # Here we are using the role name instead of the task name to keep the same behavior  as a
                    #  traditional role
                    if self.group_roles_by_name:
                        # If we are grouping roles, we use the hash of role name as the node id
                        role_node_id = "role_" + hash_value(task_or_block._role_name)
                    else:
                        # Otherwise, a random id is used
                        role_node_id = generate_id("role_")
                    role_node = RoleNode(
                        task_or_block._role_name,
                        node_id=role_node_id,
                        when=convert_when_to_str(task_or_block.when),
                        raw_object=task_or_block,
                        parent=parent_nodes[-1],
                        include_role=True,
                    )
                    parent_nodes[-1].add_node(
                        f"{node_type}s",
                        role_node,
                    )

                    if task_or_block.loop:  # Looping on include_role is not supported
                        continue  # Go the next task
                    else:
                        if self.include_role_tasks:
                            # If we have an include_role, and we want to include its tasks, the parent node now becomes
                            # the role.
                            parent_nodes.append(role_node)

                        block_list, _ = task_or_block.get_block_list(
                            play=current_play,
                            loader=self.data_loader,
                            variable_manager=self.variable_manager,
                        )
                else:
                    display.v(
                        f"An 'include_tasks' found. Including tasks from '{task_or_block.get_name()}'"
                    )

                    templar = Templar(loader=self.data_loader, variables=task_vars)
                    try:
                        included_file_path = handle_include_path(
                            original_task=task_or_block,
                            loader=self.data_loader,
                            templar=templar,
                        )
                    except AnsibleUndefinedVariable as e:
                        # TODO: mark this task with some special shape or color
                        display.warning(
                            f"Unable to translate the include task '{task_or_block.get_name()}' due to an undefined variable: {str(e)}. "
                            "Some variables are available only during the execution of the playbook."
                        )
                        self._add_task(
                            task=task_or_block,
                            task_vars=task_vars,
                            node_type=node_type,
                            parent_node=parent_nodes[-1],
                        )
                        continue

                    data = self.data_loader.load_from_file(included_file_path)
                    if data is None:
                        display.warning(
                            f"The file '{included_file_path}' is empty and has no tasks to include"
                        )
                        continue
                    elif not isinstance(data, list):
                        raise AnsibleParserError(
                            "Included task files must contain a list of tasks", obj=data
                        )

                    # get the blocks from the include_tasks
                    block_list = load_list_of_blocks(
                        data,
                        play=current_play,
                        variable_manager=self.variable_manager,
                        role=task_or_block._role,
                        loader=self.data_loader,
                        parent_block=task_or_block,
                    )

                for (
                    b
                ) in (
                    block_list
                ):  # loop through the blocks inside the included tasks or role
                    self._include_tasks_in_blocks(
                        current_play=current_play,
                        parent_nodes=parent_nodes,
                        block=b,
                        play_vars=task_vars,
                        node_type=node_type,
                    )
                if (
                    self.include_role_tasks
                    and isinstance(task_or_block, IncludeRole)
                    and len(parent_nodes) > 1
                ):
                    # We remove the parent node we have added if we included some tasks from a role
                    parent_nodes.pop()
            else:  # It's here that we add the task in the graph
                if (
                    len(parent_nodes) > 1  # 1
                    and not has_role_parent(task_or_block)  # 2
                    and parent_nodes[-1].raw_object != task_or_block._parent  # 3
                ):
                    # We remove a parent node :
                    # 1. When have at least two parents. Every node (except the playbook) should have a parent node
                    #   AND
                    # 2. The current node doesn't have a role as parent
                    #   AND
                    # 3. The last parent node is different from the current node parent. This means that we are
                    #   done with the child nodes of this parent node
                    parent_nodes.pop()

                # check if this task comes from a role, and we don't want to include tasks of the role
                if has_role_parent(task_or_block) and not self.include_role_tasks:
                    # skip role's task
                    display.vv(
                        f"The task '{task_or_block.get_name()}' has a role as parent and include_role_tasks is false. "
                        "It will be skipped."
                    )
                    # skipping
                    continue

                self._add_task(
                    task=task_or_block,
                    task_vars=play_vars,
                    node_type=node_type,
                    parent_node=parent_nodes[-1],
                )
