"""Reference and cross-reference manager."""

from typing import Optional, List, Dict, Any
from ..models import Node, Reference
from ..db import ReferenceRepository


class ReferenceManager:
    """
    Manages cross-references and mentions in a document.
    Handles resolving references, validating targets, and generating display text.
    """

    def __init__(self, repo: ReferenceRepository):
        self.repo = repo
        self.cache: Dict[str, Optional[Node]] = {}

    def create_reference(self, source_node: Node, target_node: Node, reference_type: str = "auto", display_text: Optional[str] = None) -> Reference:
        """Create and save a reference from source to target."""
        ref = Reference(
            source_node_id=source_node.node_id,
            target_node_id=target_node.node_id,
            reference_type=reference_type,
            display_text=display_text,
        )
        self.repo.save_reference(ref)
        return ref

    def resolve_reference(self, ref: Reference, document_root: Node) -> Optional[Node]:
        """Resolve a reference to the target node."""
        # Check cache first
        if ref.target_node_id in self.cache:
            return self.cache[ref.target_node_id]

        # Search document tree
        target = document_root.find_node(ref.target_node_id)
        if target:
            self.cache[ref.target_node_id] = target
        return target

    def get_reference_display_text(self, ref: Reference, target_node: Optional[Node]) -> str:
        """
        Get the display text for a reference.
        If ref.display_text is set, use that. Otherwise, generate based on target and reference_type.
        """
        if ref.display_text:
            return ref.display_text

        if not target_node:
            return f"[broken reference]"

        # Auto-generate based on target node type
        if target_node.node_type == "article":
            article_num = target_node.data.get('number', '?')
            return f"Άρθρο {article_num}"
        elif target_node.node_type == "paragraph":
            para_num = target_node.data.get('number', '?')
            return f"Παράγραφος {para_num}"
        else:
            return f"[reference to {target_node.node_type}]"

    def get_backlinks(self, target_node_id: str) -> List[Reference]:
        """Get all references pointing to a node (useful for navigation)."""
        return self.repo.get_references_to_target(target_node_id)

    def validate_references(self, document_root: Node) -> Dict[str, Any]:
        """
        Validate all references in a document.
        Returns a dict with statistics: total, valid, broken.
        """
        all_nodes = document_root.get_all_nodes()
        total_refs = 0
        valid_refs = 0
        broken_refs = []

        for node in all_nodes:
            refs = self.repo.get_references_by_source(node.node_id)
            for ref in refs:
                total_refs += 1
                target = self.resolve_reference(ref, document_root)
                if target:
                    valid_refs += 1
                else:
                    broken_refs.append({
                        "reference_id": ref.reference_id,
                        "source_node_id": ref.source_node_id,
                        "target_node_id": ref.target_node_id,
                    })

        return {
            "total": total_refs,
            "valid": valid_refs,
            "broken": len(broken_refs),
            "broken_details": broken_refs,
        }
