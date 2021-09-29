import pytest

from ansibleplaybookgrapher import PlaybookParser
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI


@pytest.mark.parametrize('grapher_cli', [["with_block.yml"]], indirect=True)
def test_block_parsing(grapher_cli: PlaybookGrapherCLI, display):
    """

    :return:
    """
    parser = PlaybookParser(grapher_cli.options.playbook_filename, display=display)
    playbook_node = parser.parse()
