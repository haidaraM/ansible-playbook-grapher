import pytest
from ansible.errors import AnsibleOptionsError
from ansible.release import __version__ as ansible_version

from ansibleplaybookgrapher import __prog__, __version__
from ansibleplaybookgrapher.cli import get_cli_class, IS_ANSIBLE_2_9_X


@pytest.mark.parametrize("help_option", ['-h', '--help'])
def test_cli_help(help_option, capfd):
    """
    Test for the help option : -h, --help
    :param help_option:
    :param capfd:
    :return:
    """
    args = [__prog__, help_option]

    cli = get_cli_class()(args)

    with pytest.raises(SystemExit) as exception_info:
        cli.parse()

    out, err = capfd.readouterr()

    assert "Make graphs from your Ansible Playbooks." in out


def test_cli_version(capfd):
    """
    Test version printing
    :return:
    """
    cli = get_cli_class()([__prog__, '--version'])
    with pytest.raises(SystemExit) as exception_info:
        cli.parse()

    out, err = capfd.readouterr()
    assert out == "%s %s (with ansible %s)\n" % (__prog__, __version__, ansible_version)


@pytest.mark.parametrize("save_dot_file_option, expected",
                         [(['--'], False), (['-s'], True), (['--save-dot-file'], True)],
                         ids=['default', 'save-dot-file-short-option', 'save-dot-file-long-option'])
def test_cli_save_dot_file(save_dot_file_option, expected):
    """
    Test for the save dot file option: -s, --save-dot-file
    :param save_dot_file_option:
    :param expected:
    :return:
    """
    args = [__prog__] + save_dot_file_option + ['playbook.yml']

    cli = get_cli_class()(args)

    cli.parse()

    assert cli.options.save_dot_file == expected


@pytest.mark.parametrize("output_filename_option, expected",
                         [(['--'], "playbook"), (['-o', 'output'], 'output'),
                          (['--ouput-file-name', 'output'], 'output')],
                         ids=['default', 'output-filename-short-option', 'output-filename-long-option'])
def test_cli_output_filename(output_filename_option, expected):
    """
    Test for the output filename option: -o, --ouput-file-name
    :param output_filename_option:
    :param expected:
    :return:
    """
    args = [__prog__] + output_filename_option + ['playbook.yml']

    cli = get_cli_class()(args)

    cli.parse()

    assert cli.options.output_filename == expected


@pytest.mark.parametrize("include_role_tasks_option, expected", [(['--'], False), (['--include-role-tasks'], True)],
                         ids=['default', 'include'])
def test_cli_include_role_tasks(include_role_tasks_option, expected):
    """
    Test for the include role tasks option: --include-role-tasks
    :param include_role_tasks_option:
    :param expected:
    :return:
    """

    args = [__prog__] + include_role_tasks_option + ['playboook.yml']

    cli = get_cli_class()(args)

    cli.parse()

    assert cli.options.include_role_tasks == expected


@pytest.mark.parametrize("tags_option, expected",
                         [(['--'], ['all']), (['-t', 'tag1'], ['tag1']),
                          (['-t', 'tag1', '-t', 'tag2'], ['tag1', 'tag2']),
                          (['-t', 'tag1,tag2'], ['tag1', 'tag2'])],
                         ids=['no_tags_provided', 'one-tag', 'multiple-tags', 'multiple-tags2'])
@pytest.mark.xfail(not IS_ANSIBLE_2_9_X, reason="This will fail in ansible 2.8 due to some global variables.")
# TODO: Remove xfail when we drop support for Ansible 2.8
def test_cli_tags(tags_option, expected):
    """

    :param tags_option:
    :param expected:
    :return:
    """
    args = [__prog__] + tags_option + ['playbook.yml']

    cli = get_cli_class()(args)

    cli.parse()

    # Ansible uses a set to construct the tags list. It may happen that the order of tags changes between two runs. As
    # the order of tags doesn't matter, I sorted them to avoid the test to fail
    assert sorted(cli.options.tags) == sorted(expected)


@pytest.mark.parametrize("skip_tags_option, expected",
                         [(['--'], []), (['--skip-tags', 'tag1'], ['tag1']),
                          (['--skip-tags', 'tag1', '--skip-tags', 'tag2'], ['tag1', 'tag2']),
                          (['--skip-tags', 'tag1,tag2'], ['tag1', 'tag2'])],
                         ids=['no_skip_tags_provided', 'one-skip-tag', 'multiple-skip-tags', 'multiple-skip-tags2'])
@pytest.mark.xfail(not IS_ANSIBLE_2_9_X, reason="This will fail in ansible 2.8 due to some global variables.")
# TODO: Remove xfail when we drop support for Ansible 2.8
def test_skip_tags(skip_tags_option, expected):
    """

    :param tags_option:
    :param expected:
    :return:
    """
    args = [__prog__] + skip_tags_option + ['playbook.yml']

    cli = get_cli_class()(args)

    cli.parse()

    # Ansible uses a set to construct the tags list. It may happen that the order of tags changes between two runs. As
    # the order of tags doesn't matter, I sorted them to avoid the test to fail
    assert sorted(cli.options.skip_tags) == sorted(expected)


def test_cli_no_playbook():
    """
    Test with no playbook provided
    :return:
    """
    args = [__prog__]

    cli = get_cli_class()(args)

    with pytest.raises((AnsibleOptionsError, SystemExit)) as exception_info:
        cli.parse()


def test_cli_multiple_playbooks():
    """
    Test with multiple playbooks provided
    :return:
    """
    args = [__prog__, 'playbook1.yml', 'playbook2.yml']

    cli = get_cli_class()(args)

    with pytest.raises((AnsibleOptionsError, SystemExit)) as exception_info:
        cli.parse()
