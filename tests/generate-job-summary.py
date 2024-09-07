import os
from pathlib import Path

from jinja2 import Template

DIR_PATH = Path(__file__).parent.resolve()


def list_mermaid_files() -> list[str]:
    """Return the list of files matching the pattern
    :return:
    """
    return list(map(str, Path(os.environ["MERMAID_FILES_PATH"]).rglob("*.mmd")))


if __name__ == "__main__":
    with (DIR_PATH / "job-summary.md.j2").open() as template_file:
        template = Template(template_file.read())

    mermaid_files = list_mermaid_files()
    matrix_job_identifier = os.environ["MATRIX_JOB_IDENTIFIER"]
    files = []
    for filename in mermaid_files:
        files.append({"name": filename, "content": Path(filename).open().read()})

    print(template.render(files=files, matrix_job_identifier=matrix_job_identifier))
