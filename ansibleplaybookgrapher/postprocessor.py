import os
from typing import Dict

from lxml import etree

from ansibleplaybookgrapher.utils import GraphRepresentation

JQUERY = 'https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js'
SVG_NAMESPACE = "http://www.w3.org/2000/svg"


def _read_data(filename: str) -> str:
    """
    Read the script and return is as string
    :param filename:
    :return:
    """
    current_dir = os.path.abspath(os.path.dirname(__file__))
    javascript_path = os.path.join(current_dir, 'data', filename)

    with open(javascript_path) as javascript:
        return javascript.read()


class PostProcessor:
    """
    Post process the svg by adding some javascript and css
    """

    def __init__(self, svg_path: str):
        """

        :param svg_path:
        """
        self.svg_path = svg_path
        self.tree = etree.parse(svg_path)
        self.root = self.tree.getroot()

    def insert_script_tag(self, index: int, attrib: Dict):
        """

        :param index:
        :param attrib:
        :return:
        """
        element_script_tag = etree.Element('script', attrib=attrib)

        self.root.insert(index, element_script_tag)

    def insert_cdata(self, index: int, tag: str, attrib: Dict, cdata_text: str):
        """
        Insert cdata in the SVG
        :param index:
        :param tag:
        :param attrib:
        :param cdata_text:
        :return:
        """
        element = etree.Element(tag, attrib=attrib)
        element.text = etree.CDATA(cdata_text)

        self.root.insert(index, element)

    def post_process(self, graph_representation: GraphRepresentation = None, *args, **kwargs):
        """

        :param graph_representation:
        :param args:
        :param kwargs:
        :return:
        """
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

        if graph_representation:
            # Insert the graph representation for the links between the nodes
            self._insert_graph_representation(graph_representation)

    def write(self, output_filename: str = None):
        if output_filename is None:
            output_filename = self.svg_path

        self.tree.write(output_filename, xml_declaration=True, encoding="UTF-8")

    def _insert_graph_representation(self, graph_representation: GraphRepresentation):
        """
        Insert graph in the SVG
        """
        for node, node_links in graph_representation.graph_dict.items():

            # Find the group g with the specified id
            xpath_result = self.root.xpath("ns:g/*[@id='%s']" % node, namespaces={'ns': SVG_NAMESPACE})
            if xpath_result:
                element = xpath_result[0]
                root_subelement = etree.Element('links')
                for link in node_links:
                    root_subelement.append(etree.Element('link', attrib={'target': link}))

                element.append(root_subelement)
