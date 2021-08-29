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
    Base Parser
    """

    def __init__(self, tags: List[str] = None, skip_tags: List[str] = None, display: Display = None):

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

        self.display.vv(f"Adding {node_type}: '{task.get_name()}' to the graph")

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

    def __init__(self, playbook_filename: str, display: Display = None, include_role_tasks=False, tags=None,
                 skip_tags=None):
        """

        :param include_role_tasks: If true, the tasks of the role will be included.
        :param playbook_filename:
        """

        super().__init__(tags=tags, skip_tags=skip_tags, display=display)

        self.include_role_tasks = include_role_tasks
        self.playbook_filename = playbook_filename
        self.playbook = Playbook.load(playbook_filename, loader=self.data_loader,
                                      variable_manager=self.variable_manager)

    def generate_graph(self, *args, **kwargs) -> PlaybookNode:
        """
        Loop through the playbook and generate the graph.

        The graph is drawn following this order (https://docs.ansible.com/ansible/2.4/playbooks_reuse_roles.html#using-roles)
        for each play:
            draw pre_tasks
            draw roles
                if  include_role_tasks
                    draw role_tasks
            draw tasks
            draw post_tasks
        :return:
        """

        # the root node
        playbook_root_node = PlaybookNode(self.playbook_filename)

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
            playbook_root_node.add_play(play_node, str(play_counter))

            # loop through the pre_tasks
            self.display.v("Parsing pre_tasks...")
            nb_pre_tasks = 0
            for pre_task_block in play.pre_tasks:
                nb_pre_tasks = self._include_tasks_in_blocks(current_play=play, parent_node=play_node,
                                                             block=pre_task_block, current_counter=nb_pre_tasks,
                                                             play_vars=play_vars, node_type="pre_task")

            # global_tasks_counter will hold the number of pre_tasks + tasks + and post_tasks
            global_tasks_counter = nb_pre_tasks

            self.display.v(f"{global_tasks_counter} pre_task(s) added to the graph.")
            # loop through the roles
            self.display.v("Parsing roles...")
            role_number = 0
            for role in play.get_roles():
                # Don't insert tasks from ``import/include_role``, preventing duplicate graphing
                if role.from_include:
                    continue

                # the role object doesn't inherit the tags from the play. So we add it manually.
                role.tags = role.tags + play.tags
                if not role.evaluate_tags(only_tags=self.tags, skip_tags=self.skip_tags,
                                          all_vars=play_vars):
                    self.display.vv(f"The role '{role.get_name()}' is skipped due to the tags.")
                    # Go to the next role
                    continue

                role_number += 1

                role_node = RoleNode("[role] " + clean_name(role.get_name()))
                # edge from play to role
                play_node.add_node("roles", EdgeNode(str(role_number + global_tasks_counter), play_node, role_node))

                # loop through the tasks of the roles
                if self.include_role_tasks:
                    role_tasks_counter = 0  # the role tasks start a 0
                    for block in role.compile(play):
                        role_tasks_counter = self._include_tasks_in_blocks(current_play=play, parent_node=role_node,
                                                                           block=block, play_vars=play_vars,
                                                                           current_counter=role_tasks_counter,
                                                                           node_type="task")
                        role_tasks_counter += 1
                # end of roles loop
            self.display.v(f"{role_number} role(s) added to the graph")

            # loop through the tasks
            self.display.v("Parsing tasks...")
            for task_block in play.tasks:
                global_tasks_counter = self._include_tasks_in_blocks(current_play=play, parent_node=play_node,
                                                                     block=task_block, play_vars=play_vars,
                                                                     current_counter=role_number + global_tasks_counter,
                                                                     node_type="task")
            nb_tasks = global_tasks_counter - role_number - nb_pre_tasks
            self.display.v(f"{nb_tasks} task(s) added to the graph.")

            # loop through the post_tasks
            self.display.v("Parsing post_tasks...")
            for post_task_block in play.post_tasks:
                global_tasks_counter = self._include_tasks_in_blocks(current_play=play, parent_node=play_node,
                                                                     block=post_task_block, play_vars=play_vars,
                                                                     current_counter=global_tasks_counter,
                                                                     node_type="post_task")
            nb_post_tasks = global_tasks_counter - nb_tasks - role_number - nb_pre_tasks
            self.display.v(f"{nb_post_tasks} post_task(s) added to the graph.")

            self.display.banner(f"Done parsing {play_name}")
            self.display.display("")  # just an empty line
            # moving to the next play

        return playbook_root_node

    def _include_tasks_in_blocks(self, current_play: Play, parent_node: CompositeNode, block: Union[Block, TaskInclude],
                                 current_counter: int, play_vars: Dict = None, node_type: str = "") -> int:
        """
        Recursively read all the tasks of the block and add it to the graph
        FIXME: This function needs some refactoring
        :param current_play:
        :param block:
        :param current_counter:
        :param play_vars:
        :param node_type:
        :return:
        """

        # loop through the tasks
        for counter, task_or_block in enumerate(block.block, 1):
            if isinstance(task_or_block, Block):
                current_counter = self._include_tasks_in_blocks(current_play=current_play, parent_node=parent_node,
                                                                block=task_or_block, node_type=node_type,
                                                                current_counter=current_counter, play_vars=play_vars)
            elif isinstance(task_or_block, TaskInclude):  # include, include_tasks, include_role are dynamic
                # So we need to process them explicitly because Ansible does it during the execution of the playbook

                task_vars = self.variable_manager.get_vars(play=current_play, task=task_or_block)

                if isinstance(task_or_block, IncludeRole):
                    # Here we have an 'include_role'. The class IncludeRole is a subclass of TaskInclude.
                    # We do this because the management of an 'include_role' is different.
                    # See :func:`~ansible.playbook.included_file.IncludedFile.process_include_results` from line 155

                    self.display.v(f"An 'include_role' found. Including tasks from '{task_or_block.args['name']}'")
                    my_blocks, _ = task_or_block.get_block_list(play=current_play, loader=self.data_loader,
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
                        current_counter += 1
                        self._add_task(task=task_or_block, loop_counter=current_counter, task_vars=task_vars,
                                       node_type=node_type, parent_node=parent_node)
                        continue

                    data = self.data_loader.load_from_file(include_file)
                    if data is None:
                        self.display.warning(f"The file '{include_file}' is empty and has no tasks to include")
                        continue
                    elif not isinstance(data, list):
                        raise AnsibleParserError("Included task files must contain a list of tasks", obj=data)

                    # get the blocks from the include_tasks
                    my_blocks = load_list_of_blocks(data, play=current_play, variable_manager=self.variable_manager,
                                                    role=task_or_block._role, loader=self.data_loader,
                                                    parent_block=task_or_block)

                for b in my_blocks:  # loop through the blocks inside the included tasks or role
                    current_counter = self._include_tasks_in_blocks(current_play=current_play, parent_node=parent_node,
                                                                    block=b, play_vars=task_vars, node_type=node_type,
                                                                    current_counter=current_counter)
            else:
                # check if this task comes from a role, and we don't want to include tasks of the role
                if has_role_parent(task_or_block) and not self.include_role_tasks:
                    # skip role's task
                    self.display.vv(
                        f"The task '{task_or_block.get_name()}' has a role as parent and include_role_tasks is false. "
                        "It will be skipped.")
                    # skipping
                    continue

                task_included = self._add_task(task=task_or_block, loop_counter=current_counter + 1,
                                               task_vars=play_vars, node_type=node_type, parent_node=parent_node)
                if task_included:
                    # only increment the counter if task has been successfully included.
                    current_counter += 1

        return current_counter
