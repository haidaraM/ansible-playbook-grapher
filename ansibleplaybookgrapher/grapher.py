import os
from abc import ABC, abstractmethod
from typing import Dict, Union, List

from ansible.errors import AnsibleParserError, AnsibleUndefinedVariable, AnsibleError
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.yaml.objects import AnsibleUnicode
from ansible.playbook import Playbook, Play
from ansible.playbook.block import Block
from ansible.playbook.helpers import load_list_of_blocks
from ansible.playbook.role_include import IncludeRole
from ansible.playbook.task import Task
from ansible.playbook.task_include import TaskInclude
from ansible.template import Templar
from ansible.utils.display import Display
from ansible.vars.manager import VariableManager
from graphviz import Digraph

from ansibleplaybookgrapher.utils import GraphRepresentation, clean_name, get_play_colors, \
    handle_include_path, has_role_parent, generate_id

DEFAULT_GRAPH_ATTR = {"ratio": "fill", "rankdir": "LR", "concentrate": "true", "ordering": "in"}
DEFAULT_EDGE_ATTR = {"sep": "10", "esep": "5"}


class CustomDigraph(Digraph):
    """
    Custom digraph to avoid quoting issue with node names. Nothing special here except I put some double quotes around
    the node and edge names and override some methods.
    """
    _head = "digraph \"%s\"{"
    _edge = "\t\"%s\" -> \"%s\"%s"
    _node = "\t\"%s\"%s"
    _subgraph = "subgraph \"%s\"{"
    _quote = staticmethod(clean_name)
    _quote_edge = staticmethod(clean_name)


class BaseGrapher(ABC):
    """
    Base grapher
    """

    def __init__(self, data_loader: DataLoader, inventory_manager: InventoryManager, variable_manager: VariableManager,
                 graph_representation: GraphRepresentation, tags: List[str] = None, skip_tags: List[str] = None,
                 graphiz_graph: CustomDigraph = None, display: Display = None):

        self.data_loader = data_loader
        self.inventory_manager = inventory_manager
        self.variable_manager = variable_manager
        self.graph_representation = graph_representation
        self.graphiz_graph = graphiz_graph or CustomDigraph(edge_attr=DEFAULT_EDGE_ATTR, graph_attr=DEFAULT_GRAPH_ATTR,
                                                            format="svg")
        self.tags = tags or ["all"]
        self.skip_tags = skip_tags or []
        self.display = display or Display()

    @abstractmethod
    def make_graph(self, *args, **kwargs):
        """
        Make the graph
        """
        pass

    def render_graph(self, output_filename: str, save_dot_file=False) -> str:
        """
        Render the graph
        :param output_filename: Output file name without '.svg' extension.
        :param save_dot_file: If true, the dot file will be saved when rendering the graph.
        :return: The rendered file path (output_filename.svg)
        """

        rendered_file_path = self.graphiz_graph.render(cleanup=not save_dot_file, format="svg",
                                                       filename=output_filename)
        if save_dot_file:
            # add .dot extension. The render doesn't add an extension
            final_name = output_filename + ".dot"
            os.rename(output_filename, final_name)
            self.display.display(f"Graphviz dot file has been exported to {final_name}")

        return rendered_file_path

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

    def _graph_task(self, task: Task, loop_counter: int, task_vars: Dict, graph: CustomDigraph, node_name_prefix: str,
                    color: str, parent_node_id: str, parent_node_name: str) -> bool:
        """
        Include the task in the graph.
        :return: True if the task has been included, false otherwise
        """

        self.display.vv(f"Adding {node_name_prefix.strip()}: '{task.get_name()}' to the graph")

        if not task.evaluate_tags(only_tags=self.tags, skip_tags=self.skip_tags, all_vars=task_vars):
            self.display.vv(f"The task '{task.get_name()}' is skipped due to the tags.")
            return False

        task_edge_label = str(loop_counter)
        if len(task.when) > 0:
            when = "".join(map(str, task.when))
            task_edge_label += "  [when: " + when + "]"

        task_name = clean_name(node_name_prefix + self.template(task.get_name(), task_vars))
        # get prefix id from node_name
        id_prefix = node_name_prefix.replace("[", "").replace("]", "").replace(" ", "_")
        task_id = id_prefix + generate_id()
        edge_id = "edge_" + generate_id()

        graph.node(task_id, label=task_name, shape="octagon", id=task_id, tooltip=task_name)
        graph.edge(parent_node_name, task_id, label=task_edge_label, color=color, fontcolor=color, style="bold",
                   id=edge_id)
        self.graph_representation.add_link(parent_node_id, edge_id)
        self.graph_representation.add_link(edge_id, task_id)

        return True


class PlaybookGrapher(BaseGrapher):
    """
    The playbook grapher. This is the main entrypoint responsible to graph the playbook.
    """

    def __init__(self, data_loader: DataLoader, inventory_manager: InventoryManager, variable_manager: VariableManager,
                 playbook_filename: str, display: Display, include_role_tasks=False, tags=None, skip_tags=None):
        """
        Main grapher responsible to parse the playbook and draw graph
        :param data_loader:
        :param inventory_manager:
        :param variable_manager:
        :param include_role_tasks: If true, the tasks of the role will be included.
        :param playbook_filename:
        """

        self.include_role_tasks = include_role_tasks
        self.playbook_filename = playbook_filename
        self.playbook = Playbook.load(playbook_filename, loader=data_loader, variable_manager=variable_manager)
        graphiz_graph = CustomDigraph(edge_attr=DEFAULT_EDGE_ATTR, graph_attr=DEFAULT_GRAPH_ATTR,
                                      format="svg", name=playbook_filename)

        super().__init__(data_loader=data_loader, inventory_manager=inventory_manager,
                         graphiz_graph=graphiz_graph, variable_manager=variable_manager,
                         graph_representation=GraphRepresentation(), tags=tags, skip_tags=skip_tags,
                         display=display)

    def make_graph(self, *args, **kwargs):
        """
        Loop through the playbook and make the graph.

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
        self.graphiz_graph.node(self.playbook_filename, style="dotted", id="root_node")

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
            play_id = "play_" + generate_id()

            self.display.banner("Graphing " + play_name)

            self.graph_representation.add_node(play_id)

            with self.graphiz_graph.subgraph(name=play_name) as play_subgraph:
                color, play_font_color = get_play_colors(play)
                # play node
                play_subgraph.node(play_name, id=play_id, style="filled", shape="box", color=color,
                                   fontcolor=play_font_color, tooltip="     ".join(play_hosts))

                # edge from root node to plays
                play_edge_id = "edge_" + generate_id()
                play_subgraph.edge(self.playbook_filename, play_name, id=play_edge_id, style="bold",
                                   label=str(play_counter), color=color, fontcolor=color)

                # loop through the pre_tasks
                self.display.v("Graphing pre_tasks...")
                nb_pre_tasks = 0
                for pre_task_block in play.pre_tasks:
                    nb_pre_tasks = self._include_tasks_in_blocks(current_play=play, graph=play_subgraph,
                                                                 parent_node_name=play_name,
                                                                 parent_node_id=play_id,
                                                                 block=pre_task_block, color=color,
                                                                 current_counter=nb_pre_tasks,
                                                                 play_vars=play_vars,
                                                                 node_name_prefix="[pre_task] ")

                # global_tasks_counter will hold the number of pre_tasks + tasks + and post_tasks
                global_tasks_counter = nb_pre_tasks

                self.display.v(f"{global_tasks_counter} pre_task(s) added to the graph.")
                # loop through the roles
                self.display.v("Graphing roles...")
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
                    role_name = "[role] " + clean_name(role.get_name())

                    # edge from play to role
                    edge_id = "edge_" + generate_id()
                    play_subgraph.edge(play_name, role_name, label=str(role_number + global_tasks_counter), color=color,
                                       fontcolor=color, id=edge_id)
                    self.graph_representation.add_link(play_id, edge_id)

                    with self.graphiz_graph.subgraph(name=role_name, node_attr={}) as role_subgraph:

                        role_id = "role_" + generate_id()
                        role_subgraph.node(role_name, id=role_id)
                        self.graph_representation.add_link(edge_id, role_id)

                        # loop through the tasks of the roles
                        if self.include_role_tasks:
                            role_tasks_counter = 0  # the role tasks start a 0
                            for block in role.compile(play):
                                role_tasks_counter = self._include_tasks_in_blocks(current_play=play,
                                                                                   graph=role_subgraph,
                                                                                   parent_node_name=role_name,
                                                                                   parent_node_id=role_id, block=block,
                                                                                   color=color, play_vars=play_vars,
                                                                                   current_counter=role_tasks_counter,
                                                                                   node_name_prefix="[task] ")
                                role_tasks_counter += 1
                # end of roles loop
                self.display.v(f"{role_number} role(s) added to the graph")

                # loop through the tasks
                self.display.v("Graphing tasks...")
                for task_block in play.tasks:
                    global_tasks_counter = self._include_tasks_in_blocks(current_play=play, graph=play_subgraph,
                                                                         parent_node_name=play_name,
                                                                         parent_node_id=play_id,
                                                                         block=task_block, color=color,
                                                                         current_counter=role_number + global_tasks_counter,
                                                                         play_vars=play_vars,
                                                                         node_name_prefix="[task] ")
                nb_tasks = global_tasks_counter - role_number - nb_pre_tasks
                self.display.v(f"{nb_tasks} task(s) added to the graph.")

                # loop through the post_tasks
                self.display.v("Graphing post_tasks...")
                for post_task_block in play.post_tasks:
                    global_tasks_counter = self._include_tasks_in_blocks(current_play=play, graph=play_subgraph,
                                                                         parent_node_name=play_name,
                                                                         parent_node_id=play_id, block=post_task_block,
                                                                         color=color,
                                                                         current_counter=global_tasks_counter,
                                                                         play_vars=play_vars,
                                                                         node_name_prefix="[post_task] ")
                nb_post_tasks = global_tasks_counter - nb_tasks - role_number - nb_pre_tasks
                self.display.v(f"{nb_post_tasks} post_task(s) added to the graph.")

            self.display.banner(f"Done graphing {play_name}")
            self.display.display("")  # just an empty line
            # moving to the next play

    def _include_tasks_in_blocks(self, current_play: Play, graph: CustomDigraph, parent_node_name: str,
                                 parent_node_id: str, block: Union[Block, TaskInclude], color: str,
                                 current_counter: int, play_vars: Dict = None, node_name_prefix: str = "") -> int:
        """
        Recursively read all the tasks of the block and add it to the graph
        FIXME: This function needs some refactoring. Thinking of a BlockGrapher to handle this
        :param current_play:
        :param graph:
        :param parent_node_name:
        :param parent_node_id:
        :param block:
        :param color:
        :param current_counter:
        :param play_vars:
        :param node_name_prefix:
        :return:
        """

        # loop through the tasks
        for counter, task_or_block in enumerate(block.block, 1):
            if isinstance(task_or_block, Block):
                current_counter = self._include_tasks_in_blocks(current_play=current_play, graph=graph,
                                                                parent_node_name=parent_node_name,
                                                                parent_node_id=parent_node_id, block=task_or_block,
                                                                color=color, current_counter=current_counter,
                                                                play_vars=play_vars, node_name_prefix=node_name_prefix)
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
                        self._graph_task(task=task_or_block, loop_counter=current_counter, task_vars=task_vars,
                                         graph=graph, node_name_prefix=node_name_prefix, color=color,
                                         parent_node_id=parent_node_id, parent_node_name=parent_node_name)
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
                    current_counter = self._include_tasks_in_blocks(current_play=current_play, graph=graph,
                                                                    parent_node_name=parent_node_name,
                                                                    parent_node_id=parent_node_id, block=b, color=color,
                                                                    current_counter=current_counter,
                                                                    play_vars=task_vars,
                                                                    node_name_prefix=node_name_prefix)
            else:
                # check if this task comes from a role, and we don't want to include tasks of the role
                if has_role_parent(task_or_block) and not self.include_role_tasks:
                    # skip role's task
                    self.display.vv(
                        f"The task '{task_or_block.get_name()}' has a role as parent and include_role_tasks is false. "
                        "It will be skipped.")
                    # skipping
                    continue

                task_included = self._graph_task(task=task_or_block, loop_counter=current_counter + 1,
                                                 task_vars=play_vars, graph=graph, node_name_prefix=node_name_prefix,
                                                 color=color, parent_node_id=parent_node_id,
                                                 parent_node_name=parent_node_name)
                if task_included:
                    # only increment the counter if task has been successfully included.
                    current_counter += 1

        return current_counter
