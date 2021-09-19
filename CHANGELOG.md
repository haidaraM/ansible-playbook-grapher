# 1.0.0 (Unreleased)

- refactor: See [\#81](https://github.com/haidaraM/ansible-playbook-grapher/pull/81)
    - Completely rewrite the grapher: the parser, the graph and the renderer to graphviz have been split.
    - Hide some ansible internals in the parser.
    - Clean code.
- feat:
    - Consider inclue_role as normal role instead of
      task [\#82](https://github.com/haidaraM/ansible-playbook-grapher/pull/82)
    - feat: Curved edge label based on the path [\#84](https://github.com/haidaraM/ansible-playbook-grapher/pull/84)
- fix:
    - front: Refactor the JS part and fix issue when selecting/unselecting nodes
    - front: Do not unhighlight the current selected node when hovering on parent node
    - cli(typo): rename `--ouput-file-name` to `--output-file-name`
    - fix: Use the correct tooltip for edges
- test:
    - Add Ansible 2.10.7 in the test matrix
    - Make test verbose by default with `-vv` in the args
- docs:
    - Reformat CHANGELOG
    - Reformat README.md
- Dependencies:
    - bump pytest from 6.2.4 to 6.2.5 [\#83](https://github.com/haidaraM/ansible-playbook-grapher/pull/83)

# 0.11.1 (2021-07-28)

- Dependencies:
    - Unpin requirements. See [\#71](https://github.com/haidaraM/ansible-playbook-grapher/issues/71)
    - Bump pytest-cov from 2.11.1 to 2.12.1 [\#78](https://github.com/haidaraM/ansible-playbook-grapher/issues/78)
    - Bump pytest from 6.2.2 to 6.2.4 [\#76](https://github.com/haidaraM/ansible-playbook-grapher/issues/76)
    - Upgrade to GitHub-native Dependabot [\#72](https://github.com/haidaraM/ansible-playbook-grapher/issues/72)
- Drop support for ansible 2.8. **The grapher requires at least ansible
  2.9** [\#74](https://github.com/haidaraM/ansible-playbook-grapher/issues/74)
- Fix:
    - Correct graph exported display message. See [\#69](https://github.com/haidaraM/ansible-playbook-grapher/issues/69)
- CI: Run github actions on pull requests

# 0.11.0

- Feat:
    - Add type annotations to the source code
    - Add more debug info + improve counter
- Fix:
    - Attach play to role edge to play_subgraph instead of role one
    - Fix display verbosity
    - Fix pytest warning (remove `rootdir` from pytest.ini)
    - Fix: Show task name instead of its ID on hover. See issue #57
    - ci: Fix coverage
- Refactor:
    - Rewriting the grapher, clean code.
    - Generate node IDs from an util function
- Style: Replace some `format` by f-string
- CI: Replace Travis by Github actions (#54)
- Dependencies:
    - Bump pytest from 6.0.1 to 6.2.2 (PRs #50, #51, #62, #67)
    - Bump pytest-cov from 2.10.0 to 2.11.1 (PRs #49, #65)
    - Bump pyquery from 1.4.1 to 1.4.3 (PRs #58)
    - Bump lxml from 4.5.2 to 4.6.2 (PRs #53, #61)
    - Bump graphviz from 0.14.1 to 0.16 (PRs #52, #64)
    - Bump graphviz from 0.14.1 to 0.16 (PRs #52, #64)
    - Bump packaging from 20.4 to 20.9 (PRs #66)

# 0.10.0

- Fix [\#13](https://github.com/haidaraM/ansible-playbook-grapher/issues/13): Tasks with same names are not mapped
  anymore to the same nodes.
- Fix: Do not add the skipped tags to the graph [\#24](https://github.com/haidaraM/ansible-playbook-grapher/issues/24)
- Do not run some tests with Ansible 2.8: Ansible 2.8 sets some global variables causing the tests to fail. To avoid
  that, these tests are marked to fail. This "mark" should be removed when we drop support for Ansible 2.8
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
- Make sure that an element exists before assigning
  it ([\#26](https://github.com/haidaraM/ansible-playbook-grapher/pull/26))

# 0.9.2

- Add support for Ansible 2.9 ([\#25](https://github.com/haidaraM/ansible-playbook-grapher/pull/25))

# 0.9.1

Fix issue [\#18](https://github.com/haidaraM/ansible-playbook-grapher/issues/18) with Ansible 2.8: the CLI was
refactored in https://github.com/ansible/ansible/pull/50069.
See https://github.com/haidaraM/ansible-playbook-grapher/pull/19 for the related changes.

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
