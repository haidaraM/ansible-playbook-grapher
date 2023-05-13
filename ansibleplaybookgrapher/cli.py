# Copyright (C) 2023 Mohamed El Mouctar HAIDARA
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

from ansible.cli import CLI
from ansible.cli.arguments import option_helpers
from ansible.errors import AnsibleOptionsError
from ansible.release import __version__ as ansible_version
from ansible.utils.display import Display

from ansibleplaybookgrapher import __prog__, __version__, Grapher
from ansibleplaybookgrapher.renderer import OPEN_PROTOCOL_HANDLERS
from ansibleplaybookgrapher.renderer.graphviz import GraphvizRenderer
from ansibleplaybookgrapher.renderer.mermaid import (
    MermaidFlowChartRenderer,
    DEFAULT_DIRECTIVE as MERMAID_DEFAULT_DIRECTIVE,
    DEFAULT_ORIENTATION as MERMAID_DEFAULT_ORIENTATION,
)

# The display is a singleton. This instruction will NOT return a new instance.
# We explicitly set the verbosity after the init.
display = Display()


class PlaybookGrapherCLI(CLI):
    """
    The dedicated playbook grapher CLI
    """

    name = __prog__

    def __init__(self, args, callback=None):
        super().__init__(args=args, callback=callback)
        # We keep the old options as instance attribute for backward compatibility for the grapher CLI.
        # From Ansible 2.8, they remove this instance attribute 'options' and use a global context instead.
        # But this may change in the future:
        # https://github.com/ansible/ansible/blob/bcb64054edaa7cf636bd38b8ab0259f6fb93f3f9/lib/ansible/context.py#L8
        self.options = None

    def run(self):
        super().run()

        display.verbosity = self.options.verbosity
        grapher = Grapher(self.options.playbook_filenames)
        playbook_nodes, roles_usage = grapher.parse(
            include_role_tasks=self.options.include_role_tasks,
            tags=self.options.tags,
            skip_tags=self.options.skip_tags,
            group_roles_by_name=self.options.group_roles_by_name,
        )

        if self.options.renderer == "graphviz":
            renderer = GraphvizRenderer(
                playbook_nodes=playbook_nodes,
                roles_usage=roles_usage,
            )
            output_path = renderer.render(
                open_protocol_handler=self.options.open_protocol_handler,
                open_protocol_custom_formats=self.options.open_protocol_custom_formats,
                output_filename=self.options.output_filename,
                view=self.options.view,
                save_dot_file=self.options.save_dot_file,
            )

            return output_path
        else:
            renderer = MermaidFlowChartRenderer(
                playbook_nodes=playbook_nodes,
                roles_usage=roles_usage,
            )
            output_path = renderer.render(
                open_protocol_handler=self.options.open_protocol_handler,
                open_protocol_custom_formats=self.options.open_protocol_custom_formats,
                output_filename=self.options.output_filename,
                view=self.options.view,
                directive=self.options.renderer_mermaid_directive,
                orientation=self.options.renderer_mermaid_orientation,
            )
            return output_path

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
            help="Save the graphviz dot file used to generate the graph.",
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
                                 vscode, set it to: 
                                 '{"file": "vscode://file/{path}:{line}:{column}", "folder": "{path}"}'.
                                  path: the absolute path to the file containing the the plays/tasks/roles.
                                  line/column: the position of the plays/tasks/roles in the file.  
                                  You can optionally add the attribute "remove_from_path" to remove some parts of the 
                                  path if you want relative paths. 
                                 """,
        )

        self.parser.add_argument(
            "--group-roles-by-name",
            action="store_true",
            default=False,
            help="When rendering the graph, only a single role will be display for all roles having the same names. Default: %(default)s",
        )

        self.parser.add_argument(
            "--renderer",
            choices=["graphviz", "mermaid-flowchart"],
            default="graphviz",
            help="The renderer to use to generate the graph. Default: %(default)s",
        )

        self.parser.add_argument(
            "--renderer-mermaid-directive",
            default=MERMAID_DEFAULT_DIRECTIVE,
            help="The directive for the mermaid renderer. Can be used to customize the output: fonts, theme, curve etc. More info at https://mermaid.js.org/config/directives.html. Default: '%(default)s'",
        )

        self.parser.add_argument(
            "--renderer-mermaid-orientation",
            default=MERMAID_DEFAULT_ORIENTATION,
            choices=["TD", "RL", "BT", "RL", "LR"],
            help="The orientation of the flow chart. Default: '%(default)s'",
        )

        self.parser.add_argument(
            "--version",
            action="version",
            version=f"{__prog__} {__version__} (with ansible {ansible_version})",
        )

        self.parser.add_argument(
            "playbook_filenames",
            help="Playbook(s) to graph",
            metavar="playbooks",
            nargs="+",
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
            basenames = map(ntpath.basename, self.options.playbook_filenames)
            basenames_without_ext = "-".join(
                [os.path.splitext(basename)[0] for basename in basenames]
            )
            self.options.output_filename = basenames_without_ext

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
    cli = PlaybookGrapherCLI(args)

    cli.run()


if __name__ == "__main__":
    main(sys.argv)
