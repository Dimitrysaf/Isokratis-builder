"""Demo script: initialize templates and create a sample document."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.db import create_schema, DocumentRepository, TemplateRepository
from src.models import Document, Node, Template


def load_default_templates(template_repo: TemplateRepository, templates_dir: Path):
    """Load all *.json template files from the templates directory."""
    json_files = sorted(templates_dir.rglob("*.json"))
    if not json_files:
        print(f"No template files found in {templates_dir}")
        return

    for path in json_files:
        with open(path, "r", encoding="utf-8") as f:
            tpl_data = json.load(f)
        template = Template.from_dict(tpl_data)
        template_repo.save_template(template)
        print(f"✓ Loaded template: {template.name}  ({path.name})")


def create_sample_document(doc_repo: DocumentRepository, template_repo: TemplateRepository) -> str:
    """Create a sample document with articles and paragraphs."""
    
    # Create document
    doc = Document(title="Νόμος Δείγματος (Sample Law)")
    
    # Create an Article node (template instance)
    article_template = template_repo.load_template("tpl_article")
    if not article_template:
        print("Template tpl_article not found")
        return None
    
    article_node = Node(
        node_type="template_instance",
        template_id="tpl_article",
        data={
            "article_number": 1,
            "title": "Πρώτη διάταξη"
        }
    )
    
    # Create paragraph nodes (nested templates)
    para_template = template_repo.load_template("tpl_paragraph")
    
    para1 = Node(
        node_type="template_instance",
        template_id="tpl_paragraph",
        data={
            "paragraph_number": "1",
            "content": "Η παρούσα διάταξη εφαρμόζεται σε όλα τα υποκείμενα του δικαίου."
        }
    )
    
    para2 = Node(
        node_type="template_instance",
        template_id="tpl_paragraph",
        data={
            "paragraph_number": "2",
            "content": "Οι ρυθμίσεις του παρόντος άρθρου ισχύουν αντικειμενικά και χωρίς εξαιρέσεις."
        }
    )
    
    article_node.add_child(para1)
    article_node.add_child(para2)
    
    # Add article to document root
    doc.root.add_child(article_node)
    
    # Add another article
    article2 = Node(
        node_type="template_instance",
        template_id="tpl_article",
        data={
            "article_number": 2,
            "title": "Δεύτερη διάταξη"
        }
    )
    
    para3 = Node(
        node_type="template_instance",
        template_id="tpl_paragraph",
        data={
            "paragraph_number": "1",
            "content": "Ο εφαρμογέας της παρούσας διάταξης είναι το αρμόδιο υπουργείο."
        }
    )
    
    article2.add_child(para3)
    doc.root.add_child(article2)
    
    # Save document
    doc_repo.save_document(doc)
    print(f"✓ Created sample document: {doc.doc_id}")
    print(f"  Title: {doc.title}")
    print(f"  Articles: {len(doc.root.children)}")
    
    return doc.doc_id


def main():
    """Initialize database and load templates."""
    print("=== Isokratis Demo Initialization ===\n")
    
    # Setup database
    db_path = Path.home() / ".isokratis" / "documents.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Database: {db_path}")
    create_schema(str(db_path))
    print("✓ Database schema created\n")
    
    # Initialize repositories
    doc_repo = DocumentRepository(str(db_path))
    template_repo = TemplateRepository(str(db_path))
    
    # Load default templates
    templates_dir = Path(__file__).parent / "templates"
    print("Loading templates...")
    load_default_templates(template_repo, templates_dir)
    print()
    
    # Create sample document
    print("Creating sample document...")
    doc_id = create_sample_document(doc_repo, template_repo)
    print()
    
    # Export sample
    if doc_id:
        doc = doc_repo.load_document(doc_id)
        print("Sample exports:")
        
        # HTML export
        from src.renderers import HTMLRenderer
        templates = {t.template_id: t for t in template_repo.load_all_templates()}
        html_renderer = HTMLRenderer(templates)
        html = html_renderer.render(doc)
        with open("/tmp/sample.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("  ✓ /tmp/sample.html")
        
        # LaTeX export
        from src.renderers import LaTeXRenderer
        latex_renderer = LaTeXRenderer(templates)
        latex = latex_renderer.render(doc)
        with open("/tmp/sample.tex", "w", encoding="utf-8") as f:
            f.write(latex)
        print("  ✓ /tmp/sample.tex")
        
        # XML export
        from src.renderers import LegalXMLRenderer
        xml_renderer = LegalXMLRenderer(templates)
        xml = xml_renderer.render(doc)
        with open("/tmp/sample.xml", "w", encoding="utf-8") as f:
            f.write(xml)
        print("  ✓ /tmp/sample.xml")
    
    print("\n=== Done! ===")
    print(f"Run 'python app.py' to start the application.")


if __name__ == "__main__":
    main()
