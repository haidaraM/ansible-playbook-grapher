# Ansible Playbook Grapher

ansible-playbook-grapher is a command line tool to create a graph representing your Ansible playbook tasks and roles. The aim of
this project is to quickly have an overview of your playbook.

Inspired by [Ansible Inventory Grapher](https://github.com/willthames/ansible-inventory-grapher).

## Pérequis
 * **Ansible** >= 2.4: The script has not been tested yet with an earlier version of Ansible. 
 ```sudo pip3 install 'ansible>=2.4'```
 * **graphviz**: The tool used to generate the graph in SVG. `sudo apt-get install graphviz`.
 
## Installation
```bash
$ sudo pip3 install ansible-playbook-grapher
```

## Usage

```yaml
# file: examples/playbook.yml
TODO
```


```bash
$ ansible-playbook-grapher examples/playbook.yml
```

Some options are available:

```bash
$ ansible-playbook-grapher --help
```


## TODO

 - More colors: For the moment, a random color is chosen from a set of defined colors for each play
 found in the playbook. Maybe generate some colors specific automatically for each play.
 - Properly rank the edge of the graph to represent the order of the execution of the tasks and roles
  