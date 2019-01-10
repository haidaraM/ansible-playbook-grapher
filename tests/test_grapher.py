import os

import pytest
from lxml import etree

from ansibleplaybookgrapher.cli import main
from tests import FIXTURES_DIR


@pytest.fixture
def tmp_path(tmpdir):
    return tmpdir.join('output').strpath


def test_simple_playbook(tmp_path):
    args = ['', '-o', tmp_path, FIXTURES_DIR + "simple_playbook.yml"]
    main(args)
    svg_path = tmp_path + '.svg'

    # test if the file exist. It will exist only if we write in it
    assert os.path.isfile(svg_path), "The svg file should exist"

    tree = etree.parse(svg_path)
    root = tree.getroot()
