import pytest

from ansibleplaybookgrapher import PlaybookParser
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI
from ansibleplaybookgrapher.graph import TaskNode, BlockNode


@pytest.mark.parametrize('grapher_cli', [["with_block.yml"]], indirect=True)
def test_block_parsing(grapher_cli: PlaybookGrapherCLI, display):
    """
    The parsing of a playbook with blocks
    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbook_filename, display=display)
    playbook_node = parser.parse()
    assert len(playbook_node.plays) == 1

    play_node = playbook_node.plays[0].destination
    tasks = play_node.tasks
    post_tasks = play_node.post_tasks
    assert len(tasks) == 2
    assert len(post_tasks) == 1

    # Check tasks
    task_1 = tasks[0].destination
    assert isinstance(task_1, TaskNode)
    assert task_1.name == "[task] Install tree"

    # Check the second task: the first block
    first_block = tasks[1].destination
    assert isinstance(first_block, BlockNode)
    assert first_block.name == "Install Apache"
    assert len(first_block.tasks) == 4
    # Check the second block (nested block)
    nested_block = first_block.tasks[2].destination
    assert len(nested_block.tasks) == 2
    assert nested_block.tasks[0].destination.name == "get_url"
    assert nested_block.tasks[1].destination.name == "command"

    # Check the post task
    assert post_tasks[0].destination.name == "[post_task] Debug"
