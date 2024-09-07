import os
from pathlib import Path

import pytest

from ansibleplaybookgrapher import __prog__
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI
from tests import FIXTURES_DIR

# This file directory abspath
DIR_PATH = Path(__file__).parent.resolve()


def run_grapher(
    playbook_files: list[str],
    output_filename: str | None = None,
    additional_args: list[str] | None = None,
) -> tuple[str, list[str]]:
    """Utility function to run the grapher
    :param output_filename:
    :param additional_args:
    :param playbook_files:
    :return: Mermaid file path and playbooks absolute paths.
    """
    additional_args = additional_args or []
    # Explicitly add verbosity to the tests
    additional_args.insert(0, "-vvv")

    if os.environ.get("TEST_VIEW_GENERATED_FILE") == "1":
        additional_args.insert(0, "--view")

    playbook_paths = [str(FIXTURES_DIR / p_file) for p_file in playbook_files]
    args = [__prog__]

    # Clean the name a little bit
    output_filename = (
        output_filename.replace("[", "-").replace("]", "").replace(".yml", "")
    )
    # put the generated file in a dedicated folder
    args.extend(["-o", str(DIR_PATH / "generated-mermaids" / output_filename)])

    args.extend(additional_args)

    args.extend(["--renderer", "mermaid-flowchart"])

    args.extend(playbook_paths)

    cli = PlaybookGrapherCLI(args)

    return cli.run(), playbook_paths


def _common_tests(mermaid_file_path: str, playbook_paths: list[str], **kwargs) -> None:
    """Some common tests for mermaid renderer
    :param mermaid_file_path:
    :param playbook_paths:
    :param kwargs:
    :return:
    """
    # TODO: add proper tests on the mermaid code.
    #  Need a parser to make sure the outputs contain all the playbooks, plays, tasks and roles
    # Test if the file exist. It will exist only if we write in it.
    mermaid_path_obj = Path(mermaid_file_path)
    assert (
        mermaid_path_obj.is_file()
    ), f"The mermaid file should exist at '{mermaid_file_path}'"

    with mermaid_path_obj.open() as mermaid_file:
        mermaid_data = mermaid_file.read()
        for playbook_path in playbook_paths:
            assert (
                playbook_path in mermaid_data
            ), "The playbook path should be in the generated code"


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
def test_playbook(request, playbook_file: str) -> None:
    """Test the renderer with a single playbook."""
    mermaid_path, playbook_paths = run_grapher(
        [playbook_file],
        output_filename=request.node.name,
        additional_args=[
            "--include-role-tasks",
        ],
    )
    _common_tests(mermaid_path, playbook_paths)


def test_multiple_playbooks(request) -> None:
    """Test the renderer with multiple playbooks in a single graph."""
    mermaid_path, playbook_paths = run_grapher(
        ["multi-plays.yml", "relative_var_files.yml", "with_roles.yml"],
        output_filename=request.node.name,
        additional_args=[
            "--include-role-tasks",
        ],
    )
    _common_tests(mermaid_path, playbook_paths)
