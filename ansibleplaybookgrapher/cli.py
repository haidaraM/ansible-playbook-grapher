import ntpath
import os
import sys
from abc import ABC

from ansible.cli import CLI
from ansible.errors import AnsibleOptionsError
from ansible.release import __version__ as ansible_version
from ansible.utils.display import Display
from packaging import version

from ansibleplaybookgrapher import __prog__, __version__
from ansibleplaybookgrapher.grapher import PlaybookGrapher
from ansibleplaybookgrapher.postprocessor import PostProcessor

# We need to know if we are using ansible 2.8 because the CLI has been refactored in
# https://github.com/ansible/ansible/pull/50069
IS_ANSIBLE_2_9_X = version.parse(ansible_version) >= version.parse("2.9")


def get_cli_class():
    """
    Utility function to return the class to use as CLI depending on Ansible version
    :return:
    """
    if IS_ANSIBLE_2_9_X:
        return PlaybookGrapherCLI29
    else:
        return PlaybookGrapherCLI28


class GrapherCLI(CLI, ABC):
    """
    An abstract class to provide to be implemented by the different Grapher CLIs.
    """

    def run(self):
        super(GrapherCLI, self).run()

        loader, inventory, variable_manager = CLI._play_prereqs()
        # Looks like the display is a singleton. This instruction will NOT return a new instance.
        # This is why we set the verbosity later because someone set it before us.
        display = Display()
        display.verbosity = self.options.verbosity

        grapher = PlaybookGrapher(data_loader=loader, inventory_manager=inventory, variable_manager=variable_manager,
                                  display=display, tags=self.options.tags, skip_tags=self.options.skip_tags,
                                  playbook_filename=self.options.playbook_filename,
                                  include_role_tasks=self.options.include_role_tasks)

        grapher.make_graph()

        svg_path = grapher.render_graph(self.options.output_filename, self.options.save_dot_file)
        post_processor = PostProcessor(svg_path=svg_path)
        post_processor.post_process(graph_representation=grapher.graph_representation)
        post_processor.write()

        display.display(f"fThe graph has been exported to {svg_path}")

        return svg_path


class PlaybookGrapherCLI28(GrapherCLI):
    """
    The dedicated playbook CLI for Ansible 2.8.
    """

    def __init__(self, args, callback=None):
        super(PlaybookGrapherCLI28, self).__init__(args=args, callback=callback)
        # we keep the old options as instance attribute for backward compatibility for the grapher
        # Ansible 2.8 has removed it and use a global context instead
        self.options = None

    def _add_my_options(self):
        """
        Method to add some options specific to the grapher
        :return:
        """
        self.parser.add_option('-i', '--inventory', dest='inventory', action="append",
                               help="specify inventory host path or comma separated host list.")

        self.parser.add_option("--include-role-tasks", dest="include_role_tasks", action='store_true', default=False,
                               help="Include the tasks of the role in the graph.")

        self.parser.add_option("-s", "--save-dot-file", dest="save_dot_file", action='store_true', default=False,
                               help="Save the dot file used to generate the graph.")

        self.parser.add_option("-o", "--ouput-file-name", dest='output_filename',
                               help="Output filename without the '.svg' extension. Default: <playbook>.svg")

        self.parser.version = "%s %s (with ansible %s)" % (__prog__, __version__, ansible_version)

    def init_parser(self, usage="", desc=None, epilog=None):
        super(PlaybookGrapherCLI28, self).init_parser(usage="%s [options] playbook.yml" % __prog__,
                                                      desc="Make graphs from your Ansible Playbooks.", epilog=epilog)
        self._add_my_options()

        from ansible.cli.arguments import optparse_helpers as opt_help

        opt_help.add_subset_options(self.parser)
        opt_help.add_vault_options(self.parser)
        opt_help.add_runtask_options(self.parser)

    def post_process_args(self, options, args):
        options, args = super(PlaybookGrapherCLI28, self).post_process_args(options, args)

        if len(args) == 0:
            raise AnsibleOptionsError("You must specify a playbook file to graph.")

        if len(args) > 1:
            raise AnsibleOptionsError("You must specify only one playbook file to graph.")

        # init the options
        self.options = options
        self.options.playbook_filename = args[0]

        if self.options.output_filename is None:
            # use the playbook name (without the extension) as output filename
            self.options.output_filename = os.path.splitext(ntpath.basename(self.options.playbook_filename))[0]

        return options, args


class PlaybookGrapherCLI29(GrapherCLI):
    """
    The dedicated playbook CLI for Ansible 2.9 and above.
    Note: Use this class as the main CLI when we drop support for ansible < 2.9
    """

    def __init__(self, args, callback=None):
        super(PlaybookGrapherCLI29, self).__init__(args=args, callback=callback)
        # we keep the old options as instance attribute for backward compatibility for the grapher
        # Ansible 2.8 has removed it and use a global context instead
        self.options = None

    def _add_my_options(self):
        """
        Add some of my options to the parser
        :param parser:
        :return:
        """
        self.parser.prog = __prog__

        self.parser.add_argument('-i', '--inventory', dest='inventory', action="append",
                                 help="specify inventory host path or comma separated host list.")

        self.parser.add_argument("--include-role-tasks", dest="include_role_tasks", action='store_true', default=False,
                                 help="Include the tasks of the role in the graph.")

        self.parser.add_argument("-s", "--save-dot-file", dest="save_dot_file", action='store_true', default=False,
                                 help="Save the dot file used to generate the graph.")

        self.parser.add_argument("-o", "--ouput-file-name", dest='output_filename',
                                 help="Output filename without the '.svg' extension. Default: <playbook>.svg")

        self.parser.add_argument('--version', action='version',
                                 version="%s %s (with ansible %s)" % (__prog__, __version__, ansible_version))

        self.parser.add_argument('playbook_filename', help='Playbook to graph', metavar='playbook')

    def init_parser(self, usage="", desc=None, epilog=None):
        super(PlaybookGrapherCLI29, self).init_parser(usage="%s [options] playbook.yml" % __prog__,
                                                      desc="Make graphs from your Ansible Playbooks.", epilog=epilog)

        self._add_my_options()

        # add ansible specific options
        from ansible.cli.arguments import option_helpers as opt_help
        opt_help.add_subset_options(self.parser)
        opt_help.add_vault_options(self.parser)
        opt_help.add_runtask_options(self.parser)

    def post_process_args(self, options):
        options = super(PlaybookGrapherCLI29, self).post_process_args(options)

        # init the options
        self.options = options

        if self.options.output_filename is None:
            # use the playbook name (without the extension) as output filename
            self.options.output_filename = os.path.splitext(ntpath.basename(self.options.playbook_filename))[0]

        return options


def main(args=None):
    args = args or sys.argv
    cli = get_cli_class()(args)

    cli.run()


if __name__ == "__main__":
    main(sys.argv)
