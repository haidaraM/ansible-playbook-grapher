from ansibleplaybookgrapher.graph import RoleNode, TaskNode, EdgeNode, PlayNode


def test_get_all_links():
    """
    Test get all links
    :return:
    """
    play = PlayNode("composite_node")

    role = RoleNode("my_role_1")
    edge_role = EdgeNode("from play to role", play, role)
    play.add_node("roles", edge_role)
    # play -> role -> edge 1 -> task 1
    task_1 = TaskNode("task 1")
    edge_1 = EdgeNode("from role1 to task 1", role, task_1)
    role.add_node("tasks", edge_1)

    # play -> role -> edge 2 -> task 2
    task_2 = TaskNode("task 2")
    edge_2 = EdgeNode("from role1 to task 2", role, task_2)
    role.add_node("tasks", edge_2)

    # play -> edge 3 -> task 3
    task_3 = TaskNode("task 3")
    edge_3 = EdgeNode("from play to task 3", play, task_3)
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
