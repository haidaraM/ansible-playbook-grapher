import json
import os
from typing import List, Tuple, Dict

import jq
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
    :param playbook_files:
    :param output_filename:
    :param additional_args:
    :return:
    """
    additional_args = additional_args or []
    # Explicitly add verbosity to the tests
    additional_args.insert(0, "-vvv")

    if os.environ.get("TEST_VIEW_GENERATED_FILE") == "1":
        additional_args.insert(0, "--view")

    playbook_paths = [os.path.join(FIXTURES_DIR, p_file) for p_file in playbook_files]
    args = [__prog__]

    # Clean the name a little bit
    output_filename = output_filename.replace("[", "-").replace("]", "")
    # put the generated file in a dedicated folder
    args.extend(["-o", os.path.join(DIR_PATH, "generated-jsons", output_filename)])

    args.extend(["--renderer", "json"])
    args.extend(additional_args + playbook_paths)

    cli = PlaybookGrapherCLI(args)

    return cli.run(), playbook_paths


def _common_tests(
    json_path: str,
    playbooks_number: int = 1,
    plays_number: int = 0,
    tasks_number: int = 0,
    post_tasks_number: int = 0,
    roles_number: int = 0,
    pre_tasks_number: int = 0,
    blocks_number: int = 0,
) -> Dict:
    """
    Do some checks on the generated json files.

    We are using JQ to avoid traversing the JSON ourselves (much easier).
    :param json_path:
    :return:
    """
    with open(json_path, "r") as f:
        output = json.load(f)

    playbooks = jq.compile(".playbooks[]").input(output).all()

    plays = jq.compile(".playbooks[].plays").input(output).first()
    pre_tasks = (
        jq.compile(
            '.playbooks[].plays[] | .. | objects | select(.type == "TaskNode" and (.id | startswith("pre_task_")))'
        )
        .input(output)
        .all()
    )
    tasks = (
        jq.compile(
            '.playbooks[].plays[] | .. | objects | select(.type == "TaskNode" and (.id | startswith("task_")))'
        )
        .input(output)
        .all()
    )
    post_tasks = (
        jq.compile(
            '.playbooks[].plays[] | .. | objects | select(.type == "TaskNode" and (.id | startswith("post_task_")))'
        )
        .input(output)
        .all()
    )

    roles = (
        jq.compile(
            '.playbooks[].plays[] | .. | objects | select(.type == "RoleNode" and (.id | startswith("role_")))'
        )
        .input(output)
        .all()
    )

    blocks = (
        jq.compile(
            '.playbooks[].plays[] | .. | objects | select(.type == "BlockNode" and (.id | startswith("block_")))'
        )
        .input(output)
        .all()
    )

    assert (
        len(playbooks) == playbooks_number
    ), f"The file '{json_path}' should contains {playbooks_number} playbook(s) but we found {len(playbooks)} playbook(s)"

    assert (
        len(plays) == plays_number
    ), f"The file '{json_path}' should contains {plays_number} play(s) but we found {len(plays)} play(s)"

    assert (
        len(pre_tasks) == pre_tasks_number
    ), f"The file '{json_path}' should contains {pre_tasks_number} pre tasks(s) but we found {len(pre_tasks)} pre tasks"

    assert (
        len(roles) == roles_number
    ), f"The file '{json_path}' should contains {roles_number} role(s) but we found {len(roles)} role(s)"

    assert (
        len(tasks) == tasks_number
    ), f"The file '{json_path}' should contains {tasks_number} tasks(s) but we found {len(tasks)} tasks"

    assert (
        len(post_tasks) == post_tasks_number
    ), f"The file '{json_path}' should contains {post_tasks_number} post tasks(s) but we found {len(post_tasks)} post tasks"

    assert (
        len(blocks) == blocks_number
    ), f"The file '{json_path}' should contains {blocks_number} block(s) but we found {len(blocks)} blocks"

    # Check the play
    for play in plays:
        assert (
            play.get("colors") is not None
        ), f"The play '{play['name']}' is missing colors'"

    return {
        "tasks": tasks,
        "plays": plays,
        "post_tasks": post_tasks,
        "pre_tasks": pre_tasks,
        "roles": roles,
        "blocks": blocks,
    }


def test_simple_playbook(request):
    """

    :return:
    """
    json_path, playbook_paths = run_grapher(
        ["simple_playbook.yml"],
        output_filename=request.node.name,
        additional_args=[
            "-i",
            os.path.join(FIXTURES_DIR, "inventory"),
            "--include-role-tasks",
        ],
    )
    _common_tests(json_path, plays_number=1, post_tasks_number=2)


def test_with_block(request):
    """

    :return:
    """
    json_path, playbook_paths = run_grapher(
        ["with_block.yml"],
        output_filename=request.node.name,
        additional_args=[
            "-i",
            os.path.join(FIXTURES_DIR, "inventory"),
            "--include-role-tasks",
        ],
    )
    _common_tests(
        json_path,
        plays_number=1,
        pre_tasks_number=4,
        roles_number=1,
        tasks_number=7,
        blocks_number=4,
        post_tasks_number=2,
    )


@pytest.mark.parametrize(
    ["flag", "roles_number", "tasks_number", "post_tasks_number"],
    [("--", 6, 9, 8), ("--group-roles-by-name", 6, 9, 8)],
    ids=["no_group", "group"],
)
def test_group_roles_by_name(
    request, flag, roles_number, tasks_number, post_tasks_number
):
    """
    Test when grouping roles by name. This doesn't really affect the JSON renderer: multiple nodes will have the same ID.
    This test ensures that regardless of the flag '--group-roles-by-name', we get the same nodes in the output.
    :param request:
    :return:
    """
    json_path, playbook_paths = run_grapher(
        ["group-roles-by-name.yml"],
        output_filename=request.node.name,
        additional_args=["--include-role-tasks", flag],
    )

    _common_tests(
        json_path,
        plays_number=1,
        roles_number=roles_number,
        tasks_number=tasks_number,
        post_tasks_number=post_tasks_number,
        blocks_number=1,
    )
