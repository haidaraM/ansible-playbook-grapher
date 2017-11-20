import pytest

from ansibleplaybookgrapher.utils import PostProcessor, SVG_NAMESPACE
from tests import FIXTURES_DIR


def _assert_common_svg(svg_root):
    """
    Assert some common structures of the generated svg
    :param svg_root:
    :return:
    """

    assert svg_root.get('id') == 'svg'

    # jquery must be the first element because the next script need jquery
    assert svg_root[0].get('id') == 'jquery'
    assert svg_root[1].get('id') == 'my_javascript'
    assert svg_root[2].get('id') == 'my_css'


@pytest.fixture(name='simple_post_processor')
def fixture_simple_postprocessor():
    """
    Return a post processor without a graph representation and with the simple_playbook_no_postproccess
    :return:
    """
    svg_path = FIXTURES_DIR + "simple_playbook_no_postproccess.svg"

    post_processor = PostProcessor(svg_path=svg_path, graph_representation=None)
    return post_processor


def test_post_processor_insert_tag(simple_post_processor):
    simple_post_processor.insert_script_tag(0, attrib={'id': 'toto'})

    assert simple_post_processor.root[0].tag == 'script'
    assert simple_post_processor.root[0].get('id') == 'toto'


def test_post_processor_remove_title(simple_post_processor):
    simple_post_processor._remove_title()
    root = simple_post_processor.root
    resultats = root.xpath("ns:g[@id='graph0']/ns:title", namespaces={'ns': SVG_NAMESPACE})

    assert len(resultats) == 0


def test_post_processor_without_graph_representation(simple_post_processor, tmpdir):
    svg_path_out = "simple_playbook_postproccess.svg"
    svg_post_proccessed_path = tmpdir.join(svg_path_out)

    simple_post_processor.post_process()

    simple_post_processor.write(output_filename=svg_post_proccessed_path.strpath)

    root = simple_post_processor.root
    _assert_common_svg(root)

    # no links should be in the svg when there is no graph_representation
    assert len(root.xpath("//links")) == 0
