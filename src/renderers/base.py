"""Base renderer class."""

from abc import ABC, abstractmethod
from ..models import Document


class BaseRenderer(ABC):
    """Abstract base class for document renderers."""

    @abstractmethod
    def render(self, doc: Document) -> str:
        """Render document to output string."""
        pass
