"""
Simple grapher for an Ansible Playbook.

You will need to install Ansible, graphviz on your system (sudo apt-get install graphviz).

Has been tested with Ansible 2.4.
"""

import argparse
import ntpath
import os

from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook import Playbook
from ansible.playbook.block import Block
from ansible.vars.manager import VariableManager
from colour import Color
from graphviz import Digraph

from ansibleplaybookgrapher.utils import post_process_svg, GraphRepresentation, clean_id, clean_name

__version__ = "0.3.2"


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


def include_tasks_in_blocks(graph, parent_node_name, parent_node_id, block, color, current_counter,
                            graph_representation, node_name_prefix=''):
    """
    Recursively read all the tasks of the block and add it to the graph
    :param parent_node_id:
    :param graph_representation:
    :param node_name_prefix:
    :param color:
    :param current_counter:
    :param graph:
    :param parent_node_name:
    :param block:
    :return:
    """
    loop_counter = current_counter
    # loop through the tasks
    for counter, task_or_block in enumerate(block.block, 1):
        if isinstance(task_or_block, Block):
            loop_counter = include_tasks_in_blocks(graph, parent_node_name, parent_node_id, task_or_block, color,
                                                   loop_counter, graph_representation, node_name_prefix)
        else:
            task_name = clean_name(node_name_prefix + task_or_block.get_name())
            task_id = clean_id(task_name)
            graph.node(task_name, shape="octagon", id=task_id)

            edge_id = parent_node_id + task_id

            graph.edge(parent_node_name, task_name, label=str(loop_counter + 1), color=color, fontcolor=color,
                       style="bold", id=edge_id)
            graph_representation.add_link(parent_node_id, task_id)
            graph_representation.add_link(parent_node_id, edge_id)

            loop_counter += 1

    return loop_counter


def dump_playbok(playbook, loader, variable_manager, include_role_tasks, save_dot_file, output_file_name):
    """
    Dump the playbook in a svg file. Optionally save the dot file.

    The graph is drawn following this order (https://docs.ansible.com/ansible/2.4/playbooks_reuse_roles.html#using-roles)
    for each play:
        draw pre_tasks
        draw roles
            if  include_role_tasks
                draw role_tasks
        draw tasks
        draw post_tasks

    :param loader:
    :param save_dot_file:
    :param playbook:
    :param variable_manager:
    :param include_role_tasks:
    :param output_file_name:
    :return:
    """
    playbook_name = playbook._file_name
    if output_file_name is None:
        output_file_name = os.path.splitext(ntpath.basename(playbook_name))[0]

    graph_attr = {'ratio': "fill", "rankdir": "LR", 'concentrate': 'true', 'ordering': 'in'}
    dot = CustomDigrah(filename=output_file_name, edge_attr={'sep': "10", "esep": "5"}, graph_attr=graph_attr,
                       format="svg")

    # the root node
    dot.node(playbook_name, style="dotted")

    graph_representation = GraphRepresentation()

    # loop through the plays
    for play_counter, play in enumerate(playbook.get_plays(), 1):

        # TODO: Check the if the picked color is (almost) white. We can't see a white edge on the graph

        picked_color = Color(pick_for=play)
        color = picked_color.get_hex_l()
        play_font_color = "black" if picked_color.get_luminance() > 0.6 else "white"

        play_name = "hosts: " + clean_name(str(play))
        play_id = clean_id("play_" + play_name)
        play_vars = variable_manager.get_vars(play)

        graph_representation.add_node(play_id)

        with dot.subgraph(name=play_name) as play_subgraph:

            # role cluster color
            play_subgraph.attr(color=color)

            # play node

            play_subgraph.node(play_name, id=play_id, style='filled', shape="box", color=color,
                               fontcolor=play_font_color, tooltip="     ".join(play_vars['ansible_play_hosts']))

            # edge from root node to plays
            play_subgraph.edge(playbook_name, play_name, style="bold", label=str(play_counter), color=color,
                               fontcolor=color)

            # loop through the pre_tasks
            nb_pre_tasks = 0
            for pre_task_block in play.pre_tasks:
                nb_pre_tasks = include_tasks_in_blocks(play_subgraph, play_name, play_id, pre_task_block, color,
                                                       nb_pre_tasks, graph_representation, '[pre_task] ')

            # loop through the roles
            for role_counter, role in enumerate(play.get_roles()):
                role_name = '[role] ' + clean_name(str(role))

                with dot.subgraph(name=role_name, node_attr={}) as role_subgraph:
                    current_counter = role_counter + nb_pre_tasks + 1
                    role_id = clean_id("role_" + role_name)
                    role_subgraph.node(role_name, id=role_id)

                    when = "".join(role.when)
                    play_to_node_label = str(current_counter) if len(when) == 0 else str(
                        current_counter) + "  [when: " + when + "]"

                    edge_id = clean_id("edge_" + play_id + role_id)

                    role_subgraph.edge(play_name, role_name, label=play_to_node_label, color=color, fontcolor=color,
                                       id=edge_id)

                    graph_representation.add_link(play_id, edge_id)

                    graph_representation.add_link(play_id, role_id)

                    # loop through the tasks of the roles
                    if include_role_tasks:
                        role_tasks_counter = 0
                        for block in role.get_task_blocks():
                            role_tasks_counter = include_tasks_in_blocks(role_subgraph, role_name, role_id, block,
                                                                         color, role_tasks_counter,
                                                                         graph_representation,
                                                                         '[task] ')
                            role_tasks_counter += 1

            nb_roles = len(play.get_roles())
            # loop through the tasks
            nb_tasks = 0
            for task_block in play.tasks:
                nb_tasks = include_tasks_in_blocks(play_subgraph, play_name, play_id, task_block, color,
                                                   nb_roles + nb_pre_tasks,
                                                   graph_representation, '[task] ')

            # loop through the post_tasks
            for post_task_block in play.post_tasks:
                include_tasks_in_blocks(play_subgraph, play_name, play_id, post_task_block, color, nb_tasks,
                                        graph_representation, '[post_task] ')

    dot.render(cleanup=save_dot_file)
    post_process_svg(output_file_name + ".svg", graph_representation)


def main():
    parser = argparse.ArgumentParser(description=__doc__, prog='ansible-playbook-grapher')

    parser.add_argument("playbook", help="The playbook to grah.")

    parser.add_argument("-i", "--inventory", "--inventory-file",
                        help="Ansible inventory. Useful if you want to have a tooltip with hostnames on the play nodes.")

    parser.add_argument("--include-role-tasks", dest="include_role_tasks", action='store_true',
                        help="Include the tasks of the role in the graph. Can produce a huge graph if you have lot of roles.")

    parser.add_argument("-s", "--save-dot-file", dest="save_dot_file", action='store_false',
                        help="Save the dot file used to generate the graph.")

    parser.add_argument("-o", "--ouput-file-name", dest='output_file_name',
                        help="Output filename without the '.svg' extension. Default: <playbook>.svg")

    parser.add_argument("-v", "--version", dest="version", action="version", help="Print version and exit.",
                        version='%(prog)s ' + __version__)

    args = parser.parse_args()

    loader = DataLoader()
    inventory = InventoryManager(loader=loader, sources=args.inventory)
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    # Reading of the playbook: tasks, roles and so on...
    pb = Playbook.load(args.playbook, loader=loader, variable_manager=variable_manager)

    dump_playbok(pb, loader, variable_manager, args.include_role_tasks, args.save_dot_file, args.output_file_name)


if __name__ == "__main__":
    main()
