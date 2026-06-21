"""Main application entry point."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.db import create_schema, DocumentRepository, TemplateRepository
from src.ui import MainWindow


def main():
    """Run the Isokratis application."""
    # Initialize database
    db_path = Path.home() / ".isokratis" / "documents.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    create_schema(str(db_path))

    # Initialize repositories
    doc_repo = DocumentRepository(str(db_path))
    template_repo = TemplateRepository(str(db_path))

    # Create Qt application
    app = QApplication(sys.argv)

    # Create and show main window
    window = MainWindow(doc_repo, template_repo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
