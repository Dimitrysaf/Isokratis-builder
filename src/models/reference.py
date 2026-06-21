"""Reference and mention system for cross-references."""

import uuid
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Reference:
    """
    A reference to another node (for cross-references and mentions).
    - reference_id: unique identifier
    - source_node_id: node that contains this reference
    - target_node_id: node being referenced
    - reference_type: how to display (e.g., "article_number", "paragraph_number", "full_path")
    - display_text: custom display text (if provided)
    """
    reference_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_node_id: str = ""
    target_node_id: str = ""
    reference_type: str = "auto"  # "auto" = infer from target type
    display_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "reference_id": self.reference_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "reference_type": self.reference_type,
            "display_text": self.display_text,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Reference':
        """Deserialize from dict."""
        return Reference(
            reference_id=data.get("reference_id", str(uuid.uuid4())),
            source_node_id=data.get("source_node_id", ""),
            target_node_id=data.get("target_node_id", ""),
            reference_type=data.get("reference_type", "auto"),
            display_text=data.get("display_text"),
        )
