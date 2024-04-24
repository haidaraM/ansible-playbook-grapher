# 2.2.1 (2024-04-24)

## What's Changed
* fix: Only display mermaid live editor URL with the flag -vv
* chore(deps): bump pytest from 8.0.2 to 8.1.1 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/185
* chore(deps): bump pytest-cov from 4.1.0 to 5.0.0 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/182
* chore(deps): update black requirement from ~=24.2 to ~=24.3 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/184
* chore(deps): update ansible-core requirement from <2.16.5,>=2.15 to >=2.15,<2.16.6 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/183

**Full Changelog**: https://github.com/haidaraM/ansible-playbook-grapher/compare/v2.2.0...v2.2.1

# 2.2.0 (2024-04-21)

## What's Changed

* feat: Add support for hiding empty plays and plays without roles https://github.com/haidaraM/ansible-playbook-grapher/pull/177.
  * Add a new flag `--hide-empty-plays` to not show in the graph the plays that end up being empty after applying the filters.
  * Add a new flag `--hide-plays-without-roles` to not show in the graph the plays that end up with no roles. Only roles at the play level and include_role as tasks are considered (no import_role).
* Add support for viewing mermaid graphs in the browser with `--view --renderer mermaid-flowchart` in https://github.com/haidaraM/ansible-playbook-grapher/pull/181
* refactor(internal): `PlaybookNode.plays` is now a method instead of property.   
* refactor(internal): Do not access the `_compositions` in the child classes: use method from the CompositeNode.   
* chore(deps): update black requirement from ~=24.1 to ~=24.2 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/175
* chore(deps): bump pytest from 8.0.0 to 8.0.2 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/173
* fix: make sure pip install from github works by @haidaraM in https://github.com/haidaraM/ansible-playbook-grapher/pull/178
* chore(deps): update ansible-core requirement from <2.16.4,>=2.15 to >=2.15,<2.16.5 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/174

**Full Changelog**: https://github.com/haidaraM/ansible-playbook-grapher/compare/v2.1.2...v2.2.0

# 2.1.2 (2024-02-25)

## What's Changed

Dependency updates:

* chore(deps): bump actions/upload-artifact from 3 to 4 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/166
* chore(deps): bump actions/setup-python from 4 to 5 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/165
* chore(deps): bump pytest from 7.4.3 to 7.4.4 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/168
* chore(deps): update black requirement from ~=23.11 to ~=23.12 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/169
* chore(deps): update lxml requirement from <5 to <6 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/167
* chore(deps): update ansible-core requirement from <2.16,>=2.15 to >=2.15,<2.17 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/164
* chore(deps): bump pytest from 7.4.4 to 8.0.0 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/171
* chore(deps): update black requirement from ~=23.12 to ~=24.1 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/172
* chore(deps): update ansible-core requirement from <2.16.1,>=2.15 to >=2.15,<2.16.4 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/170

**Full Changelog**: https://github.com/haidaraM/ansible-playbook-grapher/compare/v2.1.1...v2.1.2

# 2.1.1 (2023-12-02)

## What's Changed

* fix: pin to ansible-core 2.15.5 before fixing the grapher
* chore(deps): bump pytest from 7.4.2 to 7.4.3 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/160
* chore(deps): update black requirement from ~=23.9 to ~=23.10 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/161
* chore(deps): bump stefanzweifel/git-auto-commit-action from 4 to 5 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/159
* chore(deps): update black requirement from ~=23.10 to ~=23.11 by @dependabot in https://github.com/haidaraM/ansible-playbook-grapher/pull/163

**Full Changelog**: https://github.com/haidaraM/ansible-playbook-grapher/compare/v2.1.0...v2.1.1

# 2.1.0 (2023-10-01)

## What's Changed

* Support for ansible-core 2.15 by @haidaraM in https://github.com/haidaraM/ansible-playbook-grapher/pull/151.
* chore(deps): bump pytest-cov from 4.0.0 to 4.1.0 by @dependabot
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/149
* chore(deps): update black requirement from ~=23.3 to ~=23.7 by @dependabot
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/153
* chore(deps): bump pytest from 7.3.1 to 7.4.0 by @dependabot
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/152
* chore(deps): bump pytest from 7.4.0 to 7.4.2 by @dependabot
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/157
* chore(deps): update black requirement from ~=23.7 to ~=23.9 by @dependabot
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/156
* chore(deps): bump actions/checkout from 3 to 4 by @dependabot
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/155

**Full Changelog**: https://github.com/haidaraM/ansible-playbook-grapher/compare/v2.0.0...v2.1.0

# 2.0.0 (2023-06-03)

## What's Changed

- 🚀🚀Add support for MermaidJS 🚀🚀. See https://github.com/haidaraM/ansible-playbook-grapher/issues/137
- Add generated images in the CI job summary
- Update various Dependencies: pytest, pytest-cov, ansible-core, pyquery etc...
- ci: Add dependabot for github-actions
- Rename some tests files

## Breaking changes

This version contains the following breaking changes. Some of them may likely affect you if you were using the grapher
as a library inside another project:

- Completely refactor the rendering part of the grapher by making it more extensible in order to support Mermaid.
- Fill the plays, blocks and node with color to make them more visible in the output
- Rename the file `graph.py` to `graph_model.py`
- Use the concatenation of the playbook names as the output filename when graphing multiple playbooks instead of the
  first playbook.

# 1.2.0 (2022-08-21)

## What's Changed

* feat: Add test case for community downloaded roles and collections by @haidaraM
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/117
* feat: Add support multiple playbooks in one graph by @haidaraM
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/118
* fix: Roles usages and do not use multiple edges for role tasks by @haidaraM
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/120
* feat: Add a flag to group roles by name - Revert the old behavior by @haidaraM
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/122
* fix: Avoid recursive endless loop when a role references itself by @haidaraM
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/123

**Full Changelog**: https://github.com/haidaraM/ansible-playbook-grapher/compare/v1.1.3...v1.2.0

# 1.1.3 (2022-07-17)

## What's Changed

* fix: Render a single node when multiple playbooks use the same role by @haidaraM
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/111
* fix: Improve the position of the conditions on the edges by @haidaraM
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/116

**Full Changelog**: https://github.com/haidaraM/ansible-playbook-grapher/compare/v1.1.2...v1.1.3

# 1.1.2 (2022-06-22)

## What's Changed

* refactor(internal): Remove useless EdgeNode by @haidaraM
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/109
* chore(deps): bump pytest from 7.1.1 to 7.1.2 by @dependabot
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/107
* Forbid incompatible ansible-core versions >= 2.13 by @jheidbrink
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/114

## New Contributors

* @jheidbrink made their first contribution in https://github.com/haidaraM/ansible-playbook-grapher/pull/114

**Full Changelog**: https://github.com/haidaraM/ansible-playbook-grapher/compare/v1.1.1...v1.1.2

# 1.1.1 (2022-05-16)

* ci: Ansible 2.11.8 and 2.12.2 and ubuntu-latest by @haidaraM
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/103
* fix: Properly rank the edges in the graphs and sub-graphs by @haidaraM
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/104
* chore(deps): bump pytest from 6.2.5 to 7.0.1 by @dependabot
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/105
* chore(deps): bump pytest from 7.0.1 to 7.1.1 by @dependabot
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/106

# 1.1.0 (2022-02-12)

- fix: Do not pass display as param since it's a singleton + init locale to fix warning
- feat: Open node file when double-clicking on it from a
  browser [\#79](https://github.com/haidaraM/ansible-playbook-grapher/pull/79)
- fix: Unhighlight the current node when clicking on a new one
- fix: Use the correct LICENSE GPLv3 [\#100](https://github.com/haidaraM/ansible-playbook-grapher/pull/100)
- Add some news messages + fix typo and type hint
- refactor: format the code with black [\#102](https://github.com/haidaraM/ansible-playbook-grapher/pull/102)

- **Full Changelog**: https://github.com/haidaraM/ansible-playbook-grapher/compare/v1.0.2...v1.1.0

# 1.0.2 (2022-01-16)

* fix: Fix include_role with loop by @haidaraM in https://github.com/haidaraM/ansible-playbook-grapher/pull/92
* fix: Fix include_role with loop and list index out of range by @haidaraM
  in https://github.com/haidaraM/ansible-playbook-grapher/pull/99

**Full Changelog**: https://github.com/haidaraM/ansible-playbook-grapher/compare/v1.0.1...v1.0.2

# 1.0.1

* fix: Block can only contain tasks regardless of the context by @haidaraM
  in [\#96](https://github.com/haidaraM/ansible-playbook-grapher/pull/96)
  and [\#97](https://github.com/haidaraM/ansible-playbook-grapher/pull/97)

**Full Changelog**: https://github.com/haidaraM/ansible-playbook-grapher/compare/v1.0.0...v1.0.1

# 1.0.0

- refactor: See [\#81](https://github.com/haidaraM/ansible-playbook-grapher/pull/81)
    - Completely rewrite the grapher: the parser, the graph and the renderer to graphviz have been split.
    - Hide some ansible internals in the parser.
- feat:
    - Consider include_role as normal role instead of
      task [\#82](https://github.com/haidaraM/ansible-playbook-grapher/pull/82)
    - feat: Curved edge label based on the path [\#84](https://github.com/haidaraM/ansible-playbook-grapher/pull/84)
    - feat: Add option to automatically view the generated
      file [\#88](https://github.com/haidaraM/ansible-playbook-grapher/pull/88)
    - feat: Add support for block [\#86](https://github.com/haidaraM/ansible-playbook-grapher/pull/86). They are now
      visible in the graph.
    - Add support for when on include_role.
    - Only Ansible >= 2.11 is supported. **Python >=3.8** is now
      required [\#94](https://github.com/haidaraM/ansible-playbook-grapher/pull/94).
- fix:
    - front: Refactor the JS part and fix issue when selecting/unselecting nodes
    - front: Do not unhighlight the current selected node when hovering on parent node
    - cli(typo): rename `--ouput-file-name` to `--output-file-name`
    - Use the correct tooltip for edges
    - style: Do not use bold style by default and apply color on nodes border
    - Merge when condition with `and`
    - Explicitly set color luminance to avoid bright colors
    - Reduce Node ID lengths. No need to use the full UUID
    - Make grapher works with graphviz >= 0.18.
      See [\#91](https://github.com/haidaraM/ansible-playbook-grapher/issues/91)
- test:
    - Make test verbose by default with `-vv` in the args
    - Fix test_install in GitHub Actions which was not using the correct Ansible version.
- docs:
    - Reformat CHANGELOG.md and README.md
- Dependencies:
    - bump pytest from 6.2.4 to 6.2.5 [\#83](https://github.com/haidaraM/ansible-playbook-grapher/pull/83)
    - bump pytest-cov from 2.12.1 to 3.0.0 [\#90](https://github.com/haidaraM/ansible-playbook-grapher/pull/90)
    - chore(deps): Remove packaging dependency

# 0.11.2 (2021-11-07)

- fix: Restrict graphviz to <=0.17. Fix [\#91](https://github.com/haidaraM/ansible-playbook-grapher/issues/91)

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
- CI: Replace Travis by GitHub actions (#54)
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
