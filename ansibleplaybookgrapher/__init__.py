"""
Simple grapher for an Ansible Playbook.

You will need to install Ansible, graphviz on your system (sudo apt-get install graphviz).

Has been tested with Ansible 2.4.
"""

import random
import argparse
import ntpath
import os

from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook import Playbook
from ansible.playbook.block import Block
from ansible.vars.manager import VariableManager
from graphviz import Digraph

__version__ = "0.0.1"

# TODO: add more colors
colors = ["red", "#007FFF", "green", "purple", "brown", "orange", "#F562FF", "#5ED4FF", "#50C878", "#0095B6", "#FFD700",
          "#61FF46", "#CC8899"]


def clean_name(name):
    """
    Clean a name for the node, edge...
    :param name:
    :return:
    """
    return name.strip()


class CustomDiagram(Digraph):
    """
    Custom digraph to avoid quoting issue with node names. Nothing special here expect I put some double quotes around
    the node and edge names and overrided some methods.
    """
    _edge = '\t"%s" -> "%s"%s'
    _node = '\t"%s"%s'
    _subgraph = 'subgraph "%s"{'
    _quote = staticmethod(clean_name)
    _quote_edge = staticmethod(clean_name)


def include_tasks_in_blocks(graph, parent_node_name, block, color, current_counter, node_name_prefix=''):
    """
    Recursively read all the tasks of the block and add it to the graph
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
            loop_counter = include_tasks_in_blocks(graph, parent_node_name, task_or_block, color, loop_counter,
                                                   node_name_prefix)
        else:
            task_name = clean_name(node_name_prefix + task_or_block.get_name())
            graph.node(task_name, shape="octagon")
            graph.edge(parent_node_name, task_name, label=str(loop_counter + 1), color=color, fontcolor=color,
                       style="bold")

            loop_counter += 1

    return loop_counter


def dump_playbok(playbook, variable_manager, include_role_tasks, save_dot_file):
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

    :param save_dot_file:
    :param playbook:
    :param variable_manager:
    :param include_role_tasks:
    :return:
    """
    playbook_name = playbook._file_name
    output_file_name = os.path.splitext(ntpath.basename(playbook_name))[0]

    graph_attr = {'ratio': "fill", "rankdir": "LR", 'concentrate': 'true', 'ordering': 'in'}
    dot = CustomDiagram(filename=output_file_name, edge_attr={'sep': "10", "esep": "5"}, graph_attr=graph_attr,
                        format="svg")

    # the root node
    dot.node(playbook_name, style="dotted")

    # loop through the plays
    for play_counter, play in enumerate(playbook.get_plays(), 1):
        color = random.choice(colors)

        play_name = clean_name("hosts: " + clean_name(str(play)))

        play_vars = variable_manager.get_vars(play)

        with dot.subgraph(name=play_name) as play_subgraph:

            # role cluster color
            play_subgraph.attr(color=color)

            # play node
            play_subgraph.node(play_name, style='filled', shape="box", color=color,
                               tooltip="     ".join(play_vars['ansible_play_hosts']))

            # edge from root node to plays
            play_subgraph.edge(playbook_name, play_name, style="bold", label=str(play_counter), color=color,
                               fontcolor=color)

            # loop through the pre_tasks
            nb_pre_tasks = 0
            for pre_task_block in play.pre_tasks:
                nb_pre_tasks = include_tasks_in_blocks(play_subgraph, play_name, pre_task_block, color, nb_pre_tasks,
                                                       '[pre_task] ')

            # loop through the roles
            for role_counter, role in enumerate(play.get_roles()):
                role_tasks_counter = 0
                role_name = '[role] ' + clean_name(str(role))

                with dot.subgraph(name=role_name, node_attr={'style': 'bold'}) as role_subgraph:
                    current_counter = play_counter + role_counter + nb_pre_tasks

                    when = "".join(role.when)
                    label = str(current_counter) if len(when) == 0 else str(current_counter) + "  [when: " + when + "]"

                    role_subgraph.edge(play_name, role_name, label=label, color=color, fontcolor=color)

                    # loop through the tasks of the roles
                    if include_role_tasks:
                        for block in role.get_task_blocks():
                            role_tasks_counter = include_tasks_in_blocks(role_subgraph, role_name, block, color,
                                                                         role_tasks_counter, '[task] ')
                            role_tasks_counter += 1

            nb_roles = len(play.get_roles())
            # loop through the tasks
            nb_tasks = 0
            for task_block in play.tasks:
                nb_tasks = include_tasks_in_blocks(play_subgraph, play_name, task_block, color, nb_roles + nb_pre_tasks,
                                                   '[task] ')

            # loop through the post_tasks
            nb_post_tasks = 0
            for post_task_block in play.post_tasks:
                nb_post_tasks = include_tasks_in_blocks(play_subgraph, play_name, post_task_block, color,
                                                        nb_tasks, '[post_task] ')

    dot.render(cleanup=save_dot_file)


def main():
    parser = argparse.ArgumentParser(description=__doc__, prog='ansible-playbook-grapher')

    parser.add_argument("playbook", help="The playbook to grah.")
    parser.add_argument("-i", "--inventory",
                        help="The inventory. Useful if you want to have a tooltip with hostnames on the play nodes.")
    parser.add_argument("--include-role-tasks", dest="include_role_tasks", action='store_true',
                        help="Include tasks of the role in the graph. Can produce a big graph if you have lot of roles.")
    parser.add_argument("--save-dot-file", dest="save_dot_file", action='store_false',
                        help="Save the dot file used to generate the graph.")
    parser.add_argument("-V", "--version", dest="version", action="store_true", help="Print version and exits")

    args = parser.parse_args()

    if args.version:
        print(__version__)
        exit(0)

    loader = DataLoader()
    inventory = InventoryManager(loader=loader, sources=args.inventory)
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    # Reading of the playbook: tasks, roles and so on...
    pb = Playbook.load(args.playbook, loader=loader, variable_manager=variable_manager)

    dump_playbok(pb, variable_manager, args.include_role_tasks, args.save_dot_file)


if __name__ == "__main__":
    main()
