"""Generic node/AST system for documents."""

import uuid
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class NodeType(str, Enum):
    """Built-in node types."""
    DOCUMENT = "document"
    TEMPLATE_INSTANCE = "template_instance"
    TEXT = "text"
    PARAGRAPH = "paragraph"
    HEADER = "header"
    IMAGE = "image"
    TABLE = "table"
    SIGNATURE = "signature"
    REFERENCE = "reference"
    MENTION = "mention"


@dataclass
class Node:
    """
    Generic node in the document tree.
    - node_id: unique identifier
    - node_type: type of node (built-in or custom)
    - template_id: if this is a template instance, points to template definition
    - data: generic dict holding node-specific data (form parameters, content, etc.)
    - children: list of child nodes (order matters)
    """
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type: str = NodeType.DOCUMENT
    template_id: Optional[str] = None  # if null, this is a raw node; if set, it's a template instance
    data: Dict[str, Any] = field(default_factory=dict)
    children: List['Node'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)  # for timestamps, author, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (for JSON storage)."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "template_id": self.template_id,
            "data": self.data,
            "children": [child.to_dict() for child in self.children],
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Node':
        """Deserialize from dict."""
        children = [Node.from_dict(child_data) for child_data in data.get("children", [])]
        return Node(
            node_id=data.get("node_id", str(uuid.uuid4())),
            node_type=data.get("node_type", NodeType.DOCUMENT),
            template_id=data.get("template_id"),
            data=data.get("data", {}),
            children=children,
            metadata=data.get("metadata", {}),
        )

    def add_child(self, child: 'Node') -> None:
        """Add a child node."""
        self.children.append(child)

    def remove_child(self, child_id: str) -> bool:
        """Remove a child by node_id. Returns True if found and removed."""
        for i, child in enumerate(self.children):
            if child.node_id == child_id:
                self.children.pop(i)
                return True
        return False

    def find_node(self, node_id: str) -> Optional['Node']:
        """Recursively find a node by ID."""
        if self.node_id == node_id:
            return self
        for child in self.children:
            result = child.find_node(node_id)
            if result:
                return result
        return None

    def get_all_nodes(self) -> List['Node']:
        """Return flattened list of all nodes (DFS)."""
        nodes = [self]
        for child in self.children:
            nodes.extend(child.get_all_nodes())
        return nodes
