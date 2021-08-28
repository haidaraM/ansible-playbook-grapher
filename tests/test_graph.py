from ansibleplaybookgrapher.graph import CompositeNode, RoleNode, TaskNode


def test_get_all_links():
    """
    Test get all links
    :return:
    """
    composite = CompositeNode("composite_node", "id_composite")

    role = RoleNode("my_role_1")
    composite.add_node("roles", role)
    task_1 = TaskNode("task_1")
    task_2 = TaskNode("task_2")
    role.add_node("tasks", task_1)
    role.add_node("tasks", task_2)

    task_3 = TaskNode("task_2")
    composite.add_node("tasks", task_3)

    post_task = TaskNode("post_task_3")
    composite.add_node("post_tasks", post_task)

    all_links = composite.links_structure()
    assert len(all_links) == 2, "The links should contains only two elements"
    assert len(all_links[role.id]) == 2, "The role should be linked only to two task nodes"
    assert len(all_links[composite.id]) == 2, "The composite should be linked only to one task node"

    #assert task_1.id in all_links[role.id]
    #assert task_2.id in all_links[role.id]
    #assert task_3.id in all_links[composite.id]
