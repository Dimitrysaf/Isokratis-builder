"""Main application entry point."""

import json
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.db import create_schema, DocumentRepository, TemplateRepository, VersionRepository
from src.models import Template
from src.ui import MainWindow


def _sync_templates(template_repo: TemplateRepository, templates_dir: Path):
    """Load all *.json template files from templates/ into the DB on every startup."""
    for path in sorted(templates_dir.rglob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                tpl_data = json.load(f)
            template = Template.from_dict(tpl_data)
            template_repo.save_template(template)
        except Exception as e:
            print(f"Warning: could not load template {path.name}: {e}")


def main():
    """Run the Isokratis application."""
    # Initialize database
    db_path = Path.home() / ".isokratis" / "documents.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    create_schema(str(db_path))

    # Initialize repositories
    doc_repo = DocumentRepository(str(db_path))
    template_repo = TemplateRepository(str(db_path))
    version_repo = VersionRepository(str(db_path))

    # Sync templates from JSON files into DB
    templates_dir = Path(__file__).parent / "templates"
    _sync_templates(template_repo, templates_dir)

    # Create Qt application with Fusion style (consistent cross-platform look)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Create and show main window
    window = MainWindow(doc_repo, template_repo, version_repo, db_path=str(db_path))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
