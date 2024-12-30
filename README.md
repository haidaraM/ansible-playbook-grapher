# Ansible Playbook Grapher

[![Testing](https://github.com/haidaraM/ansible-playbook-grapher/actions/workflows/testing.yaml/badge.svg)](https://github.com/haidaraM/ansible-playbook-grapher/actions/workflows/testing.yaml)
[![PyPI version](https://badge.fury.io/py/ansible-playbook-grapher.svg)](https://badge.fury.io/py/ansible-playbook-grapher)
[![Coverage Status](https://coveralls.io/repos/github/haidaraM/ansible-playbook-grapher/badge.svg?branch=main)](https://coveralls.io/github/haidaraM/ansible-playbook-grapher?branch=main)
[![PyPI Downloads](https://static.pepy.tech/badge/ansible-playbook-grapher)](https://pepy.tech/projects/ansible-playbook-grapher)

[ansible-playbook-grapher](https://github.com/haidaraM/ansible-playbook-grapher) is a command line tool to create a
graph representing your Ansible playbooks, plays, tasks and roles. The aim of this project is to have an overview of
your playbooks that you can use as documentation.

Inspired by [Ansible Inventory Grapher](https://github.com/willthames/ansible-inventory-grapher).

## Features

- Multiple [rendering formats](#renderers): graphviz, mermaid and JSON.
- Automatically find all your installed roles and collection.
- Native support for Ansible filters based on tags.
- Variables interpolation (when possible).
- Support for `import_*` and `include_*`.
- Multiple flags to hide empty plays, group roles by name, etc...
- Support for playbooks in collections.

The following features are available when opening the SVGs in a browser (recommended) or a viewer that supports
JavaScript:

- Highlighting of all the related nodes of a given node when clicking or hovering. Example: Click on a role to select
  all its tasks when `--include-role-tasks` is set.
- A double click on a node opens the corresponding file or folder depending on whether it's a playbook, a play, a task
  or a role. By default, the browser will open folders and download files since it may not be able to render the YAML
  file.  
  Optionally, you can
  set [the open protocol to use VSCode](https://code.visualstudio.com/docs/editor/command-line#_opening-vs-code-with-urls)
  with `--open-protocol-handler vscode`: it will open the folders when double-clicking on roles (not `include_role`) and
  the files for the other nodes. The cursor will be at the task exact position in the file.  
  Lastly, you can provide your own protocol formats
  with `--open-protocol-handler custom --open-protocol-custom-formats '{}'`. See the help
  and [an example.](https://github.com/haidaraM/ansible-playbook-grapher/blob/34e0aef74b82808dceb6ccfbeb333c0b531eac12/ansibleplaybookgrapher/renderer/__init__.py#L32-L41)
  To not confuse
  with [Ansible Handlers.](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_handlers.html)
- Export the dot file used to generate the graph with Graphviz.

## Prerequisites

- Python 3.10 at least. It might work with previous versions, but the code is NOT tested against them.
  See
  the [support matrix](https://docs.ansible.com/ansible/latest/reference_appendices/release_and_maintenance.html#ansible-core-support-matrix)
  and the matrix in the [testing workflow](.github/workflows/testing.yaml).
- A virtual environment from which to run the grapher. This is **highly recommended** because the grapher depends on
  some versions of ansible-core which are not necessarily installed in your environment and may cause issues if you use
  some older versions of Ansible (
  since `ansible` [package has been split](https://www.ansible.com/blog/ansible-3.0.0-qa)).
- **Graphviz**: The tool used to generate the graph in SVG. Optional if you don't plan to use the `graphviz` renderer.
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

1. `graphviz` (default): Generate the graph in SVG. Has more features than the other renderers.
2. `mermaid-flowchart`: Generate the graph in [Mermaid](https://mermaid.js.org/syntax/flowchart.html) format. You can
   directly embed the graph in your Markdown and GitHub (
   and [other integrations](https://mermaid.js.org/ecosystem/integrations.html)) will render it.
3. `json`: Generate a JSON representation of the graph. The corresponding JSON schema
   is [here.](https://github.com/haidaraM/ansible-playbook-grapher/tree/main/tests/fixtures/json-schemas) The JSON
   output will give you more flexibility to create your own renderer outside the grapher.

Comparison of the renderers:

|                                                          | `graphviz` (.svg) | `mermaid-flowchart` (.mmd) |                      `json` (.json)                      |
|----------------------------------------------------------|:-----------------:|:--------------------------:|:--------------------------------------------------------:|
| Click on nodes to open the files (open protocol handler) |         ✅         |             ❌              |          ✅: the file location is in the output           |
| Highlight on hover                                       |         ✅         |             ❌              |                          ❌: NA                           |
| Change graph orientation                                 |         ❌         |             ✅              |                          ❌: NA                           |
| Group roles by name                                      |         ✅         |             ✅              | ✅: the roles with the same names will have the same IDs. |
| Hide empty roles and blocks                              |         ✅         |             ✅              |        ❌: The empty roles are kept in the output         |
| View the output file in your the OS default viewer       |         ✅         | ✅ on https://mermaid.live/ |                            ✅                             |
| Tests of the output                                      |     Automatic     |   Manual (need a parser)   |                        Automatic                         |

If you are interested to support more renderers, feel free to create an issue or raise a PR based on the existing
renderers.

## Usage

```shell
ansible-playbook-grapher tests/fixtures/example.yml
```

![Example](https://raw.githubusercontent.com/haidaraM/ansible-playbook-grapher/main/img/example.png)

```shell
ansible-playbook-grapher --include-role-tasks  tests/fixtures/with_roles.yml
```

![Example](https://raw.githubusercontent.com/haidaraM/ansible-playbook-grapher/main/img/with_roles.png)

```shell
ansible-playbook-grapher tests/fixtures/with_block.yml
```

![Example](https://raw.githubusercontent.com/haidaraM/ansible-playbook-grapher/main/img/block.png)

```shell
ansible-playbook-grapher --include-role-tasks --renderer mermaid-flowchart tests/fixtures/multi-plays.yml
```

```mermaid
---
title: Ansible Playbook Grapher
---
%%{ init: { "flowchart": { "curve": "bumpX" } } }%%
flowchart LR
	%% Start of the playbook 'tests/fixtures/multi-plays.yml'
	playbook_a27d9bec("tests/fixtures/multi-plays.yml")
		%% Start of the play 'Play: all (0)'
		play_d6dd122d["Play: all (0)"]
		style play_d6dd122d stroke:#ba1a12,fill:#ba1a12,color:#ffffff
		playbook_a27d9bec --> |"1"| play_d6dd122d
		linkStyle 0 stroke:#ba1a12,color:#ba1a12
			pre_task_676cdcb1["[pre_task] Pretask"]
			style pre_task_676cdcb1 stroke:#ba1a12,fill:#ffffff
			play_d6dd122d --> |"1"| pre_task_676cdcb1
			linkStyle 1 stroke:#ba1a12,color:#ba1a12
			pre_task_44476583["[pre_task] Pretask 2"]
			style pre_task_44476583 stroke:#ba1a12,fill:#ffffff
			play_d6dd122d --> |"2"| pre_task_44476583
			linkStyle 2 stroke:#ba1a12,color:#ba1a12
			%% Start of the role '[role] fake_role'
			play_d6dd122d --> |"3"| role_f0c07194
			linkStyle 3 stroke:#ba1a12,color:#ba1a12
			role_f0c07194(["[role] fake_role"])
			style role_f0c07194 fill:#ba1a12,color:#ffffff,stroke:#ba1a12
				task_90876ffc["[task] fake_role : Debug 1"]
				style task_90876ffc stroke:#ba1a12,fill:#ffffff
				role_f0c07194 --> |"1 [when: ansible_distribution == 'Debian']"| task_90876ffc
				linkStyle 4 stroke:#ba1a12,color:#ba1a12
				task_bb701882["[task] fake_role : Debug 2"]
				style task_bb701882 stroke:#ba1a12,fill:#ffffff
				role_f0c07194 --> |"2 [when: ansible_distribution == 'Debian']"| task_bb701882
				linkStyle 5 stroke:#ba1a12,color:#ba1a12
				task_c00c5d61["[task] fake_role : Debug 3 with double quote &#34;here&#34; in the name"]
				style task_c00c5d61 stroke:#ba1a12,fill:#ffffff
				role_f0c07194 --> |"3 [when: ansible_distribution == 'Debian']"| task_c00c5d61
				linkStyle 6 stroke:#ba1a12,color:#ba1a12
			%% End of the role '[role] fake_role'
			%% Start of the role '[role] display_some_facts'
			play_d6dd122d --> |"4"| role_a168caef
			linkStyle 7 stroke:#ba1a12,color:#ba1a12
			role_a168caef(["[role] display_some_facts"])
			style role_a168caef fill:#ba1a12,color:#ffffff,stroke:#ba1a12
				task_737e2be9["[task] display_some_facts : ansible_architecture"]
				style task_737e2be9 stroke:#ba1a12,fill:#ffffff
				role_a168caef --> |"1"| task_737e2be9
				linkStyle 8 stroke:#ba1a12,color:#ba1a12
				task_61bbb3fb["[task] display_some_facts : ansible_date_time"]
				style task_61bbb3fb stroke:#ba1a12,fill:#ffffff
				role_a168caef --> |"2"| task_61bbb3fb
				linkStyle 9 stroke:#ba1a12,color:#ba1a12
				task_3b7308dc["[task] display_some_facts : Specific included task for Debian"]
				style task_3b7308dc stroke:#ba1a12,fill:#ffffff
				role_a168caef --> |"3"| task_3b7308dc
				linkStyle 10 stroke:#ba1a12,color:#ba1a12
			%% End of the role '[role] display_some_facts'
			task_c8b76065["[task] Add backport {{backport}}"]
			style task_c8b76065 stroke:#ba1a12,fill:#ffffff
			play_d6dd122d --> |"5"| task_c8b76065
			linkStyle 11 stroke:#ba1a12,color:#ba1a12
			task_f7cebcbb["[task] Install packages"]
			style task_f7cebcbb stroke:#ba1a12,fill:#ffffff
			play_d6dd122d --> |"6"| task_f7cebcbb
			linkStyle 12 stroke:#ba1a12,color:#ba1a12
			post_task_caafa665["[post_task] Posttask"]
			style post_task_caafa665 stroke:#ba1a12,fill:#ffffff
			play_d6dd122d --> |"7"| post_task_caafa665
			linkStyle 13 stroke:#ba1a12,color:#ba1a12
			post_task_b5ade468["[post_task] Posttask 2"]
			style post_task_b5ade468 stroke:#ba1a12,fill:#ffffff
			play_d6dd122d --> |"8"| post_task_b5ade468
			linkStyle 14 stroke:#ba1a12,color:#ba1a12
		%% End of the play 'Play: all (0)'
		%% Start of the play 'Play: database (0)'
		play_d780677e["Play: database (0)"]
		style play_d780677e stroke:#686864,fill:#686864,color:#ffffff
		playbook_a27d9bec --> |"2"| play_d780677e
		linkStyle 15 stroke:#686864,color:#686864
			%% Start of the role '[role] fake_role'
			play_d780677e --> |"1"| role_1e6bf323
			linkStyle 16 stroke:#686864,color:#686864
			role_1e6bf323(["[role] fake_role"])
			style role_1e6bf323 fill:#686864,color:#ffffff,stroke:#686864
				task_3cb17d25["[task] fake_role : Debug 1"]
				style task_3cb17d25 stroke:#686864,fill:#ffffff
				role_1e6bf323 --> |"1 [when: ansible_distribution == 'Debian']"| task_3cb17d25
				linkStyle 17 stroke:#686864,color:#686864
				task_1f6232f4["[task] fake_role : Debug 2"]
				style task_1f6232f4 stroke:#686864,fill:#ffffff
				role_1e6bf323 --> |"2 [when: ansible_distribution == 'Debian']"| task_1f6232f4
				linkStyle 18 stroke:#686864,color:#686864
				task_0361ffa3["[task] fake_role : Debug 3 with double quote &#34;here&#34; in the name"]
				style task_0361ffa3 stroke:#686864,fill:#ffffff
				role_1e6bf323 --> |"3 [when: ansible_distribution == 'Debian']"| task_0361ffa3
				linkStyle 19 stroke:#686864,color:#686864
			%% End of the role '[role] fake_role'
			%% Start of the role '[role] display_some_facts'
			play_d780677e --> |"2"| role_a8b4b712
			linkStyle 20 stroke:#686864,color:#686864
			role_a8b4b712(["[role] display_some_facts"])
			style role_a8b4b712 fill:#686864,color:#ffffff,stroke:#686864
				task_c1d17653["[task] display_some_facts : ansible_architecture"]
				style task_c1d17653 stroke:#686864,fill:#ffffff
				role_a8b4b712 --> |"1"| task_c1d17653
				linkStyle 21 stroke:#686864,color:#686864
				task_8353a2ef["[task] display_some_facts : ansible_date_time"]
				style task_8353a2ef stroke:#686864,fill:#ffffff
				role_a8b4b712 --> |"2"| task_8353a2ef
				linkStyle 22 stroke:#686864,color:#686864
				task_d8141ffa["[task] display_some_facts : Specific included task for Debian"]
				style task_d8141ffa stroke:#686864,fill:#ffffff
				role_a8b4b712 --> |"3"| task_d8141ffa
				linkStyle 23 stroke:#686864,color:#686864
			%% End of the role '[role] display_some_facts'
		%% End of the play 'Play: database (0)'
		%% Start of the play 'Play: webserver (0)'
		play_4d3ee472["Play: webserver (0)"]
		style play_4d3ee472 stroke:#43418b,fill:#43418b,color:#ffffff
		playbook_a27d9bec --> |"3"| play_4d3ee472
		linkStyle 24 stroke:#43418b,color:#43418b
			%% Start of the role '[role] nested_include_role'
			play_4d3ee472 --> |"1"| role_f611e648
			linkStyle 25 stroke:#43418b,color:#43418b
			role_f611e648(["[role] nested_include_role"])
			style role_f611e648 fill:#43418b,color:#ffffff,stroke:#43418b
				task_8d2e4414["[task] nested_include_role : Ensure postgresql is at the latest version"]
				style task_8d2e4414 stroke:#43418b,fill:#ffffff
				role_f611e648 --> |"1"| task_8d2e4414
				linkStyle 26 stroke:#43418b,color:#43418b
				task_d1bc52f0["[task] nested_include_role : Ensure that postgresql is started"]
				style task_d1bc52f0 stroke:#43418b,fill:#ffffff
				role_f611e648 --> |"2"| task_d1bc52f0
				linkStyle 27 stroke:#43418b,color:#43418b
				%% Start of the role '[role] display_some_facts'
				role_f611e648 --> |"3 [when: x is not defined]"| role_39ad2981
				linkStyle 28 stroke:#43418b,color:#43418b
				role_39ad2981(["[role] display_some_facts"])
				style role_39ad2981 fill:#43418b,color:#ffffff,stroke:#43418b
					task_110062e7["[task] display_some_facts : ansible_architecture"]
					style task_110062e7 stroke:#43418b,fill:#ffffff
					role_39ad2981 --> |"1"| task_110062e7
					linkStyle 29 stroke:#43418b,color:#43418b
					task_05309d40["[task] display_some_facts : ansible_date_time"]
					style task_05309d40 stroke:#43418b,fill:#ffffff
					role_39ad2981 --> |"2"| task_05309d40
					linkStyle 30 stroke:#43418b,color:#43418b
					task_d8106118["[task] display_some_facts : Specific included task for Debian"]
					style task_d8106118 stroke:#43418b,fill:#ffffff
					role_39ad2981 --> |"3"| task_d8106118
					linkStyle 31 stroke:#43418b,color:#43418b
				%% End of the role '[role] display_some_facts'
				%% Start of the role '[role] fake_role'
				role_f611e648 --> |"4"| role_60085133
				linkStyle 32 stroke:#43418b,color:#43418b
				role_60085133(["[role] fake_role"])
				style role_60085133 fill:#43418b,color:#ffffff,stroke:#43418b
					task_aa202401["[task] fake_role : Debug 1"]
					style task_aa202401 stroke:#43418b,fill:#ffffff
					role_60085133 --> |"1"| task_aa202401
					linkStyle 33 stroke:#43418b,color:#43418b
					task_bb8335d6["[task] fake_role : Debug 2"]
					style task_bb8335d6 stroke:#43418b,fill:#ffffff
					role_60085133 --> |"2"| task_bb8335d6
					linkStyle 34 stroke:#43418b,color:#43418b
					task_7e0c8ed3["[task] fake_role : Debug 3 with double quote &#34;here&#34; in the name"]
					style task_7e0c8ed3 stroke:#43418b,fill:#ffffff
					role_60085133 --> |"3"| task_7e0c8ed3
					linkStyle 35 stroke:#43418b,color:#43418b
				%% End of the role '[role] fake_role'
			%% End of the role '[role] nested_include_role'
			%% Start of the role '[role] display_some_facts'
			play_4d3ee472 --> |"2"| role_ff23a4e9
			linkStyle 36 stroke:#43418b,color:#43418b
			role_ff23a4e9(["[role] display_some_facts"])
			style role_ff23a4e9 fill:#43418b,color:#ffffff,stroke:#43418b
				task_8fc8f4bc["[task] display_some_facts : ansible_architecture"]
				style task_8fc8f4bc stroke:#43418b,fill:#ffffff
				role_ff23a4e9 --> |"1"| task_8fc8f4bc
				linkStyle 37 stroke:#43418b,color:#43418b
				task_6a9bc407["[task] display_some_facts : ansible_date_time"]
				style task_6a9bc407 stroke:#43418b,fill:#ffffff
				role_ff23a4e9 --> |"2"| task_6a9bc407
				linkStyle 38 stroke:#43418b,color:#43418b
				task_b6121d94["[task] display_some_facts : Specific included task for Debian"]
				style task_b6121d94 stroke:#43418b,fill:#ffffff
				role_ff23a4e9 --> |"3"| task_b6121d94
				linkStyle 39 stroke:#43418b,color:#43418b
			%% End of the role '[role] display_some_facts'
		%% End of the play 'Play: webserver (0)'
	%% End of the playbook 'tests/fixtures/multi-plays.yml'
```

```shell
ansible-playbook-grapher --renderer json tests/fixtures/simple_playbook.yml
```

<details> 

<summary>Json output</summary>

```json
{
  "version": 1,
  "playbooks": [
    {
      "type": "PlaybookNode",
      "id": "playbook_75f89ea1",
      "name": "tests/fixtures/simple_playbook.yml",
      "when": "",
      "index": 1,
      "location": {
        "type": "file",
        "path": "tests/fixtures/simple_playbook.yml",
        "line": 1,
        "column": 1
      },
      "plays": [
        {
          "type": "PlayNode",
          "id": "play_b348eb24",
          "name": "all",
          "when": "",
          "index": 1,
          "location": {
            "type": "file",
            "path": "/Users/mohamedelmouctarhaidara/projects/ansible-playbook-grapher/tests/fixtures/simple_playbook.yml",
            "line": 2,
            "column": 3
          },
          "post_tasks": [
            {
              "type": "TaskNode",
              "id": "post_task_d67cb13a",
              "name": "Post task 1",
              "when": "",
              "index": 1,
              "location": {
                "type": "file",
                "path": "/Users/mohamedelmouctarhaidara/projects/ansible-playbook-grapher/tests/fixtures/simple_playbook.yml",
                "line": 4,
                "column": 7
              }
            },
            {
              "type": "TaskNode",
              "id": "post_task_2f8f97a7",
              "name": "Post task 2",
              "when": "",
              "index": 2,
              "location": {
                "type": "file",
                "path": "/Users/mohamedelmouctarhaidara/projects/ansible-playbook-grapher/tests/fixtures/simple_playbook.yml",
                "line": 7,
                "column": 7
              }
            }
          ],
          "pre_tasks": [],
          "roles": [],
          "tasks": [],
          "handlers": [],
          "hosts": [],
          "colors": {
            "main": "#4a826b",
            "font": "#ffffff"
          }
        }
      ]
    }
  ],
  "title": "Ansible Playbook Grapher"
}
```

</details>

Note on block: Since a `block` is a logical group of tasks, the conditional `when` is not displayed on the edges
pointing to them but on the tasks inside the block. This
mimics [Ansible behavior](https://docs.ansible.com/ansible/latest/user_guide/playbooks_blocks.html#grouping-tasks-with-blocks)
regarding the blocks.

### CLI options

The available options:

```
usage: ansible-playbook-grapher [-h] [-v] [--exclude-roles EXCLUDE_ROLES] [--only-roles] [-i INVENTORY] [--include-role-tasks] [-s]
                                [--view] [-o OUTPUT_FILENAME] [--open-protocol-handler {default,vscode,custom}]
                                [--open-protocol-custom-formats OPEN_PROTOCOL_CUSTOM_FORMATS] [--group-roles-by-name]
                                [--renderer {graphviz,mermaid-flowchart,json}]
                                [--renderer-mermaid-directive RENDERER_MERMAID_DIRECTIVE]
                                [--renderer-mermaid-orientation {TD,RL,BT,RL,LR}] [--version] [--hide-plays-without-roles]
                                [--hide-empty-plays] [--title TITLE] [--show-handlers] [-t TAGS] [--skip-tags SKIP_TAGS]
                                [--vault-id VAULT_IDS] [-J | --vault-password-file VAULT_PASSWORD_FILES] [-e EXTRA_VARS]
                                playbooks [playbooks ...]

Make graphs from your Ansible Playbooks.

positional arguments:
  playbooks             Playbook(s) to graph. You can specify multiple playbooks, separated by spaces and reference playbooks in
                        collections.

options:
  --exclude-roles EXCLUDE_ROLES
                        Specify file path or comma separated list of roles, which should be excluded. This argument may be specified
                        multiple times.
  --group-roles-by-name
                        When rendering the graph (graphviz and mermaid), only a single role will be displayed for all roles having the
                        same names. Default: False
  --hide-empty-plays    Hide the plays that end up with no tasks in the graph (after applying the tags filter).
  --hide-plays-without-roles
                        Hide the plays that end up with no roles in the graph (after applying the tags filter). Only roles at the play level and include_role as
                        tasks are considered (no import_role).
  --include-role-tasks  Include the tasks of the roles in the graph. Default: False. This only applies to roles at the play level and include_role tasks. The
                        tasks from an 'import_role' are always added to the graph.
  --only-roles          Only render the roles in the graph (ignoring the tasks)
  --open-protocol-custom-formats OPEN_PROTOCOL_CUSTOM_FORMATS
                        The custom formats to use as URLs for the nodes in the graph. Required if --open-protocol-handler is set to
                        custom. You should provide a JSON formatted string like: {"file": "", "folder": ""}. Example: If you want to
                        open folders (roles) inside the browser and files (tasks) in vscode, set it to: '{"file":
                        "vscode://file/{path}:{line}:{column}", "folder": "{path}"}'. path: the absolute path to the file containing
                        the the plays/tasks/roles. line/column: the position of the plays/tasks/roles in the file. You can optionally
                        add the attribute "remove_from_path" to remove some parts of the path if you want relative paths.
  --open-protocol-handler {default,vscode,custom}
                        The protocol to use to open the nodes when double-clicking on them in your SVG viewer (only for graphviz). Your
                        SVG viewer must support double-click and Javascript. The supported values are 'default', 'vscode' and 'custom'.
                        For 'default', the URL will be the path to the file or folders. When using a browser, it will open or download
                        them. For 'vscode', the folders and files will be open with VSCode. For 'custom', you need to set a custom
                        format with --open-protocol-custom-formats.
  --renderer {graphviz,mermaid-flowchart,json}
                        The renderer to use to generate the graph. Default: graphviz
  --renderer-mermaid-directive RENDERER_MERMAID_DIRECTIVE
                        The directive for the mermaid renderer. Can be used to customize the output: fonts, theme, curve etc. More info
                        at https://mermaid.js.org/config/directives.html. Default: '%%{ init: { "flowchart": { "curve": "bumpX" } }
                        }%%'
  --renderer-mermaid-orientation {TD,RL,BT,RL,LR}
                        The orientation of the flow chart. Default: 'LR'
  --show-handlers       Show the handlers in the graph. See the limitations in the project README on GitHub.
  --skip-tags SKIP_TAGS
                        only run plays and tasks whose tags do not match these values. This argument may be specified multiple times.
  --title TITLE         The title to display in the graph. Default: 'Ansible Playbook Grapher'. Set it to an empty string to remove the
                        title.
  --vault-id VAULT_IDS  the vault identity to use. This argument may be specified multiple times.
  --vault-password-file, --vault-pass-file VAULT_PASSWORD_FILES
                        vault password file
  --version             show program's version number and exit
  --view                Automatically open the resulting SVG file with your system's default viewer application for the file type
  -J, --ask-vault-password, --ask-vault-pass
                        ask for vault password
  -e, --extra-vars EXTRA_VARS
                        set additional variables as key=value or YAML/JSON, if filename prepend with @. This argument may be specified
                        multiple times.
  -h, --help            show this help message and exit
  -i, --inventory INVENTORY
                        Specify inventory host path or comma separated host list. This argument may be specified multiple times.
  -o, --output-file-name OUTPUT_FILENAME
                        Output filename without the '.svg' extension (for graphviz), '.mmd' for Mermaid or `.json`. The extension will
                        be added automatically.
  -s, --save-dot-file   Save the graphviz dot file used to generate the graph.
  -t, --tags TAGS       only run plays and tasks tagged with these values. This argument may be specified multiple times.
  -v, --verbose         Causes Ansible to print more debug messages. Adding multiple -v will increase the verbosity, the builtin plugins currently evaluate up to
                        -vvvvvv. A reasonable level to start is -vvv, connection debugging might require -vvvv. This argument may be specified multiple times.
```

## Configuration: ansible.cfg

The content of `ansible.cfg` is loaded automatically when running the grapher according to Ansible's behavior. The
corresponding environment variables are also loaded.

The values in the config file (and their corresponding environment variables) may affect the behavior of the grapher.
For example `TAGS_RUN` and `TAGS_SKIP` or vault configuration.

More information [here](https://docs.ansible.com/ansible/latest/reference_appendices/config.html).

## Limitations and notes

- Since Ansible Playbook Grapher is a static analyzer that parses your playbook, it's limited to what can be determined
  statically: no task is run against your inventory. The parser tries to interpolate the variables, but some of them are
  only available when running your playbook ( `ansible_os_family`, `ansible_system`, etc.). The tasks inside any
  `import_*` or `include_*` with some variables in their arguments may not appear in the graph.
- The rendered SVG graph may sometime display tasks in a wrong order. I cannot control this behavior of Graphviz yet.
  Always check the edge label to know the task order.
- The label of the edges may overlap with each other. They are positioned so that they are as close as possible to
  the target nodes. If the same role is used in multiple plays or playbooks, the labels can overlap.
- **Ansible Handlers**: The handlers are partially supported for the moment. Their position in the graph doesn't
  entirely
  reflect their real order of execution in the playbook. They are displayed at the end of the play and roles, but they
  might be executed before that.
- Looping on tasks and roles is not supported. The tasks using loop are displayed as a single task.

## Contribution

Contributions are welcome. Feel free to contribute by creating an issue or submitting a PR :smiley:

### Local development

To set up a new local development environment:

- Install graphviz (see above)
- pip install -r requirements.txt -r tests/requirements_tests.txt
- (cd tests/fixtures && ansible-galaxy install -r requirements.yml)

> The project contains some collections in [collections](tests/fixtures/collections). If you modify them, you need to do
> a force install with `ansible-galaxy install -r requirements.yml --force`

Run the tests and open the generated files in your system’s default viewer application:

```shell script
export TEST_VIEW_GENERATED_FILE=1
make test # run all tests
```

The graphs are generated in the folders `tests/generated-svgs`, `tests/generated-mermaids` and `tests/generated-jsons`.
They are also generated as artifacts in [GitHub Actions](https://github.com/haidaraM/ansible-playbook-grapher/actions).
Feel free to look at them when submitting PRs.

### Lint and format

The project uses ruff to format and lint the code. Run `make lint` to format and lint.

## License

GNU General Public License v3.0 or later (Same as Ansible)

See [LICENSE](./LICENSE) for the full text
