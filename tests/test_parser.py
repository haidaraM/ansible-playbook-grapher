import os
from typing import List

import pytest
from ansible.utils.display import Display

from ansibleplaybookgrapher import PlaybookParser
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI
from ansibleplaybookgrapher.graph import (
    TaskNode,
    BlockNode,
    RoleNode,
    get_all_tasks_nodes,
    CompositeNode,
)
from tests import FIXTURES_DIR

# This file directory abspath
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
# Fixtures abspath
FIXTURES_PATH = os.path.join(DIR_PATH, FIXTURES_DIR)


def get_all_tasks(composites: List[CompositeNode]) -> List[TaskNode]:
    """
    Get all tasks from a list of composite nodes
    :param composites:
    :return:
    """
    tasks = []

    for c in composites:
        tasks.extend(get_all_tasks_nodes(c))

    return tasks


@pytest.mark.parametrize("grapher_cli", [["example.yml"]], indirect=True)
def test_example_parsing(grapher_cli: PlaybookGrapherCLI, display: Display):
    """
    Test the parsing of example.yml
    :param grapher_cli:
    :param display:
    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbook_filename)
    playbook_node = parser.parse()
    assert len(playbook_node.plays) == 1
    assert playbook_node.path == os.path.join(FIXTURES_PATH, "example.yml")
    assert playbook_node.line == 1
    assert playbook_node.column == 1

    play_node = playbook_node.plays[0].destination
    assert play_node.path == os.path.join(FIXTURES_PATH, "example.yml")
    assert play_node.line == 2

    pre_tasks = play_node.pre_tasks
    tasks = play_node.tasks
    post_tasks = play_node.post_tasks
    assert len(pre_tasks) == 2
    assert len(tasks) == 4
    assert len(post_tasks) == 2


@pytest.mark.parametrize("grapher_cli", [["with_roles.yml"]], indirect=True)
def test_with_roles_parsing(grapher_cli: PlaybookGrapherCLI):
    """
    Test the parsing of with_roles.yml
    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbook_filename)
    playbook_node = parser.parse()
    assert len(playbook_node.plays) == 1
    play_node = playbook_node.plays[0].destination
    assert len(play_node.roles) == 2

    fake_role = play_node.roles[0].destination
    assert isinstance(fake_role, RoleNode)
    assert not fake_role.include_role
    assert fake_role.path == os.path.join(FIXTURES_PATH, "roles", "fake_role")
    assert fake_role.line is None
    assert fake_role.column is None


@pytest.mark.parametrize("grapher_cli", [["include_role.yml"]], indirect=True)
def test_include_role_parsing(grapher_cli: PlaybookGrapherCLI, capsys):
    """
    Test parsing of include_role
    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbook_filename, include_role_tasks=True
    )
    playbook_node = parser.parse()
    assert len(playbook_node.plays) == 1
    play_node = playbook_node.plays[0].destination
    tasks = play_node.tasks
    assert len(tasks) == 6

    # Since we use some loops inside the playbook, a warning should be displayed
    assert (
        "Looping on tasks or roles are not supported for the moment"
        in capsys.readouterr().err
    ), "A warning should be displayed regarding loop being not supported"

    # first include_role
    include_role_1 = tasks[0].destination
    assert isinstance(include_role_1, RoleNode)
    assert include_role_1.include_role
    assert include_role_1.path == os.path.join(FIXTURES_PATH, "include_role.yml")
    assert include_role_1.line == 6
    assert (
        len(include_role_1.tasks) == 0
    ), "We don't support adding tasks from include_role with loop"

    # first task
    assert tasks[1].destination.name == "(1) Debug"
    assert tasks[1].name == '[when: ansible_os == "ubuntu"]'

    # second include_role
    include_role_2 = tasks[2].destination
    assert isinstance(include_role_2, RoleNode)
    assert include_role_2.include_role
    assert len(include_role_2.tasks) == 3

    # second task
    assert tasks[3].destination.name == "(3) Debug 2"

    # third include_role
    include_role_3 = tasks[4].destination
    assert tasks[4].name == "[when: x is not defined]"
    assert isinstance(include_role_3, RoleNode)
    assert include_role_3.include_role
    assert len(include_role_3.tasks) == 3

    # fourth include_role
    include_role_4 = tasks[5].destination
    assert isinstance(include_role_4, RoleNode)
    assert include_role_4.include_role
    assert (
        len(include_role_4.tasks) == 0
    ), "We don't support adding tasks from include_role with loop"


@pytest.mark.parametrize("grapher_cli", [["with_block.yml"]], indirect=True)
def test_block_parsing(grapher_cli: PlaybookGrapherCLI):
    """
    The parsing of a playbook with blocks
    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbook_filename, include_role_tasks=True
    )
    playbook_node = parser.parse()
    assert len(playbook_node.plays) == 1

    play_node = playbook_node.plays[0].destination
    pre_tasks = play_node.pre_tasks
    tasks = play_node.tasks
    post_tasks = play_node.post_tasks
    total_pre_tasks = get_all_tasks(pre_tasks)
    total_tasks = get_all_tasks(tasks)
    total_post_tasks = get_all_tasks(post_tasks)
    assert (
        len(total_pre_tasks) == 4
    ), f"The play should contain 4 pre tasks but we found {len(total_pre_tasks)} pre task(s)"
    assert (
        len(total_tasks) == 7
    ), f"The play should contain 3 tasks but we found {len(total_tasks)} task(s)"
    assert (
        len(total_post_tasks) == 2
    ), f"The play should contain 2 post tasks but we found {len(total_post_tasks)} post task(s)"

    # Check pre tasks
    assert isinstance(
        pre_tasks[0].destination, RoleNode
    ), "The first edge should have a RoleNode as destination"
    pre_task_block = pre_tasks[1].destination
    assert isinstance(
        pre_task_block, BlockNode
    ), "The second edge should have a BlockNode as destination"
    assert pre_task_block.path == os.path.join(FIXTURES_PATH, "with_block.yml")
    assert pre_task_block.line == 7

    # Check tasks
    task_1 = tasks[0].destination
    assert isinstance(task_1, TaskNode)
    assert task_1.name == "Install tree"

    # Check the second task: the first block
    first_block = tasks[1].destination
    assert isinstance(first_block, BlockNode)
    assert first_block.name == "Install Apache"
    assert len(first_block.tasks) == 4

    # Check the second block (nested block)
    nested_block = first_block.tasks[2].destination
    assert isinstance(nested_block, BlockNode)
    assert len(nested_block.tasks) == 2
    assert nested_block.tasks[0].destination.name == "get_url"
    assert nested_block.tasks[1].destination.name == "command"

    # Check the post task
    assert post_tasks[0].destination.name == "Debug"
