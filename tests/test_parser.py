from pathlib import Path

import pytest
from ansible.utils.display import Display

from ansibleplaybookgrapher.cli import PlaybookGrapherCLI
from ansibleplaybookgrapher.graph_model import (
    BlockNode,
    CompositeNode,
    Node,
    RoleNode,
    TaskNode,
)
from ansibleplaybookgrapher.parser import PlaybookParser
from tests import FIXTURES_DIR_PATH


def get_all_tasks(nodes: list[Node]) -> list[TaskNode]:
    """Recursively Get all tasks from a list of nodes
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


def get_all_roles(nodes: list[Node]) -> list[RoleNode]:
    """Recursively get all roles from a list of nodes
    :param nodes:
    :return:
    """
    roles = []

    for n in nodes:
        if isinstance(n, CompositeNode):
            roles.extend(n.get_all_roles())
        else:
            roles.append(n)

    return roles


@pytest.mark.parametrize("grapher_cli", [["example.yml"]], indirect=True)
def test_example_parsing(grapher_cli: PlaybookGrapherCLI, display: Display) -> None:
    """Test the parsing of example.yml
    :param grapher_cli:
    :param display:
    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbooks[0])
    playbook_node = parser.parse()
    assert len(playbook_node.plays()) == 1
    assert playbook_node.location.path == str(FIXTURES_DIR_PATH / "example.yml")
    assert playbook_node.location.line == 1
    assert playbook_node.location.column == 1
    assert (
        playbook_node.index is None
    ), "The index of the playbook should be None (it has no parent)"

    play_node = playbook_node.plays()[0]
    assert play_node.location.path == str(FIXTURES_DIR_PATH / "example.yml")
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
def test_with_roles_parsing(grapher_cli: PlaybookGrapherCLI) -> None:
    """Test the parsing of with_roles.yml
    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbooks[0])
    playbook_node = parser.parse()
    assert len(playbook_node.plays()) == 1
    play_node = playbook_node.plays()[0]
    assert play_node.index == 1

    assert len(play_node.roles) == 2

    fake_role = play_node.roles[0]
    assert isinstance(fake_role, RoleNode)
    assert not fake_role.include_role
    assert fake_role.location.path == str(FIXTURES_DIR_PATH / "roles" / "fake_role")
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
def test_include_role_parsing(
    grapher_cli: PlaybookGrapherCLI,
    capsys: pytest.CaptureFixture,
) -> None:
    """Test parsing of include_role
    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbooks[0],
        include_role_tasks=True,
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
    assert include_role_1.location.path == str(FIXTURES_DIR_PATH / "include_role.yml")
    assert (
        include_role_1.location.line == 10
    ), "The first include role should be at line 9"
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


@pytest.mark.parametrize("grapher_cli", [["group-roles-by-name.yml"]], indirect=True)
@pytest.mark.parametrize(
    ("include_role_tasks", "nested_include_role_tasks_count"), [(True, 4), (False, 0)]
)
def test_include_role_parsing_with_different_include_role_tasks(
    include_role_tasks: bool,
    nested_include_role_tasks_count: int,
    grapher_cli: PlaybookGrapherCLI,
) -> None:
    """Test parsing of include_role with different include_role_tasks options.

    :param include_role_tasks:
    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbooks[0],
        include_role_tasks=include_role_tasks,
    )
    playbook_node = parser.parse()
    assert len(playbook_node.plays()) == 1

    play_node = playbook_node.plays()[0]

    assert (
        len(play_node.roles) == 2
    ), "Two roles should be at the play level (the ones in the 'roles:' section)"

    # The first task of the play is an include role in the block
    assert len(play_node.tasks) == 1
    assert isinstance(play_node.tasks[0], BlockNode)
    assert isinstance(play_node.tasks[0].tasks[0], RoleNode)

    # The first post task is an include role as well but with nested include roles
    assert len(play_node.post_tasks) == 1
    assert isinstance(play_node.post_tasks[0], RoleNode)
    assert len(play_node.post_tasks[0].tasks) == nested_include_role_tasks_count


@pytest.mark.parametrize(
    "exclude_roles",
    [
        None,
        ([]),
        (["fake_role"]),
        (["fake_role", "display_some_facts"]),
    ],
    ids=["none", "empty_list", "exclude_single_role", "exclude_multiple_roles"],
)
@pytest.mark.parametrize("grapher_cli", [["include_role.yml"]], indirect=True)
def test_include_role_parsing_with_exclude_roles(
    grapher_cli: PlaybookGrapherCLI, exclude_roles: list[str]
) -> None:
    """Test parsing of include_role
    :param grapher_cli:
    :param exclude_roles: flag to exclude certain roles
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbooks[0],
        include_role_tasks=True,
        exclude_roles=exclude_roles,
    )
    playbook_node = parser.parse()

    # If the exclude roles option is set, then there should be no roles with the names identical to the option arguments
    if exclude_roles is not None:
        all_roles = get_all_roles([playbook_node])
        role_names = list(map(lambda role_node: role_node.name, all_roles))
        assert all(exclude_role not in role_names for exclude_role in exclude_roles)


@pytest.mark.parametrize("grapher_cli", [["include_role.yml"]], indirect=True)
def test_include_role_parsing_with_only_roles(
    grapher_cli: PlaybookGrapherCLI,
) -> None:
    """Test parsing of include_role with only roles option
    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbooks[0],
        include_role_tasks=True,
        only_roles=True,
    )
    playbook_node = parser.parse()

    # If only roles option is set then there should be no Task Nodes
    all_tasks = get_all_tasks([playbook_node])
    assert (
        len(all_tasks) == 0
    ), "There should be no Task Nodes when running with only roles option"


@pytest.mark.parametrize("grapher_cli", [["with_block.yml"]], indirect=True)
def test_block_parsing(grapher_cli: PlaybookGrapherCLI) -> None:
    """The parsing of a playbook with blocks
    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbooks[0],
        include_role_tasks=True,
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
        pre_tasks[0],
        RoleNode,
    ), "The first edge should have a RoleNode as destination"
    pre_task_block = pre_tasks[1]
    assert isinstance(
        pre_task_block,
        BlockNode,
    ), "The second edge should have a BlockNode as destination"
    assert pre_task_block.location.path == str(FIXTURES_DIR_PATH / "with_block.yml")
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

    # Check the post_tasks
    assert post_tasks[0].name == "Debug"
    assert post_tasks[0].index == 6


@pytest.mark.parametrize("grapher_cli", [["blocks_with_role.yml"]], indirect=True)
def test_block_with_roles_parsing(grapher_cli: PlaybookGrapherCLI) -> None:
    """Test the parsing of a playbook with blocks and roles.


    :param grapher_cli:
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbooks[0],
        include_role_tasks=True,
    )
    playbook_node = parser.parse()
    play = playbook_node.plays()[0]

    assert len(play.pre_tasks) == 1
    assert isinstance(play.pre_tasks[0], BlockNode)
    assert len(play.pre_tasks[0].tasks) == 1

    assert len(play.roles) == 1
    role = play.roles[0]
    assert len(role.tasks) == 4
    assert isinstance(role.tasks[1], BlockNode)
    assert len(role.tasks[1].tasks) == 1
    assert isinstance(role.tasks[3], BlockNode)
    assert len(role.tasks[3].tasks) == 1

    assert len(play.tasks) == 2
    assert isinstance(play.tasks[1], BlockNode)
    assert len(play.tasks[1].tasks) == 1


@pytest.mark.parametrize("grapher_cli", [["multi-plays.yml"]], indirect=True)
@pytest.mark.parametrize(
    (
        "group_roles_by_name",
        "roles_number",
        "nb_fake_role",
        "nb_display_some_facts",
        "nb_nested_include_role",
    ),
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
) -> None:
    """Test the role_usages method for multiple plays referencing the same roles.

    :param grapher_cli:
    :param roles_number: The number of uniq roles in the graph
    :param group_roles_by_name: flag to enable grouping roles or not
    :param nb_fake_role: number of usages for the role fake_role
    :param nb_display_some_facts: number of usages for the role display_some_facts
    :param nb_nested_include_role: number of usages for the role nested_include_role
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbooks[0],
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
        roles_usage,
    ), "The number of unique roles should be equal to the number of usages"

    for role, plays in roles_usage.items():
        assert all(
            (node.id.startswith("play_") for node in plays),
        ), "All nodes IDs should be play"

        nb_plays_for_the_role = len(plays)

        assert (
            expectation.get(role.name) == nb_plays_for_the_role
        ), f"The role '{role.name}' is used {nb_plays_for_the_role} times but we expect {expectation.get(role.name)}"


@pytest.mark.parametrize("grapher_cli", [["group-roles-by-name.yml"]], indirect=True)
@pytest.mark.parametrize(
    "group_roles_by_name",
    [(False,), (True,)],
    ids=["no_group", "group"],
)
def test_roles_usage_single_play(
    grapher_cli: PlaybookGrapherCLI,
    group_roles_by_name: bool,
) -> None:
    """Test the role_usages method for a single play using the same roles multiple times.

    The role usage should always be one regardless of the number of usages
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbooks[0],
        include_role_tasks=True,
        group_roles_by_name=group_roles_by_name,
    )
    playbook_node = parser.parse()
    roles_usage = playbook_node.roles_usage()
    for plays in roles_usage.values():
        assert len(plays) == 1, "The number of plays should be equal to 1"


@pytest.mark.parametrize("grapher_cli", [["roles_dependencies.yml"]], indirect=True)
def test_roles_dependencies(grapher_cli: PlaybookGrapherCLI) -> None:
    """Test if the role dependencies in meta/main.yml are included in the graph.
    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbooks[0],
        include_role_tasks=True,
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


@pytest.mark.parametrize(
    "grapher_cli", [["roles_argument_validation.yml"]], indirect=True
)
def test_roles_with_argument_validation(grapher_cli: PlaybookGrapherCLI) -> None:
    """Test if the task automatically added by ansible when setting the argument validation is parsed

    More info at https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#role-argument-validation

    :return:
    """
    parser = PlaybookParser(
        grapher_cli.options.playbooks[0],
        include_role_tasks=True,
    )
    playbook_node = parser.parse()
    roles = playbook_node.plays()[0].roles
    assert len(roles) == 1, "Only one explicit role is called inside the playbook"
    role_with_dependencies = roles[0]
    tasks = role_with_dependencies.tasks

    expected_tasks = 1 + 2  # 1 validation task added by ansible and 2 tasks in the role
    assert (
        len(tasks) == expected_tasks
    ), f"There should be {expected_tasks} tasks in the graph"


@pytest.mark.parametrize(
    "grapher_cli",
    [
        ["haidaram.test_collection.test"],
        [
            f"{Path('~/.ansible/collections/ansible_collections/haidaram/test_collection/playbooks/test.yml').expanduser()}"
        ],
    ],
    indirect=True,
)
def test_parsing_playbook_in_collection(
    grapher_cli: PlaybookGrapherCLI,
) -> None:
    """Test the parsing of a playbook in a collection from a collection name and from its absolute path.

    :param grapher_cli:
    :return:
    """
    playbook_path = grapher_cli.get_playbook_path(grapher_cli.options.playbooks[0])
    parser = PlaybookParser(
        playbook_path,
        include_role_tasks=True,
    )
    playbook_node = parser.parse()

    assert playbook_node.location.path == playbook_path
    assert playbook_node.location.line == 1
    assert playbook_node.location.column == 1
    assert len(playbook_node.plays()) == 1

    play = playbook_node.plays()[0]
    roles = play.roles
    assert len(roles) == 2, "Two roles should be in the play"

    all_tasks = get_all_tasks([playbook_node])
    assert (
        len(all_tasks) == 4 + 2
    ), "There should be 6 tasks in the playbook: 4 from the roles and 2 from the tasks at the playbook level"


@pytest.mark.parametrize("grapher_cli", [["handlers.yml"]], indirect=True)
def test_parsing_of_handlers(grapher_cli: PlaybookGrapherCLI) -> None:
    """Test if we are able to get the handlers in each play and add them in the graph
    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbooks[0])
    playbook_node = parser.parse()
    plays = playbook_node.plays()

    assert len(plays) == 2
    play_1, play_2 = playbook_node.plays()[0], playbook_node.plays()[1]

    assert len(play_1.pre_tasks) == 1, "The first play should have 1 pre_tasks"
    assert len(play_1.tasks) == 2, "The first play should have 2 tasks"

    play_1_expected_handlers = [
        "restart nginx",
        "restart mysql",
        "restart mysql in the pre_tasks",
    ]
    assert len(play_1.handlers) == len(play_1_expected_handlers)
    for idx, h in enumerate(play_1.handlers):
        assert (
            h.name == play_1_expected_handlers[idx]
        ), f"The handler should be '{play_1_expected_handlers[idx]}'"
        assert h.is_handler()

    # Second play
    assert len(play_2.tasks) == 4, "The second play should have 6 tasks"
    play_1_expected_handler = [
        "restart postgres",
        "stop traefik",
        "restart apache",
    ]
    assert len(play_2.handlers) == len(play_1_expected_handler)
    for idx, h in enumerate(play_2.handlers):
        assert (
            h.name == play_1_expected_handler[idx]
        ), f"The handler should be '{play_1_expected_handler[idx]}'"
        assert h.is_handler()
        assert h.location is not None


@pytest.mark.parametrize("grapher_cli", [["handlers-in-role.yml"]], indirect=True)
def test_parsing_handler_in_role(grapher_cli: PlaybookGrapherCLI) -> None:
    """Test if we are able to get the handlers defined in a role and add them in the graph
    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbooks[0], include_role_tasks=True)
    playbook_node = parser.parse()
    plays = playbook_node.plays()

    assert len(plays) == 1
    play = plays[0]
    assert len(play.handlers) == 1, "The play should have 1 handler"
    handler = play.handlers[0]
    assert handler.name == "restart postgres"

    assert len(play.roles) == 1, "The play should have 1 role"
    role = play.roles[0]
    assert len(role.tasks) == 1, "The role should have 1 task"
    assert len(role.handlers) == 1, "The role should have 1 handler"

    assert role.handlers[0].name == f"{role.name} : restart postgres from the role"
    assert role.handlers[0].location is not None

    assert (
        len(set(play.handlers + role.handlers)) == 2
    ), "The total number of handlers should be 2"
