import sys

from ansible.cli import CLI
from ansible.errors import AnsibleOptionsError
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager

from ansibleplaybookgrapher.grapher import Grapher

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()

from ansibleplaybookgrapher import __prog__, __version__


class PlaybookGrapherCLI(CLI):
    """
    Playbook grapher CLI
    """

    def run(self):
        super(PlaybookGrapherCLI, self).run()

        playbook = self.args[0]

        loader = DataLoader()
        inventory = InventoryManager(loader=loader, sources=self.options.inventory)
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        grapher = Grapher(data_loader=loader, inventory_manager=inventory, variable_manager=variable_manager,
                          playbook_filename=playbook, output_filename=self.options.output_file_name)

        grapher.make_graph(include_role_tasks=self.options.include_role_tasks, tags=self.options.tags,
                           skip_tags=self.options.skip_tags)

        grapher.render_graph(save_dot_file=self.options.save_dot_file)

        grapher.post_process_svg()

    def parse(self):
        # create parser for CLI options
        parser = CLI.base_parser(
            usage="%s [options] playbook.yml" % __prog__,
            subset_opts=True,
            vault_opts=False,
            desc="Make graph from your Playbook.",
        )

        parser.add_option('-i', '--inventory', dest='inventory', action="append",
                          help="specify inventory host path (default=[%s]) or comma separated host list. ")

        parser.add_option("--include-role-tasks", dest="include_role_tasks", action='store_true', default=False,
                          help="Include the tasks of the role in the graph.")

        parser.add_option("-s", "--save-dot-file", dest="save_dot_file", action='store_false', default=True,
                          help="Save the dot file used to generate the graph.")

        parser.add_option("-o", "--ouput-file-name", dest='output_file_name',
                          help="Output filename without the '.svg' extension. Default: <playbook>.svg")

        parser.version = "%s %s" % (__prog__, __version__)

        self.parser = parser

        super(PlaybookGrapherCLI, self).parse()

        if len(self.args) == 0:
            raise AnsibleOptionsError("You must specify a playbook file to graph.")

        if len(self.args) > 1:
            raise AnsibleOptionsError("You must specify only one playbook to graph.")

        display.verbosity = self.options.verbosity


def main():
    cli = PlaybookGrapherCLI(sys.argv)

    cli.parse()

    cli.run()


if __name__ == "__main__":
    main()
