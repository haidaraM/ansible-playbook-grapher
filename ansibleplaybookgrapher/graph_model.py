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
from pathlib import Path
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
        is_hidden: bool = False,
    ) -> None:
        """

        :param node_name: The name of the node
        :param node_id: An identifier for this node
        :param when: The condition attached to the node
        :param raw_object: The raw ansible object matching this node in the graph. Will be None if there is no match on
        Ansible side
        :param parent: The parent node of this node
        :param is_hidden: Whether the node is hidden or not. Hidden nodes are not displayed in the graph.
        """
        self.name = node_name
        self.parent = parent
        self.id = node_id
        self.when = when
        self.raw_object = raw_object
        self.is_hidden = is_hidden

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

    def get_first_parent_matching_type(self, node_type: type) -> type | None:
        """Get the first parent of this node matching the given type.

        :param node_type: The type of the parent node to get.
        :return: The first parent matching the given type or None if no parent matches the type.
        """
        current_parent = self.parent

        while current_parent is not None:
            if isinstance(current_parent, node_type):
                return current_parent
            current_parent = current_parent.parent

        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name='{self.name}', id='{self.id}', index={self.index})"

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
            "location": asdict(self.location) if self.location else None,
        }

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
        self.supported_compositions = supported_compositions or []
        # The dict will contain the different types of composition: plays, tasks, roles...
        self._compositions = defaultdict(list)  # type: dict[str, list]

    def _check_target_composition(self, target_composition: str) -> None:
        """Check if the target composition is supported.

        :param target_composition:
        :return:
        """
        if target_composition not in self.supported_compositions:
            msg = f"The node {type(self).__name__} doesn't support '{target_composition}'. The supported ones are: {self.supported_compositions}"
            raise ValueError(
                msg,
            )

    def add_node(self, target_composition: str, node: Node) -> None:
        """Add a node in the target composition.

        :param target_composition: The name of the target composition
        :param node: The node to add in the given composition
        :return:
        """
        self._check_target_composition(target_composition)
        self._compositions[target_composition].append(node)

    def remove_node(self, target_composition: str, node: Node) -> None:
        """Remove a node from the target composition.

        :param target_composition: The name of the target composition
        :param node: The node to remove from the given composition
        :return:
        """
        self._check_target_composition(target_composition)
        self._compositions[target_composition].remove(node)

    def calculate_indices(self) -> None:
        """Calculate the indices of all nodes based on their composition type and whether they are supposed to be included
        or not.

        """
        current_index = 1
        for comp_type in self.supported_compositions:
            for node in self._compositions[comp_type]:
                if node.is_hidden:
                    node.index = None
                    continue

                if (
                    isinstance(node, CompositeNode) and node.is_empty()
                ):  # Skip empty nodes
                    node.index = None
                    node.is_hidden = True
                    continue

                node.index = current_index
                current_index += 1

                if isinstance(node, CompositeNode):
                    node.calculate_indices()

    def get_nodes(self, target_composition: str) -> list:
        """Get a node from the compositions.

        :param target_composition:
        :return: A list of the nodes.
        """
        self._check_target_composition(target_composition)
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
        for _, nodes in self._compositions.items():
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

        A composite node with at least one task is not empty.
        :return:
        """
        for nodes in self._compositions.values():
            for node in nodes:
                if isinstance(node, CompositeNode):
                    if not node.is_empty():
                        return False
                else:
                    # We have a task node here => the composite node is not empty
                    return False
        return True

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

    def remove_all_nodes_types(self, types: list[type]):
        """Remove all the nodes of the given types from the composite node.

        :param types: List of types to remove.
        :return:
        """
        for target_composition, nodes in self._compositions.items():
            for node in nodes[:]:
                if isinstance(node, tuple(types)):
                    self.remove_node(target_composition, node)
                elif isinstance(node, CompositeNode):
                    node.remove_all_nodes_types(types)

    def to_dict(self, exclude_compositions: list[str] | None = None, **kwargs) -> dict:
        """Return a dictionary representation of this composite node. This representation is not meant to get the
        original object back.

        Caller can eventually pass a list of target compositions to NOT include in the output. If provided, the target
        compositions will be set to an empty list in the output.

        :param exclude_compositions: List of compositions to exclude from the output.
        :return: Dictionary representation of the composite node.
        """
        node_dict = super().to_dict(**kwargs)
        exclude_compositions = exclude_compositions or []

        for composition in self.supported_compositions:
            if composition in exclude_compositions:
                node_dict[composition] = []
            else:
                nodes = self._compositions.get(composition, [])
                node_dict[composition] = [
                    node.to_dict(**kwargs) for node in nodes if not node.is_hidden
                ]

        return node_dict

    def hide_task_nodes(self):
        """Hide all the task nodes from the playbook.

        :return:
        """
        for target_composition, nodes in self._compositions.items():
            for node in nodes:
                if isinstance(node, TaskNode):
                    node.is_hidden = True
                elif isinstance(node, CompositeNode):
                    node.hide_task_nodes()


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
                path=str(Path(self.raw_object._file_name).resolve()),
                line=1,
                column=1,
            )

    @property
    def plays(
        self,
    ) -> list["PlayNode"]:
        """Return the list of plays.

        :return:
        """

        return self.get_nodes("plays")

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

    def remove_empty_plays(self):
        """Remove the empty plays from the playbook.

        :return:
        """
        to_exclude = [play for play in self.plays if play.is_empty()]

        for play in to_exclude:
            self.remove_node("plays", play)

    def hide_plays_without_roles(self):
        """Hide the plays that do not have at least one role.

        :return:
        """
        for play in self.plays:
            if not play.has_node_type(RoleNode):
                play.is_hidden = True


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

        This is closer to what ansible-playbook --list-tasks does.
        :return:
        """
        return f"play #{self.index} ({self.name}): {len(self.hosts)}"

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

    def to_dict(
        self,
        exclude_compositions: list[str] | None = None,
        include_handlers: bool = False,
        **kwargs,
    ) -> dict:
        """Return a dictionary representation of this composite node. This representation is not meant to get the
        original object back.

        :param exclude_compositions: List of compositions to exclude from the output.
        :param include_handlers: Whether to include the handlers in the output or not
        :return:
        """
        exclude_compositions = exclude_compositions or []
        if not include_handlers:
            exclude_compositions.append("handlers")

        data = super().to_dict(
            exclude_compositions=exclude_compositions,
            include_handlers=include_handlers,
            **kwargs,
        )

        data["hosts"] = self.hosts
        data["colors"] = {"main": self.colors[0], "font": self.colors[1]}

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

    def display_name(self) -> str:
        """Return the display name of the node.

        When a task is from a role, we just display the name of the task. In this case, its name already contains the
        role name.
        :return:
        """
        if self.get_first_parent_matching_type(RoleNode):
            return self.name

        return super().display_name()

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

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name='{self.name}', id='{self.id}', index={self.index}, include_role={self.include_role})"

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

    def to_dict(
        self,
        exclude_compositions: list[str] | None = None,
        include_handlers: bool = False,
        include_role_tasks: bool = False,
        **kwargs,
    ) -> dict:
        """Return a dictionary representation of this composite node. This representation is not meant to get the
        original object back.

        :param exclude_compositions: List of compositions to exclude from the output.
        :param include_handlers: Whether to include the handlers in the output or not
        :param include_role_tasks: Whether to include the role tasks in the output or not.
        :param kwargs:
        :return:
        """
        exclude_compositions = exclude_compositions or []

        if not include_role_tasks:
            exclude_compositions.append("tasks")

        if not include_handlers:
            exclude_compositions.append("handlers")

        node_dict = super().to_dict(
            exclude_compositions=exclude_compositions,
            include_handlers=include_handlers,
            include_role_tasks=include_role_tasks,
            **kwargs,
        )
        node_dict["include_role"] = self.include_role

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

    def is_empty(self) -> bool:
        """Return true if the role is empty, false otherwise.

        :return:
        """
        if self.has_loop():
            # We can't parse roles with a loop. So we consider them as not empty.
            return False

        return super().is_empty()
