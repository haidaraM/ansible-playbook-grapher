import os

from lxml import etree

JQUERY = 'https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js'
SVG_NAMESPACE = "http://www.w3.org/2000/svg"

_ROOT = os.path.abspath(os.path.dirname(__file__))


def clean_name(name):
    """
    Clean a name for the node, edge...
    :param name:
    :return:
    """
    return name.strip()


def clean_id(identifier):
    """
    Remove special characters from the string
    :param identifier:
    :return:
    """
    chars_to_remove = [' ', '[', ']', ':', '-', ',', '.', '(', ')', '#', '/', '|', '{', '}', '&', '~']
    for c in chars_to_remove:
        identifier = identifier.replace(c, '')
    return identifier


class GraphRepresentation(object):
    """
    A simple structure to represent the link between the node of the graph. It's used during the postprocessing of the svg
    to add these links in order to highlight the nodes and edge on hover.
    """

    def __init__(self, graph_dict=None):
        if graph_dict is None:
            graph_dict = {}
        self.graph_dict = graph_dict

    def add_node(self, node_name):
        if node_name not in self.graph_dict:
            self.graph_dict[node_name] = []

    def add_link(self, node1, node2):
        self.add_node(node1)
        edges = self.graph_dict[node1]
        edges.append(node2)
        self.graph_dict[node1] = edges

    def __str__(self):
        print(self.graph_dict)


def _get_data_absolute_path(path):
    """
    Return the data absolute path
    :param path:
    :return:
    """
    return os.path.join(_ROOT, 'data', path)


def _read_data(filename):
    """
    Read the script and return is as string
    :param filename:
    :return:
    """
    javascript_path = _get_data_absolute_path(filename)

    with open(javascript_path) as javascript:
        return javascript.read()


def insert_javascript_elements(svg_root):
    """
    Insert the required elements needed to run javascript
    :param svg_root:
    :return:
    """
    # jquery tag
    jquery_element = etree.Element("script", attrib={'type': 'text/javascript', 'href': JQUERY})

    # insert jquery script tag
    svg_root.insert(0, jquery_element)

    javascript = _read_data("highlight-hover.js")

    javascript_element = etree.Element('script', attrib={'type': 'text/javascript'})
    javascript_element.text = etree.CDATA("\n" + javascript)

    svg_root.insert(1, javascript_element)


def insert_css_element(svg_root, css_filename):
    """
    Insert css style
    :param css_filename:
    :param svg_root:
    :return:
    """
    style_element = etree.Element("style", attrib={'type': 'text/css'})

    style = _read_data(css_filename)
    style_element.text = etree.CDATA("\n" + style)

    svg_root.insert(2, style_element)


def insert_graph_representation(tree, graph_representation):
    """
    Insert the graph representation in the svg
    :param tree:
    :param graph_representation:
    :return:
    """
    for node, node_links in graph_representation.graph_dict.items():
        # Find the group g with the specified id
        element = tree.find("./ns:g/*[@id='%s']" % node, namespaces={'ns': SVG_NAMESPACE})

        root_subelement = etree.Element('links')

        for link in node_links:
            root_subelement.append(etree.Element('link', attrib={'target': link}))

        element.append(root_subelement)


def post_process_svg(svg_filename, graph_representation):
    """
    Post process the svg as xml to add the javascript and css and the links between the nodes
    :param graph_representation:
    :param svg_filename:
    :return:
    """
    tree = etree.parse(svg_filename)
    svg_root = tree.getroot()

    svg_root.set("id", "svg")

    insert_javascript_elements(svg_root)
    insert_css_element(svg_root, "graph.css")

    insert_graph_representation(tree, graph_representation)

    tree.write(svg_filename, xml_declaration=True, encoding="UTF-8")
