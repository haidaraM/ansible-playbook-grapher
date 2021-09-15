from abc import ABC, abstractmethod
from typing import Dict, Union, List

from ansible.cli import CLI
from ansible.errors import AnsibleParserError, AnsibleUndefinedVariable, AnsibleError
from ansible.parsing.yaml.objects import AnsibleUnicode
from ansible.playbook import Playbook, Play
from ansible.playbook.block import Block
from ansible.playbook.helpers import load_list_of_blocks
from ansible.playbook.role_include import IncludeRole
from ansible.playbook.task import Task
from ansible.playbook.task_include import TaskInclude
from ansible.template import Templar
from ansible.utils.display import Display

from ansibleplaybookgrapher.graph import EdgeNode, TaskNode, PlaybookNode, RoleNode, PlayNode, CompositeNode
from ansibleplaybookgrapher.utils import clean_name, handle_include_path, has_role_parent, generate_id


class BaseParser(ABC):
    """
    Base Parser of a playbook
    """

    def __init__(self, tags: List[str] = None, skip_tags: List[str] = None, display: Display = None):
        """

        :param tags: Only add plays and tasks tagged with these values
        :param skip_tags: Only add plays and tasks whose tags do not match these values
        :param display: Ansible display used to print some messages in the console
        """
        loader, inventory, variable_manager = CLI._play_prereqs()
        self.data_loader = loader
        self.inventory_manager = inventory
        self.variable_manager = variable_manager

        self.tags = tags or ["all"]
        self.skip_tags = skip_tags or []
        self.display = display or Display()

    @abstractmethod
    def generate_graph(self, *args, **kwargs) -> PlaybookNode:
        pass

    def template(self, data: Union[str, AnsibleUnicode], variables: Dict,
                 fail_on_undefined=False) -> Union[str, AnsibleUnicode]:
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
            # Sometime we need to export
            if fail_on_undefined:
                raise
            self.display.warning(ansible_error)
            return data

    def _add_task(self, task: Task, loop_counter: int, task_vars: Dict, node_type: str,
                  parent_node: CompositeNode) -> bool:
        """
        Include the task in the graph.
        :return: True if the task has been included, false otherwise
        """

        self.display.vv(f"Adding {node_type} '{task.get_name()}' to the graph with counter {loop_counter}")

        if not task.evaluate_tags(only_tags=self.tags, skip_tags=self.skip_tags, all_vars=task_vars):
            self.display.vv(f"The task '{task.get_name()}' is skipped due to the tags.")
            return False

        task_edge_name = str(loop_counter)
        if len(task.when) > 0:
            when = "".join(map(str, task.when))
            task_edge_name += "  [when: " + when + "]"

        task_name = clean_name(f"[{node_type}] " + self.template(task.get_name(), task_vars))

        edge_node = EdgeNode(task_edge_name, parent_node, TaskNode(task_name, generate_id(f"{node_type}_")))
        parent_node.add_node(target_composition=f"{node_type}s", node=edge_node)

        return True


class PlaybookParser(BaseParser):
    """
    The playbook parser. This is the main entrypoint responsible to parser the playbook into a graph structure
    """

    def __init__(self, playbook_filename: str, include_role_tasks=False, tags: List[str] = None,
                 skip_tags: List[str] = None, display: Display = None):
        """
        :param playbook_filename: The filename of the playbook to parse
        :param display: Ansible display used to print some messages in the console
        :param include_role_tasks: If true, the tasks of the role will be included in the graph
        :param tags: Only add plays and tasks tagged with these values
        :param skip_tags: Only add plays and tasks whose tags do not match these values
        """

        super().__init__(tags=tags, skip_tags=skip_tags, display=display)

        self.include_role_tasks = include_role_tasks
        self.playbook_filename = playbook_filename
        self.playbook = Playbook.load(playbook_filename, loader=self.data_loader,
                                      variable_manager=self.variable_manager)
        # the root node
        self.playbook_root_node = PlaybookNode(self.playbook_filename)

    def generate_graph(self, *args, **kwargs) -> PlaybookNode:
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

        # loop through the plays
        for play_counter, play in enumerate(self.playbook.get_plays(), 1):

            # the load basedir is relative to the playbook path
            if play._included_path is not None:
                self.data_loader.set_basedir(play._included_path)
            else:
                self.data_loader.set_basedir(self.playbook._basedir)
            self.display.vvv(f"Loader basedir set to {self.data_loader.get_basedir()}")

            play_vars = self.variable_manager.get_vars(play)
            play_hosts = [h.get_name() for h in self.inventory_manager.get_hosts(self.template(play.hosts, play_vars))]
            play_name = "Play #{}: {} ({})".format(play_counter, clean_name(play.get_name()), len(play_hosts))
            play_name = self.template(play_name, play_vars)

            self.display.banner("Parsing " + play_name)

            play_node = PlayNode(play_name, hosts=play_hosts)
            self.playbook_root_node.add_play(play_node, str(play_counter))

            # loop through the pre_tasks
            self.display.v("Parsing pre_tasks...")
            for pre_task_block in play.pre_tasks:
                self._include_tasks_in_blocks(current_play=play, parent_nodes=[play_node], block=pre_task_block,
                                              play_vars=play_vars, node_type="pre_task")

            # loop through the roles
            self.display.v("Parsing roles...")

            for role_counter, role in enumerate(play.get_roles(), 1):
                # Don't insert tasks from ``import/include_role``, preventing duplicate graphing
                if role.from_include:
                    continue

                # the role object doesn't inherit the tags from the play. So we add it manually.
                role.tags = role.tags + play.tags
                if not role.evaluate_tags(only_tags=self.tags, skip_tags=self.skip_tags, all_vars=play_vars):
                    self.display.vv(f"The role '{role.get_name()}' is skipped due to the tags.")
                    # Go to the next role
                    continue

                role_node = RoleNode("[role] " + clean_name(role.get_name()))
                # edge from play to role
                play_node.add_node("roles",
                                   EdgeNode(str(role_counter + len(play_node.pre_tasks)), play_node, role_node))

                if self.include_role_tasks:
                    # loop through the tasks of the roles
                    for block in role.compile(play):
                        self._include_tasks_in_blocks(current_play=play, parent_nodes=[role_node], block=block,
                                                      play_vars=play_vars, node_type="task")
                # end of roles loop

            # loop through the tasks
            self.display.v("Parsing tasks...")
            for task_block in play.tasks:
                self._include_tasks_in_blocks(current_play=play, parent_nodes=[play_node], block=task_block,
                                              play_vars=play_vars, node_type="task")

            # loop through the post_tasks
            self.display.v("Parsing post_tasks...")
            for post_task_block in play.post_tasks:
                self._include_tasks_in_blocks(current_play=play, parent_nodes=[play_node], block=post_task_block,
                                              play_vars=play_vars, node_type="post_task")
            # Summary
            self.display.display("")  # just an empty line
            self.display.v(f"{len(play_node.pre_tasks)} pre_task(s) added to the graph.")
            self.display.v(f"{len(play_node.roles)} role(s) added to the play")
            self.display.v(f"{len(play_node.tasks)} task(s) added to the play")
            self.display.v(f"{len(play_node.post_tasks)} post_task(s) added to the play")

            self.display.banner(f"Done parsing {play_name}")
            self.display.display("")  # just an empty line
            # moving to the next play

        return self.playbook_root_node

    def _include_tasks_in_blocks(self, current_play: Play, parent_nodes: List[CompositeNode],
                                 block: Union[Block, TaskInclude], node_type: str, play_vars: Dict = None):
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

        # loop through the tasks
        for task_or_block in block.block:
            if isinstance(task_or_block, Block):
                self._include_tasks_in_blocks(current_play=current_play, parent_nodes=parent_nodes, block=task_or_block,
                                              node_type=node_type, play_vars=play_vars)
            elif isinstance(task_or_block, TaskInclude):  # include, include_tasks, include_role are dynamic
                # So we need to process them explicitly because Ansible does it during the execution of the playbook

                task_vars = self.variable_manager.get_vars(play=current_play, task=task_or_block)

                if isinstance(task_or_block, IncludeRole):
                    # Here we have an 'include_role'. The class IncludeRole is a subclass of TaskInclude.
                    # We do this because the management of an 'include_role' is different.
                    # See :func:`~ansible.playbook.included_file.IncludedFile.process_include_results` from line 155
                    self.display.v(
                        f"An 'include_role' found. Including tasks from the role '{task_or_block.args['name']}'")

                    role_node = RoleNode(task_or_block.args['name'])
                    parent_nodes[-1].add_node("roles",
                                              EdgeNode(str(parent_nodes[-1].total_length + 1), parent_nodes[-1],
                                                       role_node))

                    if self.include_role_tasks:
                        # If we have an include_role and we want to include role tasks, the parent node now becomes
                        # the role.
                        parent_nodes.append(role_node)

                    block_list, _ = task_or_block.get_block_list(play=current_play, loader=self.data_loader,
                                                                 variable_manager=self.variable_manager)
                else:
                    self.display.v(f"An 'include_tasks' found. Including tasks from '{task_or_block.get_name()}'")

                    templar = Templar(loader=self.data_loader, variables=task_vars)
                    try:
                        include_file = handle_include_path(original_task=task_or_block, loader=self.data_loader,
                                                           templar=templar)
                    except AnsibleUndefinedVariable as e:
                        # TODO: mark this task with some special shape or color
                        self.display.warning(
                            f"Unable to translate the include task '{task_or_block.get_name()}' due to an undefined variable: {str(e)}. "
                            "Some variables are available only during the execution of the playbook.")
                        self._add_task(task=task_or_block, loop_counter=parent_nodes[-1].total_length + 1,
                                       task_vars=task_vars, node_type=node_type, parent_node=parent_nodes[-1])
                        continue

                    data = self.data_loader.load_from_file(include_file)
                    if data is None:
                        self.display.warning(f"The file '{include_file}' is empty and has no tasks to include")
                        continue
                    elif not isinstance(data, list):
                        raise AnsibleParserError("Included task files must contain a list of tasks", obj=data)

                    # get the blocks from the include_tasks
                    block_list = load_list_of_blocks(data, play=current_play, variable_manager=self.variable_manager,
                                                     role=task_or_block._role, loader=self.data_loader,
                                                     parent_block=task_or_block)

                for b in block_list:  # loop through the blocks inside the included tasks or role
                    self._include_tasks_in_blocks(current_play=current_play, parent_nodes=parent_nodes, block=b,
                                                  play_vars=task_vars, node_type=node_type)
            else:
                if len(parent_nodes) > 1 and not has_role_parent(task_or_block):
                    # We add a new parent node only if we found an include_role. If an include_role is not found, and we
                    # have a task that is not from an include_role, we remove the last RoleNode we have added.
                    parent_nodes.pop()

                # check if this task comes from a role, and we don't want to include tasks of the role
                if has_role_parent(task_or_block) and not self.include_role_tasks:
                    # skip role's task
                    self.display.vv(
                        f"The task '{task_or_block.get_name()}' has a role as parent and include_role_tasks is false. "
                        "It will be skipped.")
                    # skipping
                    continue

                self._add_task(task=task_or_block, loop_counter=parent_nodes[-1].total_length + 1, task_vars=play_vars,
                               node_type=node_type, parent_node=parent_nodes[-1])
