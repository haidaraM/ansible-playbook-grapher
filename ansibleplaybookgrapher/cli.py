# Copyright (C) 2022 Mohamed El Mouctar HAIDARA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import json
import ntpath
import os
import sys
from abc import ABC

from ansible.cli import CLI
from ansible.cli.arguments import option_helpers
from ansible.errors import AnsibleOptionsError
from ansible.release import __version__ as ansible_version
from ansible.utils.display import Display, initialize_locale

from ansibleplaybookgrapher import __prog__, __version__
from ansibleplaybookgrapher.parser import PlaybookParser
from ansibleplaybookgrapher.postprocessor import GraphVizPostProcessor
from ansibleplaybookgrapher.renderer import GraphvizRenderer, OPEN_PROTOCOL_HANDLERS

# The display is a singleton. This instruction will NOT return a new instance.
# We explicitly set the verbosity after the init.
display = Display()


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
        super().run()

        # Required to fix the warning "ansible.utils.display.initialize_locale has not been called..."
        initialize_locale()
        display.verbosity = self.options.verbosity

        parser = PlaybookParser(
            tags=self.options.tags,
            skip_tags=self.options.skip_tags,
            playbook_filename=self.options.playbook_filename,
            include_role_tasks=self.options.include_role_tasks,
        )

        playbook_node = parser.parse()
        renderer = GraphvizRenderer(
            playbook_node,
            open_protocol_handler=self.options.open_protocol_handler,
            open_protocol_custom_formats=self.options.open_protocol_custom_formats,
        )
        svg_path = renderer.render(
            self.options.output_filename, self.options.save_dot_file, self.options.view
        )

        post_processor = GraphVizPostProcessor(svg_path=svg_path)
        display.v("Post processing the SVG...")
        post_processor.post_process(playbook_node=playbook_node)
        post_processor.write()

        display.display(f"The graph has been exported to {svg_path}", color="green")

        return svg_path


class PlaybookGrapherCLI(GrapherCLI):
    """
    The dedicated playbook grapher CLI
    """

    def __init__(self, args, callback=None):
        super().__init__(args=args, callback=callback)
        # We keep the old options as instance attribute for backward compatibility for the grapher CLI.
        # From Ansible 2.8, they remove this instance attribute 'options' and use a global context instead.
        # But this may change in the future:
        # https://github.com/ansible/ansible/blob/bcb64054edaa7cf636bd38b8ab0259f6fb93f3f9/lib/ansible/context.py#L8
        self.options = None

    def _add_my_options(self):
        """
        Add some of my options to the parser
        :return:
        """
        self.parser.prog = __prog__

        self.parser.add_argument(
            "-i",
            "--inventory",
            dest="inventory",
            action="append",
            help="specify inventory host path or comma separated host list.",
        )

        self.parser.add_argument(
            "--include-role-tasks",
            dest="include_role_tasks",
            action="store_true",
            default=False,
            help="Include the tasks of the role in the graph.",
        )

        self.parser.add_argument(
            "-s",
            "--save-dot-file",
            dest="save_dot_file",
            action="store_true",
            default=False,
            help="Save the dot file used to generate the graph.",
        )

        self.parser.add_argument(
            "--view",
            action="store_true",
            default=False,
            help="Automatically open the resulting SVG file with your system’s default viewer application for the file type",
        )

        self.parser.add_argument(
            "-o",
            "--output-file-name",
            dest="output_filename",
            help="Output filename without the '.svg' extension. Default: <playbook>.svg",
        )

        self.parser.add_argument(
            "--open-protocol-handler",
            dest="open_protocol_handler",
            choices=list(OPEN_PROTOCOL_HANDLERS.keys()),
            default="default",
            help="""The protocol to use to open the nodes when double-clicking on them in your SVG 
                                 viewer. Your SVG viewer must support double-click and Javascript. 
                                 The supported values are 'default', 'vscode' and 'custom'. 
                                 For 'default', the URL will be the path to the file or folders. When using a browser, 
                                 it will open or download them. 
                                 For 'vscode', the folders and files will be open with VSCode.
                                 For 'custom', you need to set a custom format with --open-protocol-custom-formats.
                                 """,
        )

        self.parser.add_argument(
            "--open-protocol-custom-formats",
            dest="open_protocol_custom_formats",
            default=None,
            help="""The custom formats to use as URLs for the nodes in the graph. Required if
                                 --open-protocol-handler is set to custom.
                                 You should provide a JSON formatted string like: {"file": "", "folder": ""}.
                                 Example: If you want to open folders (roles) inside the browser and files (tasks) in
                                 vscode, set this to 
                                 '{"file": "vscode://file/{path}:{line}:{column}", "folder": "{path}"}'
                                 """,
        )

        self.parser.add_argument(
            "--version",
            action="version",
            version=f"{__prog__} {__version__} (with ansible {ansible_version})",
        )

        self.parser.add_argument(
            "playbook_filename", help="Playbook to graph", metavar="playbook"
        )

        # Use ansible helper to add some default options also
        option_helpers.add_subset_options(self.parser)
        option_helpers.add_vault_options(self.parser)
        option_helpers.add_runtask_options(self.parser)

    def init_parser(self, usage="", desc=None, epilog=None):
        super().init_parser(
            usage=f"{__prog__} [options] playbook.yml",
            desc="Make graphs from your Ansible Playbooks.",
            epilog=epilog,
        )

        self._add_my_options()

    def post_process_args(self, options):
        options = super().post_process_args(options)

        # init the options
        self.options = options

        if self.options.output_filename is None:
            # use the playbook name (without the extension) as output filename
            self.options.output_filename = os.path.splitext(
                ntpath.basename(self.options.playbook_filename)
            )[0]

        if self.options.open_protocol_handler == "custom":
            self.validate_open_protocol_custom_formats()

        return options

    def validate_open_protocol_custom_formats(self):
        """
        Validate the provided open protocol format
        :return:
        """
        error_msg = 'Make sure to provide valid formats. Example: {"file": "vscode://file/{path}:{line}:{column}", "folder": "{path}"}'
        format_str = self.options.open_protocol_custom_formats
        if not format_str:
            raise AnsibleOptionsError(
                "When the protocol handler is to set to custom, you must provide the formats to "
                "use with --open-protocol-custom-formats."
            )
        try:
            format_dict = json.loads(format_str)
        except Exception as e:
            display.error(
                f"{type(e).__name__} when reading the provided formats '{format_str}': {e}"
            )
            display.error(error_msg)
            sys.exit(1)

        if "file" not in format_dict or "folder" not in format_dict:
            display.error(
                f"The field 'file' or 'folder' is missing from the provided format '{format_str}'"
            )
            display.error(error_msg)
            sys.exit(1)

        # Replace the string with a dict
        self.options.open_protocol_custom_formats = format_dict


def main(args=None):
    args = args or sys.argv
    cli = get_cli_class()(args)

    cli.run()


if __name__ == "__main__":
    main(sys.argv)
