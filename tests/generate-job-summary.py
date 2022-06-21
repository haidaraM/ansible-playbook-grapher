import glob
import os
from typing import List

from jinja2 import Template

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def list_svg_files(path_pattern: str) -> List[str]:
    """

    :param path_pattern:
    :return:
    """
    return glob.glob(path_pattern)


if __name__ == "__main__":
    with open(os.path.join(DIR_PATH, "job-summary.md.j2")) as template_file:
        template = Template(template_file.read())

    svg_files = list_svg_files(f"{os.environ['SVG_FILES_PATH']}/*.svg")
    links = []
    for f in svg_files:
        links.append(
            f"https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/{os.environ['SVG_COMMIT_HASH']}/{f}"
        )

    print(template.render(svg_files=links))
