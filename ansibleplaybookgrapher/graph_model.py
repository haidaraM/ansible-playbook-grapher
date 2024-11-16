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
from typing import Any

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
        index: int | None = None,
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
        self.index: int | None = index

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
                # Here we likely have a task a validate argument spec task inserted by Ansible
                pass

    def get_first_parent_matching_type(self, node_type: type) -> type:
        """Get the first parent of this node matching the given type.

        :param node_type: The type of the parent to get
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
        index: int | None = None,
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
            index=index,
        )
        self._supported_compositions = supported_compositions or []
        # The dict will contain the different types of composition: plays, tasks, roles...
        self._compositions = defaultdict(list)  # type: Dict[str, List]
        # Used to count the number of nodes in this composite node
        self._node_counter = 0

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
        # The node index is position in the composition regardless of the type of the node
        node.index = self._node_counter + 1
        self._node_counter += 1

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
        self._get_all_tasks_nodes(tasks)
        return tasks

    def _get_all_tasks_nodes(self, task_acc: list["Node"]) -> None:
        """Recursively get all tasks.

        :param task_acc:
        :return:
        """
        items = self._compositions.items()
        for _, nodes in items:
            for node in nodes:
                if isinstance(node, TaskNode):
                    task_acc.append(node)
                elif isinstance(node, CompositeNode):
                    node._get_all_tasks_nodes(task_acc)

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


class CompositeTasksNode(CompositeNode):
    """A special composite node which only support adding "tasks". Useful for block and role."""

    def __init__(
        self,
        node_name: str,
        node_id: str,
        when: str = "",
        raw_object: Any = None,
        parent: "Node" = None,
        index: int | None = None,
    ) -> None:
        super().__init__(
            node_name=node_name,
            node_id=node_id,
            when=when,
            raw_object=raw_object,
            parent=parent,
            index=index,
        )
        self._supported_compositions = ["tasks"]

    def add_node(self, target_composition: str, node: Node) -> None:
        """Override the add_node because the composite tasks only contains "tasks" regardless of the context
         (pre_tasks or post_tasks).

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


class PlaybookNode(CompositeNode):
    """A playbook is a list of play."""

    def __init__(
        self,
        node_name: str,
        node_id: str | None = None,
        when: str = "",
        raw_object: Any = None,
        index: int | None = None,
    ) -> None:
        super().__init__(
            node_name=node_name,
            node_id=node_id or generate_id("playbook_"),
            when=when,
            raw_object=raw_object,
            index=index,
            supported_compositions=["plays"],
        )

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
        **kwargs,
    ) -> dict:
        """Return a dictionary representation of this playbook.

        :param exclude_empty_plays: Whether to exclude the empty plays from the result or not
        :param exclude_plays_without_roles: Whether to exclude the plays that do not have roles
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
            playbook_dict["plays"].append(play.to_dict(**kwargs))

        return playbook_dict


class PlayNode(CompositeNode):
    """A play is a list of:
    - pre_tasks
    - roles
    - tasks
    - post_tasks.
    """

    def __init__(
        self,
        node_name: str,
        node_id: str | None = None,
        when: str = "",
        raw_object: Any = None,
        parent: "Node" = None,
        index: int | None = None,
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
            index=index,
            supported_compositions=["pre_tasks", "roles", "tasks", "post_tasks"],
        )
        self.hosts = hosts or []
        self.colors: tuple[str, str] = get_play_colors(self.id)

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

    def to_dict(self, **kwargs) -> dict:
        """Return a dictionary representation of this composite node. This representation is not meant to get the
        original object back.

        :return:
        """
        data = super().to_dict(**kwargs)
        data["hosts"] = self.hosts
        data["colors"] = {"main": self.colors[0], "font": self.colors[1]}

        return data


class BlockNode(CompositeTasksNode):
    """A block node: https://docs.ansible.com/ansible/latest/user_guide/playbooks_blocks.html."""

    def __init__(
        self,
        node_name: str,
        node_id: str | None = None,
        when: str = "",
        raw_object: Any = None,
        parent: "Node" = None,
        index: int | None = None,
    ) -> None:
        super().__init__(
            node_name=node_name,
            node_id=node_id or generate_id("block_"),
            when=when,
            raw_object=raw_object,
            parent=parent,
            index=index,
        )


class TaskNode(LoopMixin, Node):
    """A task node. This matches an Ansible Task."""

    def __init__(
        self,
        node_name: str,
        node_id: str | None = None,
        when: str = "",
        raw_object: Any = None,
        parent: "Node" = None,
        index: int | None = None,
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
            index=index,
        )


class RoleNode(LoopMixin, CompositeTasksNode):
    """A role node. A role is a composition of tasks."""

    def __init__(
        self,
        node_name: str,
        node_id: str | None = None,
        when: str = "",
        raw_object: Any = None,
        parent: "Node" = None,
        index: int | None = None,
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
            index=index,
        )

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
            # Only include_role supports loop
            return False

        return super().has_loop()

    def to_dict(self, **kwargs) -> dict:
        """Return a dictionary representation of this composite node. This representation is not meant to get the
        original object back.

        :param kwargs:
        :return:
        """
        node_dict = super().to_dict(**kwargs)
        node_dict["include_role"] = self.include_role

        return node_dict
