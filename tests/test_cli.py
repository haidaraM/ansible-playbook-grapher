from pathlib import Path

import pytest
from ansible.errors import AnsibleOptionsError
from ansible.release import __version__ as ansible_version

from ansibleplaybookgrapher import __prog__, __version__
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI


@pytest.mark.parametrize(
    ("exclude_roles_option", "expected"),
    [
        (["--"], None),
        (["--exclude-roles", "fake_role"], ["fake_role"]),
        (
            ["--exclude-roles", "fake_role,display_some_facts"],
            ["display_some_facts", "fake_role"],
        ),
    ],
    ids=[
        "default",
        "exclude_roles_single_role",
        "exclude_roles_multiple_roles",
    ],
)
def test_cli_exclude_roles(
    exclude_roles_option: list[str],
    expected: list[str],
) -> None:
    """Test for the exclude roles option: --exclude-roles
    :param exclude_roles_option:
    :param expected:
    :return:
    """
    args = [__prog__, *exclude_roles_option, "playbook.yml"]

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    assert cli.options.exclude_roles == expected


@pytest.mark.parametrize(
    ("exclude_roles_option", "expected"),
    [
        (["--exclude-roles", "exclude_roles.txt"], ["display_some_facts", "fake_role"]),
    ],
    ids=[
        "exclude_roles_with_file",
    ],
)
def test_cli_exclude_roles_with_file(
    exclude_roles_option: list[str],
    expected: list[str],
    tmp_path: Path,
) -> None:
    """Test for the exclude roles option with a file path as argument: --exclude-roles
    :param exclude_roles_option:
    :param expected:
    :return:
    """
    content = "fake_role\ndisplay_some_facts"
    exclude_role_file = tmp_path / exclude_roles_option[1]
    exclude_role_file.write_text(content)
    exclude_roles_option[1] = str(exclude_role_file)

    args = [__prog__, *exclude_roles_option, "playbook.yml"]

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    assert cli.options.exclude_roles == expected


@pytest.mark.parametrize(
    ("exclude_roles_option", "expected"),
    [
        (
            ["--exclude-roles", "path/to/example_role/"],
            ["example_role"],
        ),
    ],
    ids=[
        "exclude_roles_with_dir",
    ],
)
def test_cli_exclude_roles_with_dir(
    exclude_roles_option: list[str],
    expected: list[str],
    tmp_path: Path,
) -> None:
    """Test for the exclude roles option with directory path as argument: --exclude-roles
    :param exclude_roles_option:
    :param expected:
    :return:
    """
    example_dir_path = tmp_path / exclude_roles_option[1]
    example_dir_path.mkdir(parents=True, exist_ok=True)
    exclude_roles_option[1] = str(example_dir_path)

    args = [__prog__, *exclude_roles_option, "playbook.yml"]

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    assert cli.options.exclude_roles == expected


@pytest.mark.parametrize(
    ("only_roles_option", "expected"),
    [(["--"], False), (["--only-roles"], True)],
    ids=["default", "only_roles"],
)
def test_cli_only_roles(only_roles_option: str, expected: bool) -> None:
    """Test for the only roles option: --only-roles
    :param only_roles_option:
    :param expected:
    :return:
    """
    args = [__prog__, *only_roles_option, "playbook.yml"]

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    assert cli.options.only_roles == expected


@pytest.mark.parametrize("help_option", ["-h", "--help"])
def test_cli_help(help_option: str, capfd: pytest.CaptureFixture) -> None:
    """Test for the help option: -h, --help
    :param help_option:
    :param capfd:
    :return:
    """
    args = [__prog__, help_option]

    cli = PlaybookGrapherCLI(args)

    with pytest.raises(SystemExit):
        cli.parse()

    out, err = capfd.readouterr()

    assert "Make graphs from your Ansible Playbooks." in out


def test_cli_version(capfd: pytest.CaptureFixture) -> None:
    """Test version printing
    :return:
    """
    cli = PlaybookGrapherCLI([__prog__, "--version"])
    with pytest.raises(SystemExit):
        cli.parse()

    out, err = capfd.readouterr()
    assert out == f"{__prog__} {__version__} (with ansible {ansible_version})\n"


@pytest.mark.parametrize(
    ("save_dot_file_option", "expected"),
    [(["--"], False), (["-s"], True), (["--save-dot-file"], True)],
    ids=["default", "save-dot-file-short-option", "save-dot-file-long-option"],
)
def test_cli_save_dot_file(save_dot_file_option: list[str], expected: bool) -> None:
    """Test for the save dot file option: -s, --save-dot-file
    :param save_dot_file_option:
    :param expected:
    :return:
    """
    args = [__prog__, *save_dot_file_option, "playbook.yml"]

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    assert cli.options.save_dot_file == expected


@pytest.mark.parametrize(
    ("output_filename_option", "expected"),
    [
        (["--"], "playbook"),
        (["-o", "output"], "output"),
        (["--output-file-name", "output"], "output"),
    ],
    ids=["default", "output-filename-short-option", "output-filename-long-option"],
)
def test_cli_output_filename(output_filename_option: list[str], expected: str) -> None:
    """Test for the output filename option: -o, --output-file-name
    :param output_filename_option:
    :param expected:
    :return:
    """
    args = [__prog__, *output_filename_option, "playbook.yml"]

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    assert cli.options.output_filename == expected


def test_cli_output_filename_multiple_playbooks() -> None:
    """Test for the output filename when using multiple playbooks
    :return:
    """
    args = [__prog__, "playbook.yml", "second-playbook.yml", "third-playbook.yaml"]

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    assert cli.options.output_filename == "playbook-second-playbook-third-playbook"


@pytest.mark.parametrize(
    ("include_role_tasks_option", "expected"),
    [(["--"], False), (["--include-role-tasks"], True)],
    ids=["default", "include"],
)
def test_cli_include_role_tasks(
    include_role_tasks_option: list[str],
    expected: bool,
) -> None:
    """Test for the include role tasks option: --include-role-tasks
    :param include_role_tasks_option:
    :param expected:
    :return:
    """
    args = [__prog__, *include_role_tasks_option, "playboook.yml"]

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    assert cli.options.include_role_tasks == expected


@pytest.mark.parametrize(
    ("show_handlers_option", "expected"),
    [(["--"], False), (["--show-handlers"], True)],
    ids=["default", "include"],
)
def test_cli_show_handlers(
    show_handlers_option: list[str],
    expected: bool,
) -> None:
    """Test for show handlers options: --show-handlers

    :param show_handlers_option:
    :param expected:
    :return:
    """
    args = [__prog__, *show_handlers_option, "playboook.yml"]

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    assert cli.options.show_handlers == expected


@pytest.mark.parametrize(
    ("tags_option", "expected"),
    [
        (["--"], ["all"]),
        (["-t", "tag1"], ["tag1"]),
        (["-t", "tag1", "-t", "tag2"], ["tag1", "tag2"]),
        (["-t", "tag1,tag2"], ["tag1", "tag2"]),
    ],
    ids=["no_tags_provided", "one-tag", "multiple-tags", "multiple-tags2"],
)
def test_cli_tags(tags_option: list[str], expected: list[str]) -> None:
    """:param tags_option:
    :param expected:
    :return:
    """
    args = [__prog__, *tags_option, "playbook.yml"]

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    # Ansible uses a set to construct the tags list. It may happen that the order of tags changes between two runs. As
    # the order of tags doesn't matter, I sorted them to avoid the test to fail
    assert sorted(cli.options.tags) == sorted(expected)


@pytest.mark.parametrize(
    ("skip_tags_option", "expected"),
    [
        (["--"], []),
        (["--skip-tags", "tag1"], ["tag1"]),
        (["--skip-tags", "tag1", "--skip-tags", "tag2"], ["tag1", "tag2"]),
        (["--skip-tags", "tag1,tag2"], ["tag1", "tag2"]),
    ],
    ids=[
        "no_skip_tags_provided",
        "one-skip-tag",
        "multiple-skip-tags",
        "multiple-skip-tags2",
    ],
)
def test_skip_tags(skip_tags_option: list[str], expected: list[str]) -> None:
    """:param skip_tags_option:
    :param expected:
    :return:
    """
    args = [__prog__, *skip_tags_option, "playbook.yml"]

    cli = PlaybookGrapherCLI(args)

    cli.parse()

    # Ansible uses a set to construct the tags list. It may happen that the order of tags changes between two runs. As
    # the order of tags doesn't matter, I sorted them to avoid the test to fail
    assert sorted(cli.options.skip_tags) == sorted(expected)


def test_cli_no_playbook() -> None:
    """Test with no playbook provided
    :return:
    """
    args = [__prog__]

    cli = PlaybookGrapherCLI(args)

    with pytest.raises((AnsibleOptionsError, SystemExit)):
        cli.parse()


def test_cli_multiple_playbooks() -> None:
    """Test with multiple playbooks provided
    :return:
    """
    args = [__prog__, "playbook1.yml", "playbook2.yml"]

    cli = PlaybookGrapherCLI(args)
    cli.parse()

    assert cli.options.playbooks == ["playbook1.yml", "playbook2.yml"]


@pytest.mark.parametrize(
    ("verbosity", "verbosity_number"),
    [("--", 0), ("-v", 1), ("-vv", 2), ("-vvv", 3)],
    ids=["no_verbose", "simple_verbose", "double_verbose", "triple_verbose"],
)
def test_cli_verbosity_options(verbosity: str, verbosity_number: int) -> None:
    """Test verbosity options."""
    args = [__prog__, verbosity, "playbook1.yml"]

    cli = PlaybookGrapherCLI(args)
    cli.parse()

    assert cli.options.verbosity == verbosity_number


def test_cli_open_protocol_custom_formats() -> None:
    """The provided format should be converted to a dict
    :return:
    """
    formats_str = '{"file": "{path}", "folder": "{path}"}'
    args = [
        __prog__,
        "--open-protocol-handler",
        "custom",
        "--open-protocol-custom-formats",
        formats_str,
        "playbook1.yml",
    ]

    cli = PlaybookGrapherCLI(args)
    cli.parse()
    assert cli.options.open_protocol_custom_formats == {
        "file": "{path}",
        "folder": "{path}",
    }, "The formats should be converted to json"


def test_cli_open_protocol_custom_formats_not_provided() -> None:
    """The custom formats must be provided when the protocol handler is set to custom
    :return:
    """
    args = [__prog__, "--open-protocol-handler", "custom", "playbook1.yml"]

    cli = PlaybookGrapherCLI(args)
    with pytest.raises(AnsibleOptionsError) as exception_info:
        cli.parse()

    assert (
        "you must provide the formats to use with --open-protocol-custom-formats"
        in exception_info.value.message
    )


@pytest.mark.parametrize(
    ("protocol_format", "expected_message"),
    [
        ("invalid_json", "JSONDecodeError"),
        ("{}", "The field 'file' or 'folder' is missing"),
    ],
)
def test_cli_open_protocol_custom_formats_invalid_inputs(
    protocol_format: str,
    expected_message: str,
    capsys: pytest.CaptureFixture,
) -> None:
    """The custom formats must be a valid json data
    :return:
    """
    args = [
        __prog__,
        "--open-protocol-handler",
        "custom",
        "--open-protocol-custom-formats",
        protocol_format,
        "playbook1.yml",
    ]

    cli = PlaybookGrapherCLI(args)
    with pytest.raises(SystemExit):
        cli.parse()

    error_msg = capsys.readouterr().err
    assert expected_message in error_msg


def test_cli_resolve_playbook_path_from_collection():
    """Test resolving the playbook path from a collection

    :return:
    """

    playbooks = ["haidaram.test_collection.test", "second-playbook.yml"]
    args = [__prog__, *playbooks]

    # Since I'm not overriding the paths where the collections are installed, they should in this folder:
    expected_collection_path = Path(
        "~/.ansible/collections/ansible_collections/haidaram/test_collection/playbooks/test.yml"
    ).expanduser()

    cli = PlaybookGrapherCLI(args)
    cli.parse()
    cli.resolve_playbooks_paths()

    assert cli.get_playbook_path(playbooks[0]) == f"{expected_collection_path}"
    assert cli.get_playbook_path(playbooks[1]) == "second-playbook.yml"
