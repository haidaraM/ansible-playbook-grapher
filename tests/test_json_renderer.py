import json
import os
from pathlib import Path

import jq
import pytest
from jsonschema import validate
from jsonschema.validators import Draft202012Validator

from ansibleplaybookgrapher import __prog__
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI
from tests import FIXTURES_DIR_PATH, INVENTORY_PATH

# This file directory abspath
DIR_PATH = Path(__file__).parent.resolve()


def run_grapher(
        playbooks: list[str],
        output_filename: str | None = None,
        additional_args: list[str] | None = None,
) -> tuple[str, list[str]]:
    """Utility function to run the grapher
    :param playbooks:
    :param output_filename:
    :param additional_args:
    :return:
    """
    additional_args = additional_args or []
    # Explicitly add verbosity to the tests
    additional_args.insert(0, "-vvv")

    if os.environ.get("TEST_VIEW_GENERATED_FILE") == "1":
        additional_args.insert(0, "--view")

    for idx, p_file in enumerate(playbooks):
        if ".yml" in p_file:
            playbooks[idx] = str(FIXTURES_DIR_PATH / p_file)

    args = [__prog__]

    # Clean the name a little bit
    output_filename = output_filename.replace("[", "-").replace("]", "")
    # put the generated file in a dedicated folder
    args.extend(["-o", str(DIR_PATH / "generated-jsons" / output_filename)])

    args.extend(["--renderer", "json"])
    args.extend(additional_args + playbooks)

    cli = PlaybookGrapherCLI(args)

    return cli.run(), playbooks


def _common_tests(
        json_path: str,
        playbooks_number: int = 1,
        plays_number: int = 0,
        tasks_number: int = 0,
        post_tasks_number: int = 0,
        roles_number: int = 0,
        pre_tasks_number: int = 0,
        blocks_number: int = 0,
) -> dict:
    """Do some checks on the generated json files.

    We are using JQ to avoid traversing the JSON ourselves (much easier).
    :param json_path:
    :return:
    """
    with Path(json_path).open() as f:
        output = json.load(f)

    with (FIXTURES_DIR_PATH / "json-schemas/v1.json").open() as schema_file:
        schema = json.load(schema_file)

    # If no exception is raised by validate(), the instance is valid.
    # I currently don't use format but added it here to not forget to add in case I use in the future.
    validate(
        instance=output,
        schema=schema,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )

    playbooks = jq.compile(".playbooks[]").input(output).all()

    plays = (
        jq.compile(
            '.. | objects | select(.type == "PlayNode" and (.id | startswith("play_")))',
        )
        .input(output)
        .all()
    )

    pre_tasks = (
        jq.compile(
            '.. | objects | select(.type == "TaskNode" and (.id | startswith("pre_task_")))',
        )
        .input(output)
        .all()
    )
    tasks = (
        jq.compile(
            '.. | objects | select(.type == "TaskNode" and (.id | startswith("task_")))',
        )
        .input(output)
        .all()
    )
    post_tasks = (
        jq.compile(
            '.. | objects | select(.type == "TaskNode" and (.id | startswith("post_task_")))',
        )
        .input(output)
        .all()
    )

    roles = (
        jq.compile(
            '.. | objects | select(.type == "RoleNode" and (.id | startswith("role_")))',
        )
        .input(output)
        .all()
    )

    blocks = (
        jq.compile(
            '.. | objects | select(.type == "BlockNode" and (.id | startswith("block_")))',
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


def test_simple_playbook(request: pytest.FixtureRequest) -> None:
    """:return:"""
    json_path, playbook_paths = run_grapher(
        ["simple_playbook.yml"],
        output_filename=request.node.name,
        additional_args=[
            "-i",
            str(INVENTORY_PATH),
            "--include-role-tasks",
        ],
    )
    _common_tests(json_path, plays_number=1, post_tasks_number=2)


def test_with_block(request: pytest.FixtureRequest) -> None:
    """:return:"""
    json_path, playbook_paths = run_grapher(
        ["with_block.yml"],
        output_filename=request.node.name,
        additional_args=[
            "-i",
            str(INVENTORY_PATH),
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
    ("flag", "roles_number", "tasks_number", "post_tasks_number"),
    [("--", 6, 9, 8), ("--group-roles-by-name", 6, 9, 8)],
    ids=["no_group", "group"],
)
def test_group_roles_by_name(
        request: pytest.FixtureRequest,
        flag: str,
        roles_number: int,
        tasks_number: int,
        post_tasks_number: int,
) -> None:
    """Test when grouping roles by name. This doesn't really affect the JSON renderer: multiple nodes will have the same ID.
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


def test_multi_playbooks(request: pytest.FixtureRequest) -> None:
    """:param request:
    :return:
    """
    json_path, playbook_paths = run_grapher(
        ["multi-plays.yml", "relative_var_files.yml", "with_roles.yml"],
        output_filename=request.node.name,
        additional_args=["--include-role-tasks"],
    )

    _common_tests(
        json_path,
        playbooks_number=3,
        plays_number=5,
        pre_tasks_number=4,
        roles_number=10,
        tasks_number=35,
        post_tasks_number=4,
    )
