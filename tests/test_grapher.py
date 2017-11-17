import os
from lxml import etree

from ansibleplaybookgrapher.grapher import Grapher
from tests import FIXTURES_DIR


def _assert_common_svg(svg_tree):
    """
    Assert some common structures of the generated svg
    :param svg_tree:
    :return:
    """
    root = svg_tree.getroot()

    assert root.get('id') == 'svg'

    # jquery must be the first element because the next script need jquery
    assert root[0].get('id') == 'jquery'
    assert root[1].get('id') == 'my_javascript'
    assert root[2].get('id') == 'my_css'


def test_simple_task(data_loader, inventory_manager, variable_manager, tmpdir):
    playbook = FIXTURES_DIR + "simple_playbook.yml"
    output_filepath = tmpdir.join('output')
    grapher = Grapher(data_loader=data_loader, inventory_manager=inventory_manager, variable_manager=variable_manager,
                      playbook_filename=playbook, output_filename=output_filepath.strpath)

    grapher.make_graph()

    grapher.render_graph()

    grapher.post_process_svg()

    svg_filepath = output_filepath.strpath + ".svg"

    # test if the file exist. It will exist only if we write in it
    assert os.path.isfile(svg_filepath)

    tree = etree.parse(svg_filepath)

    _assert_common_svg(tree)
