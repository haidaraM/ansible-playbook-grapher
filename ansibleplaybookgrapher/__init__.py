"""
Simple grapher for an Ansible Playbook.

You will need to install Ansible, graphviz on your system (sudo apt-get install graphviz).

Has been tested with Ansible 2.4.
"""

import argparse

from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager

from ansibleplaybookgrapher.grapher import Grapher
from ansibleplaybookgrapher.utils import post_process_svg, GraphRepresentation, clean_id, clean_name

__version__ = "0.4.0"


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

    parser.add_argument('-t', '--tags', dest='tags', default=[], action='append',
                        help="Only show tasks tagged with these values.")

    parser.add_argument('--skip-tags', dest='skip_tags', default=[], action='append',
                        help="Only show tasks whose tags do not match these values.")

    parser.add_argument("-v", "--version", dest="version", action="version", help="Print version and exit.",
                        version='%(prog)s ' + __version__)

    args = parser.parse_args()

    # process tags
    tags = set()
    for tag_set in args.tags:
        for tag in tag_set.split(u','):
            tags.add(tag.strip())

    tags = list(tags)

    skip_tags = set()
    for skip_tag_set in args.skip_tags:
        for skip_tag in skip_tag_set.split(u','):
            skip_tags.add(skip_tag.strip())
    skip_tags = list(skip_tags)

    loader = DataLoader()
    inventory = InventoryManager(loader=loader, sources=args.inventory)
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    grapher = Grapher(data_loader=loader, inventory_manager=inventory, variable_manager=variable_manager,
                      playbook_filename=args.playbook, output_file_name=args.output_file_name)

    grapher.make_graph(include_role_tasks=args.include_role_tasks, tags=tags, skip_tags=skip_tags)

    grapher.render_graph(save_dot_file=args.save_dot_file)

    grapher.post_process_svg()


if __name__ == "__main__":
    main()
