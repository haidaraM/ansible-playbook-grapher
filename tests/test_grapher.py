import os
from ansibleplaybookgrapher.grapher import Grapher
from tests import FIXTURES_DIR


def test_simple_task(data_loader, inventory_manager, variable_manager, tmpdir):
    playbook = FIXTURES_DIR + "simple_task.yml"
    output_file_path = tmpdir.join('output')
    grapher = Grapher(data_loader=data_loader, inventory_manager=inventory_manager, variable_manager=variable_manager,
                      playbook_filename=playbook, output_filename=output_file_path.strpath)

    grapher.make_graph()

    grapher.render_graph()

    # test if the file exist. It will exist only if we write in it
    assert os.path.isfile(output_file_path.strpath + ".svg")




