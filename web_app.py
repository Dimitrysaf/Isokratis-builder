"""Flask web interface for Isokratis Legislature Builder."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser

from flask import Flask, render_template, request, jsonify, redirect, url_for, Response

from src.db import create_schema, DocumentRepository, TemplateRepository, VersionRepository
from src.models import Document, Node, Template, TemplateField, TemplateChildSlot
from src.renderers import HTMLRenderer, LaTeXRenderer, LegalXMLRenderer

app = Flask(__name__, template_folder="templates_web")

# Database setup
DB_PATH = Path.home() / ".isokratis" / "documents.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
create_schema(str(DB_PATH))

doc_repo = DocumentRepository(str(DB_PATH))
template_repo = TemplateRepository(str(DB_PATH))
version_repo = VersionRepository(str(DB_PATH))


def _sync_templates():
    """Load JSON template files into DB; remove any DB entries whose file was deleted."""
    templates_dir = Path(__file__).parent / "templates"
    file_ids: set[str] = set()
    for path in sorted(templates_dir.rglob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                tpl_data = json.load(f)
            template = Template.from_dict(tpl_data)
            template_repo.save_template(template)
            file_ids.add(template.template_id)
        except Exception as e:
            print(f"Warning: could not load template {path.name}: {e}")
    # Remove DB templates whose JSON files no longer exist
    for tpl in template_repo.load_all_templates():
        if tpl.template_id not in file_ids:
            template_repo.delete_template(tpl.template_id)


def _get_templates_dict():
    """Return all templates as a dict keyed by template_id."""
    return {t.template_id: t for t in template_repo.load_all_templates()}


_sync_templates()


# ──────────────────────────────────────────────────────────────
# Document list
# ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    docs = doc_repo.list_documents()
    return render_template("index.html", docs=docs)


# ──────────────────────────────────────────────────────────────
# New document
# ──────────────────────────────────────────────────────────────

@app.route("/documents/new", methods=["GET", "POST"])
def new_document():
    if request.method == "POST":
        title = request.form.get("title", "").strip() or "Untitled Document"
        doc = Document(title=title)
        doc_repo.save_document(doc)
        return redirect(url_for("edit_document", doc_id=doc.doc_id))
    return render_template("new_document.html")


# ──────────────────────────────────────────────────────────────
# Edit document
# ──────────────────────────────────────────────────────────────

@app.route("/documents/<doc_id>")
def edit_document(doc_id):
    _sync_templates()
    doc = doc_repo.load_document(doc_id)
    if not doc:
        return "Document not found", 404
    templates = template_repo.load_all_templates()
    versions = version_repo.list_versions(doc_id)
    templates_dicts = [t.to_dict() for t in templates]
    return render_template(
        "edit_document.html",
        doc=doc,
        templates=templates,
        templates_json=json.dumps(templates_dicts),
        versions=versions,
        doc_json=json.dumps(doc.to_dict()),
    )


# ──────────────────────────────────────────────────────────────
# Save document (AJAX)
# ──────────────────────────────────────────────────────────────

@app.route("/api/documents/<doc_id>/save", methods=["POST"])
def save_document(doc_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    try:
        doc = Document.from_dict(data)
        doc.doc_id = doc_id
        doc.update_modified_time()
        doc_repo.save_document(doc)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────
# Delete document
# ──────────────────────────────────────────────────────────────

@app.route("/documents/<doc_id>/delete", methods=["POST"])
def delete_document(doc_id):
    doc_repo.delete_document(doc_id)
    return redirect(url_for("index"))


# ──────────────────────────────────────────────────────────────
# Save version (AJAX)
# ──────────────────────────────────────────────────────────────

@app.route("/api/documents/<doc_id>/version", methods=["POST"])
def save_version(doc_id):
    data = request.get_json() or {}
    note = data.get("note", "")
    doc = doc_repo.load_document(doc_id)
    if not doc:
        return jsonify({"error": "Not found"}), 404
    version_id = version_repo.save_version(doc, note=note)
    versions = version_repo.list_versions(doc_id)
    return jsonify({"ok": True, "version_id": version_id, "versions": versions})


# List versions (AJAX)
# ──────────────────────────────────────────────────────────────

@app.route("/api/documents/<doc_id>/versions", methods=["GET"])
def list_versions(doc_id):
    versions = version_repo.list_versions(doc_id)
    return jsonify({"versions": versions})


# ──────────────────────────────────────────────────────────────
# Restore version
# ──────────────────────────────────────────────────────────────

@app.route("/api/documents/<doc_id>/restore/<version_id>", methods=["POST"])
def restore_version(doc_id, version_id):
    restored = version_repo.load_version(version_id)
    if not restored:
        return jsonify({"error": "Version not found"}), 404
    restored.doc_id = doc_id
    restored.update_modified_time()
    doc_repo.save_document(restored)
    return jsonify({"ok": True, "doc": restored.to_dict()})


# ──────────────────────────────────────────────────────────────
# Export routes
# ──────────────────────────────────────────────────────────────

@app.route("/documents/<doc_id>/export/html")
def export_html(doc_id):
    doc = doc_repo.load_document(doc_id)
    if not doc:
        return "Document not found", 404
    renderer = HTMLRenderer(_get_templates_dict())
    html = renderer.render(doc)
    return Response(html, mimetype="text/html")


@app.route("/documents/<doc_id>/export/latex")
def export_latex(doc_id):
    doc = doc_repo.load_document(doc_id)
    if not doc:
        return "Document not found", 404
    renderer = LaTeXRenderer(_get_templates_dict())
    latex = renderer.render(doc)
    return Response(
        latex,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={doc_id}.tex"},
    )


@app.route("/documents/<doc_id>/export/xml")
def export_xml(doc_id):
    doc = doc_repo.load_document(doc_id)
    if not doc:
        return "Document not found", 404
    renderer = LegalXMLRenderer(_get_templates_dict())
    xml = renderer.render(doc)
    return Response(
        xml,
        mimetype="application/xml",
        headers={"Content-Disposition": f"attachment; filename={doc_id}.xml"},
    )


# ──────────────────────────────────────────────────────────────
# Templates API
# ──────────────────────────────────────────────────────────────

@app.route("/api/templates")
def list_templates():
    templates = template_repo.load_all_templates()
    return jsonify([t.to_dict() for t in templates])


@app.route("/api/templates/<template_id>")
def get_template(template_id):
    t = template_repo.load_template(template_id)
    if not t:
        return jsonify({"error": "Not found"}), 404
    return jsonify(t.to_dict())


@app.route("/templates")
def templates_page():
    templates = template_repo.load_all_templates()
    return render_template("templates.html", templates=templates)


@app.route("/templates/new", methods=["GET", "POST"])
def new_template():
    if request.method == "POST":
        try:
            data = request.get_json() or request.form.to_dict()
            if isinstance(data, dict) and "template_id" not in data:
                data["template_id"] = str(uuid.uuid4())
            template = Template.from_dict(data)
            template_repo.save_template(template)
            return jsonify({"ok": True, "template_id": template.template_id})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return render_template("template_editor.html", template=None)


@app.route("/templates/<template_id>/edit", methods=["GET", "POST"])
def edit_template(template_id):
    if request.method == "POST":
        try:
            data = request.get_json() or {}
            data["template_id"] = template_id
            template = Template.from_dict(data)
            template_repo.save_template(template)
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    t = template_repo.load_template(template_id)
    if not t:
        return "Template not found", 404
    return render_template("template_editor.html", template=t)


@app.route("/templates/<template_id>/delete", methods=["POST"])
def delete_template(template_id):
    template_repo.delete_template(template_id)
    return redirect(url_for("templates_page"))


# ──────────────────────────────────────────────────────────────
# Live preview (renders doc JSON → styled HTML)
# ──────────────────────────────────────────────────────────────

# ── PDF generation helpers ─────────────────────────────────

_DEJAVU      = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
_DEJAVU_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

_HEADING_TAGS   = {"h1", "h2", "h3", "h4", "h5", "h6"}
_BLOCK_TAGS     = _HEADING_TAGS | {"p", "li", "blockquote", "pre", "td", "th"}


class _HTMLExtractor(HTMLParser):
    """Walk rendered HTML and emit a flat list of (tag, text) pairs."""

    def __init__(self):
        super().__init__()
        self.items: list[tuple[str, str]] = []
        self._tag: str | None = None
        self._buf: list[str] = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _BLOCK_TAGS and self._tag is None:
            self._tag = tag
            self._buf = []
            self._depth = 1
        elif self._tag is not None:
            self._depth += 1

    def handle_endtag(self, tag):
        if self._tag is None:
            return
        if tag == self._tag:
            self._depth -= 1
            if self._depth <= 0:
                text = " ".join("".join(self._buf).split()).strip()
                if text:
                    self.items.append((self._tag, text))
                self._tag = None
                self._buf = []
        else:
            self._depth -= 1

    def handle_data(self, data):
        if self._tag is not None:
            self._buf.append(data)


def _generate_pdf_bytes(doc, tmpl_dict) -> bytes:
    """Render doc → HTML → parse → fpdf2 PDF bytes (no system C libs required)."""
    from fpdf import FPDF

    renderer = HTMLRenderer(tmpl_dict)
    # Seed root context with doc.title as fallback if not already in root.data
    if 'title' not in doc.root.data:
        doc.root.data['title'] = doc.title
    html_body = renderer.render_node(doc.root)
    full_html = html_body  # root renders nothing itself; children carry all content

    extractor = _HTMLExtractor()
    extractor.feed(full_html)
    items = extractor.items

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=20, top=25, right=20)
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.add_font("DejaVu", "",  _DEJAVU)
    pdf.add_font("DejaVu", "B", _DEJAVU_BOLD)

    pdf.add_page()
    effective_width = pdf.w - pdf.l_margin - pdf.r_margin  # 170 mm on A4

    for tag, text in items:
        if tag == "h1":
            pdf.set_font("DejaVu", "B", 16)
            pdf.multi_cell(effective_width, 9, text, align="C", new_x="LMARGIN", new_y="NEXT")
            # Underline rule
            x, y = pdf.l_margin, pdf.get_y() + 1
            pdf.line(x, y, x + effective_width, y)
            pdf.ln(5)
        elif tag == "h2":
            pdf.ln(4)
            pdf.set_font("DejaVu", "B", 13)
            pdf.multi_cell(effective_width, 8, text, align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif tag == "h3":
            pdf.ln(3)
            pdf.set_font("DejaVu", "B", 11.5)
            pdf.multi_cell(effective_width, 7, text, align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif tag == "li":
            pdf.set_font("DejaVu", "", 11)
            pdf.multi_cell(effective_width - 5, 6.5, f"\u2022  {text}", align="L",
                           new_x="LMARGIN", new_y="NEXT")
        else:  # p, td, th, blockquote, etc.
            pdf.set_font("DejaVu", "", 11)
            pdf.multi_cell(effective_width, 6.5, text, align="J", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    return bytes(pdf.output())


def _build_preview_html(doc, tmpl_dict):
    """Build an HTML preview string (used for the HTML fallback endpoint)."""
    renderer = HTMLRenderer(tmpl_dict)
    if 'title' not in doc.root.data:
        doc.root.data['title'] = doc.title
    body = renderer.render_node(doc.root)
    empty = '<p style="text-align:center;color:#aaa;margin-top:60pt;font-style:italic;">Document is empty — add nodes to see content here.</p>'
    return f"""<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: A4; margin: 25mm 20mm; }}
  body {{
    font-family: "Georgia", "Times New Roman", serif;
    font-size: 11pt; line-height: 1.75; color: #111;
    margin: 0; padding: 0;
  }}
  h1 {{ font-size: 15pt; font-weight: bold; margin-bottom: 16pt; text-align: center; border-bottom: 1.5pt solid #000; padding-bottom: 6pt; }}
  h2 {{ font-size: 12.5pt; font-weight: bold; margin: 14pt 0 5pt; }}
  h3 {{ font-size: 11pt; font-weight: bold; margin: 10pt 0 4pt; }}
  p  {{ margin: 5pt 0; text-align: justify; }}
  ul, ol {{ margin: 5pt 0 5pt 18pt; }}
  li {{ margin: 2pt 0; }}
</style>
</head>
<body>
{body if body.strip() else empty}
</body>
</html>"""


@app.route("/api/preview/pdf", methods=["POST"])
def live_preview_pdf():
    """Generate a real binary PDF from posted doc JSON (application/pdf)."""
    data = request.get_json()
    if not data:
        return Response(b"", status=400)
    try:
        doc = Document.from_dict(data)
        tmpl_dict = _get_templates_dict()
        pdf_bytes = _generate_pdf_bytes(doc, tmpl_dict)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": "inline; filename=preview.pdf"},
        )
    except Exception as e:
        import traceback
        print(f"PDF preview error: {traceback.format_exc()}")
        return Response(json.dumps({"error": str(e)}), status=500, mimetype="application/json")


@app.route("/api/preview", methods=["POST"])
def live_preview():
    """HTML preview (kept for fallback)."""
    data = request.get_json()
    if not data:
        return Response("<p>No data</p>", mimetype="text/html")
    try:
        doc = Document.from_dict(data)
        tmpl_dict = _get_templates_dict()
        html = _build_preview_html(doc, tmpl_dict)
        return Response(html, mimetype="text/html")
    except Exception as e:
        return Response(f"<pre style='color:red;padding:20px'>Preview error: {e}</pre>", mimetype="text/html")


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
