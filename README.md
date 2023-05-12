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
  and [an example.](https://github.com/haidaraM/ansible-playbook-grapher/blob/12cee0fbd59ffbb706731460e301f0b886515357/ansibleplaybookgrapher/graphbuilder.py#L33-L42).
- Filer tasks based on tags
- Export the dot file used to generate the graph with Graphviz.

## Prerequisites

- Python 3.8 at least
- A virtual environment from which to run the grapher. This is **highly recommended** because the grapher depends on
  some versions of ansible-core which are not necessarily installed in your environment and may cause issues if you use
  some older versions of Ansible (
  since `ansible` [package has been split](https://www.ansible.com/blog/ansible-3.0.0-qa)).
- **Graphviz**: The tool used to generate the graph in SVG.
  ```shell script
  $ sudo apt-get install graphviz # or yum install or brew install
  ```

I try to respect [Red Hat Ansible Engine Life Cycle](https://access.redhat.com/support/policy/updates/ansible-engine)
for the supported Ansible version.

## Installation

```shell script
pip install ansible-playbook-grapher
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
ansible-playbook-grapher --include-role-tasks --renderer mermaid-flowchart tests/fixtures/multi-plays.yml tests/fixtures/with_block.yml
```

```mermaid
---
title: Ansible Playbook Grapher
---
%%{ init: { 'flowchart': { 'curve': 'bumpX' } } }%%
flowchart LR
	%% Start of the playbook 'tests/fixtures/multi-plays.yml'
	playbook_bd8798bc("tests/fixtures/multi-plays.yml")
		%% Start of the play 'Play: all (0)'
		play_fb11c1f8["Play: all (0)"]
		style play_fb11c1f8 fill:#4d8b41,color:#ffffff
		playbook_bd8798bc --> |"1"| play_fb11c1f8
		linkStyle 0 stroke:#4d8b41,color:#4d8b41
			pre_task_0aea2a6b["[pre_task] Pretask"]
			style pre_task_0aea2a6b stroke:#4d8b41,fill:#ffffff
			play_fb11c1f8 --> |"1"| pre_task_0aea2a6b
			linkStyle 1 stroke:#4d8b41,color:#4d8b41
			pre_task_e48d82b5["[pre_task] Pretask 2"]
			style pre_task_e48d82b5 stroke:#4d8b41,fill:#ffffff
			play_fb11c1f8 --> |"2"| pre_task_e48d82b5
			linkStyle 2 stroke:#4d8b41,color:#4d8b41
			%% Start of the role 'fake_role'
			role_d95e9d5f("[role] fake_role")
			style role_d95e9d5f fill:#4d8b41,color:#ffffff,stroke:#4d8b41
			play_fb11c1f8 --> |"3"| role_d95e9d5f
			linkStyle 3 stroke:#4d8b41,color:#4d8b41
				task_41f6dd12["fake_role : Debug 1"]
				style task_41f6dd12 stroke:#4d8b41,fill:#ffffff
				role_d95e9d5f --> |"1 [when: ansible_distribution == 'Debian']"| task_41f6dd12
				linkStyle 4 stroke:#4d8b41,color:#4d8b41
				task_9dcf29d3["fake_role : Debug 2"]
				style task_9dcf29d3 stroke:#4d8b41,fill:#ffffff
				role_d95e9d5f --> |"2 [when: ansible_distribution == 'Debian']"| task_9dcf29d3
				linkStyle 5 stroke:#4d8b41,color:#4d8b41
				task_dc3f4611["fake_role : Debug 3 with double quote &#34;here&#34; in the name"]
				style task_dc3f4611 stroke:#4d8b41,fill:#ffffff
				role_d95e9d5f --> |"3 [when: ansible_distribution == 'Debian']"| task_dc3f4611
				linkStyle 6 stroke:#4d8b41,color:#4d8b41
			%% End of the role 'fake_role'
			%% Start of the role 'display_some_facts'
			role_2b74c9f5("[role] display_some_facts")
			style role_2b74c9f5 fill:#4d8b41,color:#ffffff,stroke:#4d8b41
			play_fb11c1f8 --> |"4"| role_2b74c9f5
			linkStyle 7 stroke:#4d8b41,color:#4d8b41
				task_1c0691fb["display_some_facts : ansible_architecture"]
				style task_1c0691fb stroke:#4d8b41,fill:#ffffff
				role_2b74c9f5 --> |"1"| task_1c0691fb
				linkStyle 8 stroke:#4d8b41,color:#4d8b41
				task_c7d6574e["display_some_facts : ansible_date_time"]
				style task_c7d6574e stroke:#4d8b41,fill:#ffffff
				role_2b74c9f5 --> |"2"| task_c7d6574e
				linkStyle 9 stroke:#4d8b41,color:#4d8b41
				task_e26456cf["display_some_facts : Specific included task for Debian"]
				style task_e26456cf stroke:#4d8b41,fill:#ffffff
				role_2b74c9f5 --> |"3"| task_e26456cf
				linkStyle 10 stroke:#4d8b41,color:#4d8b41
			%% End of the role 'display_some_facts'
			task_f0ec5674["[task] Add backport {{backport}}"]
			style task_f0ec5674 stroke:#4d8b41,fill:#ffffff
			play_fb11c1f8 --> |"5"| task_f0ec5674
			linkStyle 11 stroke:#4d8b41,color:#4d8b41
			task_614fa7f3["[task] Install packages"]
			style task_614fa7f3 stroke:#4d8b41,fill:#ffffff
			play_fb11c1f8 --> |"6"| task_614fa7f3
			linkStyle 12 stroke:#4d8b41,color:#4d8b41
			post_task_bfd4a733["[post_task] Posttask"]
			style post_task_bfd4a733 stroke:#4d8b41,fill:#ffffff
			play_fb11c1f8 --> |"7"| post_task_bfd4a733
			linkStyle 13 stroke:#4d8b41,color:#4d8b41
			post_task_6728f20f["[post_task] Posttask 2"]
			style post_task_6728f20f stroke:#4d8b41,fill:#ffffff
			play_fb11c1f8 --> |"8"| post_task_6728f20f
			linkStyle 14 stroke:#4d8b41,color:#4d8b41
		%% End of the play 'Play: all (0)'
		%% Start of the play 'Play: database (0)'
		play_200a2cda["Play: database (0)"]
		style play_200a2cda fill:#195db3,color:#ffffff
		playbook_bd8798bc --> |"2"| play_200a2cda
		linkStyle 15 stroke:#195db3,color:#195db3
			%% Start of the role 'fake_role'
			role_584c099b("[role] fake_role")
			style role_584c099b fill:#195db3,color:#ffffff,stroke:#195db3
			play_200a2cda --> |"1"| role_584c099b
			linkStyle 16 stroke:#195db3,color:#195db3
				task_4363c0b7["fake_role : Debug 1"]
				style task_4363c0b7 stroke:#195db3,fill:#ffffff
				role_584c099b --> |"1 [when: ansible_distribution == 'Debian']"| task_4363c0b7
				linkStyle 17 stroke:#195db3,color:#195db3
				task_aff132aa["fake_role : Debug 2"]
				style task_aff132aa stroke:#195db3,fill:#ffffff
				role_584c099b --> |"2 [when: ansible_distribution == 'Debian']"| task_aff132aa
				linkStyle 18 stroke:#195db3,color:#195db3
				task_69120ebe["fake_role : Debug 3 with double quote &#34;here&#34; in the name"]
				style task_69120ebe stroke:#195db3,fill:#ffffff
				role_584c099b --> |"3 [when: ansible_distribution == 'Debian']"| task_69120ebe
				linkStyle 19 stroke:#195db3,color:#195db3
			%% End of the role 'fake_role'
			%% Start of the role 'display_some_facts'
			role_f46ed679("[role] display_some_facts")
			style role_f46ed679 fill:#195db3,color:#ffffff,stroke:#195db3
			play_200a2cda --> |"2"| role_f46ed679
			linkStyle 20 stroke:#195db3,color:#195db3
				task_5f4d00e6["display_some_facts : ansible_architecture"]
				style task_5f4d00e6 stroke:#195db3,fill:#ffffff
				role_f46ed679 --> |"1"| task_5f4d00e6
				linkStyle 21 stroke:#195db3,color:#195db3
				task_fa40d63b["display_some_facts : ansible_date_time"]
				style task_fa40d63b stroke:#195db3,fill:#ffffff
				role_f46ed679 --> |"2"| task_fa40d63b
				linkStyle 22 stroke:#195db3,color:#195db3
				task_3527696f["display_some_facts : Specific included task for Debian"]
				style task_3527696f stroke:#195db3,fill:#ffffff
				role_f46ed679 --> |"3"| task_3527696f
				linkStyle 23 stroke:#195db3,color:#195db3
			%% End of the role 'display_some_facts'
		%% End of the play 'Play: database (0)'
		%% Start of the play 'Play: webserver (0)'
		play_34799e65["Play: webserver (0)"]
		style play_34799e65 fill:#7f4d73,color:#ffffff
		playbook_bd8798bc --> |"3"| play_34799e65
		linkStyle 24 stroke:#7f4d73,color:#7f4d73
			%% Start of the role 'nested_include_role'
			role_1bfe7836("[role] nested_include_role")
			style role_1bfe7836 fill:#7f4d73,color:#ffffff,stroke:#7f4d73
			play_34799e65 --> |"1"| role_1bfe7836
			linkStyle 25 stroke:#7f4d73,color:#7f4d73
				task_40d7c36f["nested_include_role : Ensure postgresql is at the latest version"]
				style task_40d7c36f stroke:#7f4d73,fill:#ffffff
				role_1bfe7836 --> |"1"| task_40d7c36f
				linkStyle 26 stroke:#7f4d73,color:#7f4d73
				task_bc9f916c["nested_include_role : Ensure that postgresql is started"]
				style task_bc9f916c stroke:#7f4d73,fill:#ffffff
				role_1bfe7836 --> |"2"| task_bc9f916c
				linkStyle 27 stroke:#7f4d73,color:#7f4d73
				%% Start of the role 'display_some_facts'
				role_dfff70cd("[role] display_some_facts")
				style role_dfff70cd fill:#7f4d73,color:#ffffff,stroke:#7f4d73
				role_1bfe7836 --> |"3 [when: x is not defined]"| role_dfff70cd
				linkStyle 28 stroke:#7f4d73,color:#7f4d73
					task_2700f9a8["display_some_facts : ansible_architecture"]
					style task_2700f9a8 stroke:#7f4d73,fill:#ffffff
					role_dfff70cd --> |"1"| task_2700f9a8
					linkStyle 29 stroke:#7f4d73,color:#7f4d73
					task_84bd5d7e["display_some_facts : ansible_date_time"]
					style task_84bd5d7e stroke:#7f4d73,fill:#ffffff
					role_dfff70cd --> |"2"| task_84bd5d7e
					linkStyle 30 stroke:#7f4d73,color:#7f4d73
					task_1b02d165["display_some_facts : Specific included task for Debian"]
					style task_1b02d165 stroke:#7f4d73,fill:#ffffff
					role_dfff70cd --> |"3"| task_1b02d165
					linkStyle 31 stroke:#7f4d73,color:#7f4d73
				%% End of the role 'display_some_facts'
				%% Start of the role 'fake_role'
				role_6433854b("[role] fake_role")
				style role_6433854b fill:#7f4d73,color:#ffffff,stroke:#7f4d73
				role_1bfe7836 --> |"4"| role_6433854b
				linkStyle 32 stroke:#7f4d73,color:#7f4d73
					task_10479304["fake_role : Debug 1"]
					style task_10479304 stroke:#7f4d73,fill:#ffffff
					role_6433854b --> |"1"| task_10479304
					linkStyle 33 stroke:#7f4d73,color:#7f4d73
					task_a13ab280["fake_role : Debug 2"]
					style task_a13ab280 stroke:#7f4d73,fill:#ffffff
					role_6433854b --> |"2"| task_a13ab280
					linkStyle 34 stroke:#7f4d73,color:#7f4d73
					task_bffa1ed0["fake_role : Debug 3 with double quote &#34;here&#34; in the name"]
					style task_bffa1ed0 stroke:#7f4d73,fill:#ffffff
					role_6433854b --> |"3"| task_bffa1ed0
					linkStyle 35 stroke:#7f4d73,color:#7f4d73
				%% End of the role 'fake_role'
			%% End of the role 'nested_include_role'
			%% Start of the role 'display_some_facts'
			role_9188508e("[role] display_some_facts")
			style role_9188508e fill:#7f4d73,color:#ffffff,stroke:#7f4d73
			play_34799e65 --> |"2"| role_9188508e
			linkStyle 36 stroke:#7f4d73,color:#7f4d73
				task_b0401984["display_some_facts : ansible_architecture"]
				style task_b0401984 stroke:#7f4d73,fill:#ffffff
				role_9188508e --> |"1"| task_b0401984
				linkStyle 37 stroke:#7f4d73,color:#7f4d73
				task_417dd6b4["display_some_facts : ansible_date_time"]
				style task_417dd6b4 stroke:#7f4d73,fill:#ffffff
				role_9188508e --> |"2"| task_417dd6b4
				linkStyle 38 stroke:#7f4d73,color:#7f4d73
				task_60860d86["display_some_facts : Specific included task for Debian"]
				style task_60860d86 stroke:#7f4d73,fill:#ffffff
				role_9188508e --> |"3"| task_60860d86
				linkStyle 39 stroke:#7f4d73,color:#7f4d73
			%% End of the role 'display_some_facts'
		%% End of the play 'Play: webserver (0)'
	%% End of the playbook 'tests/fixtures/multi-plays.yml'

	%% Start of the playbook 'tests/fixtures/with_block.yml'
	playbook_2e263466("tests/fixtures/with_block.yml")
		%% Start of the play 'Play: all (0)'
		play_74990123["Play: all (0)"]
		style play_74990123 fill:#a4288c,color:#ffffff
		playbook_2e263466 --> |"1"| play_74990123
		linkStyle 40 stroke:#a4288c,color:#a4288c
			%% Start of the role 'fake_role'
			role_5914bd45("[role] fake_role")
			style role_5914bd45 fill:#a4288c,color:#ffffff,stroke:#a4288c
			play_74990123 --> |"1"| role_5914bd45
			linkStyle 41 stroke:#a4288c,color:#a4288c
				pre_task_87f2b15f["fake_role : Debug 1"]
				style pre_task_87f2b15f stroke:#a4288c,fill:#ffffff
				role_5914bd45 --> |"1"| pre_task_87f2b15f
				linkStyle 42 stroke:#a4288c,color:#a4288c
				pre_task_64224a5c["fake_role : Debug 2"]
				style pre_task_64224a5c stroke:#a4288c,fill:#ffffff
				role_5914bd45 --> |"2"| pre_task_64224a5c
				linkStyle 43 stroke:#a4288c,color:#a4288c
				pre_task_eaf098d3["fake_role : Debug 3 with double quote &#34;here&#34; in the name"]
				style pre_task_eaf098d3 stroke:#a4288c,fill:#ffffff
				role_5914bd45 --> |"3"| pre_task_eaf098d3
				linkStyle 44 stroke:#a4288c,color:#a4288c
			%% End of the role 'fake_role'
			%% Start of the block 'Block in pre task'
			block_59e01f41["[block] Block in pre task"]
			style block_59e01f41 fill:#a4288c,color:#ffffff,stroke:#a4288c
			play_74990123 --> |"2"| block_59e01f41
			linkStyle 45 stroke:#a4288c,color:#a4288c
			subgraph subgraph_block_59e01f41["Block in pre task "]
				pre_task_d56eed17["debug"]
				style pre_task_d56eed17 stroke:#a4288c,fill:#ffffff
				block_59e01f41 --> |"1"| pre_task_d56eed17
				linkStyle 46 stroke:#a4288c,color:#a4288c
			end
			%% End of the block 'Block in pre task'
			task_13ae5b2d["[task] Install tree"]
			style task_13ae5b2d stroke:#a4288c,fill:#ffffff
			play_74990123 --> |"3"| task_13ae5b2d
			linkStyle 47 stroke:#a4288c,color:#a4288c
			%% Start of the block 'Install Apache'
			block_58464279["[block] Install Apache"]
			style block_58464279 fill:#a4288c,color:#ffffff,stroke:#a4288c
			play_74990123 --> |"4 [when: (ansible_facts['distribution'] == 'CentOS' and ansible_facts['distribution_major_version'] == '6')]"| block_58464279
			linkStyle 48 stroke:#a4288c,color:#a4288c
			subgraph subgraph_block_58464279["Install Apache "]
				task_3c6e5034["Install some packages"]
				style task_3c6e5034 stroke:#a4288c,fill:#ffffff
				block_58464279 --> |"1 [when: (ansible_facts['distribution'] == 'CentOS' and ansible_facts['distribution_major_version'] == '6')]"| task_3c6e5034
				linkStyle 49 stroke:#a4288c,color:#a4288c
				task_7f997d4e["template"]
				style task_7f997d4e stroke:#a4288c,fill:#ffffff
				block_58464279 --> |"2 [when: (ansible_facts['distribution'] == 'CentOS' and ansible_facts['distribution_major_version'] == '6')]"| task_7f997d4e
				linkStyle 50 stroke:#a4288c,color:#a4288c
				%% Start of the block ''
				block_58e72e2c["[block] "]
				style block_58e72e2c fill:#a4288c,color:#ffffff,stroke:#a4288c
				block_58464279 --> |"3 [when: (ansible_facts['distribution'] == 'CentOS' and ansible_facts['distribution_major_version'] == '6')]"| block_58e72e2c
				linkStyle 51 stroke:#a4288c,color:#a4288c
				subgraph subgraph_block_58e72e2c[" "]
					task_752a43fc["get_url"]
					style task_752a43fc stroke:#a4288c,fill:#ffffff
					block_58e72e2c --> |"1 [when: (ansible_facts['distribution'] == 'CentOS' and ansible_facts['distribution_major_version'] == '6') and True]"| task_752a43fc
					linkStyle 52 stroke:#a4288c,color:#a4288c
					task_b31070fc["command"]
					style task_b31070fc stroke:#a4288c,fill:#ffffff
					block_58e72e2c --> |"2 [when: (ansible_facts['distribution'] == 'CentOS' and ansible_facts['distribution_major_version'] == '6')]"| task_b31070fc
					linkStyle 53 stroke:#a4288c,color:#a4288c
				end
				%% End of the block ''
				task_4ff99c46["service"]
				style task_4ff99c46 stroke:#a4288c,fill:#ffffff
				block_58464279 --> |"4 [when: (ansible_facts['distribution'] == 'CentOS' and ansible_facts['distribution_major_version'] == '6')]"| task_4ff99c46
				linkStyle 54 stroke:#a4288c,color:#a4288c
			end
			%% End of the block 'Install Apache'
			task_27e5fe68["[task] Create a username for tomcat"]
			style task_27e5fe68 stroke:#a4288c,fill:#ffffff
			play_74990123 --> |"5"| task_27e5fe68
			linkStyle 55 stroke:#a4288c,color:#a4288c
			post_task_b09e48f3["[post_task] Debug"]
			style post_task_b09e48f3 stroke:#a4288c,fill:#ffffff
			play_74990123 --> |"6"| post_task_b09e48f3
			linkStyle 56 stroke:#a4288c,color:#a4288c
			%% Start of the block 'My post task block'
			block_644a319d["[block] My post task block"]
			style block_644a319d fill:#a4288c,color:#ffffff,stroke:#a4288c
			play_74990123 --> |"7"| block_644a319d
			linkStyle 57 stroke:#a4288c,color:#a4288c
			subgraph subgraph_block_644a319d["My post task block "]
				post_task_e6f19df5["template"]
				style post_task_e6f19df5 stroke:#a4288c,fill:#ffffff
				block_644a319d --> |"1"| post_task_e6f19df5
				linkStyle 58 stroke:#a4288c,color:#a4288c
			end
			%% End of the block 'My post task block'
		%% End of the play 'Play: all (0)'
	%% End of the playbook 'tests/fixtures/with_block.yml'


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
                                [--renderer {graphviz,mermaid-flowchart}]
                                [--version] [-t TAGS] [--skip-tags SKIP_TAGS]
                                [--vault-id VAULT_IDS]
                                [--ask-vault-password | --vault-password-file VAULT_PASSWORD_FILES]
                                [-e EXTRA_VARS]
                                playbooks [playbooks ...]

Make graphs from your Ansible Playbooks.

positional arguments:
  playbooks             Playbook(s) to graph

options:
  --ask-vault-password, --ask-vault-pass
                        ask for vault password
  --group-roles-by-name
                        When rendering the graph, only a single role will be
                        display for all roles having the same names.
  --include-role-tasks  Include the tasks of the role in the graph.
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
  --renderer {graphviz,mermaid-flowchart}
                        The renderer to use to generate the graph. Default:
                        graphviz
  --skip-tags SKIP_TAGS
                        only run plays and tasks whose tags do not match these
                        values
  --vault-id VAULT_IDS  the vault identity to use
  --vault-password-file VAULT_PASSWORD_FILES, --vault-pass-file VAULT_PASSWORD_FILES
                        vault password file
  --version             show program's version number and exit
  --view                Automatically open the resulting SVG file with your
                        system’s default viewer application for the file type
  -e EXTRA_VARS, --extra-vars EXTRA_VARS
                        set additional variables as key=value or YAML/JSON, if
                        filename prepend with @
  -h, --help            show this help message and exit
  -i INVENTORY, --inventory INVENTORY
                        specify inventory host path or comma separated host
                        list.
  -o OUTPUT_FILENAME, --output-file-name OUTPUT_FILENAME
                        Output filename without the '.svg' extension. Default:
                        <playbook>.svg
  -s, --save-dot-file   Save the graphviz dot file used to generate the graph.
  -t TAGS, --tags TAGS  only run plays and tasks tagged with these values
  -v, --verbose         Causes Ansible to print more debug messages. Adding
                        multiple -v will increase the verbosity, the builtin
                        plugins currently evaluate up to -vvvvvv. A reasonable
                        level to start is -vvv, connection debugging might
                        require -vvvv.
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
$ make test # run all tests
```

The graphs are generated in the folder `tests/generated-svgs`. They are also generated as artefacts
in [Github Actions](https://github.com/haidaraM/ansible-playbook-grapher/actions). Feel free to look at them when
submitting PRs.

### Lint and format

The project uses black to format the code. Run `black .` to format.

## License

GNU General Public License v3.0 or later (Same as Ansible)

See [LICENSE](./LICENSE) for the full text

