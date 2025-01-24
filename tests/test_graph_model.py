from ansibleplaybookgrapher.graph_model import (
    BlockNode,
    HandlerNode,
    PlaybookNode,
    PlayNode,
    RoleNode,
    TaskNode,
)


def test_links_structure() -> None:
    """Test links structure of a graph

    :return:
    """
    play = PlayNode("composite_node")

    # play -> role -> task 1 and 2
    role = RoleNode("my_role_1")
    play.add_node("roles", role)
    task_1 = TaskNode("task 1")
    role.add_node("tasks", task_1)
    task_2 = TaskNode("task 2")
    role.add_node("tasks", task_2)

    # play -> task 3
    task_3 = TaskNode("task 3")
    play.add_node("tasks", task_3)

    all_links = play.links_structure()
    assert len(all_links) == 2, "The links should contains only 2 elements"

    assert len(all_links[play]) == 2, "The play should be linked to 2 nodes"
    for n in [role, task_3]:
        assert n in all_links[play], f"The play should be linked to the task '{task_1}'"

    assert len(all_links[role]) == 2, "The role should be linked to two nodes"
    for n in [task_1, task_2]:
        assert n in all_links[role], f"The role should be linked to the node '{n}'"


def test_links_structure_with_handlers() -> None:
    """Test links structure of a graph with handlers

    :return:
    """
    play = PlayNode("composite_node")
    play.add_node("handlers", HandlerNode("handler 1"))
    play.add_node("handlers", HandlerNode("handler 2"))
    play.add_node(
        "handlers",
        HandlerNode("handler 3", listen=["topic"], notify=["handler 1"]),
    )

    # play -> role -> task 1 and 2
    role = RoleNode("my_role_1")
    play.add_node("roles", role)
    # task 1 -> handler 1
    task_1 = TaskNode("task 1", notify=["handler 1"])
    role.add_node("tasks", task_1)
    # task 2 -> handler 2
    task_2 = TaskNode("task 2", notify=["handler 2"])
    role.add_node("tasks", task_2)

    # play -> task 3 -> handler 3 via the listen 'topic'
    task_3 = TaskNode("task 3", notify=["topic"])
    play.add_node("tasks", task_3)

    all_links = play.links_structure()

    play_links = all_links[play]
    assert (
        len(play_links) == 5
    ), "The play should be linked to 5 nodes: 1 role, 1 task, 3 handlers"

    role_links = all_links[role]
    assert len(role_links) == 2, "The role should be linked to 2 nodes"
    for n in [task_1, task_2]:
        assert n in role_links, f"The role should be linked to the node '{n}'"

    assert all_links[task_1] == [
        play.handlers[0]
    ], "Task 1 should be linked to handler 1"
    assert all_links[task_2] == [
        play.handlers[1]
    ], "Task 2 should be linked to handler 2"
    assert all_links[task_3] == [
        play.handlers[2]
    ], "Task 3 should be linked to handler 3"

    assert all_links[play.handlers[2]] == [
        play.handlers[0]
    ], "Handler 3 should be linked to handler 1"

    print(all_links)


def test_empty_play_method() -> None:
    """Testing the emptiness of a play
    :return:
    """
    play = PlayNode("play")
    assert play.is_empty(), "The play should empty"

    role = RoleNode("my_role_1")
    play.add_node("roles", role)
    assert play.is_empty(), "The play should still be empty given the role is empty"

    task = TaskNode("Block 1")
    play.add_node("tasks", task)
    assert not play.is_empty(), "The play should not be empty here"
    play.remove_node("tasks", task)
    assert task.parent is None, "The task should not have a parent anymore"
    assert play.is_empty(), "The play should be empty again"

    role.add_node("tasks", TaskNode("task 1"))
    assert not play.is_empty(), "The play should not be empty here"


def test_remove_empty_plays() -> None:
    """Test removing empty plays from a playbook

    :return:
    """
    playbook = PlaybookNode("my-playbook.yml")
    playbook.add_node("plays", PlayNode("empty"))
    assert len(playbook.plays) == 1, "There should be only one play"
    playbook.remove_empty_plays()
    assert len(playbook.plays) == 0, "There should be no play"

    play = PlayNode("play")
    playbook.add_node("plays", play)
    play.add_node("tasks", TaskNode("task 1"))
    playbook.remove_empty_plays()
    assert len(playbook.plays) == 1, "There should be only one play"


def test_remove_plays_without_roles() -> None:
    """Test removing plays without roles from a playbook

    :return:
    """
    playbook = PlaybookNode("my-playbook.yml")
    play_1 = PlayNode("play 1")
    play_2 = PlayNode("play 2")
    play_1.add_node("roles", RoleNode("role 1"))
    playbook.add_node("plays", play_1)
    playbook.add_node("plays", play_2)

    assert len(playbook.plays) == 2, "There should be 2 plays"
    assert not play_1.is_hidden
    assert not play_2.is_hidden
    playbook.hide_plays_without_roles()
    assert not play_1.is_hidden
    assert play_2.is_hidden


def test_get_all_tasks_nodes() -> None:
    """Test the function get_all_tasks_nodes
    :return:
    """
    play = PlayNode("play")
    role_1 = RoleNode("my_role_1")
    play.add_node("roles", role_1)

    # play -> role 1 -> edge 1 -> task 1
    task_1 = TaskNode("task 1")
    role_1.add_node("tasks", task_1)

    # play -> block_1 -> task 2 and task 3
    block_1 = BlockNode("block 1")
    task_2 = TaskNode("task 2")
    task_3 = TaskNode("task 3")
    block_1.add_node("tasks", task_2)
    block_1.add_node("tasks", task_3)
    play.add_node("tasks", block_1)
    # play -> block_1 -> block_2 -> task 4
    block_2 = BlockNode("block 2")
    task_4 = TaskNode("task 4")
    block_2.add_node("tasks", task_4)
    block_1.add_node("tasks", block_2)

    all_tasks = play.get_all_tasks()
    assert len(all_tasks) == 4, "There should be 4 tasks in all"
    assert [task_1, task_2, task_3, task_4] == all_tasks


def test_has_node_type() -> None:
    """Testing the method has_node_type
    :return:
    """
    play = PlayNode("play")
    block = BlockNode("block 1")
    role = RoleNode("my_role")
    role.add_node("tasks", TaskNode("task 1"))

    block.add_node("tasks", role)
    play.add_node("tasks", block)

    assert play.has_node_type(BlockNode), "The play should have BlockNode"
    assert play.has_node_type(RoleNode), "The play should have a RoleNode"
    assert play.has_node_type(TaskNode), "The play should have a TaskNode"

    assert not role.has_node_type(BlockNode), "The role doesn't have a BlockNode"


def test_to_dict() -> None:
    """
    :return:
    """
    playbook = PlaybookNode("my-fake-playbook.yml")
    playbook.add_node("plays", PlayNode("empty"))

    role = RoleNode("my_role")
    role.add_node("tasks", TaskNode("task 1"))

    block = BlockNode("block 1")
    block.add_node("tasks", role)

    play = PlayNode("play")
    play.add_node("tasks", block)
    play.add_node("post_tasks", TaskNode("task 2"))
    playbook.add_node("plays", play)

    playbook.calculate_indices()

    playbook.remove_empty_plays()
    dict_rep = playbook.to_dict()

    assert dict_rep["type"] == "PlaybookNode"
    assert dict_rep["location"] is None, "A fake playbook does not have a location"

    assert len(dict_rep["plays"]) == 1
    assert dict_rep["plays"][0]["type"] == "PlayNode"
    assert dict_rep["plays"][0]["colors"]["font"] == "#ffffff"

    assert dict_rep["plays"][0]["name"] == "play"
    assert dict_rep["plays"][0]["tasks"][0]["name"] == "block 1"
    assert dict_rep["plays"][0]["tasks"][0]["index"] == 1
    assert dict_rep["plays"][0]["tasks"][0]["type"] == "BlockNode"


def test_role_to_dict_with_exclusion():
    """
    Test the method to_dict of the RoleNode
    :return:
    """
    role = RoleNode("my_role")
    role.add_node("tasks", TaskNode("task 1"))
    role.add_node("tasks", TaskNode("task 2"))

    dict_rep = role.to_dict(include_role_tasks=True)

    assert dict_rep["type"] == "RoleNode"
    assert dict_rep["name"] == "my_role"
    assert dict_rep["tasks"][0]["name"] == "task 1"
    assert dict_rep["tasks"][1]["name"] == "task 2"

    dict_rep = role.to_dict()
    assert dict_rep["type"] == "RoleNode"
    assert dict_rep["name"] == "my_role"
    assert len(dict_rep["tasks"]) == 0


def test_remove_node_types():
    """
    Test the method remove_node_types
    :return:
    """
    playbook = PlaybookNode("my-fake-playbook.yml")
    play = PlayNode("play")
    playbook.add_node("plays", play)

    role = RoleNode("my_role")
    role.add_node("tasks", TaskNode("task 1"))
    play.add_node("roles", role)
    assert len(playbook.plays) == 1
    assert len(play.roles) == 1, "The role should be there"
    assert len(playbook.get_all_tasks()) == 1, "The task should be there"

    playbook.remove_all_nodes_types([RoleNode])
    assert len(playbook.plays) == 1
    assert len(play.roles) == 0, "The role should have been removed"
    assert len(playbook.get_all_tasks()) == 0, "The task should have been removed"

    playbook.remove_all_nodes_types(
        [
            PlayNode,
        ]
    )
    assert len(playbook.plays) == 0, "The play should have been removed"

    assert playbook.is_empty(), "The playbook should be empty"

    playbook.add_node("plays", play)
    play.add_node("roles", role)

    for i in range(10):
        role.add_node("tasks", TaskNode(f"loop task {i}"))

    new_role = RoleNode("new_role", include_role=True)
    new_role.add_node("tasks", TaskNode("New role task"))
    role2 = RoleNode("my_role_2")
    role2.add_node("tasks", new_role)
    role2.add_node("tasks", BlockNode("My block"))

    assert len(playbook.get_all_tasks()) == 11
    playbook.remove_all_nodes_types([TaskNode, BlockNode])
    assert len(playbook.get_all_tasks()) == 0, "All tasks should have been removed"


def test_calculate_indices():
    """Test the method calculate_indices

    :return:
    """
    playbook = PlaybookNode("my-fake-playbook.yml")
    play = PlayNode("play")
    playbook.add_node("plays", play)

    role = RoleNode("nested_include_role", include_role=True)
    role.add_node("tasks", TaskNode("task 1"))
    role.add_node("tasks", TaskNode("task 2"))
    play.add_node("tasks", role)

    nested_include_1 = RoleNode("nested_include_role_1", include_role=True)
    nested_include_1.add_node("tasks", TaskNode("task 1 in nested include 1"))
    nested_include_2 = RoleNode("nested_include_role_2", include_role=True)
    nested_include_2.add_node("tasks", TaskNode("task 1 in nested include 2"))

    role.add_node("tasks", nested_include_1)
    role.add_node("tasks", nested_include_2)

    playbook.calculate_indices()
    assert play.index == 1
    assert role.index == 1
    role.tasks[0].index = 1
    role.tasks[0].index = 2
    assert nested_include_1.index == 3
    assert nested_include_2.index == 4

    playbook.hide_task_nodes()
    playbook.calculate_indices()
    assert play.index == 1
    assert role.index == 1
    role.tasks[0].index = None
    role.tasks[0].index = None
    assert nested_include_1.index == 1
    assert nested_include_2.index == 2


def test_get_handlers_from_play():
    """Test the method PlayNode.get_handler

    :return:
    """
    play = PlayNode("play 1")
    restart_nginx = HandlerNode("restart nginx")
    restart_postgres = HandlerNode("restart postgres", listen=["restart dbs"])
    restart_mysql_1 = HandlerNode("restart mysql", listen=["restart dbs"])
    restart_mysql_2 = HandlerNode("restart mysql", listen=["restart dbs"])
    play.add_node("handlers", restart_nginx)
    play.add_node("handlers", restart_postgres)
    play.add_node("handlers", restart_mysql_1)
    play.add_node("handlers", restart_mysql_2)

    play.calculate_indices()

    assert play.get_notified_handlers(["fake handler"]) == ([], ["fake handler"])
    assert play.get_notified_handlers(["restart nginx"]) == ([restart_nginx], [])
    assert play.get_notified_handlers(["restart postgres"]) == ([restart_postgres], [])

    mysql_handlers, _ = play.get_notified_handlers(["restart mysql"])
    assert len(mysql_handlers) == 1
    assert mysql_handlers[0].id == restart_mysql_2.id

    # When multiple handlers have the same listen, we return them in the order they are defined
    assert play.get_notified_handlers(["restart dbs"]) == (
        [restart_postgres, restart_mysql_2],
        [],
    )
