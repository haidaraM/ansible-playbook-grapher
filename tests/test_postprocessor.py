from ansibleplaybookgrapher.utils import PostProcessor
from tests import FIXTURES_DIR


def test_post_processor_without_graph_representation(tmpdir):
    svg_path = FIXTURES_DIR + "simple_playbook_no_postproccess.svg"
    svg_path_out = "simple_playbook_postproccess.svg"

    post_processor = PostProcessor(svg_path=svg_path, graph_representation=None)

    post_processor.post_process()

    svg_post_proccessed_path = tmpdir.join(svg_path_out)

    post_processor.write(output_filename=svg_post_proccessed_path.strpath)
