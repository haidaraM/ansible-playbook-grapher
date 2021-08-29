import os
from typing import Dict

from lxml import etree

from ansibleplaybookgrapher.graph import PlaybookNode

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

    def post_process(self, playbook_node: PlaybookNode = None, *args, **kwargs):
        """

        :param playbook_node:
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

        if playbook_node:
            # Insert the graph representation for the links between the nodes
            self._insert_graph_representation(playbook_node)

    def write(self, output_filename: str = None):
        """
        Write the svg in the given filename
        :param output_filename:
        :return:
        """
        if output_filename is None:
            output_filename = self.svg_path

        self.tree.write(output_filename, xml_declaration=True, encoding="UTF-8")

    def _insert_graph_representation(self, graph_representation: PlaybookNode):
        """
        Insert graph in the SVG
        """
        links_structure = graph_representation.links_structure()
        for node, node_links in links_structure.items():
            # Find the group g with the specified id
            xpath_result = self.root.xpath("ns:g/*[@id='%s']" % node.id, namespaces={'ns': SVG_NAMESPACE})
            if xpath_result:
                element = xpath_result[0]
                root_subelement = etree.Element('links')
                for link in node_links:
                    root_subelement.append(etree.Element('link', attrib={'target': link.id}))

                element.append(root_subelement)
