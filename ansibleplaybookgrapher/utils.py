import os
import xml.etree.ElementTree as etree

JQUERY = 'https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js'

_ROOT = os.path.abspath(os.path.dirname(__file__))


class GraphRepresentation(object):
    """
    https://www.python-course.eu/graphs_python.php
    """

    def __init__(self, graph_dict=None):
        """ initializes a graph object
            If no dictionary or None is given,
            an empty dictionary will be used
        """
        if graph_dict is None:
            graph_dict = {}
        self.graph_dict = graph_dict

    def add_node(self, node_name):
        if node_name not in self.graph_dict:
            self.graph_dict[node_name] = []

    def add_edge(self, node1, node2):
        edges = self.graph_dict[node1]
        edges.append(node2)
        self.graph_dict[node1] = edges

    def __str__(self):
        print(self.graph_dict)


# cdata support https://gist.github.com/zlalanne/5711847
def CDATA(text=None):
    element = etree.Element('![CDATA[')
    element.text = text
    return element


etree._original_serialize_xml = etree._serialize_xml


def _serialize_xml(write, elem, qnames, namespaces, short_empty_elements, **kwargs):
    if elem.tag == '![CDATA[':
        write("<%s%s]]>" % (elem.tag, elem.text))
        return
    return etree._original_serialize_xml(
        write, elem, qnames, namespaces, short_empty_elements, **kwargs)


etree._serialize_xml = etree._serialize['xml'] = _serialize_xml


def get_data_absolute_path(path):
    """
    Return the data absolute path
    :param path:
    :return:
    """
    return os.path.join(_ROOT, 'data', path)


def _read_java_script(filename="highlight-hover.js"):
    """
    Read the script and return is as string
    :param filename:
    :return:
    """
    javascript_path = get_data_absolute_path(filename)

    with open(javascript_path) as javascript:
        return javascript.read()


def _read_css(filename):
    style_path = get_data_absolute_path(filename)

    with open(style_path) as style:
        return style.read()


def insert_javascript_elements(svg_root):
    """
    Insert the required elements needed to run javascript
    :param svg_root:
    :return:
    """
    # jquery tag
    jquery_element = etree.Element("script", attrib={'type': 'text/javascript', 'xlink:href': JQUERY})

    # insert jquery script tag
    svg_root.insert(0, jquery_element)

    snap = _read_java_script('snap.svg-min.js')
    snap_element = etree.Element('script', attrib={'type': 'text/javascript'})
    snap_element.append(CDATA("\n" + snap))
    svg_root.insert(1, snap_element)

    javascript = _read_java_script()

    javascript_element = etree.Element('script', attrib={'type': 'text/javascript'})
    javascript_element.append(CDATA("\n" + javascript))

    svg_root.insert(2, javascript_element)


def insert_css_element(svg_root, css_filename):
    """
    Insert css style
    :param css_filename:
    :param svg_root:
    :return:
    """
    style_element = etree.Element("style", attrib={'type': 'text/css'})

    style = _read_css(css_filename)
    style_element.append(CDATA("\n" + style))

    svg_root.insert(2, style_element)


def insert_graph_representation(tree, graph_representation):
    for node, node_edges in graph_representation.graph_dict.items():
        element = tree.find("./ns:g/*[@id='%s']" % node,
                            namespaces={'ns': 'http://www.w3.org/2000/svg'})

        root_subelement = etree.Element('links')

        for e in node_edges:
            root_subelement.append(etree.Element('link', attrib={'target': e}))

        element.append(root_subelement)

def post_process_svg(svg_filename, graph_representation):
    """
    Post process the svg as xml to add the javascript files
    :param svg_filename:
    :return:
    """
    etree.register_namespace("", "http://www.w3.org/2000/svg")
    tree = etree.parse(svg_filename)
    svg_root = tree.getroot()

    svg_root.set("xmlns:xlink", "http://www.w3.org/1999/xlink")  # xlink namespace

    # add an id to the root
    svg_root.set("id", "svg")

    insert_javascript_elements(svg_root)
    insert_css_element(svg_root, "graph.css")

    insert_graph_representation(tree, graph_representation)

    tree.write(svg_filename, xml_declaration=True, encoding="UTF-8")
    pass
