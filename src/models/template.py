"""Template definitions (data-driven, no hardcoding)."""

import uuid
from typing import Any, Dict, List, Optional, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum


class TemplateFieldType(str, Enum):
    """Types of form fields in a template."""
    TEXT = "text"  # single-line text
    TEXTAREA = "textarea"  # multi-line rich text
    NUMBER = "number"
    CHECKBOX = "checkbox"
    SELECT = "select"  # dropdown
    MULTISELECT = "multiselect"
    DATE = "date"
    FILE = "file"
    REFERENCE = "reference"  # cross-ref picker


@dataclass
class TemplateField:
    """
    A form field in a template definition.
    - field_id: unique identifier
    - label: display name
    - field_type: type of input
    - required: whether it must be filled
    - default_value: initial value
    - options: for select/multiselect, list of choices
    - help_text: guidance text
    """
    field_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: str = ""
    field_type: str = TemplateFieldType.TEXT
    required: bool = False
    default_value: Any = None
    options: List[Dict[str, str]] = field(default_factory=list)  # [{"label": "...", "value": "..."}]
    help_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TemplateField':
        """Deserialize from dict."""
        return TemplateField(
            field_id=data.get("field_id", str(uuid.uuid4())),
            label=data.get("label", ""),
            field_type=data.get("field_type", TemplateFieldType.TEXT),
            required=data.get("required", False),
            default_value=data.get("default_value"),
            options=data.get("options", []),
            help_text=data.get("help_text", ""),
        )


@dataclass
class TemplateChildSlot:
    """
    A slot where other template instances can be inserted.
    - slot_id: unique identifier
    - label: display name
    - allowed_template_ids: explicit list of template IDs allowed; empty = use allowed_folders
    - allowed_folders: list of folder keys allowed; empty + no allowed_template_ids = all
    - min_count: minimum number of children required
    - max_count: maximum; 0 = unlimited
    """
    slot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: str = ""
    allowed_template_ids: List[str] = field(default_factory=list)
    allowed_folders: List[str] = field(default_factory=list)
    min_count: int = 0
    max_count: int = 0  # 0 = unlimited

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "slot_id": self.slot_id,
            "label": self.label,
            "allowed_template_ids": self.allowed_template_ids,
            "allowed_folders": self.allowed_folders,
            "min_count": self.min_count,
            "max_count": self.max_count,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TemplateChildSlot':
        """Deserialize from dict."""
        return TemplateChildSlot(
            slot_id=data.get("slot_id", str(uuid.uuid4())),
            label=data.get("label", ""),
            allowed_template_ids=data.get("allowed_template_ids", []),
            allowed_folders=data.get("allowed_folders", []),
            min_count=data.get("min_count", 0),
            max_count=data.get("max_count", 0),
        )


@dataclass
class Template:
    """
    A template definition (data-driven, no hardcoding).
    - template_id: unique identifier
    - name: human-readable name (e.g., "Article", "Paragraph", "Law")
    - description: what this template is for
    - fields: list of form fields (parameters)
    - child_slots: where other templates can be nested
    - render_template: Jinja2 template string for PDF/HTML rendering
    - metadata: extra config (category, icon, etc.)
    """
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    fields: List[TemplateField] = field(default_factory=list)
    child_slots: List[TemplateChildSlot] = field(default_factory=list)
    render_template: str = ""  # Jinja2 template for output
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "fields": [f.to_dict() for f in self.fields],
            "child_slots": [s.to_dict() for s in self.child_slots],
            "render_template": self.render_template,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Template':
        """Deserialize from dict."""
        fields = [TemplateField.from_dict(f) for f in data.get("fields", [])]
        child_slots = [TemplateChildSlot.from_dict(s) for s in data.get("child_slots", [])]
        return Template(
            template_id=data.get("template_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            fields=fields,
            child_slots=child_slots,
            render_template=data.get("render_template", ""),
            metadata=data.get("metadata", {}),
        )
