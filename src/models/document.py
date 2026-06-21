"""Document wrapper and management."""

import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from .node import Node


@dataclass
class Document:
    """
    A legislature document (law, gazette, regulation, etc.).
    - doc_id: unique identifier
    - title: document title
    - root: root AST node
    - metadata: document-level metadata (author, created date, etc.)
    """
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    root: Node = field(default_factory=lambda: Node(node_type="document"))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure metadata has timestamps."""
        if "created_at" not in self.metadata:
            self.metadata["created_at"] = datetime.now().isoformat()
        if "updated_at" not in self.metadata:
            self.metadata["updated_at"] = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (for JSON storage)."""
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "root": self.root.to_dict(),
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Document':
        """Deserialize from dict."""
        root = Node.from_dict(data.get("root", {"node_type": "document"}))
        return Document(
            doc_id=data.get("doc_id", str(uuid.uuid4())),
            title=data.get("title", ""),
            root=root,
            metadata=data.get("metadata", {}),
        )

    def update_modified_time(self) -> None:
        """Update the modified timestamp."""
        self.metadata["updated_at"] = datetime.now().isoformat()
