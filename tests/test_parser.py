import os
from typing import List

import pytest
from ansible.utils.display import Display

from ansibleplaybookgrapher.parser import PlaybookParser
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI
from ansibleplaybookgrapher.graph_model import (
    TaskNode,
    BlockNode,
    RoleNode,
    Node,
    CompositeNode,
)
from tests import FIXTURES_DIR

# This file directory abspath
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
# Fixtures abspath
FIXTURES_PATH = os.path.join(DIR_PATH, FIXTURES_DIR)


def get_all_tasks(nodes: List[Node]) -> List[TaskNode]:
    """
    Recursively Get all tasks from a list of nodes
    :param nodes:
    :return:
    """
    tasks = []

    for n in nodes:
        if isinstance(n, CompositeNode):
            tasks.extend(n.get_all_tasks())
        else:
            tasks.append(n)

    return tasks


@pytest.mark.parametrize("grapher_cli", [["example.yml"]], indirect=True)
def test_example_parsing(grapher_cli: PlaybookGrapherCLI, display: Display):
    """
    Test the parsing of example.yml
    :param grapher_cli:
    :param display:
    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbook_filenames[0])
    playbook_node = parser.parse()
    assert len(playbook_node.plays()) == 1
    assert playbook_node.location.path == os.path.join(FIXTURES_PATH, "example.yml")
    assert playbook_node.location.line == 1
    assert playbook_node.location.column == 1
    assert (
        playbook_node.index is None
    ), "The index of the playbook should be None (it has no parent)"

    play_node = playbook_node.plays()[0]
    assert play_node.location.path == os.path.join(FIXTURES_PATH, "example.yml")
    assert play_node.location.line == 2
    assert play_node.index == 1

    pre_tasks = play_node.pre_tasks
    assert len(pre_tasks) == 2
    assert pre_tasks[0].index == 1, "The index of the first pre_task should be 1"
    assert pre_tasks[1].index == 2, "The index of the second pre_task should be 2"

    tasks = play_node.tasks
    assert len(tasks) == 4
    for task_counter, task in enumerate(tasks):
        assert (
            task.index == task_counter + len(pre_tasks) + 1
        ), "The index of the task should start after the pre_tasks"

    post_tasks = play_node.post_tasks
    assert len(post_tasks) == 2
    for post_task_counter, task in enumerate(post_tasks):
        assert (
            task.index == post_task_counter + len(pre_tasks) + len(tasks) + 1
        ), "The index of the post task should start after the pre_tasks and tasks"


@pytest.mark.parametrize("grapher_cli", [["with_roles.yml"]], indirect=True)
def test_with_roles_parsing(grapher_cli: PlaybookGrapherCLI):
    """
    Test the parsing of with_roles.yml
    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbook_filenames[0])
    playbook_node = parser.parse()
    assert len(playbook_node.plays()) == 1
    play_node = playbook_node.plays()[0]
    assert play_node.index == 1

    assert len(play_node.roles) == 2

    fake_role = play_node.roles[0]
    assert isinstance(fake_role, RoleNode)
    assert not fake_role.include_role
    assert fake_role.location.path == os.path.join(FIXTURES_PATH, "roles", "fake_role")
    assert fake_role.location.line is None
    assert fake_role.location.column is None
    assert fake_role.index == 3

    for task_counter, task in enumerate(fake_role.tasks):
        assert (
            task.index == task_counter + 1
        ), "The index of the task in the role should start at 1"

    display_some_facts = play_node.roles[1]
    for task_counter, task in enumerate(display_some_facts.tasks):
        assert (
            task.index == task_counter + 1
        ), "The index of the task in the role the should start at 1"


@pytest.mark.parametrize("grapher_cli", [["include_role.yml"]], indirect=True)
def test_include_role_parsing(grapher_cli: PlaybookGrapherCLI, capsys):
    """
    Test parsing of include_role
    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbook_filenames[0], include_role_tasks=True
    )
    playbook_node = parser.parse()
    assert len(playbook_node.plays()) == 1
    play_node = playbook_node.plays()[0]
    tasks = play_node.tasks
    assert len(tasks) == 6

    # Since we use some loops inside the playbook, a warning should be displayed
    assert (
        "Looping on tasks or roles are not supported for the moment"
        in capsys.readouterr().err
    ), "A warning should be displayed regarding loop being not supported"

    # first include_role using a block
    block_include_role = tasks[0]
    assert isinstance(block_include_role, BlockNode)
    include_role_1 = block_include_role.tasks[0]
    assert isinstance(include_role_1, RoleNode)
    assert include_role_1.include_role
    assert include_role_1.location.path == os.path.join(FIXTURES_PATH, "include_role.yml")
    assert include_role_1.location.line == 10, "The first include role should be at line 9"
    assert (
        len(include_role_1.tasks) == 0
    ), "We don't support adding tasks from include_role with loop"
    assert include_role_1.has_loop(), "The first include role has a loop"

    # first task
    assert tasks[1].name == "(1) Debug"
    assert tasks[1].when == '[when: ansible_os == "ubuntu"]'

    # second include_role
    include_role_2 = tasks[2]
    assert isinstance(include_role_2, RoleNode)
    assert include_role_2.include_role
    assert len(include_role_2.tasks) == 3
    assert not include_role_2.has_loop(), "The second include role doesn't have a loop"

    # second task
    assert tasks[3].name == "(3) Debug 2"

    # third include_role
    include_role_3 = tasks[4]
    assert tasks[4].when == "[when: x is not defined]"
    assert isinstance(include_role_3, RoleNode)
    assert include_role_3.include_role
    assert len(include_role_3.tasks) == 3
    assert not include_role_3.has_loop(), "The second include role doesn't have a loop"

    # fourth include_role
    include_role_4 = tasks[5]
    assert isinstance(include_role_4, RoleNode)
    assert include_role_4.include_role
    assert (
        len(include_role_4.tasks) == 0
    ), "We don't support adding tasks from include_role with loop"
    assert include_role_4.has_loop(), "The third include role has a loop"


@pytest.mark.parametrize("grapher_cli", [["with_block.yml"]], indirect=True)
def test_block_parsing(grapher_cli: PlaybookGrapherCLI):
    """
    The parsing of a playbook with blocks
    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbook_filenames[0], include_role_tasks=True
    )
    playbook_node = parser.parse()
    assert len(playbook_node.plays()) == 1

    play_node = playbook_node.plays()[0]
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
        pre_tasks[0], RoleNode
    ), "The first edge should have a RoleNode as destination"
    pre_task_block = pre_tasks[1]
    assert isinstance(
        pre_task_block, BlockNode
    ), "The second edge should have a BlockNode as destination"
    assert pre_task_block.location.path == os.path.join(FIXTURES_PATH, "with_block.yml")
    assert pre_task_block.location.line == 7

    # Check tasks
    task_1 = tasks[0]
    assert isinstance(task_1, TaskNode)
    assert task_1.name == "Install tree"

    # Check the second task: the first block
    first_block = tasks[1]
    assert isinstance(first_block, BlockNode)
    assert first_block.name == "Install Apache"
    assert len(first_block.tasks) == 4
    assert first_block.index == 4
    for task_counter, task in enumerate(first_block.tasks):
        assert (
            task.index == task_counter + 1
        ), "The index of the task in the block should start at 1"

    assert first_block.tasks[0].name == "Install some packages"
    assert first_block.tasks[0].has_loop(), "The task has a 'with_items'"

    # Check the second block (nested block)
    nested_block = first_block.tasks[2]
    assert isinstance(nested_block, BlockNode)
    assert len(nested_block.tasks) == 2
    assert nested_block.tasks[0].name == "get_url"
    assert nested_block.tasks[1].name == "command"
    assert nested_block.index == 3

    for task_counter, task in enumerate(nested_block.tasks):
        assert (
            task.index == task_counter + 1
        ), "The index of the task in the block should start at 1"

    # Check the post task
    assert post_tasks[0].name == "Debug"
    assert post_tasks[0].index == 6


@pytest.mark.parametrize("grapher_cli", [["multi-plays.yml"]], indirect=True)
@pytest.mark.parametrize(
    [
        "group_roles_by_name",
        "roles_number",
        "nb_fake_role",
        "nb_display_some_facts",
        "nb_nested_include_role",
    ],
    [(False, 8, 1, 1, 1), (True, 3, 3, 3, 1)],
    ids=["no_group", "group"],
)
def test_roles_usage_multi_plays(
    grapher_cli: PlaybookGrapherCLI,
    roles_number: int,
    group_roles_by_name: bool,
    nb_fake_role: int,
    nb_display_some_facts: int,
    nb_nested_include_role: int,
):
    """
    Test the role_usages method for multiple plays referencing the same roles
    :param grapher_cli:
    :param roles_number: The number of uniq roles in the graph
    :param group_roles_by_name: flag to enable grouping roles or not
    :param nb_fake_role: number of usages for the role fake_role
    :param nb_display_some_facts: number of usages for the role display_some_facts
    :param nb_nested_include_role: number of usages for the role nested_include_role
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbook_filenames[0],
        include_role_tasks=True,
        group_roles_by_name=group_roles_by_name,
    )
    playbook_node = parser.parse()
    roles_usage = playbook_node.roles_usage()

    expectation = {
        "fake_role": nb_fake_role,
        "display_some_facts": nb_display_some_facts,
        "nested_include_role": nb_nested_include_role,
    }

    assert roles_number == len(
        roles_usage
    ), "The number of unique roles should be equal to the number of usages"

    for role, plays in roles_usage.items():
        assert all(
            map(lambda node: node.id.startswith("play_"), plays)
        ), "All nodes IDs should be play"

        nb_plays_for_the_role = len(plays)

        assert (
            expectation.get(role.name) == nb_plays_for_the_role
        ), f"The role '{role.name}' is used {nb_plays_for_the_role} times but we expect {expectation.get(role.name)}"


@pytest.mark.parametrize("grapher_cli", [["group-roles-by-name.yml"]], indirect=True)
@pytest.mark.parametrize(
    [
        "group_roles_by_name",
    ],
    [(False,), (True,)],
    ids=["no_group", "group"],
)
def test_roles_usage_single_play(
    grapher_cli: PlaybookGrapherCLI, group_roles_by_name: bool
):
    """
    Test the role_usages method for a single play using the same roles multiple times.
    The role usage should always be one regardless of the number of usages
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbook_filenames[0],
        include_role_tasks=True,
        group_roles_by_name=group_roles_by_name,
    )
    playbook_node = parser.parse()
    roles_usage = playbook_node.roles_usage()
    for role, plays in roles_usage.items():
        assert len(plays) == 1, "The number of plays should be equal to 1"


@pytest.mark.parametrize("grapher_cli", [["roles_dependencies.yml"]], indirect=True)
def test_roles_dependencies(grapher_cli: PlaybookGrapherCLI):
    """
    Test if the role dependencies in meta/main.yml are included in the graph
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbook_filenames[0], include_role_tasks=True
    )
    playbook_node = parser.parse()
    roles = playbook_node.plays()[0].roles
    assert len(roles) == 1, "Only one explicit role is called inside the playbook"
    role_with_dependencies = roles[0]
    tasks = role_with_dependencies.tasks

    expected_tasks = 5
    dependant_role_name = "fake_role"
    assert (
        len(tasks) == expected_tasks
    ), f"There should be {expected_tasks} tasks in the graph"
    # The first 3 tasks are coming from the dependency
    for task_from_dependency in tasks[:3]:
        assert (
            dependant_role_name in task_from_dependency.name
        ), f"The task name should include the dependant role name '{dependant_role_name}'"
