import pytest

from ansibleplaybookgrapher.utils import PostProcessor
from tests import FIXTURES_DIR


@pytest.fixture(name='simple_post_processor')
def fixture_simple_postprocessor():
    """
    Return a post processor without a graph representation and with the simple_playbook_no_postproccess
    :return:
    """
    svg_path = FIXTURES_DIR + "simple_playbook_no_postproccess.svg"

    post_processor = PostProcessor(svg_path=svg_path, graph_representation=None)
    return post_processor


def test_post_processor_insert_tag():
    assert False


def test_post_processor_remove_title():
    assert False


def test_post_processor_without_graph_representation(simple_post_processor, tmpdir):
    svg_path_out = "simple_playbook_postproccess.svg"
    svg_post_proccessed_path = tmpdir.join(svg_path_out)

    simple_post_processor.write(output_filename=svg_post_proccessed_path.strpath)
