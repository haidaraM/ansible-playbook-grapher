# Ansible Playbook Grapher

![Testing](https://github.com/haidaraM/ansible-playbook-grapher/workflows/Testing/badge.svg)
[![PyPI version](https://badge.fury.io/py/ansible-playbook-grapher.svg)](https://badge.fury.io/py/ansible-playbook-grapher)
[![Coverage Status](https://coveralls.io/repos/github/haidaraM/ansible-playbook-grapher/badge.svg?branch=main)](https://coveralls.io/github/haidaraM/ansible-playbook-grapher?branch=main)

[ansible-playbook-grapher](https://github.com/haidaraM/ansible-playbook-grapher) is a command line tool to create a
graph representing your Ansible playbook plays, tasks and roles. The aim of this project is to have an overview of your
playbook.

Inspired by [Ansible Inventory Grapher](https://github.com/willthames/ansible-inventory-grapher).

## Features

The following features are available when opening the SVGs in a browser (recommended) or a viewer that supports
JavaScript:

- Highlighting of all the related nodes of a given node when clicking or hovering. Example: Click on a role to select
  all its tasks when `--include-role-tasks` is set.
- A double click on a node opens the corresponding file or folder depending whether if it's a playbook, a play, a task
  or a role. By default, the browser will open folders and download files since it may not be able to render the YAML
  file.  
  Optionally, you can
  set [the open protocol to use VSCode](https://code.visualstudio.com/docs/editor/command-line#_opening-vs-code-with-urls)
  with `--open-protocol-handler vscode`: it will open the folders when double-clicking on roles (not `include_role`) and
  the files for the others nodes. The cursor will be at the task exact position in the file.  
  Lastly, you can provide your own protocol formats
  with `--open-protocol-handler custom --open-protocol-custom-formats '{}'`. See the help
  and [an example.](https://github.com/haidaraM/ansible-playbook-grapher/blob/12cee0fbd59ffbb706731460e301f0b886515357/ansibleplaybookgrapher/graphbuilder.py#L33-L42)
- Filer tasks based on tags
- Export the dot file used to generate the graph with Graphviz.

## Prerequisites

- Python 3.10 at least. Might work with some previous versions but the code is NOT tested against them.
  See [support matrix](https://docs.ansible.com/ansible/latest/reference_appendices/release_and_maintenance.html#ansible-core-support-matrix).
- A virtual environment from which to run the grapher. This is **highly recommended** because the grapher depends on
  some versions of ansible-core which are not necessarily installed in your environment and may cause issues if you use
  some older versions of Ansible (
  since `ansible` [package has been split](https://www.ansible.com/blog/ansible-3.0.0-qa)).
- **Graphviz**: The tool used to generate the graph in SVG.
  ```shell script
  sudo apt-get install graphviz # or yum install or brew install
  ```

I try to respect [Red Hat Ansible Engine Life Cycle](https://access.redhat.com/support/policy/updates/ansible-engine)
for the supported Ansible version.

## Installation

```shell
pip install ansible-playbook-grapher
```

You can also install the unpublished version from GitHub direction. Examples: 

```shell
# Install the version from the main branch
pip install "ansible-playbook-grapher @ git+https://github.com/haidaraM/ansible-playbook-grapher"

# Install the version from a specific branch
pip install "ansible-playbook-grapher @ git+https://github.com/haidaraM/ansible-playbook-grapher@specific-branch"
```

### Renderers

At the time of writing, two renderers are supported:

1. `graphviz` (default): Generate the graph in SVG. It has more features and is more tested: open protocol,
   highlight linked nodes...
2. `mermaid-flowchart`: Generate the graph in [Mermaid](https://mermaid.js.org/syntax/flowchart.html) format. You can
   directly embed the graph in your markdown and GitHub (
   and [other integrations](https://mermaid.js.org/ecosystem/integrations.html)) will render it. **Early support**.

If you are interested to support more renderers, feel free to create an issue or raise a PR based on the existing
renderers.

## Usage

```shell
ansible-playbook-grapher tests/fixtures/example.yml
```

![Example](https://raw.githubusercontent.com/haidaraM/ansible-playbook-grapher/main/img/example.png)

```bash
ansible-playbook-grapher --include-role-tasks  tests/fixtures/with_roles.yml
```

![Example](https://raw.githubusercontent.com/haidaraM/ansible-playbook-grapher/main/img/with_roles.png)

```bash
ansible-playbook-grapher tests/fixtures/with_block.yml
```

![Example](https://raw.githubusercontent.com/haidaraM/ansible-playbook-grapher/main/img/block.png)

```bash
ansible-playbook-grapher --include-role-tasks --renderer mermaid-flowchart tests/fixtures/multi-plays.yml
```

```mermaid
---
title: Ansible Playbook Grapher
---
%%{ init: { "flowchart": { "curve": "bumpX" } } }%%
flowchart LR
	%% Start of the playbook 'tests/fixtures/multi-plays.yml'
	playbook_34b89e53("tests/fixtures/multi-plays.yml")
		%% Start of the play 'Play: all (0)'
		play_8c4134b8["Play: all (0)"]
		style play_8c4134b8 fill:#656f5d,color:#ffffff
		playbook_34b89e53 --> |"1"| play_8c4134b8
		linkStyle 0 stroke:#656f5d,color:#656f5d
			pre_task_dd2c1b7d["[pre_task]  Pretask"]
			style pre_task_dd2c1b7d stroke:#656f5d,fill:#ffffff
			play_8c4134b8 --> |"1"| pre_task_dd2c1b7d
			linkStyle 1 stroke:#656f5d,color:#656f5d
			pre_task_bc33639f["[pre_task]  Pretask 2"]
			style pre_task_bc33639f stroke:#656f5d,fill:#ffffff
			play_8c4134b8 --> |"2"| pre_task_bc33639f
			linkStyle 2 stroke:#656f5d,color:#656f5d
			%% Start of the role 'fake_role'
			play_8c4134b8 --> |"3"| role_f4e6fb4d
			linkStyle 3 stroke:#656f5d,color:#656f5d
			role_f4e6fb4d("[role] fake_role")
			style role_f4e6fb4d fill:#656f5d,color:#ffffff,stroke:#656f5d
				task_94f7fc58[" fake_role : Debug 1"]
				style task_94f7fc58 stroke:#656f5d,fill:#ffffff
				role_f4e6fb4d --> |"1 [when: ansible_distribution == 'Debian']"| task_94f7fc58
				linkStyle 4 stroke:#656f5d,color:#656f5d
				task_bd56c6b5[" fake_role : Debug 2"]
				style task_bd56c6b5 stroke:#656f5d,fill:#ffffff
				role_f4e6fb4d --> |"2 [when: ansible_distribution == 'Debian']"| task_bd56c6b5
				linkStyle 5 stroke:#656f5d,color:#656f5d
				task_4f51a1cc[" fake_role : Debug 3 with double quote &#34;here&#34; in the name"]
				style task_4f51a1cc stroke:#656f5d,fill:#ffffff
				role_f4e6fb4d --> |"3 [when: ansible_distribution == 'Debian']"| task_4f51a1cc
				linkStyle 6 stroke:#656f5d,color:#656f5d
			%% End of the role 'fake_role'
			%% Start of the role 'display_some_facts'
			play_8c4134b8 --> |"4"| role_497b8470
			linkStyle 7 stroke:#656f5d,color:#656f5d
			role_497b8470("[role] display_some_facts")
			style role_497b8470 fill:#656f5d,color:#ffffff,stroke:#656f5d
				task_984b3c44[" display_some_facts : ansible_architecture"]
				style task_984b3c44 stroke:#656f5d,fill:#ffffff
				role_497b8470 --> |"1"| task_984b3c44
				linkStyle 8 stroke:#656f5d,color:#656f5d
				task_3cb4a46c[" display_some_facts : ansible_date_time"]
				style task_3cb4a46c stroke:#656f5d,fill:#ffffff
				role_497b8470 --> |"2"| task_3cb4a46c
				linkStyle 9 stroke:#656f5d,color:#656f5d
				task_715c2049[" display_some_facts : Specific included task for Debian"]
				style task_715c2049 stroke:#656f5d,fill:#ffffff
				role_497b8470 --> |"3"| task_715c2049
				linkStyle 10 stroke:#656f5d,color:#656f5d
			%% End of the role 'display_some_facts'
			task_d8b579ea["[task]  Add backport {{backport}}"]
			style task_d8b579ea stroke:#656f5d,fill:#ffffff
			play_8c4134b8 --> |"5"| task_d8b579ea
			linkStyle 11 stroke:#656f5d,color:#656f5d
			task_99117197["[task]  Install packages"]
			style task_99117197 stroke:#656f5d,fill:#ffffff
			play_8c4134b8 --> |"6"| task_99117197
			linkStyle 12 stroke:#656f5d,color:#656f5d
			post_task_f789bda0["[post_task]  Posttask"]
			style post_task_f789bda0 stroke:#656f5d,fill:#ffffff
			play_8c4134b8 --> |"7"| post_task_f789bda0
			linkStyle 13 stroke:#656f5d,color:#656f5d
			post_task_08755b4b["[post_task]  Posttask 2"]
			style post_task_08755b4b stroke:#656f5d,fill:#ffffff
			play_8c4134b8 --> |"8"| post_task_08755b4b
			linkStyle 14 stroke:#656f5d,color:#656f5d
		%% End of the play 'Play: all (0)'
		%% Start of the play 'Play: database (0)'
		play_40fea3c6["Play: database (0)"]
		style play_40fea3c6 fill:#2370a9,color:#ffffff
		playbook_34b89e53 --> |"2"| play_40fea3c6
		linkStyle 15 stroke:#2370a9,color:#2370a9
			%% Start of the role 'fake_role'
			play_40fea3c6 --> |"1"| role_38fdd7bb
			linkStyle 16 stroke:#2370a9,color:#2370a9
			role_38fdd7bb("[role] fake_role")
			style role_38fdd7bb fill:#2370a9,color:#ffffff,stroke:#2370a9
				task_54a811a1[" fake_role : Debug 1"]
				style task_54a811a1 stroke:#2370a9,fill:#ffffff
				role_38fdd7bb --> |"1 [when: ansible_distribution == 'Debian']"| task_54a811a1
				linkStyle 17 stroke:#2370a9,color:#2370a9
				task_0400749b[" fake_role : Debug 2"]
				style task_0400749b stroke:#2370a9,fill:#ffffff
				role_38fdd7bb --> |"2 [when: ansible_distribution == 'Debian']"| task_0400749b
				linkStyle 18 stroke:#2370a9,color:#2370a9
				task_e453cadd[" fake_role : Debug 3 with double quote &#34;here&#34; in the name"]
				style task_e453cadd stroke:#2370a9,fill:#ffffff
				role_38fdd7bb --> |"3 [when: ansible_distribution == 'Debian']"| task_e453cadd
				linkStyle 19 stroke:#2370a9,color:#2370a9
			%% End of the role 'fake_role'
			%% Start of the role 'display_some_facts'
			play_40fea3c6 --> |"2"| role_b05b7094
			linkStyle 20 stroke:#2370a9,color:#2370a9
			role_b05b7094("[role] display_some_facts")
			style role_b05b7094 fill:#2370a9,color:#ffffff,stroke:#2370a9
				task_153db06e[" display_some_facts : ansible_architecture"]
				style task_153db06e stroke:#2370a9,fill:#ffffff
				role_b05b7094 --> |"1"| task_153db06e
				linkStyle 21 stroke:#2370a9,color:#2370a9
				task_13df99ce[" display_some_facts : ansible_date_time"]
				style task_13df99ce stroke:#2370a9,fill:#ffffff
				role_b05b7094 --> |"2"| task_13df99ce
				linkStyle 22 stroke:#2370a9,color:#2370a9
				task_369b5720[" display_some_facts : Specific included task for Debian"]
				style task_369b5720 stroke:#2370a9,fill:#ffffff
				role_b05b7094 --> |"3"| task_369b5720
				linkStyle 23 stroke:#2370a9,color:#2370a9
			%% End of the role 'display_some_facts'
		%% End of the play 'Play: database (0)'
		%% Start of the play 'Play: webserver (0)'
		play_a68ff4e7["Play: webserver (0)"]
		style play_a68ff4e7 fill:#a905c7,color:#ffffff
		playbook_34b89e53 --> |"3"| play_a68ff4e7
		linkStyle 24 stroke:#a905c7,color:#a905c7
			%% Start of the role 'nested_include_role'
			play_a68ff4e7 --> |"1"| role_8bcf64e2
			linkStyle 25 stroke:#a905c7,color:#a905c7
			role_8bcf64e2("[role] nested_include_role")
			style role_8bcf64e2 fill:#a905c7,color:#ffffff,stroke:#a905c7
				task_bd87cdf3[" nested_include_role : Ensure postgresql is at the latest version"]
				style task_bd87cdf3 stroke:#a905c7,fill:#ffffff
				role_8bcf64e2 --> |"1"| task_bd87cdf3
				linkStyle 26 stroke:#a905c7,color:#a905c7
				task_d7674c4b[" nested_include_role : Ensure that postgresql is started"]
				style task_d7674c4b stroke:#a905c7,fill:#ffffff
				role_8bcf64e2 --> |"2"| task_d7674c4b
				linkStyle 27 stroke:#a905c7,color:#a905c7
				%% Start of the role 'display_some_facts'
				role_8bcf64e2 --> |"3 [when: x is not defined]"| role_806214e1
				linkStyle 28 stroke:#a905c7,color:#a905c7
				role_806214e1("[role] display_some_facts")
				style role_806214e1 fill:#a905c7,color:#ffffff,stroke:#a905c7
					task_b1fb63fd[" display_some_facts : ansible_architecture"]
					style task_b1fb63fd stroke:#a905c7,fill:#ffffff
					role_806214e1 --> |"1"| task_b1fb63fd
					linkStyle 29 stroke:#a905c7,color:#a905c7
					task_4a1319fd[" display_some_facts : ansible_date_time"]
					style task_4a1319fd stroke:#a905c7,fill:#ffffff
					role_806214e1 --> |"2"| task_4a1319fd
					linkStyle 30 stroke:#a905c7,color:#a905c7
					task_175005a1[" display_some_facts : Specific included task for Debian"]
					style task_175005a1 stroke:#a905c7,fill:#ffffff
					role_806214e1 --> |"3"| task_175005a1
					linkStyle 31 stroke:#a905c7,color:#a905c7
				%% End of the role 'display_some_facts'
				%% Start of the role 'fake_role'
				role_8bcf64e2 --> |"4"| role_557d6933
				linkStyle 32 stroke:#a905c7,color:#a905c7
				role_557d6933("[role] fake_role")
				style role_557d6933 fill:#a905c7,color:#ffffff,stroke:#a905c7
					task_1fa41f3c[" fake_role : Debug 1"]
					style task_1fa41f3c stroke:#a905c7,fill:#ffffff
					role_557d6933 --> |"1"| task_1fa41f3c
					linkStyle 33 stroke:#a905c7,color:#a905c7
					task_2841d72b[" fake_role : Debug 2"]
					style task_2841d72b stroke:#a905c7,fill:#ffffff
					role_557d6933 --> |"2"| task_2841d72b
					linkStyle 34 stroke:#a905c7,color:#a905c7
					task_e5fef12a[" fake_role : Debug 3 with double quote &#34;here&#34; in the name"]
					style task_e5fef12a stroke:#a905c7,fill:#ffffff
					role_557d6933 --> |"3"| task_e5fef12a
					linkStyle 35 stroke:#a905c7,color:#a905c7
				%% End of the role 'fake_role'
			%% End of the role 'nested_include_role'
			%% Start of the role 'display_some_facts'
			play_a68ff4e7 --> |"2"| role_2720d5bc
			linkStyle 36 stroke:#a905c7,color:#a905c7
			role_2720d5bc("[role] display_some_facts")
			style role_2720d5bc fill:#a905c7,color:#ffffff,stroke:#a905c7
				task_4d8d8def[" display_some_facts : ansible_architecture"]
				style task_4d8d8def stroke:#a905c7,fill:#ffffff
				role_2720d5bc --> |"1"| task_4d8d8def
				linkStyle 37 stroke:#a905c7,color:#a905c7
				task_58aea4f6[" display_some_facts : ansible_date_time"]
				style task_58aea4f6 stroke:#a905c7,fill:#ffffff
				role_2720d5bc --> |"2"| task_58aea4f6
				linkStyle 38 stroke:#a905c7,color:#a905c7
				task_800f91e9[" display_some_facts : Specific included task for Debian"]
				style task_800f91e9 stroke:#a905c7,fill:#ffffff
				role_2720d5bc --> |"3"| task_800f91e9
				linkStyle 39 stroke:#a905c7,color:#a905c7
			%% End of the role 'display_some_facts'
		%% End of the play 'Play: webserver (0)'
	%% End of the playbook 'tests/fixtures/multi-plays.yml'
```

Note on block: Since `block`s are logical group of tasks, the conditional `when` is not displayed on the edges pointing
to them but on the tasks inside the block. This
mimics [Ansible behavior](https://docs.ansible.com/ansible/latest/user_guide/playbooks_blocks.html#grouping-tasks-with-blocks)
regarding the blocks.

### CLI options

The available options:

```
usage: ansible-playbook-grapher [-h] [-v] [-i INVENTORY]
                                [--include-role-tasks] [-s] [--view]
                                [-o OUTPUT_FILENAME]
                                [--open-protocol-handler {default,vscode,custom}]
                                [--open-protocol-custom-formats OPEN_PROTOCOL_CUSTOM_FORMATS]
                                [--group-roles-by-name]
                                [--renderer {graphviz,mermaid-flowchart,json}]
                                [--renderer-mermaid-directive RENDERER_MERMAID_DIRECTIVE]
                                [--renderer-mermaid-orientation {TD,RL,BT,RL,LR}]
                                [--version] [--hide-plays-without-roles]
                                [--hide-empty-plays] [-t TAGS]
                                [--skip-tags SKIP_TAGS] [--vault-id VAULT_IDS]
                                [-J | --vault-password-file VAULT_PASSWORD_FILES]
                                [-e EXTRA_VARS]
                                playbooks [playbooks ...]

Make graphs from your Ansible Playbooks.

positional arguments:
  playbooks             Playbook(s) to graph

options:
  --group-roles-by-name
                        When rendering the graph, only a single role will be
                        display for all roles having the same names. Default:
                        False
  --hide-empty-plays    Hide the plays that end up with no tasks in the graph
                        (after applying the tags filter).
  --hide-plays-without-roles
                        Hide the plays that end up with no roles in the graph
                        (after applying the tags filter). Only roles at the
                        play level and include_role as tasks are considered
                        (no import_role).
  --include-role-tasks  Include the tasks of the roles in the graph. Applied
                        when parsing the playbooks.
  --open-protocol-custom-formats OPEN_PROTOCOL_CUSTOM_FORMATS
                        The custom formats to use as URLs for the nodes in the
                        graph. Required if --open-protocol-handler is set to
                        custom. You should provide a JSON formatted string
                        like: {"file": "", "folder": ""}. Example: If you want
                        to open folders (roles) inside the browser and files
                        (tasks) in vscode, set it to: '{"file":
                        "vscode://file/{path}:{line}:{column}", "folder":
                        "{path}"}'. path: the absolute path to the file
                        containing the the plays/tasks/roles. line/column: the
                        position of the plays/tasks/roles in the file. You can
                        optionally add the attribute "remove_from_path" to
                        remove some parts of the path if you want relative
                        paths.
  --open-protocol-handler {default,vscode,custom}
                        The protocol to use to open the nodes when double-
                        clicking on them in your SVG viewer. Your SVG viewer
                        must support double-click and Javascript. The
                        supported values are 'default', 'vscode' and 'custom'.
                        For 'default', the URL will be the path to the file or
                        folders. When using a browser, it will open or
                        download them. For 'vscode', the folders and files
                        will be open with VSCode. For 'custom', you need to
                        set a custom format with --open-protocol-custom-
                        formats.
  --renderer {graphviz,mermaid-flowchart,json}
                        The renderer to use to generate the graph. Default:
                        graphviz
  --renderer-mermaid-directive RENDERER_MERMAID_DIRECTIVE
                        The directive for the mermaid renderer. Can be used to
                        customize the output: fonts, theme, curve etc. More
                        info at https://mermaid.js.org/config/directives.html.
                        Default: '%%{ init: { "flowchart": { "curve": "bumpX"
                        } } }%%'
  --renderer-mermaid-orientation {TD,RL,BT,RL,LR}
                        The orientation of the flow chart. Default: 'LR'
  --skip-tags SKIP_TAGS
                        only run plays and tasks whose tags do not match these
                        values. This argument may be specified multiple times.
  --vault-id VAULT_IDS  the vault identity to use. This argument may be
                        specified multiple times.
  --vault-password-file VAULT_PASSWORD_FILES, --vault-pass-file VAULT_PASSWORD_FILES
                        vault password file
  --version
  --view                Automatically open the resulting SVG file with your
                        system’s default viewer application for the file type
  -J, --ask-vault-password, --ask-vault-pass
                        ask for vault password
  -e EXTRA_VARS, --extra-vars EXTRA_VARS
                        set additional variables as key=value or YAML/JSON, if
                        filename prepend with @. This argument may be
                        specified multiple times.
  -h, --help            show this help message and exit
  -i INVENTORY, --inventory INVENTORY
                        specify inventory host path or comma separated host
                        list. This argument may be specified multiple times.
  -o OUTPUT_FILENAME, --output-file-name OUTPUT_FILENAME
                        Output filename without the '.svg' extension (for
                        graphviz), '.mmd' for Mermaid or `.json`. The
                        extension will be added automatically.
  -s, --save-dot-file   Save the graphviz dot file used to generate the graph.
  -t TAGS, --tags TAGS  only run plays and tasks tagged with these values.
                        This argument may be specified multiple times.
  -v, --verbose         Causes Ansible to print more debug messages. Adding
                        multiple -v will increase the verbosity, the builtin
                        plugins currently evaluate up to -vvvvvv. A reasonable
                        level to start is -vvv, connection debugging might
                        require -vvvv. This argument may be specified multiple
                        times.

```

## Configuration: ansible.cfg

The content of `ansible.cfg` is loaded automatically when running the grapher according to Ansible's behavior. The
corresponding environment variables are also loaded.

The values in the config file (and their corresponding environment variables) may affect the behavior of the grapher.
For example `TAGS_RUN` and `TAGS_SKIP` or vault configuration.

More information [here](https://docs.ansible.com/ansible/latest/reference_appendices/config.html).

## Limitations

- Since Ansible Playbook Grapher is a static analyzer that parses your playbook, it's limited to what can be determined
  statically: no task is run against your inventory. The parser tries to interpolate the variables, but some of them are
  only available when running your playbook (
  ansible_os_family, ansible_system, etc.). The tasks inside any `import_*` or `include_*` with some variables in their
  arguments may not appear in the graph.
- The rendered SVG graph may sometime display tasks in a wrong order. I cannot control this behavior of Graphviz yet.
  Always check the edge label to know the tasks order.
- The label of the edges may overlap with each other. They are positioned so that they are as close as possible to
  the target nodes. If the same role is used in multiple plays or playbooks, the labels can overlap.

## Contribution

Contributions are welcome. Feel free to contribute by creating an issue or submitting a PR :smiley:

### Dev environment

To setup a new development environment :

- Install graphviz (see above)
- (cd tests && pip install -r requirements_tests.txt)

Run the tests and open the generated files in your system’s default viewer application:

```shell script
export TEST_VIEW_GENERATED_FILE=1
make test # run all tests
```

The graphs are generated in the folder `tests/generated-svgs`. They are also generated as artefacts
in [Github Actions](https://github.com/haidaraM/ansible-playbook-grapher/actions). Feel free to look at them when
submitting PRs.

### Lint and format

The project uses black to format the code. Run `black .` to format.

## License

GNU General Public License v3.0 or later (Same as Ansible)

See [LICENSE](./LICENSE) for the full text
