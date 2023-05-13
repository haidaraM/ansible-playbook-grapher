# Copyright (C) 2023 Mohamed El Mouctar HAIDARA
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
import os
from collections import defaultdict
from typing import Dict, List, Set, Type, Tuple, Optional

from ansibleplaybookgrapher.utils import generate_id, get_play_colors


class LoopMixin:
    """
    A mixin class for nodes that support looping
    """

    def has_loop(self) -> bool:
        """
        Return true if the node has a loop (`loop` or `with_`).
        https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_loops.html
        :return:
        """
        if self.raw_object is None:
            return False
        return self.raw_object.loop is not None


class Node:
    """
    A node in the graph. Everything of the final graph is a node: playbook, plays, tasks and roles.
    """

    def __init__(
        self,
        node_name: str,
        node_id: str,
        when: str = "",
        raw_object=None,
        parent: "Node" = None,
        index: Optional[int] = None,
    ):
        """

        :param node_name: The name of the node
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

        # Get the node position in the parsed files. Format: (path,line,column)
        self.path = self.line = self.column = None
        self.set_position()

        # The index of this node in the parent node if it has one (starting from 1)
        self.index: Optional[int] = index

    def set_position(self):
        """
        Set the path of this based on the raw object. Not all objects have path
        :return:
        """
        if self.raw_object and self.raw_object.get_ds():
            self.path, self.line, self.column = self.raw_object.get_ds().ansible_pos

    def get_first_parent_matching_type(self, node_type: Type) -> Type:
        """
        Get the first parent of this node matching the given type
        :param node_type: The type of the parent to get
        :return:
        """
        current_parent = self.parent

        while current_parent is not None:
            if isinstance(current_parent, node_type):
                return current_parent
            current_parent = current_parent.parent

        raise ValueError(f"No parent of type {node_type} found for {self}")

    def __repr__(self):
        return f"{type(self).__name__}(name='{self.name}', id='{self.id}')"

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.id)


class CompositeNode(Node):
    """
    A node composed of multiple of nodes:
     - playbook containing plays
     - play containing tasks
     - role containing tasks
     - block containing tasks
    """

    def __init__(
        self,
        node_name: str,
        node_id: str,
        when: str = "",
        raw_object=None,
        parent: "Node" = None,
        index: int = None,
        supported_compositions: List[str] = None,
    ):
        """

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
        # The dict will contain the different types of composition.
        self._compositions = defaultdict(list)  # type: Dict[str, List]
        # Used to count the number of nodes in this composite node
        self._node_counter = 0

    def add_node(self, target_composition: str, node: Node):
        """
        Add a node in the target composition
        :param target_composition: The name of the target composition
        :param node: The node to add in the given composition
        :return:
        """
        if target_composition not in self._supported_compositions:
            raise Exception(
                f"The target composition '{target_composition}' is unknown. Supported are: {self._supported_compositions}"
            )
        self._compositions[target_composition].append(node)
        # The node index is position in the composition regardless of the type of the node
        node.index = self._node_counter + 1
        self._node_counter += 1

    def get_all_tasks(self) -> List["TaskNode"]:
        """
        Return all the TaskNode inside this composite node
        :return:
        """
        tasks: List[TaskNode] = []
        self._get_all_tasks_nodes(tasks)
        return tasks

    def _get_all_tasks_nodes(self, task_acc: List["Node"]):
        """
        Recursively get all tasks
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

    def links_structure(self) -> Dict[Node, List[Node]]:
        """
        Return a representation of the composite node where each key of the dictionary is the node and the
         value is the list of the linked nodes
        :return:
        """
        links: Dict[Node, List[Node]] = defaultdict(list)
        self._get_all_links(links)
        return links

    def _get_all_links(self, links: Dict[Node, List[Node]]):
        """
        Recursively get the node links
        :return:
        """
        for _, nodes in self._compositions.items():
            for node in nodes:
                if isinstance(node, CompositeNode):
                    node._get_all_links(links)
                links[self].append(node)


class CompositeTasksNode(CompositeNode):
    """
    A special composite node which only support adding "tasks". Useful for block and role
    """

    def __init__(
        self,
        node_name: str,
        node_id: str,
        when: str = "",
        raw_object=None,
        parent: "Node" = None,
        index: int = None,
    ):
        super().__init__(
            node_name=node_name,
            node_id=node_id,
            when=when,
            raw_object=raw_object,
            parent=parent,
            index=index,
        )
        self._supported_compositions = ["tasks"]

    def add_node(self, target_composition: str, node: Node):
        """
        Override the add_node because block only contains "tasks" regardless of the context (pre_tasks or post_tasks)
        :param target_composition: This is ignored. It's always "tasks" for block
        :param node:
        :return:
        """
        super().add_node("tasks", node)

    @property
    def tasks(self) -> List[Node]:
        """
        The tasks attached to this block
        :return:
        """
        return self._compositions["tasks"]


class PlaybookNode(CompositeNode):
    """
    A playbook is a list of play
    """

    def __init__(
        self,
        node_name: str,
        node_id: str = None,
        when: str = "",
        raw_object=None,
        index: int = None,
    ):
        super().__init__(
            node_name=node_name,
            node_id=node_id or generate_id("playbook_"),
            when=when,
            raw_object=raw_object,
            index=index,
            supported_compositions=["plays"],
        )

    def set_position(self):
        """
        Playbooks only have path as position
        :return:
        """
        # Since the playbook is the whole file, the set the position as the beginning of the file
        self.path = os.path.join(os.getcwd(), self.name)
        self.line = 1
        self.column = 1

    @property
    def plays(self) -> List["PlayNode"]:
        """
        Return the list of plays
        :return:
        """
        return self._compositions["plays"]

    def roles_usage(self) -> Dict["RoleNode", Set["PlayNode"]]:
        """
        For each role in the playbook, get the uniq plays that reference the role
        :return: A dict with key as role node and value the list of uniq plays that use it
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
                            node.get_first_parent_matching_type(PlayNode)
                        )

        return usages


class PlayNode(CompositeNode):
    """
    A play is a list of:
     - pre_tasks
     - roles
     - tasks
     - post_tasks
    """

    def __init__(
        self,
        node_name: str,
        node_id: str = None,
        when: str = "",
        raw_object=None,
        parent: "Node" = None,
        index: int = None,
        hosts: List[str] = None,
    ):
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
        self.colors: Tuple[str, str] = get_play_colors(self.id)

    @property
    def roles(self) -> List["RoleNode"]:
        return self._compositions["roles"]

    @property
    def pre_tasks(self) -> List["Node"]:
        return self._compositions["pre_tasks"]

    @property
    def post_tasks(self) -> List["Node"]:
        return self._compositions["post_tasks"]

    @property
    def tasks(self) -> List["Node"]:
        return self._compositions["tasks"]


class BlockNode(CompositeTasksNode):
    """
    A block node: https://docs.ansible.com/ansible/latest/user_guide/playbooks_blocks.html
    """

    def __init__(
        self,
        node_name: str,
        node_id: str = None,
        when: str = "",
        raw_object=None,
        parent: "Node" = None,
        index: int = None,
    ):
        super().__init__(
            node_name=node_name,
            node_id=node_id or generate_id("block_"),
            when=when,
            raw_object=raw_object,
            parent=parent,
            index=index,
        )


class TaskNode(LoopMixin, Node):
    """
    A task node. This matches an Ansible Task.
    """

    def __init__(
        self,
        node_name: str,
        node_id: str = None,
        when: str = "",
        raw_object=None,
        parent: "Node" = None,
        index: int = None,
    ):
        """

        :param node_name:
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
    """
    A role node. A role is a composition of tasks
    """

    def __init__(
        self,
        node_name: str,
        node_id: str = None,
        when: str = "",
        raw_object=None,
        parent: "Node" = None,
        index: int = None,
        include_role: bool = False,
    ):
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

    def set_position(self):
        """
        Retrieve the position depending on whether it's an include_role or not
        :return:
        """
        if self.raw_object and not self.include_role:
            # If it's not an include_role, we take the role path which the path to the folder where the role is located
            # on the disk
            self.path = self.raw_object._role_path
        else:
            super().set_position()

    def has_loop(self) -> bool:
        if not self.include_role:
            # Only include_role supports loop
            return False

        return super().has_loop()
