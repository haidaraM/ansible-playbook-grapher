# Copyright (C) 2022 Mohamed El Mouctar HAIDARA
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
from typing import Dict, List, ItemsView

from ansibleplaybookgrapher.utils import generate_id


class Node:
    """
    A node in the graph. Everything of the final graph is a node: playbook, plays, edges, tasks and roles.
    """

    def __init__(self, node_name: str, node_id: str, raw_object=None):
        """

        :param node_name: The name of the node
        :param node_id: An identifier for this node
        :param raw_object: The raw ansible object matching this node in the graph. Will be None if there is no match on
        Ansible side
        """
        self.name = node_name
        self.id = node_id
        self.raw_object = raw_object
        # Trying to get the object position in the parsed files. Format: (path,line,column)
        self.path = self.line = self.column = None
        self.retrieve_position()

    def retrieve_position(self):
        """
        Set the path of this based on the raw object. Not all objects have path
        :return:
        """
        if self.raw_object and self.raw_object.get_ds():
            self.path, self.line, self.column = self.raw_object.get_ds().ansible_pos

    def __str__(self):
        return f"{type(self).__name__}(name='{self.name}')"

    def __repr__(self):
        return f"{type(self).__name__}(id='{self.id}',name='{self.name}')"

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class CompositeNode(Node):
    """
    A node that composed of multiple of nodes.
    """

    def __init__(
        self,
        node_name: str,
        node_id: str,
        raw_object=None,
        supported_compositions: List[str] = None,
    ):
        """

        :param node_name:
        :param node_id:
        :param raw_object: The raw ansible object matching this node in the graph. Will be None if there is no match on
        Ansible side
        :param supported_compositions:
        """
        super().__init__(node_name, node_id, raw_object)
        self._supported_compositions = supported_compositions or []
        # The dict will contain the different types of composition.
        self._compositions = defaultdict(list)  # type: Dict[str, List]

    def items(self) -> ItemsView[str, List[Node]]:
        """
        Return a view object (list of tuples) of all the nodes inside this composite node. The first element of the
        tuple is the composition name and the second one a list of nodes
        :return:
        """
        return self._compositions.items()

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

    def links_structure(self) -> Dict[Node, List[Node]]:
        """
        Return a representation of the composite node where each key of the dictionary is the node and the value is the
        list of the linked nodes
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
        for target, nodes in self._compositions.items():
            for node in nodes:
                if isinstance(node, CompositeNode):
                    node._get_all_links(links)
                links[self].append(node)


class CompositeTasksNode(CompositeNode):
    """
    A special composite node which only support adding "tasks"
    """

    def __init__(self, node_name: str, node_id: str, raw_object=None):
        super().__init__(node_name, node_id, raw_object=raw_object)
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
    def tasks(self) -> List["EdgeNode"]:
        """
        The tasks attached to this block
        :return:
        """
        return self._compositions["tasks"]


class PlaybookNode(CompositeNode):
    """
    A playbook is a list of play
    """

    def __init__(self, node_name: str, node_id: str = None, raw_object=None):
        super().__init__(
            node_name,
            node_id or generate_id("playbook_"),
            raw_object=raw_object,
            supported_compositions=["plays"],
        )

    def retrieve_position(self):
        """
        Playbooks only have path as position
        :return:
        """
        # Since the playbook is the whole file, the set the position as the beginning of the file
        self.path = os.path.join(os.getcwd(), self.name)
        self.line = 1
        self.column = 1

    @property
    def plays(self) -> List["EdgeNode"]:
        """
        Return the list of plays
        :return:
        """
        return self._compositions["plays"]

    def add_play(self, play: "PlayNode", edge_name: str, **kwargs) -> "EdgeNode":
        """
        Add a play to the playbook
        :param play:
        :param edge_name:
        :return:
        """
        edge = EdgeNode(self, play, edge_name)
        self.add_node("plays", edge)
        return edge


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
        raw_object=None,
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
            raw_object=raw_object,
            supported_compositions=["pre_tasks", "roles", "tasks", "post_tasks"],
        )
        self.hosts = hosts or []

    @property
    def roles(self) -> List["EdgeNode"]:
        return self._compositions["roles"]

    @property
    def pre_tasks(self) -> List["EdgeNode"]:
        return self._compositions["pre_tasks"]

    @property
    def post_tasks(self) -> List["EdgeNode"]:
        return self._compositions["post_tasks"]

    @property
    def tasks(self) -> List["EdgeNode"]:
        return self._compositions["tasks"]


class BlockNode(CompositeTasksNode):
    """
    A block node: https://docs.ansible.com/ansible/latest/user_guide/playbooks_blocks.html
    """

    def __init__(self, node_name: str, node_id: str = None, raw_object=None):
        super().__init__(
            node_name, node_id or generate_id("block_"), raw_object=raw_object
        )


class EdgeNode(CompositeNode):
    """
    An edge between two nodes. It's a special case of composite node with only one composition with one element
    """

    def __init__(
        self, source: Node, destination: Node, node_name: str = "", node_id: str = None
    ):
        """

        :param node_name: The edge name
        :param source: The edge source node
        :param destination: The edge destination node
        :param node_id: The edge id
        """
        super().__init__(
            node_name,
            node_id or generate_id("edge_"),
            raw_object=None,
            supported_compositions=["destination"],
        )
        self.source = source
        self.add_node("destination", destination)

    def add_node(self, target_composition: str, node: Node):
        """
        Override the add_node. An edge node should only have one linked node
        :param target_composition:
        :param node:
        :return:
        """
        current_nodes = self._compositions[target_composition]
        if len(current_nodes) == 1:
            raise Exception("An EdgeNode should have at most one linked node")
        return super().add_node(target_composition, node)

    @property
    def destination(self) -> Node:
        """
        Return the destination of the edge
        :return:
        """
        return self._compositions["destination"][0]


class TaskNode(Node):
    """
    A task node. Can be pre_task, task or post_task
    """

    def __init__(self, node_name: str, node_id: str = None, raw_object=None):
        """

        :param node_name:
        :param node_id:
        :param raw_object:
        """
        super().__init__(node_name, node_id or generate_id("task_"), raw_object)


class RoleNode(CompositeTasksNode):
    """
    A role node. A role is a composition of tasks
    """

    def __init__(
        self,
        node_name: str,
        node_id: str = None,
        raw_object=None,
        include_role: bool = False,
    ):
        """

        :param node_name:
        :param node_id:
        :param raw_object:
        """
        super().__init__(
            node_name, node_id or generate_id("role_"), raw_object=raw_object
        )
        self.include_role = include_role
        if raw_object and not include_role:
            # If it's not an include_role, we take the role path which the path to the folder where the role is located
            # on the disk
            self.path = raw_object._role_path


def _get_all_tasks_nodes(composite: CompositeNode, task_acc: List[TaskNode]):
    """
    :param composite:
    :param task_acc:
    :return:
    """
    items = composite.items()
    for _, nodes in items:
        for node in nodes:
            if isinstance(node, TaskNode):
                task_acc.append(node)
            elif isinstance(node, CompositeNode):
                _get_all_tasks_nodes(node, task_acc)


def get_all_tasks_nodes(composite: CompositeNode) -> List[TaskNode]:
    """
    Return all the TaskNode inside a composite node
    :param composite:
    :return:
    """
    tasks: List[TaskNode] = []
    _get_all_tasks_nodes(composite, tasks)
    return tasks
