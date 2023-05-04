from _elementtree import Element

import pytest
from lxml import etree

from ansibleplaybookgrapher.graph import PlaybookNode, PlayNode, TaskNode
from ansibleplaybookgrapher.renderer.postprocessor import GraphVizPostProcessor, SVG_NAMESPACE
from tests import SIMPLE_PLAYBOOK_SVG


@pytest.fixture(name="post_processor")
def fixture_simple_postprocessor(request):
    """
    Return a post processor without a graph structure and with the simple_playbook_no_postproccess
    :return:
    """
    try:
        svg_path = request.param
    except AttributeError:
        # if the svg is not provided, we use the simple one
        svg_path = SIMPLE_PLAYBOOK_SVG

    post_processor = GraphVizPostProcessor(svg_path=svg_path)
    return post_processor


def _assert_common_svg(svg_root: Element):
    """
    Assert some common structures of the generated svg
    :param svg_root:
    :return:
    """

    assert svg_root.get("id") == "svg"

    # jquery must be the first element because the next script need jquery
    assert svg_root[0].get("id") == "jquery"
    assert svg_root[1].get("id") == "my_javascript"
    assert svg_root[2].get("id") == "my_css"


def test_post_processor_insert_tag(post_processor: GraphVizPostProcessor):
    """
    Test method insert_tag of the PostProcessor
    :param post_processor:
    :return:
    """
    post_processor.insert_script_tag(0, attrib={"id": "toto"})

    assert post_processor.root[0].tag == "script"
    assert post_processor.root[0].get("id") == "toto"


def test_post_processor_write(post_processor: GraphVizPostProcessor, tmpdir):
    """
    Test method write of the PostProcessor
    :param post_processor:
    :return:
    """
    svg_post_processed_path = tmpdir.join("test_post_processor_write.svg")
    post_processor.write(output_filename=svg_post_processed_path.strpath)

    assert svg_post_processed_path.check(file=1)


@pytest.mark.parametrize("post_processor", [SIMPLE_PLAYBOOK_SVG], indirect=True)
def test_post_processor_without_graph_representation(
    post_processor: GraphVizPostProcessor, tmpdir
):
    """
    Test the post processor without a graph representation
    :param post_processor:
    :param tmpdir:
    :return:
    """
    svg_post_processed_path = tmpdir.join("simple_playbook_postprocess_no_graph.svg")

    post_processor.post_process()

    post_processor.write(output_filename=svg_post_processed_path.strpath)

    assert svg_post_processed_path.check(file=1)

    root = etree.parse(svg_post_processed_path.strpath).getroot()
    _assert_common_svg(root)

    # no links should be in the svg when there is no graph_representation
    assert len(root.xpath("//ns:links", namespaces={"ns": SVG_NAMESPACE})) == 0


@pytest.mark.parametrize("post_processor", [SIMPLE_PLAYBOOK_SVG], indirect=True)
def test_post_processor_with_graph_representation(
    post_processor: GraphVizPostProcessor, tmpdir
):
    """
    Test the post processor for a graph representation
    :param post_processor:
    :param tmpdir:
    :return:
    """
    playbook_node = PlaybookNode("")
    svg_post_processed_path = tmpdir.join("simple_playbook_postprocess_graph.svg")

    play = PlayNode("play 1", node_id="play_hostsall")
    playbook_node.add_node("plays", play)
    task_1 = TaskNode("task 1")
    task_2 = TaskNode("task 1")
    play.add_node("tasks", task_1)
    play.add_node("tasks", task_2)

    post_processor.post_process([playbook_node])

    post_processor.write(output_filename=svg_post_processed_path.strpath)

    assert svg_post_processed_path.check(file=1)

    root = etree.parse(svg_post_processed_path.strpath).getroot()

    _assert_common_svg(root)
    elements_links = root.xpath(
        f"ns:g/*[@id='{play.id}']//ns:link", namespaces={"ns": SVG_NAMESPACE}
    )
    assert len(elements_links) == 2, "Play should have two links"
    assert [task_1.id, task_2.id] == [
        e.get("target") for e in elements_links
    ], "The tasks ID should equal to the targets"
