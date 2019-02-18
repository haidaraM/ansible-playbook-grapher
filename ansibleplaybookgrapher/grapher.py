from ansible.errors import AnsibleError, AnsibleParserError
from ansible.playbook import Playbook
from ansible.playbook.block import Block
from ansible.playbook.helpers import load_list_of_blocks
from ansible.playbook.task_include import TaskInclude
from ansible.template import Templar
from ansible.utils.display import Display
from graphviz import Digraph

from ansibleplaybookgrapher.utils import GraphRepresentation, clean_name, clean_id, PostProcessor, get_play_colors

display = Display()

NOT_TAGGED = "not_tagged"


class CustomDigrah(Digraph):
    """
    Custom digraph to avoid quoting issue with node names. Nothing special here except I put some double quotes around
    the node and edge names and overrided some methods.
    """
    _edge = '\t"%s" -> "%s"%s'
    _node = '\t"%s"%s'
    _subgraph = 'subgraph "%s"{'
    _quote = staticmethod(clean_name)
    _quote_edge = staticmethod(clean_name)


class Grapher(object):
    """
    Main class to make the graph
    """
    DEFAULT_GRAPH_ATTR = {'ratio': "fill", "rankdir": "LR", 'concentrate': 'true', 'ordering': 'in'}
    DEFAULT_EDGE_ATTR = {'sep': "10", "esep": "5"}

    def __init__(self, data_loader, inventory_manager, variable_manager, playbook_filename, graph=None,
                 output_filename=None):
        """

        :param data_loader:
        :param inventory_manager:
        :param variable_manager:
        :param playbook_filename:
        :param graph:
        :param output_filename: The output filename without the extension
        """
        self.variable_manager = variable_manager
        self.inventory_manager = inventory_manager
        self.data_loader = data_loader
        self.playbook_filename = playbook_filename
        self.output_filename = output_filename

        self.graph_representation = GraphRepresentation()

        self.playbook = Playbook.load(self.playbook_filename, loader=self.data_loader,
                                      variable_manager=self.variable_manager)

        # need playbook basedir. It's used to get tasks included with `include_tasks`
        # Ansible currently resets it to the CWD when the parsing is done
        self.data_loader.set_basedir(self.playbook._basedir)

        if graph is None:
            self.graph = CustomDigrah(edge_attr=self.DEFAULT_EDGE_ATTR, graph_attr=self.DEFAULT_GRAPH_ATTR,
                                      format="svg")

    def template(self, data, variables, fail_on_undefined=False):
        """
        Template the data using Jinja. Return data if an error occurs during the templating
        :param fail_on_undefined:
        :param data:
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
            display.warning(ansible_error)
            return data

    def make_graph(self, include_role_tasks=False, tags=None, skip_tags=None):
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
        if tags is None:
            tags = ['all']

        if skip_tags is None:
            skip_tags = []

        # the root node
        self.graph.node(self.playbook_filename, style="dotted", id="root_node")

        # loop through the plays
        for play_counter, play in enumerate(self.playbook.get_plays(), 1):

            play_vars = self.variable_manager.get_vars(play)
            # get only the hosts name for the moment
            play_hosts = [h.get_name() for h in self.inventory_manager.get_hosts(self.template(play.hosts, play_vars))]
            nb_hosts = len(play_hosts)

            color, play_font_color = get_play_colors(play)

            play_name = "{} ({})".format(clean_name(str(play)), nb_hosts)

            play_name = self.template(play_name, play_vars)

            play_id = "play_" + clean_id(play_name)

            self.graph_representation.add_node(play_id)

            with self.graph.subgraph(name=play_name) as play_subgraph:

                # play node
                play_subgraph.node(play_name, id=play_id, style='filled', shape="box", color=color,
                                   fontcolor=play_font_color, tooltip="     ".join(play_hosts))

                # edge from root node to plays
                play_edge_id = "edge_" + clean_id(self.playbook_filename + play_name + str(play_counter))
                play_subgraph.edge(self.playbook_filename, play_name, id=play_edge_id, style="bold",
                                   label=str(play_counter), color=color, fontcolor=color)

                # loop through the pre_tasks
                nb_pre_tasks = 0
                for pre_task_block in play.pre_tasks:
                    nb_pre_tasks = self._include_tasks_in_blocks(current_play=play, graph=play_subgraph,
                                                                 parent_node_name=play_name, parent_node_id=play_id,
                                                                 block=pre_task_block, color=color,
                                                                 current_counter=nb_pre_tasks, play_vars=play_vars,
                                                                 node_name_prefix='[pre_task] ', tags=tags,
                                                                 skip_tags=skip_tags)

                # loop through the roles
                for role_counter, role in enumerate(play.get_roles(), 1):
                    role_name = '[role] ' + clean_name(str(role))

                    # the role object doesn't inherit the tags from the play. So we add it manually
                    role.tags = role.tags + play.tags

                    role_not_tagged = ''
                    if not role.evaluate_tags(only_tags=tags, skip_tags=skip_tags, all_vars=play_vars):
                        role_not_tagged = NOT_TAGGED

                    with self.graph.subgraph(name=role_name, node_attr={}) as role_subgraph:
                        current_counter = role_counter + nb_pre_tasks
                        role_id = "role_" + clean_id(role_name + role_not_tagged)
                        role_subgraph.node(role_name, id=role_id)

                        when = "".join(role.when)
                        play_to_node_label = str(current_counter) if len(when) == 0 else str(
                            current_counter) + "  [when: " + when + "]"

                        edge_id = "edge_" + clean_id(play_id + role_id + role_not_tagged)

                        role_subgraph.edge(play_name, role_name, label=play_to_node_label, color=color, fontcolor=color,
                                           id=edge_id)

                        self.graph_representation.add_link(play_id, edge_id)

                        self.graph_representation.add_link(edge_id, role_id)

                        # loop through the tasks of the roles
                        if include_role_tasks:
                            role_tasks_counter = 0
                            for block in role.get_task_blocks():
                                role_tasks_counter = self._include_tasks_in_blocks(current_play=play,
                                                                                   graph=role_subgraph,
                                                                                   parent_node_name=role_name,
                                                                                   parent_node_id=role_id, block=block,
                                                                                   color=color, play_vars=play_vars,
                                                                                   current_counter=role_tasks_counter,
                                                                                   node_name_prefix='[task] ',
                                                                                   tags=tags, skip_tags=skip_tags)
                                role_tasks_counter += 1

                nb_roles = len(play.get_roles())
                # loop through the tasks
                nb_tasks = 0
                for task_block in play.tasks:
                    nb_tasks = self._include_tasks_in_blocks(current_play=play, graph=play_subgraph,
                                                             parent_node_name=play_name, parent_node_id=play_id,
                                                             block=task_block, color=color,
                                                             current_counter=nb_roles + nb_pre_tasks,
                                                             play_vars=play_vars, node_name_prefix='[task] ', tags=tags,
                                                             skip_tags=skip_tags)

                # loop through the post_tasks
                for post_task_block in play.post_tasks:
                    self._include_tasks_in_blocks(current_play=play, graph=play_subgraph, parent_node_name=play_name,
                                                  parent_node_id=play_id, block=post_task_block, color=color,
                                                  current_counter=nb_tasks, play_vars=play_vars,
                                                  node_name_prefix='[post_task] ', tags=tags, skip_tags=skip_tags)

    def render_graph(self, output_filename=None, save_dot_file=False):
        """
        Render the graph
        :param output_filename:
        :param save_dot_file:
        :return:
        """
        if output_filename is None:
            output_filename = self.output_filename

        self.graph.render(cleanup=not save_dot_file, filename=output_filename)

    def post_process_svg(self, output_filename=None):
        """
        Post process the rendered svg
        :param output_filename: The output filename without the extension
        :return:
        """
        if output_filename is None:
            output_filename = self.output_filename + ".svg"

        post_processor = PostProcessor(svg_path=output_filename)

        post_processor.post_process(graph_representation=self.graph_representation)

        post_processor.write()

        return output_filename

    def _include_tasks_in_blocks(self, current_play, graph, parent_node_name, parent_node_id, block, color,
                                 current_counter, play_vars=None, node_name_prefix='', tags=None, skip_tags=None):
        """
       Recursively read all the tasks of the block and add it to the graph
        :param current_play:
       :param play_vars:
       :param tags:
       :param parent_node_id:
       :param node_name_prefix:
       :param color:
       :param current_counter:
       :param graph:
       :param parent_node_name:
       :param block:
       :return:
       """
        if tags is None:
            tags = ['all']

        if skip_tags is None:
            skip_tags = []

        # get prefix id from node_name
        id_prefix = node_name_prefix.replace("[", "").replace("]", "").replace(" ", "_")

        loop_counter = current_counter
        # loop through the tasks
        for counter, task_or_block in enumerate(block.block, 1):
            if isinstance(task_or_block, Block):
                loop_counter = self._include_tasks_in_blocks(current_play=current_play, graph=graph,
                                                             parent_node_name=parent_node_name,
                                                             parent_node_id=parent_node_id, block=task_or_block,
                                                             color=color, current_counter=loop_counter,
                                                             play_vars=play_vars, node_name_prefix=node_name_prefix,
                                                             tags=tags, skip_tags=skip_tags)
            elif isinstance(task_or_block, TaskInclude):
                # here we have an `include_tasks` which is dynamic. So we need to process it explicitly because Ansible
                # does it during th execution of the playbook
                include_target = self.template(task_or_block.args['_raw_params'], play_vars, fail_on_undefined=True)
                include_file = self.data_loader.path_dwim(include_target)
                data = self.data_loader.load_from_file(include_file)
                if data is None:
                    display.warning("file %s is empty and had no tasks to include" % include_file)
                    continue
                elif not isinstance(data, list):
                    raise AnsibleParserError("included task files must contain a list of tasks", obj=data)

                # get the blocks from the include_tasks
                blocks = load_list_of_blocks(data, play=current_play, variable_manager=self.variable_manager)

                for b in blocks:  # loop through the blocks inside the included tasks
                    loop_counter = self._include_tasks_in_blocks(current_play=current_play, graph=graph,
                                                                 parent_node_name=parent_node_name,
                                                                 parent_node_id=parent_node_id, block=b, color=color,
                                                                 current_counter=loop_counter, play_vars=play_vars,
                                                                 node_name_prefix=node_name_prefix, tags=tags,
                                                                 skip_tags=skip_tags)
            else:
                # check if the task should be included
                tagged = ''
                if not task_or_block.evaluate_tags(only_tags=tags, skip_tags=skip_tags, all_vars=play_vars):
                    tagged = NOT_TAGGED

                task_name = clean_name(node_name_prefix + self.template(task_or_block.get_name(), play_vars))
                task_id = id_prefix + clean_id(
                    task_name + tagged)
                graph.node(task_name, shape="octagon", id=task_id)

                edge_id = "edge_" + parent_node_id + task_id + str(loop_counter) + tagged

                graph.edge(parent_node_name, task_name, label=str(loop_counter + 1), color=color, fontcolor=color,
                           style="bold", id=edge_id)
                self.graph_representation.add_link(parent_node_id, edge_id)
                self.graph_representation.add_link(edge_id, task_id)

                loop_counter += 1

        return loop_counter
