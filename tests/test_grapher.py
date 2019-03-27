import os

import pytest
from pyquery import PyQuery

from ansibleplaybookgrapher import __prog__
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI
from tests import FIXTURES_DIR


def run_grapher(playbook_path, output_filename=None, additional_args=None):
    """
    Utility function to run the grapher
    :param output_filename:
    :type output_filename: str
    :param additional_args:
    :type additional_args: list
    :param playbook_path:
    :type playbook_path: str
    :return:
    :rtype:
    """
    additional_args = additional_args or []
    args = [__prog__]

    if output_filename:  # the default filename is the playbook file name minus .yml
        # put the generated svg in a dedicated folder
        dir_path = os.path.dirname(os.path.realpath(__file__))  # current file directory
        args.extend(['-o', os.path.join(dir_path, "generated_svg", output_filename)])

    args.extend(additional_args)

    args.append(playbook_path)

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    return cli.run()


def _common_tests(svg_path, playbook_path, plays_number=0, tasks_number=0, post_tasks_number=0, pre_tasks_number=0,
                  roles_number=0):
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
    roles = pq("g[id^='role_']")

    assert plays_number == len(plays), "The playbook '{}' should contains {} play(s) but we found {} play(s)".format(
        playbook_path, plays_number, len(plays))
    assert tasks_number == len(tasks), "The playbook '{}' should contains {} tasks(s) we found {} tasks".format(
        playbook_path, tasks_number, len(tasks))
    assert post_tasks_number == len(post_tasks), "The '{}' playbook should contains {} post tasks(s) we found {} " \
                                                 "post tasks".format(playbook_path, post_tasks_number, len(post_tasks))
    assert pre_tasks_number == len(pre_tasks), "The playbook '{}' should contains {} pre tasks(s) but we found {} " \
                                               "pre tasks".format(playbook_path, pre_tasks_number, len(pre_tasks))

    assert roles_number == len(roles), "The playbook '{}' should contains {} role(s) but we found {} role(s)".format(
        playbook_path, roles_number, len(roles))

    return {'tasks': tasks, 'plays': plays, 'pq': pq, 'post_tasks': post_tasks, 'pre_tasks': pre_tasks}


def test_simple_playbook(request):
    """
    Test simple_playbook.yml
    """
    playbook_path = os.path.join(FIXTURES_DIR, "simple_playbook.yml")
    svg_path = run_grapher(playbook_path, output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, post_tasks_number=2)


def test_example(request):
    """
    Test example.yml
    :return:
    :rtype:
    """

    playbook_path = os.path.join(FIXTURES_DIR, "example.yml")
    svg_path = run_grapher(playbook_path, output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=4,
                  post_tasks_number=2, pre_tasks_number=2)


def test_include_tasks(request):
    """
    Test include_tasks.yml, an example with some included tasks
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "include_tasks.yml")
    svg_path = run_grapher(playbook_path, output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=7)


def test_import_tasks(request):
    """
    Test include_tasks.yml, an example sime some imported tasks
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "import_tasks.yml")
    svg_path = run_grapher(playbook_path, output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=4)


@pytest.mark.parametrize(["include_role_tasks_option", "expected_tasks_number"],
                         [("--", 2), ("--include-role-tasks", 5)],
                         ids=["no_include_role_tasks_option", "include_role_tasks_option"])
def test_with_roles(request, include_role_tasks_option, expected_tasks_number):
    """
    Test with_roles.yml, an example with roles
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "with_roles.yml")
    svg_path = run_grapher(playbook_path, output_filename=request.node.name,
                           additional_args=[include_role_tasks_option])

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=expected_tasks_number,
                  post_tasks_number=2, pre_tasks_number=2, roles_number=1)


@pytest.mark.parametrize(["include_role_tasks_option", "expected_tasks_number"],
                         [("--", 0), ("--include-role-tasks", 3)],
                         ids=["no_include_role_tasks_option", "include_role_tasks_option"])
def test_include_role(request, include_role_tasks_option, expected_tasks_number):
    """
    Test include_role.yml, an example with include_role
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "include_role.yml")
    svg_path = run_grapher(playbook_path, output_filename=request.node.name,
                           additional_args=[include_role_tasks_option])

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=expected_tasks_number)


def test_with_block(request):
    """
    Test with_roles.yml, an example with roles
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "with_block.yml")
    svg_path = run_grapher(playbook_path, output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=3)


def test_nested_include_tasks(request):
    """
    Test nested_include.yml, an example with an include tasks that include another tasks
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "nested_include_tasks.yml")
    svg_path = run_grapher(playbook_path, output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=3)


@pytest.mark.parametrize(["include_role_tasks_option", "expected_tasks_number"],
                         [("--", 1), ("--include-role-tasks", 7)],
                         ids=["no_include_role_tasks_option", "include_role_tasks_option"])
def test_import_role(request, include_role_tasks_option, expected_tasks_number):
    """
    Test import_role.yml, an example with import role.
    Import role is special because the tasks imported from role are treated as "normal tasks" when the playbook is
    parsed.
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "import_role.yml")
    svg_path = run_grapher(playbook_path, output_filename=request.node.name,
                           additional_args=[include_role_tasks_option])

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=expected_tasks_number,
                  roles_number=1)


def test_import_playbook(request):
    """
    Test import_playbook
    :param request:
    :type request:
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "import_playbook.yml")
    svg_path = run_grapher(playbook_path, output_filename=request.node.name)
    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, pre_tasks_number=2, tasks_number=4,
                  post_tasks_number=2)


def test_nested_import_playbook(request):
    """
    Test some nested import playbook
    :return:
    :rtype:
    """
    playbook_path = os.path.join(FIXTURES_DIR, "nested_import_playbook.yml")
    svg_path = run_grapher(playbook_path, output_filename=request.node.name)
    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=3)
