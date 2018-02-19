import os
import hashlib
from lxml import etree

JQUERY = 'https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js'
SVG_NAMESPACE = "http://www.w3.org/2000/svg"

_ROOT = os.path.abspath(os.path.dirname(__file__))


def clean_name(name):
    """
    Clean a name for the node, edge...
    Because every name we use is double quoted,
    then we just have to convert double quotes to html special char
    See https://www.graphviz.org/doc/info/lang.html on the bottom.

    :param name: pretty name of the object
    :return: string with double quotes converted to html special char
    """
    return name.strip().replace('"', "&#34;")


def clean_id(identifier):
    """
    Convert name to md5 to avoid issues with special chars,
    The ID are not visible to end user in web/rendered graph so we do
    not have to care to make them look pretty.
    There are chances for hash collisions but we do not care for that
    so much in here.
    :param identifier: string which represents id
    :return: string representing a hex hash
    """

    m = hashlib.md5()
    m.update(identifier.encode('utf-8'))
    return m.hexdigest()


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


class PostProcessor(object):
    """
    Post process the svg by adding some javascript and css
    """

    def __init__(self, svg_path):
        self.svg_path = svg_path
        self.tree = etree.parse(svg_path)
        self.root = self.tree.getroot()

    def insert_script_tag(self, index, attrib):
        element_script_tag = etree.Element('script', attrib=attrib)

        self.root.insert(index, element_script_tag)

    def insert_cdata(self, index, tag, attrib, cdata_text):
        element = etree.Element(tag, attrib=attrib)
        element.text = etree.CDATA(cdata_text)

        self.root.insert(index, element)

    def _remove_title(self):
        """
        There is title tag in the graph (<title>%3</title>) that I can't change for the moment. So I remove it
        :return:
        """
        # element g with id=graph0 is the root group for the graph.
        graph_group_element = self.root.xpath("ns:g[@id='graph0']", namespaces={'ns': SVG_NAMESPACE})[0]
        title_element = graph_group_element.xpath("ns:title", namespaces={'ns': SVG_NAMESPACE})[0]

        graph_group_element.remove(title_element)

    def post_process(self, graph_representation=None, *args, **kwargs):

        self.root.set('id', 'svg')

        jquery_tag_index = 0
        javascript_tag_index = 1
        css_tag_index = 2

        # insert jquery
        self.insert_script_tag(jquery_tag_index, attrib={'type': 'text/javascript', 'href': JQUERY, 'id': 'jquery'})

        # insert my javascript
        highlight_script = _read_data("highlight-hover.js")
        self.insert_cdata(javascript_tag_index, 'script', attrib={'type': 'text/javascript', 'id': 'my_javascript'},
                          cdata_text=highlight_script)

        css = _read_data("graph.css")

        # insert my css
        self.insert_cdata(css_tag_index, 'style', attrib={'type': 'text/css', 'id': 'my_css'}, cdata_text=css)

        self._remove_title()

        if graph_representation:
            # insert the graph representation for the links between the nodes
            self._insert_graph_representation(graph_representation)

    def write(self, output_filename=None):
        if output_filename is None:
            output_filename = self.svg_path

        self.tree.write(output_filename, xml_declaration=True, encoding="UTF-8")

    def _insert_graph_representation(self, graph_representation):
        for node, node_links in graph_representation.graph_dict.items():
            # Find the group g with the specified id
            element = self.root.xpath("ns:g/*[@id='%s']" % node, namespaces={'ns': SVG_NAMESPACE})[0]

            root_subelement = etree.Element('links')

            for link in node_links:
                root_subelement.append(etree.Element('link', attrib={'target': link}))

            element.append(root_subelement)
