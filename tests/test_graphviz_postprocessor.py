from _elementtree import Element

import pytest
from lxml import etree

from ansibleplaybookgrapher.graph_model import PlaybookNode, PlayNode, TaskNode
from ansibleplaybookgrapher.renderer.graphviz.postprocessor import (
    SVG_NAMESPACE,
    GraphvizPostProcessor,
)
from tests import FIXTURES_DIR_PATH

SIMPLE_PLAYBOOK_SVG = FIXTURES_DIR_PATH / "simple_playbook_no_postproccess.svg"


@pytest.fixture(name="post_processor")
def fixture_simple_postprocessor(
    request: pytest.FixtureRequest,
) -> GraphvizPostProcessor:
    """Return a post processor without a graph structure and with the simple_playbook_no_postproccess
    :return:
    """
    try:
        svg_path = request.param
    except AttributeError:
        # if the svg is not provided, we use the simple one
        svg_path = SIMPLE_PLAYBOOK_SVG

    return GraphvizPostProcessor(svg_path=svg_path)


def _assert_common_svg(svg_root: Element) -> None:
    """Assert some common structures of the generated svg
    :param svg_root:
    :return:
    """
    assert svg_root.get("id") == "svg"

    # jquery must be the first element because the next script need jquery
    assert svg_root[0].get("id") == "jquery"
    assert svg_root[1].get("id") == "my_javascript"
    assert svg_root[2].get("id") == "my_css"


def test_post_processor_insert_tag(post_processor: GraphvizPostProcessor) -> None:
    """Test method insert_tag of the PostProcessor
    :param post_processor:
    :return:
    """
    post_processor.insert_script_tag(0, attrib={"id": "toto"})

    assert post_processor.root[0].tag == "script"
    assert post_processor.root[0].get("id") == "toto"


def test_post_processor_write(post_processor: GraphvizPostProcessor, tmpdir) -> None:  # noqa: ANN001
    """Test method write of the PostProcessor
    :param post_processor:
    :return:
    """
    svg_post_processed_path = tmpdir.join("test_post_processor_write.svg")
    post_processor.write(output_filename=svg_post_processed_path.strpath)

    assert svg_post_processed_path.check(file=1)


@pytest.mark.parametrize("post_processor", [SIMPLE_PLAYBOOK_SVG], indirect=True)
def test_post_processor_without_graph_representation(
    post_processor: GraphvizPostProcessor,
    tmpdir,  # noqa: ANN001
) -> None:
    """Test the post processor without a graph representation
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
    post_processor: GraphvizPostProcessor,
    tmpdir,  # noqa: ANN001
) -> None:
    """Test the post processor for a graph representation
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
        f"ns:g/*[@id='{play.id}']//ns:link",
        namespaces={"ns": SVG_NAMESPACE},
    )
    assert len(elements_links) == 2, "Play should have two links"
    assert [task_1.id, task_2.id] == [
        e.get("target") for e in elements_links
    ], "The tasks ID should equal to the targets"
