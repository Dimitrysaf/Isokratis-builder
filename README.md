# Isokratis - Legislature Builder

A modular, template-driven document editor for Greek legislature documents (laws, gazettes, regulations) with support for nested templates, cross-references, and multiple export formats.

## Features

- **Modular Templates**: Define templates with form fields and rendering rules (no hardcoding).
- **Nested Templates**: Templates can contain other templates; parameters are filled as forms.
- **Node-based AST**: Generic, tree-based document structure.
- **Cross-References**: Mention and reference other nodes (articles, paragraphs, etc.); resolve and track backlinks.
- **Multiple Export Formats**: HTML, PDF, LaTeX, custom Legal XML.
- **SQLite Storage**: Persistent storage with FTS5 search.
- **Qt/PySide6 UI**: Native desktop application on Linux and Windows.

## Project Structure

```
Isokratis-builder/
├── src/
│   ├── models/           # Core data models (Node, Template, Document, Reference)
│   ├── db/              # Database schema and persistence layer
│   ├── renderers/       # Output renderers (HTML, PDF, LaTeX, XML)
│   ├── managers/        # Business logic (ReferenceManager, etc.)
│   └── ui/              # Qt/PySide6 user interface
├── templates/           # Default template definitions (JSON)
├── venv/               # Python virtual environment
├── app.py              # Application entry point
├── demo_init.py        # Demo: load templates and create sample document
├── test_suite.py       # Comprehensive test suite
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Installation

### Prerequisites

- Python 3.9+
- Linux (tested on Linux Mint) or Windows
- System libraries (on Linux): `libxcb-cursor0`, `libxcb-xinerama0`, `libxcb-shape0`

### Setup (Step-by-Step)

1. **Clone/navigate to the repository:**
   ```bash
   cd /home/dimitrys/Dev/Isokratis-builder
   ```

2. **Create a Python virtual environment:**
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # On Linux/macOS:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

4. **Install system libraries (Linux only):**
   ```bash
   sudo apt-get install -y libxcb-cursor0 libxcb-xinerama0 libxcb-shape0
   ```

5. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Running the Application

### Launch the GUI
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py
```

This opens the Isokratis main window where you can:
- Create and edit documents
- View the document tree structure on the left
- Edit template parameters in the right panel
- Add/delete nodes
- Export to multiple formats

### Initialize Demo Data
```bash
source venv/bin/activate
python demo_init.py
```

This:
- Creates the SQLite database in `~/.isokratis/documents.db`
- Loads 5 default templates (Article, Paragraph, Sub-paragraph, Header, Signature)
- Creates a sample law document with 2 articles
- Exports samples to `/tmp/sample.html`, `/tmp/sample.tex`, `/tmp/sample.xml`

### Run Tests
```bash
source venv/bin/activate
python test_suite.py
```

Tests verify:
- ✓ Node creation and tree manipulation
- ✓ Template definition and serialization
- ✓ Document creation and persistence
- ✓ Reference (cross-reference) system
- ✓ Database persistence (SQLite)
- ✓ HTML, LaTeX, XML renderers
- ✓ ReferenceManager (backlinks, validation)

## Usage Guide

### Creating a Document

1. **File → New Document**
2. The document tree shows structure on the left
3. Select a node to view/edit its parameters on the right
4. Click "Add Child Node" to insert content
5. Click "Save Document" to persist changes

### Using Templates

Templates are JSON files in the `templates/` directory. Example:

```json
{
  "template_id": "article",
  "name": "Άρθρο (Article)",
  "description": "A law article with number and paragraphs",
  "fields": [
    {
      "field_id": "article_number",
      "label": "Article Number",
      "field_type": "number",
      "required": true,
      "default_value": 1
    }
  ],
  "child_slots": [
    {
      "slot_id": "paragraphs",
      "label": "Paragraphs",
      "allowed_template_ids": ["paragraph"],
      "min_count": 1,
      "max_count": 0
    }
  ],
  "render_template": "<h2>Άρθρο {{ article_number }}</h2>{% for child in children %}{{ child }}{% endfor %}"
}
```

### Cross-References

The ReferenceManager handles mentions and cross-references:
- Create references between nodes
- Auto-generate display text (e.g., "Article 1", "Paragraph 2")
- Validate references (find broken links)
- Track backlinks (find all references pointing to a node)

### Exporting Documents

**Menu: Export**
- **Export as HTML**: Opens in browser, includes CSS styling
- **Export as PDF**: Requires WeasyPrint (or wkhtmltopdf)
- **Export as LaTeX**: For academic/publishing workflows
- **Export as Legal XML**: Custom Greek legal structure

## Architecture

### Core Models (`src/models/`)

**Node**: Generic tree node
```python
Node(
    node_id: str,
    node_type: str,  # "document", "article", "paragraph", or custom
    template_id: Optional[str],  # if set, this is a template instance
    data: Dict[str, Any],  # form parameters (article_number, content, etc.)
    children: List[Node],
    metadata: Dict[str, Any]
)
```

**Template**: Template definition (data-driven, no hardcoding)
```python
Template(
    template_id: str,
    name: str,
    fields: List[TemplateField],  # form inputs
    child_slots: List[TemplateChildSlot],  # where to nest templates
    render_template: str  # Jinja2 template for output
)
```

**Document**: Container for a legislature document
```python
Document(
    doc_id: str,
    title: str,
    root: Node,  # root AST node
    metadata: Dict[str, Any]
)
```

### Database (`src/db/`)

- **schema.py**: SQLite schema definition
- **persistence.py**: Repositories for CRUD operations
  - `DocumentRepository`: save/load documents
  - `TemplateRepository`: manage templates
  - `ReferenceRepository`: track cross-references

### Renderers (`src/renderers/`)

All inherit from `BaseRenderer`:
- **HTMLRenderer**: renders to HTML (with CSS)
- **PDFRenderer**: renders to PDF (WeasyPrint)
- **LaTeXRenderer**: renders to LaTeX
- **LegalXMLRenderer**: renders to custom Greek legal XML

Each renderer walks the AST and uses the template's Jinja2 render string.

### UI (`src/ui/`)

**MainWindow**: Qt/PySide6 window with:
- **Left panel**: Document tree (interactive, double-click to edit)
- **Right panel**: Form editor (fields from selected template)
- **Menu bar**: File (New, Open, Save), Export, Templates

### Managers (`src/managers/`)

**ReferenceManager**: Cross-reference system
- `create_reference()`: create a reference from one node to another
- `resolve_reference()`: find the target node
- `validate_references()`: check for broken links
- `get_backlinks()`: find all references pointing to a node

## Customization

### Adding a New Template

1. Create a JSON file in `templates/` (e.g., `templates/my_template.json`):
   ```json
   {
     "template_id": "my_tpl",
     "name": "My Custom Template",
     "fields": [
       {"field_id": "field1", "label": "Field 1", "field_type": "text"}
     ],
     "render_template": "<div>{{ field1 }}</div>"
   }
   ```

2. Restart the app or run `demo_init.py` to load templates

### Extending Export Formats

Subclass `BaseRenderer` and implement `render(doc: Document) -> str`:

```python
from src.renderers import BaseRenderer

class MyCustomRenderer(BaseRenderer):
    def render(self, doc: Document) -> str:
        # Walk doc.root and generate output
        return self.render_node(doc.root)
```

### Adding New Field Types

Edit `src/models/template.py` `TemplateFieldType` enum:
```python
class TemplateFieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    MY_CUSTOM = "my_custom"  # <-- add here
```

## Development Roadmap

- [ ] Template manager UI (create/edit templates without JSON)
- [ ] Drag/drop reordering in document tree
- [ ] Embedded web-based rich text editor (Lexical/ProseMirror) for paragraph content
- [ ] Auto-numbering (articles, paragraphs) with re-numbering
- [ ] Full-text search across documents
- [ ] Document history / version control
- [ ] Collaborative editing (future)
- [ ] Custom export plugins (WASM)

## Troubleshooting

### Qt Platform Plugin Error

If you see: `Could not load the Qt platform plugin "xcb"`

**Solution (Linux):**
```bash
sudo apt-get install libxcb-cursor0 libxcb-xinerama0 libxcb-shape0
```

### PDF Export Error

If PDF export fails: `TypeError: PDF.__init__()`

**Solution:**
- WeasyPrint version compatibility issue
- Use `Export as HTML` and print-to-PDF from your browser as a workaround
- Or run: `pip install --upgrade weasyprint pydyf`

### Database Lock Error

If you see: `database is locked`

- Close the application
- Delete `~/.isokratis/documents.db` to start fresh
- Re-run `python demo_init.py`

## License

TBD

## Contributing

Contributions welcome! Please:
- Follow PEP 8 style guidelines
- Add docstrings to new classes/functions
- Test renderers with sample documents
- Update this README for new features

## Support

For questions or issues, please open an issue on the repository or contact the development team.

---

**Status**: Beta (all core features working, UI refinements ongoing)
