"""Isokratis Legislature Builder — Flask web interface (Akoma Ntoso 3.0)."""

import json
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for, Response

from src.db import create_schema, DocumentRepository, VersionRepository
from src.models import Document, INSTRUMENT_TYPES, AKN_TYPES, BODY_ROOT_CAN_ADD
from src.renderers import AkomaNtosoRenderer

app = Flask(__name__, template_folder="templates_web")

DB_PATH = Path.home() / ".isokratis" / "documents.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
create_schema(str(DB_PATH))

doc_repo     = DocumentRepository(str(DB_PATH))
version_repo = VersionRepository(str(DB_PATH))
renderer     = AkomaNtosoRenderer()


# ── Document list ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    docs = doc_repo.list_documents()
    return render_template("index.html", docs=docs, instrument_types=INSTRUMENT_TYPES)


# ── New document ──────────────────────────────────────────────────────────────

@app.route("/documents/new", methods=["GET", "POST"])
def new_document():
    if request.method == "POST":
        title  = request.form.get("title", "").strip() or "Χωρίς τίτλο"
        itype  = request.form.get("instrument_type", "nomos")
        if itype not in INSTRUMENT_TYPES:
            itype = "nomos"
        doc = Document(title=title, instrument_type=itype)
        doc_repo.save_document(doc)
        return redirect(url_for("edit_document", doc_id=doc.doc_id))
    return render_template("new_document.html", instrument_types=INSTRUMENT_TYPES)


# ── Edit document ─────────────────────────────────────────────────────────────

@app.route("/documents/<doc_id>")
def edit_document(doc_id):
    doc = doc_repo.load_document(doc_id)
    if not doc:
        return "Document not found", 404
    versions = version_repo.list_versions(doc_id)
    return render_template(
        "edit_document.html",
        doc=doc,
        doc_json=json.dumps(doc.to_dict()),
        versions=versions,
        instrument_types_json=json.dumps(INSTRUMENT_TYPES),
        akn_types_json=json.dumps(AKN_TYPES),
        body_root_can_add_json=json.dumps(BODY_ROOT_CAN_ADD),
    )


# ── Save document (AJAX) ──────────────────────────────────────────────────────

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


# ── Delete document ───────────────────────────────────────────────────────────

@app.route("/documents/<doc_id>/delete", methods=["POST"])
def delete_document(doc_id):
    doc_repo.delete_document(doc_id)
    return redirect(url_for("index"))


# ── Versions ──────────────────────────────────────────────────────────────────

@app.route("/api/documents/<doc_id>/version", methods=["POST"])
def save_version(doc_id):
    data = request.get_json() or {}
    doc  = doc_repo.load_document(doc_id)
    if not doc:
        return jsonify({"error": "Not found"}), 404
    vid      = version_repo.save_version(doc, note=data.get("note", ""))
    versions = version_repo.list_versions(doc_id)
    return jsonify({"ok": True, "version_id": vid, "versions": versions})


@app.route("/api/documents/<doc_id>/restore/<version_id>", methods=["POST"])
def restore_version(doc_id, version_id):
    restored = version_repo.load_version(version_id)
    if not restored:
        return jsonify({"error": "Version not found"}), 404
    restored.doc_id = doc_id
    restored.update_modified_time()
    doc_repo.save_document(restored)
    return jsonify({"ok": True, "doc": restored.to_dict()})


# ── Export: Akoma Ntoso XML ───────────────────────────────────────────────────

@app.route("/documents/<doc_id>/export/akn")
def export_akn(doc_id):
    doc = doc_repo.load_document(doc_id)
    if not doc:
        return "Document not found", 404
    xml = renderer.render(doc)
    return Response(
        xml,
        mimetype="application/xml",
        headers={"Content-Disposition": f"attachment; filename={doc_id}.akn.xml"},
    )


# ── Live AKN XML preview (AJAX) ───────────────────────────────────────────────

@app.route("/api/preview/akn", methods=["POST"])
def live_preview_akn():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    try:
        doc = Document.from_dict(data)
        xml = renderer.render(doc)
        return jsonify({"xml": xml})
    except Exception as e:
        import traceback
        print(f"AKN preview error:\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # use_reloader=False: Werkzeug's reloader spawns a second process that
    # races with the first on every SQLite write, causing "database is locked".
    # In Replit the workflow is restarted by the agent, so auto-reload is unused.
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
