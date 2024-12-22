# Copyright (C) 2024 Mohamed El Mouctar HAIDARA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Type, TypeVar

from ansible.playbook.handler import Handler

from ansibleplaybookgrapher.utils import generate_id, get_play_colors


class LoopMixin:
    """A mixin class for nodes that support looping."""

    def has_loop(self) -> bool:
        """Return true if the node has a loop (`loop` or `with_`).
        https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_loops.html
        :return:
        """
        if self.raw_object is None:
            return False
        return self.raw_object.loop is not None


@dataclass
class NodeLocation:
    """The node location on the filesystem.
    The location can be a folder (for roles) or a specific line and column inside a file.
    """

    type: str  # file or folder
    path: str | None = None
    line: int | None = None
    column: int | None = None

    def __post_init__(self):
        if self.type not in ["folder", "file"]:
            msg = f"Type '{self.type}' not supported. Valid values: file, folder."
            raise ValueError(
                msg,
            )


class Node:
    """A node in the graph. Everything of the final graph is a node: playbook, plays, tasks and roles."""

    def __init__(
        self,
        node_name: str,
        node_id: str,
        when: str = "",
        raw_object: Any = None,
        parent: "Node" = None,
    ) -> None:
        """:param node_name: The name of the node
        :param node_id: An identifier for this node
        :param when: The conditional attached to the node
        :param raw_object: The raw ansible object matching this node in the graph. Will be None if there is no match on
        Ansible side
        :param parent: The parent node of this node
        """
        self.name = node_name
        self.parent = parent
        self.id = node_id
        self.when = when
        self.raw_object = raw_object

        self.location: NodeLocation | None = None
        self.set_location()

        # The index of this node in the parent node if it has one (starting from 1)
        self.index: int | None = None

    def display_name(self) -> str:
        """Return the display name of the node.

        It's composed of the ID prefix between brackets and the name of the node.
        Examples:
         - [playbook] My playbook
         - [play] My play
         - [pre_task] My pre task
         - [role] My role
         - [task] My task
         - [block] My block
         - [post_task] My post task

        :return:
        """
        try:
            split = self.id.split("_")
            id_prefix = "_".join(split[:-1])
            return f"[{id_prefix}] {self.name}"
        except IndexError:
            return self.name

    def set_location(self) -> None:
        """Set the location of this node based on the raw object. Not all objects have path.

        :return:
        """

        if self.raw_object and self.raw_object.get_ds():
            if hasattr(self.raw_object.get_ds(), "ansible_pos"):
                path, line, column = self.raw_object.get_ds().ansible_pos
                # By default, it's a file
                self.location = NodeLocation(
                    type="file",
                    path=path,
                    line=line,
                    column=column,
                )
            else:
                # Here we likely have a task with a validate argument spec task inserted by Ansible
                pass

    def get_first_parent_matching_type(self, node_type: type) -> type:
        """Get the first parent of this node matching the given type.

        :param node_type: The type of the parent node to get.
        :return:
        """
        current_parent = self.parent

        while current_parent is not None:
            if isinstance(current_parent, node_type):
                return current_parent
            current_parent = current_parent.parent

        msg = f"No parent of type {node_type} found for {self}"
        raise ValueError(msg)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name='{self.name}', id='{self.id}')"

    def __eq__(self, other: "Node") -> bool:
        return self.id == other.id

    def __ne__(self, other: "Node") -> bool:
        return not (self == other)

    def __hash__(self):
        return hash(self.id)

    def to_dict(self, **kwargs) -> dict:
        """Return a dictionary representation of this node. This representation is not meant to get the original object
        back.

        :return:
        """
        data = {
            "type": type(self).__name__,
            "id": self.id,
            "name": self.name,
            "when": self.when,
            "index": self.index,
        }

        if self.location is not None:
            data["location"] = asdict(self.location)
        else:
            data["location"] = None

        return data


# TypeVar is used to define a generic type T that is bound to Node. Once we switch to Python >=3.12, we can just use the recommended way: [T]
T = TypeVar("T", bound=Node)


class CompositeNode(Node):
    """A node composed of multiple of nodes:
    - playbook containing plays
    - play containing tasks
    - role containing tasks
    - block containing tasks.
    """

    def __init__(
        self,
        node_name: str,
        node_id: str,
        when: str = "",
        raw_object: Any = None,
        parent: "Node" = None,
        supported_compositions: list[str] | None = None,
    ) -> None:
        """Init a composite node.

        :param node_name:
        :param node_id:
        :param raw_object: The raw ansible object matching this node in the graph. Will be None if there is no match on
        Ansible side
        :param supported_compositions: The list of the supported compositions for this composite node.
        """
        super().__init__(
            node_name=node_name,
            node_id=node_id,
            when=when,
            raw_object=raw_object,
            parent=parent,
        )
        self._supported_compositions = supported_compositions or []
        # The dict will contain the different types of composition: plays, tasks, roles...
        self._compositions = defaultdict(list)  # type: dict[str, list]

    def add_node(self, target_composition: str, node: Node) -> None:
        """Add a node in the target composition.

        :param target_composition: The name of the target composition
        :param node: The node to add in the given composition
        :return:
        """
        if target_composition not in self._supported_compositions:
            msg = f"The target composition '{target_composition}' is unknown. Supported are: {self._supported_compositions}"
            raise ValueError(
                msg,
            )
        self._compositions[target_composition].append(node)

    def calculate_indices(self):
        """
        Calculate the indices of all nodes based on their composition type.
        This is only called when needed.
        """
        current_index = 1
        for comp_type in self._supported_compositions:
            for node in self._compositions[comp_type]:
                node.index = current_index
                current_index += 1

                if isinstance(node, CompositeNode):
                    node.calculate_indices()

    def get_nodes(self, target_composition: str) -> list:
        """Get a node from the compositions.

        :param target_composition:
        :return: A list of the nodes.
        """
        if target_composition not in self._supported_compositions:
            msg = f"The target composition '{target_composition}' is unknown. Supported ones are: {self._supported_compositions}"
            raise Exception(
                msg,
            )

        return self._compositions[target_composition]

    def get_all_tasks(self) -> list["TaskNode"]:
        """Return all the TaskNode inside this composite node.

        :return:
        """
        tasks: list[TaskNode] = []
        self._get_all_nodes_type(TaskNode, tasks)
        return tasks

    def get_all_roles(self) -> list["RoleNode"]:
        """Return all the RoleNode inside this composite node.

        :return:
        """
        roles: list[RoleNode] = []
        self._get_all_nodes_type(RoleNode, roles)
        return roles

    def _get_all_nodes_type(self, node_type: Type[T], acc: list[T]) -> None:
        """Recursively get all roles.

        :param acc: The accumulator
        :return:
        """
        items = self._compositions.items()
        for _, nodes in items:
            for node in nodes:
                if isinstance(node, node_type):
                    acc.append(node)
                elif isinstance(node, CompositeNode):
                    node._get_all_nodes_type(node_type, acc)

    def links_structure(self) -> dict[Node, list[Node]]:
        """Return a representation of the composite node where each key of the dictionary is the node and the
         value is the list of the linked nodes.

        :return:
        """
        links: dict[Node, list[Node]] = defaultdict(list)
        self._get_all_links(links)
        return links

    def _get_all_links(self, links: dict[Node, list[Node]]) -> None:
        """Recursively get the node links.

        :return:
        """
        for nodes in self._compositions.values():
            for node in nodes:
                if isinstance(node, CompositeNode):
                    node._get_all_links(links)
                links[self].append(node)

    def is_empty(self) -> bool:
        """Return true if the composite node is empty, false otherwise.

        :return:
        """
        return all(len(nodes) <= 0 for _, nodes in self._compositions.items())

    def has_node_type(self, node_type: type) -> bool:
        """Return true if the composite node has at least one node of the given type, false otherwise.

        :param node_type: The type of the node
        :return:
        """
        for nodes in self._compositions.values():
            for node in nodes:
                if isinstance(node, node_type):
                    return True

                if isinstance(node, CompositeNode):
                    return node.has_node_type(node_type)

        return False

    def to_dict(self, **kwargs) -> dict:
        """Return a dictionary representation of this composite node. This representation is not meant to get the
        original object back.

        :return:
        """
        node_dict = super().to_dict(**kwargs)

        for composition, nodes in self._compositions.items():
            nodes_dict_list = []
            for node in nodes:
                nodes_dict_list.append(node.to_dict(**kwargs))

            node_dict[composition] = nodes_dict_list

        return node_dict


class PlaybookNode(CompositeNode):
    """A playbook is a list of play."""

    def __init__(
        self,
        node_name: str,
        node_id: str | None = None,
        when: str = "",
        raw_object: Any = None,
    ) -> None:
        super().__init__(
            node_name=node_name,
            node_id=node_id or generate_id("playbook_"),
            when=when,
            raw_object=raw_object,
            supported_compositions=["plays"],
        )

    def display_name(self) -> str:
        return self.name

    def set_location(self) -> None:
        """Playbooks only have the path as position.

        :return:
        """
        # Since the playbook is the whole file, the set the position as the beginning of the file
        if self.raw_object:
            self.location = NodeLocation(
                type="file",
                path=self.raw_object._file_name,
                line=1,
                column=1,
            )

    def plays(
        self,
        exclude_empty: bool = False,
        exclude_without_roles: bool = False,
    ) -> list["PlayNode"]:
        """Return the list of plays.

        :param exclude_empty: Whether to exclude the empty plays from the result or not
        :param exclude_without_roles: Whether to exclude the plays that do not have roles
        :return:
        """
        plays = self.get_nodes("plays")

        if exclude_empty:
            plays = [play for play in plays if not play.is_empty()]

        if exclude_without_roles:
            plays = [play for play in plays if play.has_node_type(RoleNode)]

        return plays

    def roles_usage(self) -> dict["RoleNode", set["PlayNode"]]:
        """For each role in the playbook, get the uniq plays that reference the role.

        :return: A dict with key as role node and value the list of uniq plays that use it.
        """
        usages = defaultdict(set)
        links = self.links_structure()

        for node, linked_nodes in links.items():
            for linked_node in linked_nodes:
                if isinstance(linked_node, RoleNode):
                    if isinstance(node, PlayNode):
                        usages[linked_node].add(node)
                    else:
                        usages[linked_node].add(
                            node.get_first_parent_matching_type(PlayNode),
                        )

        return usages

    def to_dict(
        self,
        exclude_empty_plays: bool = False,
        exclude_plays_without_roles: bool = False,
        include_handlers: bool = False,
        **kwargs,
    ) -> dict:
        """Return a dictionary representation of this playbook.

        :param exclude_empty_plays: Whether to exclude the empty plays from the result or not
        :param exclude_plays_without_roles: Whether to exclude the plays that do not have roles
        :param include_handlers: Whether to include the handlers in the output or not
        :param kwargs:
        :return:
        """
        playbook_dict = super().to_dict(**kwargs)
        playbook_dict["plays"] = []

        # We need to explicitly get the plays here to exclude the ones we don't need
        for play in self.plays(
            exclude_empty=exclude_empty_plays,
            exclude_without_roles=exclude_plays_without_roles,
        ):
            playbook_dict["plays"].append(
                play.to_dict(include_handlers=include_handlers, **kwargs)
            )

        return playbook_dict


class PlayNode(CompositeNode):
    """A play is a list of:
    - pre_tasks
    - roles
    - tasks
    - post_tasks
    - handlers
    """

    def __init__(
        self,
        node_name: str,
        node_id: str | None = None,
        when: str = "",
        raw_object: Any = None,
        parent: "Node" = None,
        hosts: list[str] | None = None,
    ) -> None:
        """

        :param node_name:
        :param node_id:
        :param hosts: List of hosts attached to the play
        """
        super().__init__(
            node_name,
            node_id or generate_id("play_"),
            when=when,
            raw_object=raw_object,
            parent=parent,
            supported_compositions=[
                "pre_tasks",
                "roles",
                "tasks",
                "post_tasks",
                "handlers",
            ],
        )
        self.hosts = hosts or []
        self.colors: tuple[str, str] = get_play_colors(self.id)

    def display_name(self) -> str:
        """
        Return the display name of the node.
        :return:
        """
        return f"Play: {self.name} ({len(self.hosts)})"

    @property
    def roles(self) -> list["RoleNode"]:
        """Return the roles of the plays. Tasks using "include_role" are NOT returned.

        :return:
        """
        return self.get_nodes("roles")

    @property
    def pre_tasks(self) -> list["Node"]:
        return self.get_nodes("pre_tasks")

    @property
    def post_tasks(self) -> list["Node"]:
        return self.get_nodes("post_tasks")

    @property
    def tasks(self) -> list["Node"]:
        return self.get_nodes("tasks")

    @property
    def handlers(self) -> list["TaskNode"]:
        """Return the handlers defined at the play level.

        The handlers defined in roles are not included here.
        :return:
        """
        return self.get_nodes("handlers")

    def to_dict(self, include_handlers: bool = False, **kwargs) -> dict:
        """Return a dictionary representation of this composite node. This representation is not meant to get the
        original object back.

        :return:
        """

        data = super().to_dict(include_handlers=include_handlers, **kwargs)
        data["hosts"] = self.hosts
        data["colors"] = {"main": self.colors[0], "font": self.colors[1]}

        if not include_handlers:
            data["handlers"] = []

        return data


class BlockNode(CompositeNode):
    """A block node: https://docs.ansible.com/ansible/latest/user_guide/playbooks_blocks.html."""

    def __init__(
        self,
        node_name: str,
        node_id: str | None = None,
        when: str = "",
        raw_object: Any = None,
        parent: "Node" = None,
    ) -> None:
        super().__init__(
            node_name=node_name,
            node_id=node_id or generate_id("block_"),
            when=when,
            raw_object=raw_object,
            parent=parent,
            supported_compositions=["tasks"],
        )

    def add_node(self, target_composition: str, node: Node) -> None:
        """Block only supports adding tasks regardless of the context

        :param target_composition: This is ignored.
        :param node:
        :return:
        """
        super().add_node("tasks", node)

    @property
    def tasks(self) -> list[Node]:
        """The tasks attached to this block.

        :return:
        """
        return self.get_nodes("tasks")


class TaskNode(LoopMixin, Node):
    """A task node. This matches an Ansible Task."""

    def __init__(
        self,
        node_name: str,
        node_id: str | None = None,
        when: str = "",
        raw_object: Any = None,
        parent: "Node" = None,
    ) -> None:
        """:param node_name:
        :param node_id:
        :param raw_object:
        """
        super().__init__(
            node_name=node_name,
            node_id=node_id or generate_id("task_"),
            when=when,
            raw_object=raw_object,
            parent=parent,
        )

    def is_handler(self) -> bool:
        """Return true if this task is a handler, false otherwise.

        :return:
        """
        return isinstance(self.raw_object, Handler) or self.id.startswith("handler_")


class RoleNode(LoopMixin, CompositeNode):
    """A role node. A role is a composition of tasks."""

    def __init__(
        self,
        node_name: str,
        node_id: str | None = None,
        when: str = "",
        raw_object: Any = None,
        parent: "Node" = None,
        include_role: bool = False,
    ) -> None:
        """

        :param node_name:
        :param node_id:
        :param raw_object:
        """
        self.include_role = include_role
        super().__init__(
            node_name,
            node_id or generate_id("role_"),
            when=when,
            raw_object=raw_object,
            parent=parent,
            supported_compositions=["tasks", "handlers"],
        )

    def add_node(self, target_composition: str, node: Node) -> None:
        """Add a node in the target composition.

        :param target_composition: The name of the target composition
        :param node: The node to add in the given composition
        :return:
        """
        if target_composition != "handlers":
            # If we are not adding a handler, we always add the node to the task composition
            super().add_node("tasks", node)
        else:
            super().add_node("handlers", node)

    def set_location(self) -> None:
        """Retrieve the position depending on whether it's an include_role or not.

        :return:
        """
        if self.raw_object and not self.include_role:
            # If it's not an include_role, we take the role path which is the path to the folder where the role
            # is located on the disk.
            self.location = NodeLocation(type="folder", path=self.raw_object._role_path)

        else:
            super().set_location()

    def has_loop(self) -> bool:
        if not self.include_role:
            # Only the include_role supports loop
            return False

        return super().has_loop()

    def to_dict(self, include_handlers: bool = False, **kwargs) -> dict:
        """Return a dictionary representation of this composite node. This representation is not meant to get the
        original object back.

        :param include_handlers: Whether to include the handlers in the output or not
        :param kwargs:
        :return:
        """
        node_dict = super().to_dict(**kwargs)
        node_dict["include_role"] = self.include_role

        if not include_handlers:
            node_dict["handlers"] = []

        return node_dict

    @property
    def tasks(self) -> list[Node]:
        """The tasks attached to this block.

        :return:
        """
        return self.get_nodes("tasks")

    @property
    def handlers(self) -> list["TaskNode"]:
        """Return the handlers defined in the role.

        When parsing a role, the handlers are considered as tasks. This is just a convenient method to get the handlers
        of a role.
        :return:
        """
        return self.get_nodes("handlers")
