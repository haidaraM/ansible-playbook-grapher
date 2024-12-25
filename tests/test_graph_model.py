from ansibleplaybookgrapher.graph_model import (
    BlockNode,
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
    for e in [role, task_3]:
        assert e in all_links[play], f"The play should be linked to the task {task_1}"

    assert len(all_links[role]) == 2, "The role should be linked to two nodes"
    for e in [task_1, task_2]:
        assert e in all_links[role], f"The role should be linked to the edge {e}"


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


def test_empty_play() -> None:
    """Testing the emptiness of a play
    :return:
    """
    play = PlayNode("play")
    assert play.is_empty(), "The play should empty"

    role = RoleNode("my_role_1")
    play.add_node("roles", role)
    assert play.is_empty(), "The play should still be empty given the role is empty"

    role.add_node("tasks", TaskNode("task 1"))
    assert not play.is_empty(), "The play should not be empty here"


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
    """:return:"""
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

    dict_rep = playbook.to_dict(exclude_empty_plays=True)

    assert dict_rep["type"] == "PlaybookNode"
    assert dict_rep["location"] is None, "A fake playbook does not have a location"

    assert len(dict_rep["plays"]) == 1
    assert dict_rep["plays"][0]["type"] == "PlayNode"
    assert dict_rep["plays"][0]["colors"]["font"] == "#ffffff"

    assert dict_rep["plays"][0]["name"] == "play"
    assert dict_rep["plays"][0]["tasks"][0]["name"] == "block 1"
    assert dict_rep["plays"][0]["tasks"][0]["index"] == 1
    assert dict_rep["plays"][0]["tasks"][0]["type"] == "BlockNode"


# TODO: add a test for the only roles option/filter. It's no longer set when parsing the playbook
