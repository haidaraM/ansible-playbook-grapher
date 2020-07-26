import os

import pytest
from pyquery import PyQuery

from ansibleplaybookgrapher import __prog__
from ansibleplaybookgrapher.cli import get_cli_class, IS_ANSIBLE_2_9_X
from tests import FIXTURES_DIR


def run_grapher(playbook_file, output_filename=None, additional_args=None):
    """
    Utility function to run the grapher
    :param output_filename:
    :type output_filename: str
    :param additional_args:
    :type additional_args: list
    :param playbook_file:
    :type playbook_file: str
    :return:
    """
    additional_args = additional_args or []
    playbook_path = os.path.join(FIXTURES_DIR, playbook_file)
    args = [__prog__]

    if output_filename:  # the default filename is the playbook file name minus .yml
        # put the generated svg in a dedicated folder
        dir_path = os.path.dirname(os.path.realpath(__file__))  # current file directory
        args.extend(['-o', os.path.join(dir_path, "generated_svg", output_filename)])

    args.extend(additional_args)

    args.append(playbook_path)

    cli = get_cli_class()(args)

    cli.parse()

    return cli.run(), playbook_path


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
    :param post_tasks_number: Number of post tasks in the playbook
    :type post_tasks_number: int
    :return: dict[str, PyQuery]
    """

    pq = PyQuery(filename=svg_path)
    pq.remove_namespaces()

    # test if the file exist. It will exist only if we write in it.
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

    return {'tasks': tasks, 'plays': plays, 'pq': pq, 'post_tasks': post_tasks, 'pre_tasks': pre_tasks, "roles": roles}


def test_simple_playbook(request):
    """
    Test simple_playbook.yml
    """
    svg_path, playbook_path = run_grapher("simple_playbook.yml", output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, post_tasks_number=2)


def test_example(request):
    """
    Test example.yml
    """
    svg_path, playbook_path = run_grapher("example.yml", output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=4,
                  post_tasks_number=2, pre_tasks_number=2)


def test_include_tasks(request):
    """
    Test include_tasks.yml, an example with some included tasks
    """
    svg_path, playbook_path = run_grapher("include_tasks.yml", output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=7)


def test_import_tasks(request):
    """
    Test include_tasks.yml, an example sime some imported tasks
    """
    svg_path, playbook_path = run_grapher("import_tasks.yml", output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=5)


@pytest.mark.parametrize(["include_role_tasks_option", "expected_tasks_number"],
                         [("--", 2), ("--include-role-tasks", 5)],
                         ids=["no_include_role_tasks_option", "include_role_tasks_option"])
def test_with_roles(request, include_role_tasks_option, expected_tasks_number):
    """
    Test with_roles.yml, an example with roles
    """

    svg_path, playbook_path = run_grapher("with_roles.yml", output_filename=request.node.name,
                                          additional_args=[include_role_tasks_option])

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=expected_tasks_number,
                  post_tasks_number=2, pre_tasks_number=2, roles_number=1)


@pytest.mark.parametrize(["include_role_tasks_option", "expected_tasks_number"],
                         [("--", 0), ("--include-role-tasks", 3)],
                         ids=["no_include_role_tasks_option", "include_role_tasks_option"])
def test_include_role(request, include_role_tasks_option, expected_tasks_number):
    """
    Test include_role.yml, an example with include_role
    """
    svg_path, playbook_path = run_grapher("include_role.yml", output_filename=request.node.name,
                                          additional_args=[include_role_tasks_option])

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=expected_tasks_number)


def test_with_block(request):
    """
    Test with_roles.yml, an example with roles
    """
    svg_path, playbook_path = run_grapher("with_block.yml", output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=3)


def test_nested_include_tasks(request):
    """
    Test nested_include.yml, an example with an include tasks that include another tasks
    """
    svg_path, playbook_path = run_grapher("nested_include_tasks.yml", output_filename=request.node.name)

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=3)


@pytest.mark.parametrize(["include_role_tasks_option", "expected_tasks_number"],
                         [("--", 1), ("--include-role-tasks", 7)],
                         ids=["no_include_role_tasks_option", "include_role_tasks_option"])
def test_import_role(request, include_role_tasks_option, expected_tasks_number):
    """
    Test import_role.yml, an example with import role.
    Import role is special because the tasks imported from role are treated as "normal tasks" when the playbook is parsed.
    """
    svg_path, playbook_path = run_grapher("import_role.yml", output_filename=request.node.name,
                                          additional_args=[include_role_tasks_option])

    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=expected_tasks_number,
                  roles_number=1)


def test_import_playbook(request):
    """
    Test import_playbook
    """

    svg_path, playbook_path = run_grapher("import_playbook.yml", output_filename=request.node.name)
    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, pre_tasks_number=2, tasks_number=4,
                  post_tasks_number=2)


@pytest.mark.parametrize(["include_role_tasks_option", "expected_tasks_number"],
                         [("--", 4), ("--include-role-tasks", 7)],
                         ids=["no_include_role_tasks_option", "include_role_tasks_option"])
def test_nested_import_playbook(request, include_role_tasks_option, expected_tasks_number):
    """
    Test nested import playbook with an import_role and include_tasks
    """
    svg_path, playbook_path = run_grapher("nested_import_playbook.yml", output_filename=request.node.name,
                                          additional_args=[include_role_tasks_option])
    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=2, tasks_number=expected_tasks_number)


def test_relative_var_files(request):
    """
    Test a playbook with a relative var file
    """
    svg_path, playbook_path = run_grapher("relative_var_files.yml", output_filename=request.node.name)
    res = _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, tasks_number=2)

    # check if the plays title contains the interpolated variables
    assert 'Cristiano Ronaldo' in res['tasks'][0].find('text').text, 'The title should contain player name'
    assert 'Lionel Messi' in res['tasks'][1].find('text').text, 'The title should contain player name'


def test_tags(request):
    """
    Test a playbook by only graphing a specific tasks based on the given tags
    """
    svg_path, playbook_path = run_grapher("tags.yml", output_filename=request.node.name,
                                          additional_args=["-t", "pre_task_tag_1"])
    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, pre_tasks_number=1)


@pytest.mark.xfail(not IS_ANSIBLE_2_9_X, reason="This will fail in ansible 2.8 due to some global variables.")
# TODO: Remove xfail when we drop support for Ansible 2.8
def test_skip_tags(request):
    """
    Test a playbook by only graphing a specific tasks based on the given tags
    """
    svg_path, playbook_path = run_grapher("tags.yml", output_filename=request.node.name,
                                          additional_args=["--skip-tags", "pre_task_tag_1", "--include-role-tasks"])
    _common_tests(svg_path=svg_path, playbook_path=playbook_path, plays_number=1, pre_tasks_number=1, roles_number=1,
                  tasks_number=3)
