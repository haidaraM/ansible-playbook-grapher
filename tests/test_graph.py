from ansibleplaybookgrapher.graph import (
    RoleNode,
    TaskNode,
    PlayNode,
    BlockNode,
)


def test_links_structure():
    """
    Test links structure of a graph
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
    assert len(all_links) == 2, "The links should contains only 6 elements"

    assert len(all_links[play.id]) == 2, "The play should be linked to 2 nodes"
    for e in [role, task_3]:
        assert (
            e in all_links[play.id]
        ), f"The play should be linked to the task {task_1}"

    assert len(all_links[role.id]) == 2, "The role should be linked to two nodes"
    for e in [task_1, task_2]:
        assert e in all_links[role.id], f"The role should be linked to the edge {e}"


def test_get_all_tasks_nodes():
    """
    Test the function get_all_tasks_nodes
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
