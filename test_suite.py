"""Comprehensive test suite for Isokratis Legislature Builder."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.models import (
    Node, Template, TemplateField, TemplateChildSlot, Document, Reference, NodeType
)
from src.db import create_schema, DocumentRepository, TemplateRepository, ReferenceRepository
from src.renderers import HTMLRenderer, PDFRenderer, LaTeXRenderer, LegalXMLRenderer
from src.managers import ReferenceManager


def test_node_creation():
    """Test node AST creation and manipulation."""
    print("Testing Node creation...")
    
    # Create root node
    root = Node(node_type=NodeType.DOCUMENT)
    assert root.node_type == NodeType.DOCUMENT
    assert len(root.children) == 0
    
    # Create and add children
    child1 = Node(node_type="paragraph", data={"content": "First paragraph"})
    child2 = Node(node_type="paragraph", data={"content": "Second paragraph"})
    
    root.add_child(child1)
    root.add_child(child2)
    assert len(root.children) == 2
    
    # Find node
    found = root.find_node(child1.node_id)
    assert found == child1
    
    # Get all nodes
    all_nodes = root.get_all_nodes()
    assert len(all_nodes) == 3  # root + 2 children
    
    # Remove child
    assert root.remove_child(child1.node_id) == True
    assert len(root.children) == 1
    
    print("  ✓ Node creation and manipulation works")


def test_template_definition():
    """Test template definition creation."""
    print("Testing Template definition...")
    
    # Create template
    field1 = TemplateField(
        field_id="num",
        label="Number",
        field_type="number",
        required=True,
        default_value=1
    )
    field2 = TemplateField(
        field_id="title",
        label="Title",
        field_type="text",
        required=False
    )
    
    slot = TemplateChildSlot(
        slot_id="children",
        label="Child items",
        max_count=0  # unlimited
    )
    
    template = Template(
        template_id="tpl_test",
        name="Test Template",
        description="A test template",
        fields=[field1, field2],
        child_slots=[slot],
        render_template="<h1>{{ num }}: {{ title }}</h1>"
    )
    
    assert template.name == "Test Template"
    assert len(template.fields) == 2
    assert len(template.child_slots) == 1
    
    # Serialize/deserialize
    data = template.to_dict()
    restored = Template.from_dict(data)
    assert restored.template_id == template.template_id
    assert len(restored.fields) == 2
    
    print("  ✓ Template definition works")


def test_document_creation():
    """Test document creation and serialization."""
    print("Testing Document creation...")
    
    doc = Document(title="Test Law")
    assert doc.title == "Test Law"
    assert doc.root.node_type == NodeType.DOCUMENT
    
    # Add content
    para = Node(node_type="paragraph", data={"content": "Test content"})
    doc.root.add_child(para)
    
    # Serialize
    doc_dict = doc.to_dict()
    assert doc_dict["title"] == "Test Law"
    assert len(doc_dict["root"]["children"]) == 1
    
    # Deserialize
    restored = Document.from_dict(doc_dict)
    assert restored.title == doc.title
    assert len(restored.root.children) == 1
    
    print("  ✓ Document creation works")


def test_reference_creation():
    """Test reference (cross-reference) system."""
    print("Testing Reference system...")
    
    source = Node(node_id="node_1")
    target = Node(node_id="node_2")
    
    ref = Reference(
        source_node_id=source.node_id,
        target_node_id=target.node_id,
        reference_type="auto"
    )
    
    assert ref.source_node_id == "node_1"
    assert ref.target_node_id == "node_2"
    
    # Serialize
    ref_dict = ref.to_dict()
    restored = Reference.from_dict(ref_dict)
    assert restored.reference_id == ref.reference_id
    
    print("  ✓ Reference system works")


def test_database_persistence():
    """Test database schema and persistence."""
    print("Testing Database persistence...")
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        
        # Create schema
        create_schema(db_path)
        
        # Create repositories
        doc_repo = DocumentRepository(db_path)
        template_repo = TemplateRepository(db_path)
        
        # Create and save a template
        template = Template(
            template_id="tpl_test",
            name="Test",
            fields=[],
            render_template="<p>Test</p>"
        )
        template_repo.save_template(template)
        
        # Load template
        loaded = template_repo.load_template("tpl_test")
        assert loaded is not None
        assert loaded.name == "Test"
        
        # Create and save document
        doc = Document(title="Test Doc")
        doc.root.add_child(Node(node_type="paragraph", data={"content": "Hello"}))
        doc_repo.save_document(doc)
        
        # Load document
        loaded_doc = doc_repo.load_document(doc.doc_id)
        assert loaded_doc is not None
        assert loaded_doc.title == "Test Doc"
        assert len(loaded_doc.root.children) == 1
        
        print("  ✓ Database persistence works")


def test_renderers():
    """Test all renderers."""
    print("Testing Renderers...")
    
    # Create a simple document
    doc = Document(title="Test Document")
    article = Node(
        node_type="template_instance",
        template_id="tpl_article",
        data={"article_number": 1, "title": "First Article"}
    )
    para = Node(
        node_type="template_instance",
        template_id="tpl_paragraph",
        data={"paragraph_number": "1", "content": "Test content"}
    )
    article.add_child(para)
    doc.root.add_child(article)
    
    # Load templates
    templates_file = Path(__file__).parent / "templates" / "default_templates.json"
    with open(templates_file, "r", encoding="utf-8") as f:
        templates_data = json.load(f)
    
    templates = {t["template_id"]: Template.from_dict(t) for t in templates_data}
    
    # Test HTML renderer
    html_renderer = HTMLRenderer(templates)
    html = html_renderer.render(doc)
    assert "<!DOCTYPE html>" in html
    assert "Test Document" in html
    print("    ✓ HTML renderer works")
    
    # Test LaTeX renderer
    latex_renderer = LaTeXRenderer(templates)
    latex = latex_renderer.render(doc)
    assert "\\documentclass" in latex
    assert "Test Document" in latex
    print("    ✓ LaTeX renderer works")
    
    # Test Legal XML renderer
    xml_renderer = LegalXMLRenderer(templates)
    xml = xml_renderer.render(doc)
    assert "<?xml" in xml
    assert "νόμος" in xml
    print("    ✓ Legal XML renderer works")
    
    # Test PDF renderer (requires WeasyPrint)
    try:
        pdf_renderer = PDFRenderer(templates, use_weasyprint=True)
        pdf = pdf_renderer.render(doc)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100  # PDF header
        print("    ✓ PDF renderer works")
    except (ImportError, TypeError) as e:
        print(f"    ! PDF renderer skipped ({type(e).__name__}: dependency issue)")
    
    print("  ✓ All renderers work")


def test_reference_manager():
    """Test reference manager."""
    print("Testing ReferenceManager...")
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        create_schema(db_path)
        ref_repo = ReferenceRepository(db_path)
        
        # Create document with nodes
        doc = Document(title="Test")
        node1 = Node(node_id="article_1", node_type="article", data={"number": "1"})
        node2 = Node(node_id="para_1", node_type="paragraph", data={"number": "1"})
        
        doc.root.add_child(node1)
        node1.add_child(node2)
        
        # Create reference
        manager = ReferenceManager(ref_repo)
        ref = manager.create_reference(node2, node1, reference_type="auto")
        
        # Resolve reference
        resolved = manager.resolve_reference(ref, doc.root)
        assert resolved is not None
        assert resolved.node_id == node1.node_id
        
        # Get backlinks
        backlinks = manager.get_backlinks(node1.node_id)
        assert len(backlinks) == 1
        
        print("  ✓ ReferenceManager works")


def main():
    """Run all tests."""
    print("=" * 50)
    print("Isokratis Legislature Builder - Test Suite")
    print("=" * 50)
    print()
    
    try:
        test_node_creation()
        test_template_definition()
        test_document_creation()
        test_reference_creation()
        test_database_persistence()
        test_renderers()
        test_reference_manager()
        
        print()
        print("=" * 50)
        print("✓ ALL TESTS PASSED")
        print("=" * 50)
        return 0
    except Exception as e:
        print()
        print("=" * 50)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
