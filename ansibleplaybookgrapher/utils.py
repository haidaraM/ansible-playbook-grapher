import os
from typing import Dict, List, Tuple

from ansible.parsing.dataloader import DataLoader
from ansible.playbook import Play
from ansible.playbook.role_include import IncludeRole
from ansible.playbook.task import Task
from ansible.playbook.task_include import TaskInclude
from ansible.template import Templar
from colour import Color
from lxml import etree

JQUERY = 'https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js'
SVG_NAMESPACE = "http://www.w3.org/2000/svg"

_ROOT = os.path.abspath(os.path.dirname(__file__))


def clean_name(name: str):
    """
    Clean a name for the node, edge...
    Because every name we use is double quoted,
    then we just have to convert double quotes to html special char
    See https://www.graphviz.org/doc/info/lang.html on the bottom.

    :param name: pretty name of the object
    :return: string with double quotes converted to html special char
    """
    return name.strip().replace('"', "&#34;")


class GraphRepresentation:
    """
    A simple structure to represent the link between the node of the graph. It's used during the postprocessing of the
    svg to add these links in order to highlight the nodes and edge on hover.
    """

    def __init__(self, graph_dict: Dict[str, List] = None):
        if graph_dict is None:
            graph_dict = {}
        self.graph_dict = graph_dict

    def add_node(self, node_name: str):
        if node_name not in self.graph_dict:
            self.graph_dict[node_name] = []

    def add_link(self, node1: str, node2: str):
        self.add_node(node1)
        edges = self.graph_dict[node1]
        edges.append(node2)
        self.graph_dict[node1] = edges


def _get_data_absolute_path(path: str) -> str:
    """
    Return the data absolute path
    :param path:
    :return:
    """
    return os.path.join(_ROOT, 'data', path)


def _read_data(filename: str) -> str:
    """
    Read the script and return is as string
    :param filename:
    :return:
    """
    javascript_path = _get_data_absolute_path(filename)

    with open(javascript_path) as javascript:
        return javascript.read()


def get_play_colors(play: Play) -> Tuple[str, str]:
    """
    Generate two colors (in hex) for a given play: the main color and the color to use as a font color
    :param play
    :return:
    """
    # TODO: Check the if the picked color is (almost) white. We can't see a white edge on the graph
    picked_color = Color(pick_for=play)
    play_font_color = "#000000" if picked_color.get_luminance() > 0.6 else "#ffffff"

    return picked_color.get_hex_l(), play_font_color


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
            if self.root.xpath("ns:g/*[@id='%s']" % node, namespaces={'ns': SVG_NAMESPACE}):
                element = self.root.xpath("ns:g/*[@id='%s']" % node, namespaces={'ns': SVG_NAMESPACE})[0]
            root_subelement = etree.Element('links')

            for link in node_links:
                root_subelement.append(etree.Element('link', attrib={'target': link}))

            element.append(root_subelement)


def has_role_parent(task_block: Task) -> bool:
    """
    Check if one of the parent of the task or block is a role
    :param task_block:
    :return:
    """
    parent = task_block._parent
    while parent:
        if parent._role:
            return True
        parent = parent._parent

    return False


def handle_include_path(original_task: TaskInclude, loader: DataLoader, templar: Templar) -> str:
    """
    Handle include path. We may have some nested includes with relative paths to handle.

    This function is widely inspired by the static method ansible uses when executing the playbook.
    See :func:`~ansible.playbook.included_file.IncludedFile.process_include_results`

    :param original_task:
    :param loader:
    :param templar:
    :return:
    """
    parent_include = original_task._parent
    include_file = None
    # task path or role name
    include_param = original_task.args.get('_raw_params', original_task.args.get('name', None))

    cumulative_path = None
    while parent_include is not None:
        if not isinstance(parent_include, TaskInclude):
            parent_include = parent_include._parent
            continue
        if isinstance(parent_include, IncludeRole):
            parent_include_dir = parent_include._role_path
        else:
            parent_include_dir = os.path.dirname(templar.template(parent_include.args.get('_raw_params')))

        if cumulative_path is not None and not os.path.isabs(cumulative_path):
            cumulative_path = os.path.join(parent_include_dir, cumulative_path)
        else:
            cumulative_path = parent_include_dir
        include_target = templar.template(include_param)
        if original_task._role:
            new_basedir = os.path.join(original_task._role._role_path, 'tasks', cumulative_path)
            candidates = [loader.path_dwim_relative(original_task._role._role_path, 'tasks', include_target),
                          loader.path_dwim_relative(new_basedir, 'tasks', include_target)]
            for include_file in candidates:
                try:
                    # may throw OSError
                    os.stat(include_file)
                    # or select the task file if it exists
                    break
                except OSError:
                    pass
        else:
            include_file = loader.path_dwim_relative(loader.get_basedir(), cumulative_path, include_target)

        if os.path.exists(include_file):
            break
        else:
            parent_include = parent_include._parent

    if include_file is None:
        if original_task._role:
            include_target = templar.template(include_param)
            include_file = loader.path_dwim_relative(original_task._role._role_path, 'tasks', include_target)
        else:
            include_file = loader.path_dwim(templar.template(include_param))

    return include_file
