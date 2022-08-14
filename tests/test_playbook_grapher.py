import os
from _elementtree import Element
from typing import Dict, List, Tuple

import pytest
from pyquery import PyQuery

from ansibleplaybookgrapher import __prog__
from ansibleplaybookgrapher.cli import get_cli_class
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
    :return: SVG path and playbook absolute path
    """
    additional_args = additional_args or []
    # Explicitly add verbosity to the tests
    additional_args.insert(0, "-vv")

    if os.environ.get("TEST_VIEW_GENERATED_FILE") == "1":
        additional_args.insert(0, "--view")

    if "--open-protocol-handler" not in additional_args:
        additional_args.insert(0, "--open-protocol-handler")
        additional_args.insert(1, "vscode")

    playbook_paths = [os.path.join(FIXTURES_DIR, p_file) for p_file in playbook_files]
    args = [__prog__]

    if output_filename:  # the default filename is the playbook file name minus .yml
        # put the generated svg in a dedicated folder
        output_filename = output_filename.replace("[", "-").replace("]", "")
        args.extend(["-o", os.path.join(DIR_PATH, "generated_svg", output_filename)])

    args.extend(additional_args)

    args.extend(playbook_paths)

    cli = get_cli_class()(args)

    return cli.run(), playbook_paths


def _common_tests(
    svg_path: str,
    playbook_paths: List[str],
    playbooks_number: int = 1,
    plays_number: int = 0,
    tasks_number: int = 0,
    post_tasks_number: int = 0,
    roles_number: int = 0,
    pre_tasks_number: int = 0,
    blocks_number: int = 0,
) -> Dict[str, List[Element]]:
    """
    Perform some common tests on the generated svg file:
     - Existence of svg file
     - Check number of plays, tasks, pre_tasks, role_tasks, post_tasks
     - Root node text that must be the playbook path
    :param plays_number: Number of plays in the playbook
    :param pre_tasks_number: Number of pre tasks in the playbook
    :param roles_number: Number of roles in the playbook
    :param tasks_number: Number of tasks in the playbook
    :param post_tasks_number: Number of post tasks in the playbook
    :return: A dictionary with the different tasks, roles, pre_tasks as keys and a list of Elements (nodes) as values
    """

    pq = PyQuery(filename=svg_path)
    pq.remove_namespaces()

    # test if the file exist. It will exist only if we write in it.
    assert os.path.isfile(svg_path), "The svg file should exist"

    playbooks = pq("g[id^='playbook_']")
    plays = pq("g[id^='play_']")
    tasks = pq("g[id^='task_']")
    post_tasks = pq("g[id^='post_task_']")
    pre_tasks = pq("g[id^='pre_task_']")
    blocks = pq("g[id^='block_']")
    roles = pq("g[id^='role_']")

    playbooks_file_names = [e.text for e in playbooks.find("text")]
    assert (
        playbooks_file_names == playbook_paths
    ), "The playbook file names should be in the svg file"

    assert (
        len(playbooks) == playbooks_number
    ), f"The graph '{svg_path}' should contains {playbooks_number} play(s) but we found {len(playbooks)} play(s)"

    assert (
        len(plays) == plays_number
    ), f"The graph '{svg_path}' should contains {plays_number} play(s) but we found {len(plays)} play(s)"

    assert (
        len(pre_tasks) == pre_tasks_number
    ), f"The graph '{svg_path}' should contains {pre_tasks_number} pre tasks(s) but we found {len(pre_tasks)} pre tasks"

    assert (
        len(roles) == roles_number
    ), f"The playbook '{svg_path}' should contains {roles_number} role(s) but we found {len(roles)} role(s)"

    assert (
        len(tasks) == tasks_number
    ), f"The graph '{svg_path}' should contains {tasks_number} tasks(s) but we found {len(tasks)} tasks"

    assert (
        len(post_tasks) == post_tasks_number
    ), f"The graph '{svg_path}' should contains {post_tasks_number} post tasks(s) but we found {len(post_tasks)} post tasks"

    assert (
        len(blocks) == blocks_number
    ), f"The graph '{svg_path}' should contains {blocks_number} blocks(s) but we found {len(blocks)} blocks "

    return {
        "tasks": tasks,
        "plays": plays,
        "post_tasks": post_tasks,
        "pre_tasks": pre_tasks,
        "roles": roles,
    }


def test_simple_playbook(request):
    """
    Test simple_playbook.yml
    """
    svg_path, playbook_paths = run_grapher(
        ["simple_playbook.yml"],
        output_filename=request.node.name,
        additional_args=["-i", os.path.join(FIXTURES_DIR, "inventory")],
    )

    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        post_tasks_number=2,
    )


def test_example(request):
    """
    Test example.yml
    """
    svg_path, playbook_paths = run_grapher(
        ["example.yml"], output_filename=request.node.name
    )

    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=4,
        post_tasks_number=2,
        pre_tasks_number=2,
    )


def test_include_tasks(request):
    """
    Test include_tasks.yml, an example with some included tasks
    """
    svg_path, playbook_paths = run_grapher(
        ["include_tasks.yml"], output_filename=request.node.name
    )

    _common_tests(
        svg_path=svg_path, playbook_paths=playbook_paths, plays_number=1, tasks_number=7
    )


def test_import_tasks(request):
    """
    Test import_tasks.yml, an example with some imported tasks
    """
    svg_path, playbook_paths = run_grapher(
        ["import_tasks.yml"], output_filename=request.node.name
    )

    _common_tests(
        svg_path=svg_path, playbook_paths=playbook_paths, plays_number=1, tasks_number=5
    )


@pytest.mark.parametrize(
    ["include_role_tasks_option", "expected_tasks_number"],
    [("--", 2), ("--include-role-tasks", 8)],
    ids=["no_include_role_tasks_option", "include_role_tasks_option"],
)
def test_with_roles(request, include_role_tasks_option, expected_tasks_number):
    """
    Test with_roles.yml, an example with roles
    """

    svg_path, playbook_paths = run_grapher(
        ["with_roles.yml"],
        output_filename=request.node.name,
        additional_args=[include_role_tasks_option],
    )

    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=expected_tasks_number,
        post_tasks_number=2,
        roles_number=2,
        pre_tasks_number=2,
    )


@pytest.mark.parametrize(
    ["include_role_tasks_option", "expected_tasks_number"],
    [("--", 2), ("--include-role-tasks", 8)],
    ids=["no_include_role_tasks_option", "include_role_tasks_option"],
)
def test_include_role(request, include_role_tasks_option, expected_tasks_number):
    """
    Test include_role.yml, an example with include_role
    """
    svg_path, playbook_paths = run_grapher(
        ["include_role.yml"],
        output_filename=request.node.name,
        additional_args=[include_role_tasks_option],
    )

    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=expected_tasks_number,
        roles_number=3,
    )


def test_with_block(request):
    """
    Test with_block.yml, an example with roles
    """
    svg_path, playbook_paths = run_grapher(
        ["with_block.yml"],
        output_filename=request.node.name,
        additional_args=["--include-role-tasks", "--save-dot-file"],
    )

    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=7,
        post_tasks_number=2,
        roles_number=1,
        pre_tasks_number=4,
        blocks_number=4,
    )


def test_nested_include_tasks(request):
    """
    Test nested_include.yml, an example with an include_tasks that include another tasks
    """
    svg_path, playbook_paths = run_grapher(
        ["nested_include_tasks.yml"], output_filename=request.node.name
    )

    _common_tests(
        svg_path=svg_path, playbook_paths=playbook_paths, plays_number=1, tasks_number=3
    )


@pytest.mark.parametrize(
    ["include_role_tasks_option", "expected_tasks_number"],
    [("--", 1), ("--include-role-tasks", 7)],
    ids=["no_include_role_tasks_option", "include_role_tasks_option"],
)
def test_import_role(request, include_role_tasks_option, expected_tasks_number):
    """
    Test import_role.yml, an example with import role.
    Import role is special because the tasks imported from role are treated as "normal tasks" when the playbook is parsed.
    """
    svg_path, playbook_paths = run_grapher(
        ["import_role.yml"],
        output_filename=request.node.name,
        additional_args=[include_role_tasks_option],
    )

    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=expected_tasks_number,
        roles_number=1,
    )


def test_import_playbook(request):
    """
    Test import_playbook
    """

    svg_path, playbook_paths = run_grapher(
        ["import_playbook.yml"], output_filename=request.node.name
    )
    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=4,
        post_tasks_number=2,
        pre_tasks_number=2,
    )


@pytest.mark.parametrize(
    ["include_role_tasks_option", "expected_tasks_number"],
    [("--", 4), ("--include-role-tasks", 7)],
    ids=["no_include_role_tasks_option", "include_role_tasks_option"],
)
def test_nested_import_playbook(
    request, include_role_tasks_option, expected_tasks_number
):
    """
    Test nested import playbook with an import_role and include_tasks
    """
    svg_path, playbook_paths = run_grapher(
        ["nested_import_playbook.yml"],
        output_filename=request.node.name,
        additional_args=[include_role_tasks_option],
    )
    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=2,
        tasks_number=expected_tasks_number,
    )


def test_relative_var_files(request):
    """
    Test a playbook with a relative var file
    """
    svg_path, playbook_paths = run_grapher(
        ["relative_var_files.yml"], output_filename=request.node.name
    )
    res = _common_tests(
        svg_path=svg_path, playbook_paths=playbook_paths, plays_number=1, tasks_number=2
    )

    # check if the plays title contains the interpolated variables
    assert (
        "Cristiano Ronaldo" in res["tasks"][0].find("g/a/text").text
    ), "The title should contain player name"
    assert (
        "Lionel Messi" in res["tasks"][1].find("g/a/text").text
    ), "The title should contain player name"


def test_tags(request):
    """
    Test a playbook by only graphing a specific tasks based on the given tags
    """
    svg_path, playbook_paths = run_grapher(
        ["tags.yml"],
        output_filename=request.node.name,
        additional_args=["-t", "pre_task_tag_1"],
    )
    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        pre_tasks_number=1,
    )


def test_skip_tags(request):
    """
    Test a playbook by only graphing a specific tasks based on the given tags
    """
    svg_path, playbook_paths = run_grapher(
        ["tags.yml"],
        output_filename=request.node.name,
        additional_args=["--skip-tags", "pre_task_tag_1", "--include-role-tasks"],
    )
    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=3,
        roles_number=1,
        pre_tasks_number=1,
    )


def test_multi_plays(request):
    """
    Test with multiple plays, include_role and roles
    """

    svg_path, playbook_paths = run_grapher(
        ["multi-plays.yml"],
        output_filename=request.node.name,
        additional_args=["--include-role-tasks"],
    )
    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=3,
        tasks_number=10,
        post_tasks_number=2,
        roles_number=3,
        pre_tasks_number=2,
    )


def test_multiple_playbooks(request):
    """
    Test with multiple playbooks
    """

    svg_path, playbook_paths = run_grapher(
        ["multi-plays.yml", "relative_var_files.yml", "with_roles.yml"],
        output_filename=request.node.name,
        additional_args=["--include-role-tasks"],
    )
    _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        playbooks_number=3,
        plays_number=3 + 1 + 1,
        pre_tasks_number=2 + 0 + 2,
        roles_number=3,
        tasks_number=10 + 2 + 8,
        post_tasks_number=2 + 0 + 2,
    )


def test_with_roles_with_custom_protocol_handlers(request):
    """
    Test with_roles.yml with a custom protocol handlers
    """
    formats_str = '{"file": "vscode://file/{path}:{line}", "folder": "{path}"}'
    svg_path, playbook_paths = run_grapher(
        ["with_roles.yml"],
        output_filename=request.node.name,
        additional_args=[
            "--open-protocol-handler",
            "custom",
            "--open-protocol-custom-formats",
            formats_str,
        ],
    )

    res = _common_tests(
        svg_path=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=2,
        post_tasks_number=2,
        roles_number=2,
        pre_tasks_number=2,
    )

    xlink_ref_selector = "{http://www.w3.org/1999/xlink}href"
    for t in res["tasks"]:
        assert (
            t.find("g/a")
            .get(xlink_ref_selector)
            .startswith(f"vscode://file/{DIR_PATH}")
        ), "Tasks should be open with vscode"

    for r in res["roles"]:
        assert r.find("g/a").get(xlink_ref_selector).startswith(DIR_PATH)


def test_community_download_roles_and_collection(request):
    """
    Test if the grapher is able to find some downloaded roles and collections when graphing the playbook
    :return:
    """
    run_grapher(
        ["docker-mysql-galaxy.yml"],
        output_filename=request.node.name,
        additional_args=["--include-role-tasks"],
    )
