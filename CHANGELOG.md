# 0.9.0
 - New Feature: Add the support for include_role, import_role, import_playbook
 - Fix https://github.com/haidaraM/ansible-playbook-grapher/issues/16
 - Add more tests
 - CLI more verbose: `-v` or `-vv` etc...
 - Add `.dot` extension to graphviz exported file (option `-s`) 
 - ...

# 0.8.3
 - Fix: Return code of the script

# 0.8.2
 - Fix: Make entrypoint (main) args optional

# 0.8.1
 - Pypi: Fix images URL in the description

# 0.8.0
 - Add support for include_tasks [\#13](https://github.com/haidaraM/ansible-playbook-grapher/issues/13)
 - Update Graphviz and lxml versions
 - Fix hover on play nodes. The related tasks are properly highlighted now 
 - Travis: Test more versions of Ansible
 - Print Ansible version used the by grapher when printing version (`ansible-playbook-grapher --version`)
 - Add ability to run the tests with "python setup.py test"
 - Fix Pypi package description
 - Other minor changes...
