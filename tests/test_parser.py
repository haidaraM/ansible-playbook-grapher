from typing import List

import pytest
from ansible.utils.display import Display

from ansibleplaybookgrapher import PlaybookParser
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI
from ansibleplaybookgrapher.graph import TaskNode, BlockNode, RoleNode, get_all_tasks_nodes, CompositeNode


def get_all_tasks(composites: List[CompositeNode]) -> List[TaskNode]:
    """

    :param composites:
    :return:
    """
    tasks = []

    for c in composites:
        tasks.extend(get_all_tasks_nodes(c))

    return tasks


@pytest.mark.parametrize('grapher_cli', [["include_role.yml"]], indirect=True)
def test_include_role_parsing(grapher_cli: PlaybookGrapherCLI, display: Display):
    """
    Test parsing of include_role
    :param grapher_cli:
    :param display:
    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbook_filename, display=display, include_role_tasks=True)
    playbook_node = parser.parse()
    assert len(playbook_node.plays) == 1
    play_node = playbook_node.plays[0].destination
    tasks = play_node.tasks
    assert len(tasks) == 5

    # first task
    assert tasks[0].destination.name == "(1) Debug"
    assert tasks[0].name == '[when: ansible_os == "ubuntu"]'

    # first include_role
    include_role_1 = tasks[1].destination
    assert isinstance(include_role_1, RoleNode)
    assert len(include_role_1.tasks) == 3

    # second task
    assert tasks[2].destination.name == "(3) Debug 2"

    # second include_role
    include_role_2 = tasks[3].destination
    assert tasks[3].name == "[when: x is not defined]"
    assert isinstance(include_role_2, RoleNode)
    assert len(include_role_2.tasks) == 3


@pytest.mark.parametrize('grapher_cli', [["with_block.yml"]], indirect=True)
def test_block_parsing(grapher_cli: PlaybookGrapherCLI, display: Display):
    """
    The parsing of a playbook with blocks
    :param grapher_cli:
    :param display:
    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbook_filename, display=display, include_role_tasks=True)
    playbook_node = parser.parse()
    assert len(playbook_node.plays) == 1

    play_node = playbook_node.plays[0].destination
    pre_tasks = play_node.pre_tasks
    tasks = play_node.tasks
    post_tasks = play_node.post_tasks
    total_pre_tasks = get_all_tasks(pre_tasks)
    total_tasks = get_all_tasks(tasks)
    total_post_tasks = get_all_tasks(post_tasks)
    assert len(total_pre_tasks) == 4, f"The play should contain 4 pre tasks but we found {len(total_pre_tasks)} pre task(s)"
    assert len(total_tasks) == 7, f"The play should contain 3 tasks but we found {len(total_tasks)} task(s)"
    assert len(
        total_post_tasks) == 2, f"The play should contain 2 post tasks but we found {len(total_post_tasks)} post task(s)"

    # Check pre tasks
    assert isinstance(pre_tasks[0].destination, RoleNode), "The first edge should have a RoleNode as destination"
    assert isinstance(pre_tasks[1].destination, BlockNode), "The second edge should have a BlockNode as destination"

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
    assert len(nested_block.tasks) == 2
    assert nested_block.tasks[0].destination.name == "get_url"
    assert nested_block.tasks[1].destination.name == "command"

    # Check the post task
    assert post_tasks[0].destination.name == "Debug"
