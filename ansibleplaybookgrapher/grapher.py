import os
import uuid

from ansible.errors import AnsibleError, AnsibleParserError, AnsibleUndefinedVariable
from ansible.playbook import Playbook
from ansible.playbook.block import Block
from ansible.playbook.helpers import load_list_of_blocks
from ansible.playbook.role_include import IncludeRole
from ansible.playbook.task_include import TaskInclude
from ansible.template import Templar
from ansible.utils.display import Display
from graphviz import Digraph

from ansibleplaybookgrapher.utils import GraphRepresentation, clean_name, PostProcessor, get_play_colors, \
    handle_include_path, has_role_parent


class CustomDigrah(Digraph):
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


class Grapher(object):
    """
    Main class to make the graph
    """
    DEFAULT_GRAPH_ATTR = {"ratio": "fill", "rankdir": "LR", "concentrate": "true", "ordering": "in"}
    DEFAULT_EDGE_ATTR = {"sep": "10", "esep": "5"}

    def __init__(self, data_loader, inventory_manager, variable_manager, playbook_filename, options, graph=None):
        """
        Main grapher responsible to parse the playbook and draw graph
        :param data_loader:
        :type data_loader: ansible.parsing.dataloader.DataLoader
        :param inventory_manager:
        :type inventory_manager: ansible.inventory.manager.InventoryManager
        :param variable_manager:
        :type variable_manager: ansible.vars.manager.VariableManager
        :param options Command line options
        :type options: optparse.Values
        :param playbook_filename:
        :type playbook_filename: str
        :param graph:
        :type graph: Digraph
        """
        self.options = options
        self.variable_manager = variable_manager
        self.inventory_manager = inventory_manager
        self.data_loader = data_loader
        self.playbook_filename = playbook_filename
        self.options.output_filename = self.options.output_filename
        self.rendered_file_path = None
        self.display = Display(verbosity=options.verbosity)

        if self.options.tags is None:
            self.options.tags = ["all"]

        if self.options.skip_tags is None:
            self.options.skip_tags = []

        self.graph_representation = GraphRepresentation()

        self.playbook = Playbook.load(self.playbook_filename, loader=self.data_loader,
                                      variable_manager=self.variable_manager)

        if graph is None:
            self.graph = CustomDigrah(edge_attr=self.DEFAULT_EDGE_ATTR, graph_attr=self.DEFAULT_GRAPH_ATTR,
                                      format="svg", name=self.playbook_filename)

    def template(self, data, variables, fail_on_undefined=False):
        """
        Template the data using Jinja. Return data if an error occurs during the templating
        :param fail_on_undefined:
        :type fail_on_undefined: bool
        :param data:
        :type data: Union[str, ansible.parsing.yaml.objects.AnsibleUnicode]
        :param variables:
        :type variables: dict
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

    def make_graph(self):
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
        :rtype:
        """

        # the root node
        self.graph.node(self.playbook_filename, style="dotted", id="root_node")

        # loop through the plays
        for play_counter, play in enumerate(self.playbook.get_plays(), 1):

            # the load basedir is relative to the playbook path
            if play._included_path is not None:
                self.data_loader.set_basedir(play._included_path)
            else:
                self.data_loader.set_basedir(self.playbook._basedir)
            self.display.vvv("Loader basedir set to {}".format(self.data_loader.get_basedir()))

            play_vars = self.variable_manager.get_vars(play)
            play_hosts = [h.get_name() for h in self.inventory_manager.get_hosts(self.template(play.hosts, play_vars))]
            play_name = "Play #{}: {} ({})".format(play_counter, clean_name(play.get_name()), len(play_hosts))
            play_name = self.template(play_name, play_vars)

            self.display.banner("Graphing " + play_name)

            play_id = "play_" + str(uuid.uuid4())

            self.graph_representation.add_node(play_id)

            with self.graph.subgraph(name=play_name) as play_subgraph:
                color, play_font_color = get_play_colors(play)
                # play node
                play_subgraph.node(play_name, id=play_id, style="filled", shape="box", color=color,
                                   fontcolor=play_font_color, tooltip="     ".join(play_hosts))

                # edge from root node to plays
                play_edge_id = "edge_" + str(uuid.uuid4())
                play_subgraph.edge(self.playbook_filename, play_name, id=play_edge_id, style="bold",
                                   label=str(play_counter), color=color, fontcolor=color)

                # loop through the pre_tasks
                self.display.v("Graphing pre_tasks...")
                nb_pre_tasks = 0
                for pre_task_block in play.pre_tasks:
                    nb_pre_tasks = self._include_tasks_in_blocks(current_play=play, graph=play_subgraph,
                                                                 parent_node_name=play_name, parent_node_id=play_id,
                                                                 block=pre_task_block, color=color,
                                                                 current_counter=nb_pre_tasks, play_vars=play_vars,
                                                                 node_name_prefix="[pre_task] ")

                # loop through the roles
                self.display.v("Graphing roles...")
                role_number = 0
                for role in play.get_roles():
                    # Don't insert tasks from ``import/include_role``, preventing duplicate graphing
                    if role.from_include:
                        continue

                    # the role object doesn't inherit the tags from the play. So we add it manually.
                    role.tags = role.tags + play.tags
                    if not role.evaluate_tags(only_tags=self.options.tags, skip_tags=self.options.skip_tags,
                                              all_vars=play_vars):
                        self.display.vv("The role '{}' is skipped due to the tags.".format(role.get_name()))
                        # Go to the next role
                        continue

                    role_number += 1
                    role_name = "[role] " + clean_name(role.get_name())

                    with self.graph.subgraph(name=role_name, node_attr={}) as role_subgraph:
                        current_counter = role_number + nb_pre_tasks
                        role_id = "role_" + str(uuid.uuid4())
                        edge_id = "edge_" + str(uuid.uuid4())

                        role_subgraph.node(role_name, id=role_id)
                        # edge from play to role
                        role_subgraph.edge(play_name, role_name, label=str(current_counter), color=color,
                                           fontcolor=color, id=edge_id)

                        self.graph_representation.add_link(play_id, edge_id)
                        self.graph_representation.add_link(edge_id, role_id)

                        # loop through the tasks of the roles
                        if self.options.include_role_tasks:
                            role_tasks_counter = 0
                            for block in role.compile(play):
                                role_tasks_counter = self._include_tasks_in_blocks(current_play=play,
                                                                                   graph=role_subgraph,
                                                                                   parent_node_name=role_name,
                                                                                   parent_node_id=role_id, block=block,
                                                                                   color=color, play_vars=play_vars,
                                                                                   current_counter=role_tasks_counter,
                                                                                   node_name_prefix="[task] ")
                                role_tasks_counter += 1
                self.display.v("{} roles added to the graph".format(role_number))

                # loop through the tasks
                self.display.v("Graphing tasks...")
                nb_tasks = 0
                for task_block in play.tasks:
                    nb_tasks = self._include_tasks_in_blocks(current_play=play, graph=play_subgraph,
                                                             parent_node_name=play_name, parent_node_id=play_id,
                                                             block=task_block, color=color,
                                                             current_counter=role_number + nb_pre_tasks,
                                                             play_vars=play_vars, node_name_prefix="[task] ")

                # loop through the post_tasks
                self.display.v("Graphing post_tasks...")
                for post_task_block in play.post_tasks:
                    self._include_tasks_in_blocks(current_play=play, graph=play_subgraph, parent_node_name=play_name,
                                                  parent_node_id=play_id, block=post_task_block, color=color,
                                                  current_counter=nb_tasks, play_vars=play_vars,
                                                  node_name_prefix="[post_task] ")

            self.display.banner("Done graphing {}".format(play_name))
            self.display.display("")  # just an empty line
            # moving to the next play

    def render_graph(self):
        """
        Render the graph
        :return: The rendered file path
        :rtype: str
        """

        self.rendered_file_path = self.graph.render(cleanup=not self.options.save_dot_file,
                                                    filename=self.options.output_filename)
        if self.options.save_dot_file:
            # add .gv extension. The render doesn't add an extension
            final_name = self.options.output_filename + ".dot"
            os.rename(self.options.output_filename, final_name)
            self.display.display("Graphviz dot file has been exported to {}".format(final_name))

        return self.rendered_file_path

    def post_process_svg(self):
        """
        Post process the rendered svg
        :return The post processed file path
        :rtype: str
        :return:
        """
        post_processor = PostProcessor(svg_path=self.rendered_file_path)

        post_processor.post_process(graph_representation=self.graph_representation)

        post_processor.write()

        self.display.display("The graph has been exported to {}".format(self.rendered_file_path))

        return self.rendered_file_path

    def _include_tasks_in_blocks(self, current_play, graph, parent_node_name, parent_node_id, block, color,
                                 current_counter, play_vars=None, node_name_prefix=""):
        """
        Recursively read all the tasks of the block and add it to the graph
        FIXME: This function needs some refactoring. Thinking of a BlockGrapher to handle this
        :param current_play:
        :type current_play: ansible.playbook.play.Play
        :param graph:
        :type graph:
        :param parent_node_name:
        :type parent_node_name: str
        :param parent_node_id:
        :type parent_node_id: str
        :param block:
        :type block: Union[Block,TaskInclude]
        :param color:
        :type color: str
        :param current_counter:
        :type current_counter: int
        :param play_vars:
        :type play_vars: dict
        :param node_name_prefix:
        :type node_name_prefix: str
        :return:
        :rtype:
        """

        loop_counter = current_counter
        # loop through the tasks
        for counter, task_or_block in enumerate(block.block, 1):
            if isinstance(task_or_block, Block):
                loop_counter = self._include_tasks_in_blocks(current_play=current_play, graph=graph,
                                                             parent_node_name=parent_node_name,
                                                             parent_node_id=parent_node_id, block=task_or_block,
                                                             color=color, current_counter=loop_counter,
                                                             play_vars=play_vars, node_name_prefix=node_name_prefix)
            elif isinstance(task_or_block, TaskInclude):  # include, include_tasks, include_role are dynamic
                # So we need to process it explicitly because Ansible does it during th execution of the playbook

                task_vars = self.variable_manager.get_vars(play=current_play, task=task_or_block)

                if isinstance(task_or_block, IncludeRole):

                    self.display.v("An 'include_role' found. Including tasks from '{}'"
                                   .format(task_or_block.args["name"]))
                    # Here we have an include_role. The class IncludeRole is a subclass of TaskInclude.
                    # We do this because the management of an include_role is different.
                    # See :func:`~ansible.playbook.included_file.IncludedFile.process_include_results` from line 155
                    my_blocks, _ = task_or_block.get_block_list(play=current_play, loader=self.data_loader,
                                                                variable_manager=self.variable_manager)
                else:
                    self.display.v("An 'include_tasks' found. Including tasks from '{}'"
                                   .format(task_or_block.get_name()))
                    templar = Templar(loader=self.data_loader, variables=task_vars)
                    try:
                        include_file = handle_include_path(original_task=task_or_block, loader=self.data_loader,
                                                           templar=templar)
                    except AnsibleUndefinedVariable as e:
                        # TODO: mark this task with some special shape or color
                        self.display.warning(
                            "Unable to translate the include task '{}' due to an undefined variable: {}. "
                            "Some variables are available only during the real execution."
                                .format(task_or_block.get_name(), str(e)))
                        loop_counter += 1
                        self._include_task(task_or_block, loop_counter, task_vars, graph, node_name_prefix, color,
                                           parent_node_id, parent_node_name)
                        continue

                    data = self.data_loader.load_from_file(include_file)
                    if data is None:
                        self.display.warning("file %s is empty and had no tasks to include" % include_file)
                        continue
                    elif not isinstance(data, list):
                        raise AnsibleParserError("included task files must contain a list of tasks", obj=data)

                    # get the blocks from the include_tasks
                    my_blocks = load_list_of_blocks(data, play=current_play, variable_manager=self.variable_manager,
                                                    role=task_or_block._role, loader=self.data_loader,
                                                    parent_block=task_or_block)

                for b in my_blocks:  # loop through the blocks inside the included tasks or role
                    loop_counter = self._include_tasks_in_blocks(current_play=current_play, graph=graph,
                                                                 parent_node_name=parent_node_name,
                                                                 parent_node_id=parent_node_id, block=b, color=color,
                                                                 current_counter=loop_counter, play_vars=task_vars,
                                                                 node_name_prefix=node_name_prefix)
            else:
                # check if this task comes from a role, and we don't want to include tasks of the role
                if has_role_parent(task_or_block) and not self.options.include_role_tasks:
                    # skip role's task
                    self.display.vv("The task '{}' has a role as parent and include_role_tasks is false. "
                                    "It will be skipped.".format(task_or_block.get_name()))
                    # skipping
                    continue

                task_included = self._include_task(task_or_block=task_or_block, loop_counter=loop_counter + 1,
                                                   play_vars=play_vars,
                                                   graph=graph, node_name_prefix=node_name_prefix, color=color,
                                                   parent_node_id=parent_node_id, parent_node_name=parent_node_name)
                if task_included:
                    # only increment the counter if task has been successfully included.
                    loop_counter += 1

        return loop_counter

    def _include_task(self, task_or_block, loop_counter, play_vars, graph, node_name_prefix, color, parent_node_id,
                      parent_node_name):
        """
        Include the task in the graph.
        :return: True if the task has been included, false otherwise
        :rtype: bool
        """

        self.display.vv("Adding the task '{}' to the graph".format(task_or_block.get_name()))

        if not task_or_block.evaluate_tags(only_tags=self.options.tags, skip_tags=self.options.skip_tags,
                                           all_vars=play_vars):
            self.display.vv("The task '{}' is skipped due to the tags.".format(task_or_block.get_name()))
            return False

        task_edge_label = str(loop_counter)
        if len(task_or_block.when) > 0:
            when = "".join(map(str, task_or_block.when))
            task_edge_label += "  [when: " + when + "]"

        task_name = clean_name(node_name_prefix + self.template(task_or_block.get_name(), play_vars))
        # get prefix id from node_name
        id_prefix = node_name_prefix.replace("[", "").replace("]", "").replace(" ", "_")
        task_id = id_prefix + str(uuid.uuid4())
        edge_id = "edge_" + str(uuid.uuid4())

        graph.node(task_id, label=task_name, shape="octagon", id=task_id)
        graph.edge(parent_node_name, task_id, label=task_edge_label, color=color, fontcolor=color, style="bold",
                   id=edge_id)
        self.graph_representation.add_link(parent_node_id, edge_id)
        self.graph_representation.add_link(edge_id, task_id)

        return True
