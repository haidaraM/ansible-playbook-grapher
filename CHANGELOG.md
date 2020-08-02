# 0.10.0
 - Fix [\#13](https://github.com/haidaraM/ansible-playbook-grapher/issues/13): Tasks with same names are not mapped
  anymore to the same nodes.
 - Fix: Do not add the skipped tags to the graph [\#24](https://github.com/haidaraM/ansible-playbook-grapher/issues/24)
 - Do not run some tests with Ansible 2.8: Ansible 2.8 sets some global variables causing the tests to fail. 
 To avoid that, these tests are marked to fail. This "mark" should be removed when we drop support for Ansible 2.8
 - FIX. README Usage [\#41](https://github.com/haidaraM/ansible-playbook-grapher/pull/41) 
 - Bump pytest-cov from 2.8.1 to 2.9.0 via Dependant bot
 - Bump graphviz from 0.14 to 0.14.1 via Dependant bot
 - Bump pytest from 5.4.3 to 6.0.1
 - Various fixes: typo, remove useless functions

# 0.9.4
 - Fix playbook with relative var_file. Fix #35
 - Add dependant bot to the repo:
   - Update Pytest to 5.4.2
   - Update graphviz to 0.14 

# 0.9.3
 - Update dependencies ([\#29](https://github.com/haidaraM/ansible-playbook-grapher/pull/29))
 - Make sure that an element exists before assigning it ([\#26](https://github.com/haidaraM/ansible-playbook-grapher/pull/26))

# 0.9.2
 - Add support for Ansible 2.9 ([\#25](https://github.com/haidaraM/ansible-playbook-grapher/pull/25))

# 0.9.1
Fix issue [\#18](https://github.com/haidaraM/ansible-playbook-grapher/issues/18) with Ansible 2.8: the CLI was refactored in https://github.com/ansible/ansible/pull/50069. See https://github.com/haidaraM/ansible-playbook-grapher/pull/19 for the related changes. 

# 0.9.0
 - The grapher now requires Ansible >= 2.7.0
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
