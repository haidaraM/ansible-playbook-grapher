import os

from pyquery import PyQuery

from ansibleplaybookgrapher import __prog__
from ansibleplaybookgrapher.cli import main
from tests import FIXTURES_DIR


def _common_tests(svg_path, playbook_path, plays_number=0, tasks_number=0, post_tasks_number=0, pre_tasks_number=0):
    """
    Perform some common tests on the generated svg file:
     - Existence of svg file
     - Check number of plays, tasks, pre_tasks, role_tasks, post_tasks
     - Root node text that must be the playbook path
    :type svg_path: str
    :type playbook_path: str
    :param plays_number: Number of plays in the playbook
    :type plays_number: int
    :param tasks_number: Number of tasks in the playbook
    :type tasks_number: int
    :param post_tasks_number Number of post tasks in the playbook
    :type post_tasks_number: int
    :return:
    :rtype: dict[str, PyQuery]
    """

    pq = PyQuery(filename=svg_path)
    pq.remove_namespaces()

    # test if the file exist. It will exist only if we write in it
    assert os.path.isfile(svg_path), "The svg file should exist"
    assert pq('#root_node text').text() == playbook_path

    plays = pq("g[id^='play_']")
    tasks = pq("g[id^='task_']")
    post_tasks = pq("g[id^='post_task_']")
    pre_tasks = pq("g[id^='pre_task_']")

    assert plays_number == len(plays), "This playbook should contains {} play(s)".format(plays_number)
    assert tasks_number == len(tasks), "This playbook should contains {} tasks(s)".format(tasks_number)
    assert post_tasks_number == len(post_tasks), "This playbook should contains {} post tasks(s)".format(
        post_tasks_number)
    assert pre_tasks_number == len(pre_tasks), "This playbook should contains {} pre tasks(s)".format(
        pre_tasks_number)

    return {'tasks': tasks, 'plays': plays, 'pq': pq, 'post_tasks': post_tasks, 'pre_tasks': pre_tasks}


def test_grapher_simple_playbook():
    """
    Test simple_playbook.yml
    """
    playbook_path = os.path.join(FIXTURES_DIR, "simple_playbook.yml")
    args = [__prog__, playbook_path]
    svg_path = main(args)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, post_tasks_number=2)

    os.remove(svg_path)


def test_grapher_example():
    """
    Test example.yml
    :return:
    :rtype:
    """

    path_playbook_path = os.path.join(FIXTURES_DIR, "example.yml")
    args = [__prog__, path_playbook_path]
    svg_path = main(args)

    _common_tests(svg_path=svg_path, playbook_path=path_playbook_path, plays_number=1, tasks_number=4,
                  post_tasks_number=2, pre_tasks_number=2)

    os.remove(svg_path)


def test_grapher_example_include_task():
    """
    Test example_include_tasks.yml, an example with some included tasks
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "example_include_tasks.yml")
    args = [__prog__, playbook_path]
    svg_path = main(args)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=6)

    os.remove(svg_path)


def test_grapher_example_include_tasks():
    """
    Test example_include_tasks.yml, an example sime some imported tasks
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "example_import_tasks.yml")
    args = [__prog__, playbook_path]
    svg_path = main(args)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=4)

    os.remove(svg_path)


def test_example_with_roles():
    """
    Test example_with_roles.yml, an example with roles
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "example_with_roles.yml")
    args = [__prog__, '--include-role-tasks', playbook_path]
    svg_path = main(args)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=2, tasks_number=7, post_tasks_number=2,
                  pre_tasks_number=2)

    os.remove(svg_path)
