from ansibleplaybookgrapher.graph import (
    RoleNode,
    TaskNode,
    EdgeNode,
    PlayNode,
    BlockNode,
    get_all_tasks_nodes,
)


def test_links_structure():
    """
    Test links structure of a graph
    :return:
    """
    play = PlayNode("composite_node")

    role = RoleNode("my_role_1")
    edge_role = EdgeNode(play, role, "from play to role")
    play.add_node("roles", edge_role)
    # play -> role -> edge 1 -> task 1
    task_1 = TaskNode("task 1")
    edge_1 = EdgeNode(role, task_1, "from role1 to task 1")
    role.add_node("tasks", edge_1)

    # play -> role -> edge 2 -> task 2
    task_2 = TaskNode("task 2")
    edge_2 = EdgeNode(role, task_2, "from role1 to task 2")
    role.add_node("tasks", edge_2)

    # play -> edge 3 -> task 3
    task_3 = TaskNode("task 3")
    edge_3 = EdgeNode(play, task_3, "from play to task 3")
    play.add_node("tasks", edge_3)

    all_links = play.links_structure()
    assert len(all_links) == 6, "The links should contains only 6 elements"

    assert len(all_links[play]) == 2, "The play should be linked to 2 nodes"
    for e in [edge_role, edge_3]:
        assert e in all_links[play], f"The play should be linked to the edge {e}"

    assert len(all_links[role]) == 2, "The role should be linked to two nodes"
    for e in [edge_1, edge_2]:
        assert e in all_links[role], f"The role should be linked to the edge {e}"

    for e in [edge_1, edge_2, edge_3, edge_role]:
        assert len(all_links[e]) == 1, "An edge should be linked to one node"


def test_get_all_tasks_nodes():
    """
    Test the function get_all_tasks_nodes
    :return:
    """
    play = PlayNode("play")

    role_1 = RoleNode("my_role_1")
    edge_role = EdgeNode(play, role_1, "from play to role")
    play.add_node("roles", edge_role)

    # play -> role 1 -> edge 1 -> task 1
    task_1 = TaskNode("task 1")
    edge_1 = EdgeNode(role_1, task_1, "from role1 to task 1")
    role_1.add_node("tasks", edge_1)

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

    all_tasks = get_all_tasks_nodes(play)
    assert len(all_tasks) == 4, "There should be 4 tasks in all"
    assert [task_1, task_2, task_3, task_4] == all_tasks
