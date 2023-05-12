import os
from typing import List, Tuple

import pytest

from ansibleplaybookgrapher import __prog__
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI
from tests import FIXTURES_DIR

# This file directory abspath
DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def run_grapher(
    playbook_files: List[str],
    output_filename: str = None,
    additional_args: List[str] = None,
) -> Tuple[str, List[str]]:
    """
    Utility function to run the grapher
    :param output_filename:
    :param additional_args:
    :param playbook_files:
    :return: Mermaid file path and playbooks absolute paths
    """
    additional_args = additional_args or []
    # Explicitly add verbosity to the tests
    additional_args.insert(0, "-vv")

    playbook_paths = [os.path.join(FIXTURES_DIR, p_file) for p_file in playbook_files]
    args = [__prog__]

    # Clean the name a little bit
    output_filename = (
        output_filename.replace("[", "-").replace("]", "").replace(".yml", "")
    )
    # put the generated file in a dedicated folder
    args.extend(["-o", os.path.join(DIR_PATH, "generated-mermaids", output_filename)])

    args.extend(additional_args)

    args.extend(["--renderer", "mermaid-flowchart"])

    args.extend(playbook_paths)

    cli = PlaybookGrapherCLI(args)

    return cli.run(), playbook_paths


def _common_tests(mermaid_path: str, playbook_paths: List[str], **kwargs):
    """

    :param mermaid_path:
    :param playbook_paths:
    :param kwargs:
    :return:
    """

    # TODO: add proper tests on the mermaid code.
    #  Need a parser to make sure the outputs contain all the playbooks, plays, tasks and roles
    # test if the file exist. It will exist only if we write in it.
    assert os.path.isfile(
        mermaid_path
    ), f"The mermaid file should exist at '{mermaid_path}'"


@pytest.mark.parametrize(
    "playbook_file",
    [
        # FIXME: Once we have proper tests, we need to split the parameters similar to what we do with graphviz
        "docker-mysql-galaxy.yml",
        "example.yml",
        "group-roles-by-name.yml",
        "import_playbook.yml",
        "import_role.yml",
        "import_tasks.yml",
        "include_role.yml",
        "include_tasks.yml",
        "multi-plays.yml",
        "nested_import_playbook.yml",
        "nested_include_tasks.yml",
        "relative_var_files.yml",
        "roles_dependencies.yml",
        "simple_playbook.yml",
        "tags.yml",
        "with_block.yml",
        "with_roles.yml",
    ],
)
def test_single_playbook(request, playbook_file):
    """
    Test the renderer with a single playbook
    """
    mermaid_path, playbook_paths = run_grapher(
        [playbook_file],
        output_filename=request.node.name,
        additional_args=[
            "-i",
            os.path.join(FIXTURES_DIR, "inventory"),
            "--include-role-tasks",
        ],
    )
    _common_tests(mermaid_path, playbook_paths)


def test_multiple_playbooks(request):
    """
    Test the renderer with multiple playbooks in a single graph
    """
    mermaid_path, playbook_paths = run_grapher(
        ["multi-plays.yml", "relative_var_files.yml", "with_roles.yml"],
        output_filename=request.node.name,
        additional_args=[
            "-i",
            os.path.join(FIXTURES_DIR, "inventory"),
            "--include-role-tasks",
        ],
    )
    _common_tests(mermaid_path, playbook_paths)
