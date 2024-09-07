import glob
import os

from jinja2 import Template

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def list_files(path_pattern: str) -> list[str]:
    """Return the list of files matching the pattern
    :param path_pattern:
    :return:
    """
    return glob.glob(path_pattern)


if __name__ == "__main__":
    with open(os.path.join(DIR_PATH, "job-summary.md.j2")) as template_file:
        template = Template(template_file.read())

    mermaid_files = list_files(f"{os.environ['MERMAID_FILES_PATH']}/*.mmd")
    matrix_job_identifier = os.environ["MATRIX_JOB_IDENTIFIER"]
    files = []
    for filename in mermaid_files:
        files.append({"name": filename, "content": open(filename).read()})
