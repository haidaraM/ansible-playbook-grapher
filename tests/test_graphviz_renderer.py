import json
import os
from _elementtree import Element
from pathlib import Path

import pytest
from pyquery import PyQuery

from ansibleplaybookgrapher import __prog__
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI
from tests import FIXTURES_DIR_PATH, INVENTORY_PATH

# This file directory abspath
DIR_PATH = Path(__file__).parent.resolve()


def run_grapher(
    playbooks: list[str],
    output_filename: str,
    additional_args: list[str] | None = None,
) -> tuple[str, list[str]]:
    """Utility function to run the grapher
    :param output_filename:
    :param additional_args:
    :param playbooks:
    :return: SVG path and playbooks absolute paths.
    """
    additional_args = additional_args or []
    # Explicitly add verbosity to the tests
    additional_args.insert(0, "-vv")

    if os.environ.get("TEST_VIEW_GENERATED_FILE") == "1":
        additional_args.insert(0, "--view")

    if os.environ.get("GITHUB_ACTIONS") == "true":
        # Setting a custom protocol handler for browsing on GitHub
        additional_args.insert(0, "--open-protocol-handler")
        additional_args.insert(1, "custom")

        repo = os.environ["GITHUB_REPOSITORY"]
        commit_sha = os.environ["COMMIT_SHA"]
        formats = {
            "file": f"https://github.com/{repo}/blob/{commit_sha}" + "/{path}#L{line}",
            "folder": f"https://github.com/{repo}/tree/{commit_sha}" + "/{path}",
            "remove_from_path": os.environ["GITHUB_WORKSPACE"],
        }

        additional_args.insert(2, "--open-protocol-custom-formats")
        additional_args.insert(3, json.dumps(formats))

    if "--open-protocol-handler" not in additional_args:
        additional_args.insert(0, "--open-protocol-handler")
        additional_args.insert(1, "vscode")

    for idx, p_file in enumerate(playbooks):
        if ".yml" in p_file:
            playbooks[idx] = str(FIXTURES_DIR_PATH / p_file)

    args = [__prog__]

    # Clean the name a little bit and put the file in a dedicated folder
    output_filename = output_filename.replace("[", "-").replace("]", "")
    args.extend(["-o", str(DIR_PATH / "generated-svgs" / output_filename)])

    if "--title" not in additional_args:
        title_args = " ".join(additional_args + playbooks)
        args.append("--title")
        args.append(f"Args: '{title_args}'")

    args.extend(additional_args + playbooks)

    cli = PlaybookGrapherCLI(args)

    return cli.run(), playbooks


def _common_tests(
    svg_filename: str,
    playbook_paths: list[str],
    expected_title: str | None = None,
    playbooks_number: int = 1,
    plays_number: int = 0,
    tasks_number: int = 0,
    post_tasks_number: int = 0,
    roles_number: int = 0,
    pre_tasks_number: int = 0,
    blocks_number: int = 0,
    handlers_number: int = 0,
) -> dict[str, list[Element]]:
    """Perform some common tests on the generated svg file:
     - Existence of svg file
     - Check number of plays, tasks, pre_tasks, role_tasks, post_tasks
     - Root node text that must be the playbook path

    :param expected_title: The expected title of the graph
    :param plays_number: Number of plays in the playbook
    :param pre_tasks_number: Number of pre tasks in the playbook
    :param roles_number: Number of roles in the playbook
    :param tasks_number: Number of tasks in the playbook
    :param post_tasks_number: Number of post tasks in the playbook
    :param handlers_number: Number of handlers in the playbook
    :return: A dictionary with the different tasks, roles, pre_tasks as keys and a list of Elements (nodes) as values.
    """
    # test if the file exists. It will exist only if we write in it.
    assert Path(svg_filename).is_file(), "The svg file should exist"

    pq = PyQuery(filename=svg_filename)
    pq.remove_namespaces()

    graph_title: str = pq("g > text")[0].text
    playbooks: PyQuery = pq("g[id^='playbook_']")
    plays: PyQuery = pq("g[id^='play_']")
    tasks: PyQuery = pq("g[id^='task_']")
    post_tasks: PyQuery = pq("g[id^='post_task_']")
    pre_tasks: PyQuery = pq("g[id^='pre_task_']")
    blocks: PyQuery = pq("g[id^='block_']")
    roles: PyQuery = pq("g[id^='role_']")
    handlers: PyQuery = pq("g[id^='handler_']")

    if expected_title:
        assert (
            graph_title == expected_title
        ), f"The title should be '{graph_title}' but we found '{expected_title}'"

    playbooks_file_names = [e.text for e in playbooks.find("text")]
    assert (
        playbooks_file_names == playbook_paths
    ), "The playbook file names should be in the svg file"

    assert (
        len(playbooks) == playbooks_number
    ), f"The graph '{svg_filename}' should contains {playbooks_number} playbook(s) but we found {len(playbooks)} play(s)"

    assert (
        len(plays) == plays_number
    ), f"The graph '{svg_filename}' should contains {plays_number} play(s) but we found {len(plays)} play(s)"

    assert (
        len(pre_tasks) == pre_tasks_number
    ), f"The graph '{svg_filename}' should contains {pre_tasks_number} pre tasks(s) but we found {len(pre_tasks)} pre tasks"

    assert (
        len(roles) == roles_number
    ), f"The graph '{svg_filename}' should contains {roles_number} role(s) but we found {len(roles)} role(s)"

    assert (
        len(tasks) == tasks_number
    ), f"The graph '{svg_filename}' should contains {tasks_number} tasks(s) but we found {len(tasks)} tasks"

    assert (
        len(post_tasks) == post_tasks_number
    ), f"The graph '{svg_filename}' should contains {post_tasks_number} post tasks(s) but we found {len(post_tasks)} post tasks"

    assert (
        len(blocks) == blocks_number
    ), f"The graph '{svg_filename}' should contains {blocks_number} blocks(s) but we found {len(blocks)} blocks"

    assert (
        len(handlers) == handlers_number
    ), f"The graph '{svg_filename}' should contains {handlers_number} handlers(s) but we found {len(handlers)} handlers "

    return {
        "tasks": tasks,
        "plays": plays,
        "post_tasks": post_tasks,
        "pre_tasks": pre_tasks,
        "roles": roles,
        "blocks": blocks,
        "handlers": handlers,
    }


def test_simple_playbook(request: pytest.FixtureRequest) -> None:
    """Test simple_playbook.yml."""
    svg_path, playbook_paths = run_grapher(
        ["simple_playbook.yml"],
        output_filename=request.node.name,
        additional_args=["-i", str(INVENTORY_PATH), "--title", "My custom title"],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        post_tasks_number=2,
        expected_title="My custom title",
    )


def test_if_dot_file_is_saved(request: pytest.FixtureRequest) -> None:
    """Test if the dot file is saved at the expected path."""
    svg_path, playbook_paths = run_grapher(
        ["simple_playbook.yml"],
        output_filename=request.node.name,
        additional_args=["--save-dot-file"],
    )
    expected_dot_path = Path(svg_path).with_suffix(".dot")
    assert expected_dot_path.is_file()


def test_example(request: pytest.FixtureRequest) -> None:
    """Test example.yml."""
    svg_path, playbook_paths = run_grapher(
        ["example.yml"],
        output_filename=request.node.name,
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=4,
        post_tasks_number=2,
        pre_tasks_number=2,
    )


def test_include_tasks(request: pytest.FixtureRequest) -> None:
    """Test include_tasks.yml, an example with some included tasks."""
    svg_path, playbook_paths = run_grapher(
        ["include_tasks.yml"],
        output_filename=request.node.name,
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=7,
    )


def test_import_tasks(request: pytest.FixtureRequest) -> None:
    """Test import_tasks.yml, an example with some imported tasks."""
    svg_path, playbook_paths = run_grapher(
        ["import_tasks.yml"],
        output_filename=request.node.name,
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=5,
    )


@pytest.mark.parametrize(
    ("include_role_tasks_option", "expected_tasks_number"),
    [("--", 2), ("--include-role-tasks", 8)],
    ids=["no_include_role_tasks_option", "include_role_tasks_option"],
)
def test_with_roles(
    request: pytest.FixtureRequest,
    include_role_tasks_option: str,
    expected_tasks_number: int,
) -> None:
    """Test with_roles.yml, an example with roles."""
    svg_path, playbook_paths = run_grapher(
        ["with_roles.yml"],
        output_filename=request.node.name,
        additional_args=[include_role_tasks_option],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=expected_tasks_number,
        post_tasks_number=2,
        roles_number=2,
        pre_tasks_number=2,
    )


@pytest.mark.parametrize(
    ("include_role_tasks_option", "expected_tasks_number"),
    [("--", 2), ("--include-role-tasks", 14)],
    ids=["no_include_role_tasks_option", "include_role_tasks_option"],
)
def test_include_role(
    request: pytest.FixtureRequest,
    include_role_tasks_option: str,
    expected_tasks_number: int,
) -> None:
    """Test include_role.yml, an example with include_role."""
    svg_path, playbook_paths = run_grapher(
        ["include_role.yml"],
        output_filename=request.node.name,
        additional_args=[include_role_tasks_option],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        blocks_number=1,
        tasks_number=expected_tasks_number,
        roles_number=6,
    )


def test_with_block(request: pytest.FixtureRequest) -> None:
    """Test with_block.yml, an example with roles."""
    svg_path, playbook_paths = run_grapher(
        ["with_block.yml"], output_filename=request.node.name
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=7,
        post_tasks_number=2,
        roles_number=1,
        pre_tasks_number=1,
        blocks_number=4,
    )


def test_nested_include_tasks(request: pytest.FixtureRequest) -> None:
    """Test nested_include.yml, an example with an include_tasks that include another tasks."""
    svg_path, playbook_paths = run_grapher(
        ["nested_include_tasks.yml"],
        output_filename=request.node.name,
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=3,
    )


@pytest.mark.parametrize(
    ("include_role_tasks_option", "expected_tasks_number"),
    [("--", 4), ("--include-role-tasks", 7)],
    ids=["no_include_role_tasks_option", "include_role_tasks_option"],
)
def test_import_role(
    request: pytest.FixtureRequest,
    include_role_tasks_option: str,
    expected_tasks_number: int,
) -> None:
    """Test import_role.yml, an example with import role.
    Import role is special because the tasks imported from role are treated as "normal tasks" when the playbook is parsed.
    """
    svg_path, playbook_paths = run_grapher(
        ["import_role.yml"],
        output_filename=request.node.name,
        additional_args=[include_role_tasks_option],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=expected_tasks_number,
        roles_number=1,
    )


def test_import_playbook(request: pytest.FixtureRequest) -> None:
    """Test import_playbook."""
    svg_path, playbook_paths = run_grapher(
        ["import_playbook.yml"],
        output_filename=request.node.name,
    )
    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=4,
        post_tasks_number=2,
        pre_tasks_number=2,
    )


@pytest.mark.parametrize(
    ("include_role_tasks_option", "expected_tasks_number"),
    [("--", 7), ("--include-role-tasks", 7)],
    ids=["no_include_role_tasks_option", "include_role_tasks_option"],
)
def test_nested_import_playbook(
    request: pytest.FixtureRequest,
    include_role_tasks_option: str,
    expected_tasks_number: int,
) -> None:
    """Test nested import playbook with an import_role and include_tasks."""
    svg_path, playbook_paths = run_grapher(
        ["nested_import_playbook.yml"],
        output_filename=request.node.name,
        additional_args=[include_role_tasks_option],
    )
    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=2,
        tasks_number=expected_tasks_number,
    )


def test_relative_var_files(request: pytest.FixtureRequest) -> None:
    """Test a playbook with a relative var file."""
    svg_path, playbook_paths = run_grapher(
        ["relative_var_files.yml"],
        output_filename=request.node.name,
    )
    res = _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=2,
    )

    # check if the plays title contains the interpolated variables
    assert (
        "Cristiano Ronaldo" in res["tasks"][0].find("g/a/text").text
    ), "The title should contain player name"
    assert (
        "Lionel Messi" in res["tasks"][1].find("g/a/text").text
    ), "The title should contain player name"


def test_tags(request: pytest.FixtureRequest) -> None:
    """Test a playbook by only graphing a specific tasks based on the given tags."""
    svg_path, playbook_paths = run_grapher(
        ["tags.yml"],
        output_filename=request.node.name,
        additional_args=["-t", "pre_task_tag_1"],
    )
    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        pre_tasks_number=1,
    )


def test_skip_tags(request: pytest.FixtureRequest) -> None:
    """Test a playbook by only graphing a specific tasks based on the given tags."""
    svg_path, playbook_paths = run_grapher(
        ["tags.yml"],
        output_filename=request.node.name,
        additional_args=["--skip-tags", "pre_task_tag_1", "--include-role-tasks"],
    )
    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        tasks_number=3,
        roles_number=1,
        pre_tasks_number=1,
    )


def test_multi_plays(request: pytest.FixtureRequest) -> None:
    """Test with multiple plays, include_role and roles."""
    svg_path, playbook_paths = run_grapher(
        ["multi-plays.yml"],
        output_filename=request.node.name,
        additional_args=["--include-role-tasks"],
    )
    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=3,
        tasks_number=25,
        post_tasks_number=2,
        roles_number=8,
        pre_tasks_number=2,
    )


def test_multi_playbooks(request: pytest.FixtureRequest) -> None:
    """Test with multiple playbooks."""
    svg_path, playbook_paths = run_grapher(
        ["multi-plays.yml", "relative_var_files.yml", "with_roles.yml"],
        output_filename=request.node.name,
        additional_args=["--include-role-tasks"],
    )
    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        playbooks_number=3,
        plays_number=5,
        pre_tasks_number=4,
        roles_number=10,
        tasks_number=35,
        post_tasks_number=4,
    )


def test_with_roles_with_custom_protocol_handlers(
    request: pytest.FixtureRequest,
) -> None:
    """Test with_roles.yml with a custom protocol handlers."""
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
        svg_filename=svg_path,
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
        assert r.find("g/a").get(xlink_ref_selector).startswith(str(DIR_PATH))


def test_community_download_roles_and_collection(
    request: pytest.FixtureRequest,
) -> None:
    """Test if the grapher is able to find some downloaded roles and collections when graphing the playbook
    :return:
    """
    run_grapher(
        ["docker-mysql-galaxy.yml"],
        output_filename=request.node.name,
        additional_args=["--include-role-tasks"],
    )


@pytest.mark.parametrize(
    ("flag", "roles_number", "tasks_number", "post_tasks_number"),
    [("--", 6, 9, 8), ("--group-roles-by-name", 3, 6, 2)],
    ids=["no_group", "group"],
)
def test_group_roles_by_name(
    request: pytest.FixtureRequest,
    flag: str,
    roles_number: int,
    tasks_number: int,
    post_tasks_number: int,
) -> None:
    """Test group roles by name
    :return:
    """
    svg_path, playbook_paths = run_grapher(
        ["group-roles-by-name.yml"],
        output_filename=request.node.name,
        additional_args=["--include-role-tasks", flag],
    )
    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        roles_number=roles_number,
        tasks_number=tasks_number,
        post_tasks_number=post_tasks_number,
        blocks_number=1,
    )


def test_hiding_plays(request: pytest.FixtureRequest) -> None:
    """Test hiding_plays with the flag --hide-empty-plays.

    This case is about hiding plays with zero tasks (no filtering)
    :param request:
    :return:
    """
    svg_path, playbook_paths = run_grapher(
        ["play-hiding.yml"],
        output_filename=request.node.name,
        additional_args=["--hide-empty-plays"],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=2,
        roles_number=2,
        tasks_number=1,
    )


def test_hiding_empty_plays_with_tags_filter(request: pytest.FixtureRequest) -> None:
    """Test hiding plays with the flag --hide-empty-plays.

    This case is about hiding plays when filtering with tags
    :param request:
    :return:
    """
    svg_path, playbook_paths = run_grapher(
        ["play-hiding.yml"],
        output_filename=request.node.name,
        additional_args=["--hide-empty-plays", "--tags", "play1"],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        roles_number=1,
    )


def test_hiding_empty_plays_with_tags_filter_all(
    request: pytest.FixtureRequest,
) -> None:
    """Test hiding plays with the flag --hide-empty-plays.

    This case is about hiding ALL the plays when filtering with tags
    :param request:
    :return:
    """
    svg_path, playbook_paths = run_grapher(
        ["play-hiding.yml"],
        output_filename=request.node.name,
        additional_args=[
            "--hide-empty-plays",
            "--tags",
            "fake-tag-that-does-not-exist",
            "--include-role-tasks",
        ],
    )

    _common_tests(svg_filename=svg_path, playbook_paths=playbook_paths)


def test_hiding_plays_without_roles(request: pytest.FixtureRequest) -> None:
    """Test hiding plays with the flag --hide-plays-without-roles.

    :param request:
    :return:
    """
    svg_path, playbook_paths = run_grapher(
        ["play-hiding.yml"],
        output_filename=request.node.name,
        additional_args=[
            "--hide-plays-without-roles",
        ],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=2,
        roles_number=2,
        tasks_number=1,
    )


def test_hiding_plays_without_roles_with_tags_filtering(
    request: pytest.FixtureRequest,
) -> None:
    """Test hiding plays with the flag --hide-plays-without-roles.

    Also apply some tag filters
    :param request:
    :return:
    """
    svg_path, playbook_paths = run_grapher(
        ["play-hiding.yml"],
        output_filename=request.node.name,
        additional_args=[
            "--hide-plays-without-roles",
            "--tags",
            "play1",
            "--include-role-tasks",
        ],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        roles_number=1,
        tasks_number=5,
    )


@pytest.mark.parametrize(
    "playbook",
    [
        "haidaram.test_collection.test",
        f"{Path('~/.ansible/collections/ansible_collections/haidaram/test_collection/playbooks/test.yml').expanduser()}",
    ],
)
def test_graphing_a_playbook_in_a_collection(
    request: pytest.FixtureRequest, playbook: str
) -> None:
    """Test graphing a playbook in a collection

    :param request:
    :return:
    """
    svg_path, playbook_paths = run_grapher(
        [playbook],
        output_filename=request.node.name,
        additional_args=[
            "--include-role-tasks",
        ],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        roles_number=2,
        tasks_number=6,
    )


@pytest.mark.parametrize(
    ("flag", "handlers_number"),
    [("--", 0), ("--show-handlers", 6)],
    ids=["no_handlers", "show_handlers"],
)
def test_handlers(
    request: pytest.FixtureRequest,
    flag: str,
    handlers_number: int,
) -> None:
    """Test graphing a playbook with handlers

    :param request:
    :return:
    """
    svg_path, playbook_paths = run_grapher(
        ["handlers.yml"], output_filename=request.node.name, additional_args=[flag]
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        pre_tasks_number=1,
        plays_number=2,
        tasks_number=6,
        handlers_number=handlers_number,
    )


@pytest.mark.parametrize(
    ("flag", "handlers_number"),
    [("--", 0), ("--show-handlers", 3)],
    ids=["no_handlers", "show_handlers"],
)
def test_handlers_in_role(
    request: pytest.FixtureRequest,
    flag: str,
    handlers_number: int,
) -> None:
    """Test graphing a playbook with handlers

    :param request:
    :return:
    """
    svg_path, playbook_paths = run_grapher(
        ["handlers-in-role.yml"],
        output_filename=request.node.name,
        additional_args=[
            "--include-role-tasks",
            flag,
        ],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        pre_tasks_number=1,
        plays_number=1,
        tasks_number=2,
        post_tasks_number=1,
        roles_number=1,
        handlers_number=handlers_number,
    )


@pytest.mark.parametrize(
    ("include_role_tasks_option", "expected_roles_number"),
    [("--", 4), ("--include-role-tasks", 6)],
    ids=["no_include_role_tasks_option", "include_role_tasks_option"],
)
def test_only_roles_with_nested_include_roles(
    request: pytest.FixtureRequest,
    include_role_tasks_option: str,
    expected_roles_number: int,
) -> None:
    """Test graphing a playbook with the --only-roles flag.

    :param request:
    :return:
    """
    svg_path, playbook_paths = run_grapher(
        ["nested-include-role.yml"],
        output_filename=request.node.name,
        additional_args=[
            "--only-roles",
            include_role_tasks_option,
        ],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        blocks_number=1,
        roles_number=expected_roles_number,
    )


def test_only_roles_with_nested_include_roles_with_a_tag(
    request: pytest.FixtureRequest,
) -> None:
    """Test graphing a playbook with the --only-roles flag and a tag

    :param request:
    :return:
    """
    svg_path, playbook_paths = run_grapher(
        ["nested-include-role.yml"],
        output_filename=request.node.name,
        additional_args=["--only-roles", "-t", "hello"],
    )

    _common_tests(
        svg_filename=svg_path,
        playbook_paths=playbook_paths,
        plays_number=1,
        blocks_number=1,
        roles_number=1,
    )
