import os
import xml.etree.ElementTree as etree

JQUERY = 'https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js'

_ROOT = os.path.abspath(os.path.dirname(__file__))


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


def post_process_svg(svg_filename):
    """
    Post process the svg as xml to add the javascript files
    :param svg_filename:
    :return:
    """
    tree = etree.parse(svg_filename)
    etree.register_namespace("", "http://www.w3.org/2000/svg")
    svg_root = tree.getroot()

    svg_root.set("xmlns:xlink", "http://www.w3.org/1999/xlink")  # xlink namespace

    # jquery tag
    jquery_element = etree.Element("script", attrib={'type': 'text/javascript', 'xlink:href': JQUERY})

    # insert jquery script tag
    svg_root.insert(0, jquery_element)

    javascript = _read_java_script()

    javascript_element = etree.Element('script', attrib={'type': 'text/javascript'})
    javascript_element.append(CDATA(javascript))

    svg_root.insert(1, javascript_element)

    tree.write(svg_filename, xml_declaration=True, encoding="UTF-8")
