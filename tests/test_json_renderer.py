import json
import os
from typing import List, Tuple, Dict

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

    args.extend(additional_args)

    args.extend(["--renderer", "json"])

    args.extend(playbook_paths)

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
    Do some checks on the generated json files
    :param json_path:
    :return:
    """
    with open(json_path, "r") as f:
        output = json.load(f)

    playbooks = output["playbooks"]
    assert (
        len(playbooks) == playbooks_number
    ), f"The file '{json_path}' should contains {playbooks_number} playbook(s) but we found {len(playbooks)} playbook(s)"

    plays = []
    tasks = []
    post_tasks = []
    pre_tasks = []
    roles = []
    for playbook in playbooks:
        plays.extend(playbook["plays"])

    for play in plays:
        tasks.extend(play["tasks"])
        post_tasks.extend(play["post_tasks"])
        pre_tasks.extend(play["pre_tasks"])
        roles.extend(play["roles"])

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

    return output


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
