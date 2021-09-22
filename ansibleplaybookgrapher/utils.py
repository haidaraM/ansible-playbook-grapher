import os
import uuid
from typing import Tuple, List

from ansible.parsing.dataloader import DataLoader
from ansible.parsing.yaml.objects import AnsibleUnicode
from ansible.playbook.role_include import IncludeRole
from ansible.playbook.task import Task
from ansible.playbook.task_include import TaskInclude
from ansible.template import Templar
from colour import Color


def convert_when_to_str(when: List[AnsibleUnicode]) -> str:
    """
    Convert ansible conditional when to str
    :param when:
    :return:
    """

    return f"[when: {' and '.join(when)}]" if len(when) > 0 else ""


def generate_id(prefix: str = "") -> str:
    """
    Generate an uuid to be used as id
    :param prefix Prefix to add to the generated ID
    """
    return prefix + str(uuid.uuid4())


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


def get_play_colors(play) -> Tuple[str, str]:
    """
    Generate two colors (in hex) for a given play: the main color and the color to use as a font color
    :param play
    :return:
    """
    # TODO: Check the if the picked color is (almost) white. We can't see a white edge on the graph
    picked_color = Color(pick_for=play)
    play_font_color = "#000000" if picked_color.get_luminance() > 0.6 else "#ffffff"

    return picked_color.get_hex_l(), play_font_color


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
