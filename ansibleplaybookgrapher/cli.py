import ntpath
import os
import sys
from abc import ABC

from ansible.cli import CLI
from ansible.cli.arguments import option_helpers
from ansible.release import __version__ as ansible_version
from ansible.utils.display import Display

from ansibleplaybookgrapher import __prog__, __version__
from ansibleplaybookgrapher.parser import PlaybookParser
from ansibleplaybookgrapher.postprocessor import GraphVizPostProcessor
from ansibleplaybookgrapher.renderer import GraphvizRenderer


def get_cli_class():
    """
    Utility function to return the class to use as CLI
    :return:
    """

    return PlaybookGrapherCLI


class GrapherCLI(CLI, ABC):
    """
    An abstract class to be implemented by the different Grapher CLIs.
    """

    def run(self):
        super(GrapherCLI, self).run()

        # The display is a singleton. This instruction will NOT return a new instance.
        # We explicitly set the verbosity after the init.
        display = Display()
        display.verbosity = self.options.verbosity

        parser = PlaybookParser(display=display, tags=self.options.tags, skip_tags=self.options.skip_tags,
                                playbook_filename=self.options.playbook_filename,
                                include_role_tasks=self.options.include_role_tasks)

        playbook_node = parser.parse()
        renderer = GraphvizRenderer(playbook_node, display)
        display.display("Rendering the graph...")
        svg_path = renderer.render(self.options.output_filename, self.options.save_dot_file, self.options.view)

        post_processor = GraphVizPostProcessor(svg_path=svg_path)
        post_processor.post_process(playbook_node=playbook_node)
        post_processor.write()

        display.display(f"The graph has been exported to {svg_path}", color="green")

        return svg_path


class PlaybookGrapherCLI(GrapherCLI):
    """
    The dedicated playbook grapher CLI
    """

    def __init__(self, args, callback=None):
        super(PlaybookGrapherCLI, self).__init__(args=args, callback=callback)
        # We keep the old options as instance attribute for backward compatibility for the grapher CLI.
        # From Ansible 2.8, they remove this instance attribute 'options' and use a global context instead.
        # But this may change in the future:
        # https://github.com/ansible/ansible/blob/bcb64054edaa7cf636bd38b8ab0259f6fb93f3f9/lib/ansible/context.py#L8
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

        self.parser.add_argument("--view", action='store_true', default=False,
                                 help="Automatically open the resulting SVG file with your system’s default viewer application for the file type")

        self.parser.add_argument("-o", "--output-file-name", dest='output_filename',
                                 help="Output filename without the '.svg' extension. Default: <playbook>.svg")

        self.parser.add_argument('--version', action='version',
                                 version="%s %s (with ansible %s)" % (__prog__, __version__, ansible_version))

        self.parser.add_argument('playbook_filename', help='Playbook to graph', metavar='playbook')

        # Use ansible helper to add some default options also
        option_helpers.add_subset_options(self.parser)
        option_helpers.add_vault_options(self.parser)
        option_helpers.add_runtask_options(self.parser)

    def init_parser(self, usage="", desc=None, epilog=None):
        super(PlaybookGrapherCLI, self).init_parser(usage="%s [options] playbook.yml" % __prog__,
                                                    desc="Make graphs from your Ansible Playbooks.", epilog=epilog)

        self._add_my_options()

    def post_process_args(self, options):
        options = super(PlaybookGrapherCLI, self).post_process_args(options)

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
