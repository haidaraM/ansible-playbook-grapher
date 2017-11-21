import os
from lxml import etree

from ansibleplaybookgrapher.grapher import Grapher
from tests import FIXTURES_DIR


def test_grapher_simple_playbook(data_loader, inventory_manager, variable_manager, tmpdir):
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
