import ntpath
import os
import sys

from ansible.cli import CLI
from ansible.errors import AnsibleOptionsError
from ansible.release import __version__ as ansible_version
from ansible.utils.display import Display

from ansibleplaybookgrapher import __prog__, __version__
from ansibleplaybookgrapher.grapher import Grapher

display = Display()


class PlaybookGrapherCLI(CLI):
    """
    Playbook grapher CLI
    """

    def run(self):
        super(PlaybookGrapherCLI, self).run()

        playbook = self.args[0]

        loader, inventory, variable_manager = self._play_prereqs(self.options)

        grapher = Grapher(data_loader=loader, inventory_manager=inventory, variable_manager=variable_manager,
                          playbook_filename=playbook, options=self.options)

        grapher.make_graph()

        grapher.render_graph()

        return grapher.post_process_svg()

    def parse(self):
        """
        Add the grapher specific options
        FIXME: In Ansible 2.9, optparse will be replaced by argparse https://github.com/ansible/ansible/pull/50610
        :return:
        :rtype:
        """
        parser = CLI.base_parser(
            usage="%s [options] playbook.yml" % __prog__,
            subset_opts=True,
            vault_opts=True,
            runtask_opts=True,
            desc="Make graph from your Playbook.",
        )

        parser.add_option('-i', '--inventory', dest='inventory', action="append",
                          help="specify inventory host path (default=[%s]) or comma separated host list. ")

        parser.add_option("--include-role-tasks", dest="include_role_tasks", action='store_true', default=False,
                          help="Include the tasks of the role in the graph.")

        parser.add_option("-s", "--save-dot-file", dest="save_dot_file", action='store_true', default=False,
                          help="Save the dot file used to generate the graph.")

        parser.add_option("-o", "--ouput-file-name", dest='output_filename',
                          help="Output filename without the '.svg' extension. Default: <playbook>.svg")

        parser.version = "%s %s (with ansible %s)" % (__prog__, __version__, ansible_version)

        self.parser = parser

        super(PlaybookGrapherCLI, self).parse()

        if len(self.args) == 0:
            raise AnsibleOptionsError("You must specify a playbook file to graph.")

        if len(self.args) > 1:
            raise AnsibleOptionsError("You must specify only one playbook file to graph.")

        display.verbosity = self.options.verbosity

        if self.options.output_filename is None:
            # use the playbook name (without the extension) as output filename
            self.options.output_filename = os.path.splitext(ntpath.basename(self.args[0]))[0]


def main(args=None):
    args = args or sys.argv
    cli = PlaybookGrapherCLI(args)

    cli.parse()

    cli.run()


if __name__ == "__main__":
    main(sys.argv)
