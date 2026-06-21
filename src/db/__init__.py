"""Database module."""

from .schema import create_schema, get_connection
from .persistence import DocumentRepository, TemplateRepository, ReferenceRepository

__all__ = [
    "create_schema",
    "get_connection",
    "DocumentRepository",
    "TemplateRepository",
    "ReferenceRepository",
]
