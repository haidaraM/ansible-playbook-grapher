import pytest
from lxml import etree

from ansibleplaybookgrapher.utils import PostProcessor, SVG_NAMESPACE, GraphRepresentation
from tests import SIMPLE_PLAYBOOK_SVG


@pytest.fixture(name='post_processor')
def fixture_simple_postprocessor(request):
    """
    Return a post processor without a graph representation and with the simple_playbook_no_postproccess
    :return:
    """
    try:
        svg_path = request.param
    except AttributeError:
        # if the svg is not provided, we use the simple one
        svg_path = SIMPLE_PLAYBOOK_SVG

    post_processor = PostProcessor(svg_path=svg_path)
    return post_processor


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
    """
    Test method insert_tag of the PostProcessor
    :param post_processor:
    :return:
    """
    post_processor.insert_script_tag(0, attrib={'id': 'toto'})

    assert post_processor.root[0].tag == 'script'
    assert post_processor.root[0].get('id') == 'toto'


def test_post_processor_write(post_processor, tmpdir):
    """
    Test method write of the PostProcessor
    :param post_processor:
    :return:
    """
    svg_post_proccessed_path = tmpdir.join("test_post_processor_write.svg")
    post_processor.write(output_filename=svg_post_proccessed_path.strpath)

    assert svg_post_proccessed_path.check(file=1)


@pytest.mark.parametrize("post_processor", [SIMPLE_PLAYBOOK_SVG], indirect=True)
def test_post_processor_without_graph_representation(post_processor, tmpdir):
    """
    Test the post processor without a graph representation
    :param post_processor:
    :param tmpdir:
    :return:
    """
    svg_post_proccessed_path = tmpdir.join("simple_playbook_postproccess_no_graph.svg")

    post_processor.post_process()

    post_processor.write(output_filename=svg_post_proccessed_path.strpath)

    assert svg_post_proccessed_path.check(file=1)

    root = etree.parse(svg_post_proccessed_path.strpath).getroot()
    _assert_common_svg(root)

    # no links should be in the svg when there is no graph_representation
    assert len(root.xpath("//ns:links", namespaces={'ns': SVG_NAMESPACE})) == 0


@pytest.mark.parametrize("post_processor", [SIMPLE_PLAYBOOK_SVG], indirect=True)
def test_post_processor_with_graph_representation(post_processor, tmpdir):
    """
    Test the post processor a graph representation
    :param post_processor:
    :param tmpdir:
    :return:
    """
    graph_represention = GraphRepresentation()
    svg_post_proccessed_path = tmpdir.join("simple_playbook_postproccess_graph.svg")

    play_id = "play_hostsall"
    # link from play to task edges
    graph_represention.add_link(play_id, "play_hostsallpost_taskPosttask1")
    graph_represention.add_link(play_id, "play_hostsallpost_taskPosttask2")

    post_processor.post_process(graph_represention)

    post_processor.write(output_filename=svg_post_proccessed_path.strpath)

    assert svg_post_proccessed_path.check(file=1)

    root = etree.parse(svg_post_proccessed_path.strpath).getroot()

    _assert_common_svg(root)

    assert len(root.xpath("ns:g/*[@id='%s']//ns:link" % play_id, namespaces={'ns': SVG_NAMESPACE})) == 2
