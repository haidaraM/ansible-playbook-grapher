import pytest
from lxml import etree

from ansibleplaybookgrapher.grapher import Grapher
from ansibleplaybookgrapher.utils import PostProcessor, SVG_NAMESPACE
from tests import FIXTURES_DIR, SIMPLE_PLAYBOOK_SVG, SIMPLE_PLAYBOOK_YML


@pytest.fixture(name='post_processor')
def fixture_simple_postprocessor(request):
    """
    Return a post processor without a graph representation and with the simple_playbook_no_postproccess
    :return:
    """

    svg_path = SIMPLE_PLAYBOOK_SVG

    post_processor = PostProcessor(svg_path=svg_path)
    return post_processor


@pytest.fixture(name='grapher')
def fixture_simple_grapher(data_loader, inventory_manager, variable_manager, request):
    return Grapher(data_loader=data_loader, inventory_manager=inventory_manager, variable_manager=variable_manager,
                   playbook_filename=request.param)


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


def test_post_processor_insert_tag(post_processor):
    post_processor.insert_script_tag(0, attrib={'id': 'toto'})

    assert post_processor.root[0].tag == 'script'
    assert post_processor.root[0].get('id') == 'toto'


def test_post_processor_remove_title(post_processor):
    post_processor._remove_title()
    root = post_processor.root
    resultats = root.xpath("ns:g[@id='graph0']/ns:title", namespaces={'ns': SVG_NAMESPACE})

    assert len(resultats) == 0


@pytest.mark.parametrize("post_processor", [SIMPLE_PLAYBOOK_SVG], indirect=True)
def test_post_processor_without_graph_representation(post_processor, tmpdir):
    """
    Test the post processor without a graph representation
    :param post_processor:
    :param tmpdir:
    :return:
    """
    svg_path_out = "simple_playbook_postproccess.svg"
    svg_post_proccessed_path = tmpdir.join(svg_path_out)

    post_processor.post_process()

    post_processor.write(output_filename=svg_post_proccessed_path.strpath)

    root = etree.parse(svg_post_proccessed_path.strpath).getroot()
    _assert_common_svg(root)

    # no links should be in the svg when there is no graph_representation
    assert len(root.xpath("//links")) == 0


@pytest.mark.parametrize("grapher", [SIMPLE_PLAYBOOK_YML], indirect=True)
def test_post_processor_with_graph_representation(grapher):
    grapher.make_graph()

    #post_processor = PostProcessor(svg_path=grapher.output_filename + ".svg")
