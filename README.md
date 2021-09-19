# Ansible Playbook Grapher

![Testing](https://github.com/haidaraM/ansible-playbook-grapher/workflows/Testing/badge.svg)
[![PyPI version](https://badge.fury.io/py/ansible-playbook-grapher.svg)](https://badge.fury.io/py/ansible-playbook-grapher)
[![Coverage Status](https://coveralls.io/repos/github/haidaraM/ansible-playbook-grapher/badge.svg?branch=main)](https://coveralls.io/github/haidaraM/ansible-playbook-grapher?branch=main)

[ansible-playbook-grapher](https://github.com/haidaraM/ansible-playbook-grapher) is a command line tool to create a
graph representing your Ansible playbook plays, tasks and roles. The aim of this project is to have an overview of your
playbook.

Inspired by [Ansible Inventory Grapher](https://github.com/willthames/ansible-inventory-grapher).

## Prerequisites

- Python 3
- **Ansible** >= 2.9: If you still use an older version of Ansible, create a virtual environment and install
  ansible-playbook-grapher.
  **pip will install a version of Ansible >= 2.9 if not already installed.** I try to
  respect [Red Hat Ansible Engine Life Cycle](https://access.redhat.com/support/policy/updates/ansible-engine) for the
  supported Ansible version.
- **Graphviz**: The tool used to generate the graph in SVG.
  ```shell script
  $ sudo apt-get install graphviz # or yum install or brew install
  ```

## Installation

```shell script
$ pip install ansible-playbook-grapher
```

## Usage

```shell
$ ansible-playbook-grapher tests/fixtures/example.yml
```

![Example](https://raw.githubusercontent.com/haidaraM/ansible-playbook-grapher/main/img/example.png)

```bash
$ ansible-playbook-grapher --include-role-tasks  tests/fixtures/with_roles.yml
```

![Example](https://raw.githubusercontent.com/haidaraM/ansible-playbook-grapher/main/img/with_roles.png)

Some options are available:

```
$ ansible-playbook-grapher --help
usage: ansible-playbook-grapher [-h] [-v] [-i INVENTORY]
                                [--include-role-tasks] [-s]
                                [-o OUTPUT_FILENAME] [--version] [-t TAGS]
                                [--skip-tags SKIP_TAGS] [--vault-id VAULT_IDS]
                                [--ask-vault-pass | --vault-password-file VAULT_PASSWORD_FILES]
                                [-e EXTRA_VARS]
                                playbook

Make graphs from your Ansible Playbooks.

positional arguments:
  playbook              Playbook to graph

optional arguments:
  --ask-vault-pass      ask for vault password
  --include-role-tasks  Include the tasks of the role in the graph.
  --skip-tags SKIP_TAGS
                        only run plays and tasks whose tags do not match these
                        values
  --vault-id VAULT_IDS  the vault identity to use
  --vault-password-file VAULT_PASSWORD_FILES
                        vault password file
  --version             show program's version number and exit
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
  -s, --save-dot-file   Save the dot file used to generate the graph.
  -t TAGS, --tags TAGS  only run plays and tasks tagged with these values
  -v, --verbose         verbose mode (-vvv for more, -vvvv to enable
                        connection debugging)

```

## Configuration: ansible.cfg

The content of `ansible.cfg` is loaded automatically when running the grapher according to Ansible's behavior. The
corresponding environment variables are also loaded.

The values in the config file (and their corresponding environment variables) may affect the behavior of the grapher.
For example `TAGS_RUN` and `TAGS_SKIP` or vault configuration.

More information [here](https://docs.ansible.com/ansible/latest/reference_appendices/config.html).

## Contribution

Contributions are welcome. Feel free to contribute by creating an issue or submitting a PR :smiley:

### Dev environment

To setup a new development environment :

- Install graphviz `sudo apt-get install graphviz # or yum install or brew install graphviz`
- (cd tests && pip install -r requirements_tests.txt)

Run the tests with:

```shell script
$ make test # run all tests
```

The graphs are generated in the folder `tests/generated_svg`. They are also generated as artefacts
in [Github Actions](https://github.com/haidaraM/ansible-playbook-grapher/actions). Feel free to look at them when
submitting PRs.
