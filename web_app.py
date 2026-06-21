"""Flask web interface for Isokratis Legislature Builder."""

import json
import uuid
from datetime import datetime
from pathlib import Path

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
    """Load JSON template files into DB on startup."""
    templates_dir = Path(__file__).parent / "templates"
    for path in sorted(templates_dir.rglob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                tpl_data = json.load(f)
            template = Template.from_dict(tpl_data)
            template_repo.save_template(template)
        except Exception as e:
            print(f"Warning: could not load template {path.name}: {e}")


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
    return jsonify({"ok": True, "version_id": version_id})


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

@app.route("/api/preview", methods=["POST"])
def live_preview():
    data = request.get_json()
    if not data:
        return Response("<p>No data</p>", mimetype="text/html")
    try:
        doc = Document.from_dict(data)
        tmpl_dict = _get_templates_dict()
        renderer = HTMLRenderer(tmpl_dict)
        body = renderer.render_node(doc.root)
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ background: #e8e8e8; }}
  body {{
    font-family: "Georgia", "Times New Roman", serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #111;
    background: #e8e8e8;
    padding: 32px 24px;
  }}
  .page {{
    background: #fff;
    width: 210mm;
    max-width: 100%;
    min-height: 297mm;
    margin: 0 auto;
    padding: 25mm 20mm;
    box-shadow: 0 2px 20px rgba(0,0,0,0.18);
  }}
  h1 {{ font-size: 16pt; font-weight: bold; margin-bottom: 18pt; text-align: center; border-bottom: 2px solid #000; padding-bottom: 8pt; }}
  h2 {{ font-size: 13pt; font-weight: bold; margin: 14pt 0 6pt; }}
  h3 {{ font-size: 11pt; font-weight: bold; margin: 10pt 0 4pt; }}
  p {{ margin: 6pt 0; text-align: justify; }}
  ul, ol {{ margin: 6pt 0 6pt 20pt; }}
  li {{ margin: 3pt 0; }}
  .empty-doc {{ text-align: center; color: #aaa; padding: 60pt 0; font-style: italic; font-size: 10pt; }}
</style>
</head>
<body>
<div class="page">
  <h1>{_esc(doc.title)}</h1>
  {body if body.strip() else '<div class="empty-doc">Document is empty — add nodes to see content here.</div>'}
</div>
</body>
</html>"""
        return Response(html, mimetype="text/html")
    except Exception as e:
        return Response(f"<pre style='color:red;padding:20px'>Preview error: {e}</pre>", mimetype="text/html")


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
