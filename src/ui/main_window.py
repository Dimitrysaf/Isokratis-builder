"""Main application window (PySide6/Qt)."""

import json
import os
import tempfile
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit, QScrollArea, QFormLayout,
    QDialog, QDialogButtonBox, QListWidget, QListWidgetItem, QFileDialog,
    QTextEdit, QSpinBox, QComboBox, QDateEdit, QCheckBox, QMessageBox,
    QInputDialog, QStatusBar, QAbstractItemView, QGroupBox, QToolBar, QFrame,
    QStyle,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QAction, QFont
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView


from ..models import Document, Node, Template, TemplateField, TemplateFieldType
from ..db import DocumentRepository, TemplateRepository


# ─────────────────────────────────────────────────────────────
# Βοηθητικά παράθυρα διαλόγου
# ─────────────────────────────────────────────────────────────

class DocumentOpenDialog(QDialog):
    """Επιλογή υπάρχοντος εγγράφου από τη βάση δεδομένων."""

    def __init__(self, doc_repo: DocumentRepository, parent=None):
        super().__init__(parent)
        self.doc_repo = doc_repo
        self.selected_doc_id: Optional[str] = None
        self.setWindowTitle("Άνοιγμα Εγγράφου")
        self.setMinimumSize(520, 380)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Επιλέξτε έγγραφο:"))

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._accept)
        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Άνοιγμα")
        buttons.button(QDialogButtonBox.Cancel).setText("Άκυρο")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh()

    def _refresh(self):
        self.list_widget.clear()
        docs = self.doc_repo.list_documents()
        if not docs:
            self.list_widget.addItem("(Δεν υπάρχουν αποθηκευμένα έγγραφα)")
            return
        for doc in docs:
            ts = (doc.get("updated_at") or "")[:19]
            item = QListWidgetItem(f"{doc['title']}  [{ts}]")
            item.setData(Qt.UserRole, doc["doc_id"])
            self.list_widget.addItem(item)

    def _accept(self):
        item = self.list_widget.currentItem()
        if item and item.data(Qt.UserRole):
            self.selected_doc_id = item.data(Qt.UserRole)
            self.accept()


_CAT_ORDER = ["δομή", "προοίμιο", "σώμα", "κλείσιμο", "βασικά"]
_CAT_LABELS = {
    "δομή": "Δομή Εγγράφου",
    "προοίμιο": "Προοίμιο",
    "σώμα": "Σώμα Κειμένου",
    "κλείσιμο": "Κλείσιμο",
    "βασικά": "Βασικά",
}


def _build_template_tree(tree: QTreeWidget, templates, data_role=Qt.UserRole):
    """Γεμίζει QTreeWidget με templates ομαδοποιημένα ανά κατηγορία."""
    tree.clear()
    groups: Dict[str, list] = {}
    for tpl in templates:
        cat = tpl.metadata.get("category", "άλλο")
        groups.setdefault(cat, []).append(tpl)

    seen: set = set()
    for cat in _CAT_ORDER + sorted(groups):
        if cat in seen or cat not in groups:
            continue
        seen.add(cat)
        label = _CAT_LABELS.get(cat, cat.capitalize())
        header = QTreeWidgetItem([label, ""])
        f = header.font(0)
        f.setBold(True)
        header.setFont(0, f)
        header.setFlags(header.flags() & ~Qt.ItemIsSelectable)
        tree.addTopLevelItem(header)
        for tpl in groups[cat]:
            child = QTreeWidgetItem([tpl.name, tpl.description or ""])
            child.setData(0, data_role, tpl)
            header.addChild(child)

    tree.expandAll()


class TemplatePickerDialog(QDialog):
    """Επιλογή προτύπου για νέο κόμβο."""

    def __init__(self, template_repo: TemplateRepository, parent=None):
        super().__init__(parent)
        self.template_repo = template_repo
        self.selected_template: Optional[Template] = None
        self.setWindowTitle("Επιλογή Προτύπου")
        self.setMinimumSize(600, 440)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Επιλέξτε πρότυπο για τον νέο κόμβο:"))

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Πρότυπο", "Περιγραφή"])
        self.tree.setColumnWidth(0, 220)
        self.tree.header().setStretchLastSection(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Επιλογή")
        buttons.button(QDialogButtonBox.Cancel).setText("Άκυρο")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        _build_template_tree(self.tree, self.template_repo.load_all_templates())

    def _on_double_click(self, item: QTreeWidgetItem, _col: int):
        tpl = item.data(0, Qt.UserRole)
        if tpl:
            self.selected_template = tpl
            self.accept()

    def _accept(self):
        item = self.tree.currentItem()
        if item:
            tpl = item.data(0, Qt.UserRole)
            if tpl:
                self.selected_template = tpl
                self.accept()


class TemplateManagerDialog(QDialog):
    """Δημιουργία, επεξεργασία και διαγραφή προτύπων."""

    def __init__(self, template_repo: TemplateRepository, parent=None):
        super().__init__(parent)
        self.template_repo = template_repo
        self.current_template: Optional[Template] = None
        self.setWindowTitle("Διαχείριση Προτύπων")
        self.setMinimumSize(1060, 680)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(12)

        # Αριστερά: δέντρο κατηγοριών + κουμπιά
        left = QWidget()
        left.setFixedWidth(260)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(QLabel("Πρότυπα:"))

        self.tpl_tree = QTreeWidget()
        self.tpl_tree.setHeaderHidden(True)
        self.tpl_tree.setAlternatingRowColors(True)
        self.tpl_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tpl_tree.currentItemChanged.connect(self._on_selected)
        ll.addWidget(self.tpl_tree)

        btn_new = QPushButton("+ Νέο Πρότυπο")
        btn_del = QPushButton("Διαγραφή")
        btn_new.clicked.connect(self._on_new)
        btn_del.clicked.connect(self._on_delete)
        ll.addWidget(btn_new)
        ll.addWidget(btn_del)
        layout.addWidget(left)

        # Δεξιά: φόρμα επεξεργασίας
        right = QGroupBox("Επεξεργασία Προτύπου")
        rl = QFormLayout(right)
        rl.setSpacing(10)

        self.name_edit = QLineEdit()
        rl.addRow("Όνομα:", self.name_edit)

        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("π.χ. tpl_my_template")
        rl.addRow("Αναγνωριστικό:", self.id_edit)

        self.desc_edit = QLineEdit()
        rl.addRow("Περιγραφή:", self.desc_edit)

        self.render_edit = QTextEdit()
        self.render_edit.setMinimumHeight(120)
        self.render_edit.setPlaceholderText("<div>{{ field_id }}</div>")
        monospace = QFont("Monospace")
        monospace.setStyleHint(QFont.TypeWriter)
        self.render_edit.setFont(monospace)
        rl.addRow("Πρότυπο Εμφάνισης (Jinja2):", self.render_edit)

        self.fields_edit = QTextEdit()
        self.fields_edit.setMinimumHeight(200)
        self.fields_edit.setFont(monospace)
        self.fields_edit.setPlaceholderText(
            '[{"field_id": "f1", "label": "Πεδίο", "field_type": "text", "required": false}]'
        )
        rl.addRow("Πεδία (JSON):", self.fields_edit)

        btn_save = QPushButton("Αποθήκευση Προτύπου")
        btn_save.clicked.connect(self._on_save)
        rl.addRow(btn_save)

        layout.addWidget(right, 1)
        self._refresh_list()

    def _refresh_list(self):
        _build_template_tree(self.tpl_tree, self.template_repo.load_all_templates())

    def _on_selected(self, item: QTreeWidgetItem, _prev):
        if not item:
            return
        tpl = item.data(0, Qt.UserRole)
        if not tpl:
            return  # category header
        self.current_template = tpl
        self.name_edit.setText(tpl.name)
        self.id_edit.setText(tpl.template_id)
        self.desc_edit.setText(tpl.description or "")
        self.render_edit.setPlainText(tpl.render_template or "")
        self.fields_edit.setPlainText(
            json.dumps([f.to_dict() for f in tpl.fields], ensure_ascii=False, indent=2)
        )

    def _select_by_id(self, tpl_id: str):
        root = self.tpl_tree.invisibleRootItem()
        for i in range(root.childCount()):
            cat_item = root.child(i)
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                tpl = child.data(0, Qt.UserRole)
                if tpl and tpl.template_id == tpl_id:
                    self.tpl_tree.setCurrentItem(child)
                    return

    def _on_new(self):
        name, ok = QInputDialog.getText(self, "Νέο Πρότυπο", "Όνομα προτύπου:")
        if not ok or not name.strip():
            return
        tpl_id, ok = QInputDialog.getText(self, "Νέο Πρότυπο", "Αναγνωριστικό (π.χ. tpl_my):")
        if not ok or not tpl_id.strip():
            return
        tpl = Template(template_id=tpl_id.strip(), name=name.strip())
        self.template_repo.save_template(tpl)
        self._refresh_list()
        self._select_by_id(tpl_id.strip())

    def _on_save(self):
        if not self.current_template:
            QMessageBox.warning(self, "Κανένα Πρότυπο", "Επιλέξτε ή δημιουργήστε πρότυπο πρώτα.")
            return
        try:
            fields_data = json.loads(self.fields_edit.toPlainText() or "[]")
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Σφάλμα JSON", f"Μη έγκυρο JSON πεδίων:\n{e}")
            return
        self.current_template.name = self.name_edit.text()
        self.current_template.template_id = self.id_edit.text()
        self.current_template.description = self.desc_edit.text()
        self.current_template.render_template = self.render_edit.toPlainText()
        self.current_template.fields = [TemplateField.from_dict(f) for f in fields_data]
        self.template_repo.save_template(self.current_template)
        self._refresh_list()
        self._select_by_id(self.current_template.template_id)
        QMessageBox.information(self, "Αποθηκεύτηκε", "Το πρότυπο αποθηκεύτηκε.")

    def _on_delete(self):
        item = self.tpl_tree.currentItem()
        if not item:
            return
        tpl = item.data(0, Qt.UserRole)
        if not tpl:
            return  # category header
        tpl_id = tpl.template_id
        if QMessageBox.question(self, "Διαγραφή", f"Διαγραφή προτύπου '{tpl.name}';",
                                QMessageBox.Yes | QMessageBox.No,
                                defaultButton=QMessageBox.No) == QMessageBox.Yes:
            self.template_repo.delete_template(tpl_id)
            self.current_template = None
            self._refresh_list()
            for w in (self.name_edit, self.id_edit, self.desc_edit):
                w.clear()
            self.render_edit.clear()
            self.fields_edit.clear()


class HistoryDialog(QDialog):
    """Περιήγηση και επαναφορά στιγμιοτύπων εγγράφου."""

    def __init__(self, doc: Document, version_repo, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.version_repo = version_repo
        self.restored_doc: Optional[Document] = None
        self.setWindowTitle("Ιστορικό Εγγράφου")
        self.setMinimumSize(520, 380)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Στιγμιότυπα: {self.doc.title}"))

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_restore = QPushButton("Επαναφορά Επιλεγμένης Έκδοσης")
        btn_restore.clicked.connect(self._on_restore)
        layout.addWidget(btn_restore)

        close_btn = QDialogButtonBox(QDialogButtonBox.Close)
        close_btn.button(QDialogButtonBox.Close).setText("Κλείσιμο")
        close_btn.rejected.connect(self.reject)
        layout.addWidget(close_btn)

        self._refresh()

    def _refresh(self):
        self.list_widget.clear()
        versions = self.version_repo.list_versions(self.doc.doc_id)
        if not versions:
            self.list_widget.addItem(
                "(Δεν υπάρχουν στιγμιότυπα — χρησιμοποιήστε Ιστορικό → Αποθήκευση Στιγμιοτύπου)"
            )
            return
        for v in versions:
            note = f"  {v.get('note')}" if v.get("note") else ""
            item = QListWidgetItem(f"v{v['version_number']}  —  {(v['created_at'] or '')[:19]}{note}")
            item.setData(Qt.UserRole, v["version_id"])
            self.list_widget.addItem(item)

    def _on_restore(self):
        item = self.list_widget.currentItem()
        if not item or not item.data(Qt.UserRole):
            return
        if QMessageBox.question(
            self, "Επαναφορά",
            "Επαναφορά αυτής της έκδοσης; Οι μη αποθηκευμένες αλλαγές θα χαθούν.",
            QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No
        ) == QMessageBox.Yes:
            self.restored_doc = self.version_repo.load_version(item.data(Qt.UserRole))
            self.accept()


# ─────────────────────────────────────────────────────────────
# Δέντρο εγγράφου με υποστήριξη drag/drop
# ─────────────────────────────────────────────────────────────

class DocumentTreeWidget(QTreeWidget):
    """QTreeWidget με εσωτερικό drag/drop για αναδιάταξη."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self._drop_callback = None

    def set_drop_callback(self, cb):
        self._drop_callback = cb

    def dropEvent(self, event):
        super().dropEvent(event)
        if self._drop_callback:
            self._drop_callback()


# ─────────────────────────────────────────────────────────────
# Κύριο παράθυρο
# ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Κύριο παράθυρο εφαρμογής."""

    def __init__(self, doc_repo: DocumentRepository, template_repo: TemplateRepository,
                 version_repo=None, db_path: str = None):
        super().__init__()
        self.doc_repo = doc_repo
        self.template_repo = template_repo
        self.version_repo = version_repo
        self._db_path = db_path
        self._preview_tmp: Optional[str] = None
        self.current_doc: Optional[Document] = None
        self.selected_node: Optional[Node] = None
        self._field_widgets: Dict[str, object] = {}
        self._pdf_doc = QPdfDocument(self)

        self.setWindowTitle("Ισοκράτης - Δημιουργός Νομοθεσίας")
        self.setGeometry(100, 100, 1440, 920)
        self._setup_ui()
        sb = QStatusBar()
        self.setStatusBar(sb)
        if db_path:
            sb.addPermanentWidget(QLabel(f"  {db_path}  "))

    # ── Διάταξη UI ──

    def _setup_ui(self):
        sp = self.style()

        # ── Shared actions: δημιουργούνται μία φορά, χρησιμοποιούνται σε toolbar ΚΑΙ menu ──
        self._act_new  = QAction(sp.standardIcon(QStyle.SP_FileIcon),         "Νέο Έγγραφο",  self)
        self._act_open = QAction(sp.standardIcon(QStyle.SP_DialogOpenButton), "Άνοιγμα…",     self)
        self._act_save = QAction(sp.standardIcon(QStyle.SP_DialogSaveButton), "Αποθήκευση",   self)
        self._act_save.setShortcut("Ctrl+S")
        self._act_new.setToolTip("Δημιουργία νέου εγγράφου")
        self._act_open.setToolTip("Άνοιγμα αποθηκευμένου εγγράφου")
        self._act_save.setToolTip("Αποθήκευση (Ctrl+S)")
        self._act_new.triggered.connect(self._on_new_document)
        self._act_open.triggered.connect(self._on_open_document)
        self._act_save.triggered.connect(self._on_save_document)

        # ── Toolbar ──────────────────────────────────────────
        tb = QToolBar("Κύρια Εργαλεία")
        tb.setMovable(False)
        tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(tb)
        tb.addAction(self._act_new)
        tb.addAction(self._act_open)
        tb.addAction(self._act_save)
        tb.addSeparator()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Αναζήτηση στο έγγραφο…")
        self.search_input.setMaximumWidth(220)
        self.search_input.returnPressed.connect(self._on_search)
        tb.addWidget(self.search_input)

        # ── Κεντρικό layout ──────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        # ── Αριστερό panel: τίτλος + δέντρο + κουμπιά κόμβων ──
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(6, 6, 3, 6)
        ll.setSpacing(4)

        self.doc_title_edit = QLineEdit()
        self.doc_title_edit.setPlaceholderText("Τίτλος εγγράφου…")
        self.doc_title_edit.textChanged.connect(self._on_title_changed)
        ll.addWidget(self.doc_title_edit)

        self.tree_widget = DocumentTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.itemClicked.connect(self._on_tree_item_selected)
        self.tree_widget.set_drop_callback(self._on_tree_reordered)
        ll.addWidget(self.tree_widget)

        # Κουμπιά κόμβων: δίπλα στο tree, με system icons και tooltips
        node_btn_row = QHBoxLayout()
        node_btn_row.setSpacing(2)
        node_btn_row.setContentsMargins(0, 0, 0, 0)

        def _icon_btn(std_pixmap, tooltip: str, slot) -> QPushButton:
            b = QPushButton()
            b.setIcon(sp.standardIcon(std_pixmap))
            b.setToolTip(tooltip)
            b.setFixedSize(28, 28)
            b.clicked.connect(slot)
            node_btn_row.addWidget(b)
            return b

        _icon_btn(QStyle.SP_FileDialogNewFolder, "Προσθήκη κόμβου",    self._on_add_child)
        _icon_btn(QStyle.SP_ArrowUp,             "Μετακίνηση πάνω",    self._on_move_node_up)
        _icon_btn(QStyle.SP_ArrowDown,           "Μετακίνηση κάτω",    self._on_move_node_down)
        _icon_btn(QStyle.SP_TrashIcon,           "Διαγραφή κόμβου",    self._on_delete_node)
        node_btn_row.addStretch()
        ll.addLayout(node_btn_row)

        splitter.addWidget(left)

        # ── Δεξί panel: φόρμα επεξεργασίας ──────────────────
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(3, 6, 6, 6)
        rl.setSpacing(6)

        self.editor_label = QLabel("Επιλέξτε κόμβο για επεξεργασία")
        lf = QFont(self.editor_label.font())
        lf.setBold(True)
        lf.setPointSize(lf.pointSize() + 1)
        self.editor_label.setFont(lf)
        rl.addWidget(self.editor_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        rl.addWidget(sep)

        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(8)
        self.form_layout.setContentsMargins(2, 2, 2, 2)
        form_widget = QWidget()
        form_widget.setLayout(self.form_layout)
        scroll = QScrollArea()
        scroll.setWidget(form_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        rl.addWidget(scroll)

        splitter.addWidget(right)

        # ── Τρίτο panel: native PDF viewer ───────────────────
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self._pdf_doc)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
        splitter.addWidget(self.pdf_view)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)
        splitter.setSizes([300, 580, 560])

        root_layout.addWidget(splitter)
        self._setup_menu()

    def _setup_menu(self):
        mb = self.menuBar()

        # Χρησιμοποιούμε τα ίδια QAction objects — δεν υπάρχουν duplicates
        file_menu = mb.addMenu("Αρχείο")
        file_menu.addAction(self._act_new)
        file_menu.addAction(self._act_open)
        file_menu.addSeparator()
        file_menu.addAction(self._act_save)
        file_menu.addSeparator()
        self._action(file_menu, "Έξοδος", self.close)

        export_menu = mb.addMenu("Εξαγωγή")
        self._action(export_menu, "Εξαγωγή ως HTML…", self._on_export_html)
        self._action(export_menu, "Εξαγωγή ως PDF…", self._on_export_pdf)
        self._action(export_menu, "Εξαγωγή ως LaTeX…", self._on_export_latex)
        self._action(export_menu, "Εξαγωγή ως Νομικό XML…", self._on_export_xml)

        tpl_menu = mb.addMenu("Πρότυπα")
        self._action(tpl_menu, "Διαχείριση Προτύπων…", self._on_manage_templates)

        hist_menu = mb.addMenu("Ιστορικό")
        self._action(hist_menu, "Αποθήκευση Στιγμιοτύπου…", self._on_save_snapshot)
        self._action(hist_menu, "Περιήγηση Ιστορικού…", self._on_browse_history)

    def _action(self, menu, label: str, slot, shortcut: str = None):
        a = QAction(label, self)
        if shortcut:
            a.setShortcut(shortcut)
        a.triggered.connect(slot)
        menu.addAction(a)
        return a

    def _status(self, msg: str, ms: int = 3000):
        self.statusBar().showMessage(msg, ms)

    # ── Λειτουργίες εγγράφου ──

    def load_document(self, doc_id: str):
        doc = self.doc_repo.load_document(doc_id)
        if doc:
            self.current_doc = doc
            self.doc_title_edit.setText(doc.title)
            self._refresh_tree()
            self._refresh_preview()

    def _on_new_document(self):
        title, ok = QInputDialog.getText(self, "Νέο Έγγραφο", "Τίτλος εγγράφου:")
        if ok and title.strip():
            self.current_doc = Document(title=title.strip())
            self.doc_title_edit.setText(self.current_doc.title)
            self.selected_node = None
            self._refresh_tree()
            self._status(f"Νέο έγγραφο: {title}")

    def _on_open_document(self):
        dlg = DocumentOpenDialog(self.doc_repo, self)
        if dlg.exec() == QDialog.Accepted and dlg.selected_doc_id:
            self.load_document(dlg.selected_doc_id)
            self._status(f"Άνοιγμα: {self.current_doc.title}")

    def _on_title_changed(self, text: str):
        if self.current_doc:
            self.current_doc.title = text

    def _on_save_document(self):
        if not self.current_doc:
            self._status("Δεν υπάρχει ανοιχτό έγγραφο.")
            return
        self._auto_number_document()
        self.current_doc.update_modified_time()
        self.doc_repo.save_document(self.current_doc)
        self._refresh_tree()
        self._refresh_preview()
        self._status("Το έγγραφο αποθηκεύτηκε.")

    def _refresh_preview(self):
        if not self.current_doc:
            self._pdf_doc.close()
            return
        try:
            from ..renderers import PDFRenderer
            pdf_bytes = PDFRenderer(self._templates(), use_weasyprint=True).render(self.current_doc)
            self._pdf_doc.close()
            if self._preview_tmp:
                try:
                    os.unlink(self._preview_tmp)
                except OSError:
                    pass
            fd, self._preview_tmp = tempfile.mkstemp(suffix=".pdf")
            with os.fdopen(fd, "wb") as f:
                f.write(pdf_bytes)
            self._pdf_doc.load(self._preview_tmp)
        except Exception as e:
            self._status(f"Προεπισκόπηση: {e}", 5000)

    # ── Δέντρο ──

    def _refresh_tree(self):
        self.tree_widget.clear()
        if self.current_doc:
            for child in self.current_doc.root.children:
                self.tree_widget.addTopLevelItem(self._node_to_item(child))
            self.tree_widget.expandAll()

    def _node_to_item(self, node: Node) -> QTreeWidgetItem:
        label = node.node_type
        if node.template_id:
            tpl = self.template_repo.load_template(node.template_id)
            if tpl:
                first = next((str(v) for v in node.data.values() if v), "")
                label = tpl.name + (f": {first[:40]}" if first else "")
        elif node.data.get("content"):
            label += f": {str(node.data['content'])[:50]}"

        item = QTreeWidgetItem([label])
        item.setData(0, Qt.UserRole, node.node_id)
        for child in node.children:
            item.addChild(self._node_to_item(child))
        return item

    def _on_tree_item_selected(self, item: QTreeWidgetItem, _col: int):
        if not self.current_doc:
            return
        node_id = item.data(0, Qt.UserRole)
        self.selected_node = self.current_doc.root.find_node(node_id)
        self._load_node_form()

    def _on_tree_reordered(self):
        if not self.current_doc:
            return
        inv_root = self.tree_widget.invisibleRootItem()
        new_children = []
        for i in range(inv_root.childCount()):
            child_item = inv_root.child(i)
            child_node = self.current_doc.root.find_node(child_item.data(0, Qt.UserRole))
            if child_node:
                new_children.append(child_node)
                self._sync_tree_to_node(child_item, child_node)
        self.current_doc.root.children = new_children
        self._status("Η σειρά ενημερώθηκε — αποθηκεύστε για να διατηρηθεί.")

    def _sync_tree_to_node(self, tree_item: QTreeWidgetItem, node: Node):
        new_children = []
        for i in range(tree_item.childCount()):
            child_item = tree_item.child(i)
            child_node = self.current_doc.root.find_node(child_item.data(0, Qt.UserRole))
            if child_node:
                new_children.append(child_node)
                self._sync_tree_to_node(child_item, child_node)
        node.children = new_children
        self._status("Η σειρά ενημερώθηκε — αποθηκεύστε για να διατηρηθεί.")

    # ── Φόρμα ──

    def _load_node_form(self):
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self._field_widgets = {}

        if not self.selected_node:
            self.editor_label.setText("Δεν επιλέχθηκε κόμβος")
            return

        if self.selected_node.template_id:
            tpl = self.template_repo.load_template(self.selected_node.template_id)
            if tpl:
                self.editor_label.setText(tpl.name)
                for field in tpl.fields:
                    w = self._make_widget(field)
                    self._field_widgets[field.field_id] = w
                    self.form_layout.addRow(field.label, w)
                return

        self.editor_label.setText(f"Επεξεργασία: {self.selected_node.node_type}")
        w = QLineEdit(str(self.selected_node.data.get("content", "")))
        w.textChanged.connect(lambda t: self._set_field("content", t))
        self.form_layout.addRow("Περιεχόμενο:", w)

    def _make_widget(self, field: TemplateField):
        node = self.selected_node
        value = node.data.get(field.field_id, field.default_value)
        ft = field.field_type
        fid = field.field_id

        if ft == TemplateFieldType.TEXTAREA:
            w = QTextEdit()
            w.setPlainText(str(value) if value is not None else "")
            w.setMinimumHeight(80)
            w.textChanged.connect(lambda fid=fid, w=w: self._set_field(fid, w.toPlainText()))
            return w

        if ft == TemplateFieldType.NUMBER:
            w = QSpinBox()
            w.setRange(0, 999999)
            try:
                w.setValue(int(value) if value is not None else 0)
            except (ValueError, TypeError):
                w.setValue(0)
            w.valueChanged.connect(lambda v, fid=fid: self._set_field(fid, v))
            return w

        if ft in (TemplateFieldType.SELECT, TemplateFieldType.MULTISELECT):
            w = QComboBox()
            for opt in field.options:
                w.addItem(opt.get("label", ""), opt.get("value", ""))
            for i in range(w.count()):
                if w.itemData(i) == str(value or ""):
                    w.setCurrentIndex(i)
                    break
            w.currentIndexChanged.connect(lambda _, w=w, fid=fid: self._set_field(fid, w.currentData()))
            return w

        if ft == TemplateFieldType.DATE:
            w = QDateEdit()
            w.setCalendarPopup(True)
            if value:
                d = QDate.fromString(str(value), "yyyy-MM-dd")
                w.setDate(d if d.isValid() else QDate.currentDate())
            else:
                w.setDate(QDate.currentDate())
            w.dateChanged.connect(lambda d, fid=fid: self._set_field(fid, d.toString("yyyy-MM-dd")))
            return w

        if ft == TemplateFieldType.CHECKBOX:
            w = QCheckBox()
            w.setChecked(bool(value))
            w.stateChanged.connect(lambda s, fid=fid: self._set_field(fid, s == Qt.Checked))
            return w

        w = QLineEdit(str(value) if value is not None else "")
        w.textChanged.connect(lambda t, fid=fid: self._set_field(fid, t))
        return w

    def _set_field(self, field_id: str, value):
        if self.selected_node:
            self.selected_node.data[field_id] = value

    # ── Λειτουργίες κόμβου ──

    def _on_add_child(self):
        if not self.current_doc:
            self._status("Δεν υπάρχει ανοιχτό έγγραφο.")
            return
        parent = self.selected_node if self.selected_node else self.current_doc.root
        dlg = TemplatePickerDialog(self.template_repo, self)
        if dlg.exec() == QDialog.Accepted and dlg.selected_template:
            tpl = dlg.selected_template
            new_node = Node(node_type="template_instance", template_id=tpl.template_id)
            for f in tpl.fields:
                if f.default_value is not None:
                    new_node.data[f.field_id] = f.default_value
            parent.add_child(new_node)
            self._refresh_tree()
            self._status(f"Προστέθηκε: {tpl.name}")

    def _on_move_node_up(self):
        self._move_selected_node(-1)

    def _on_move_node_down(self):
        self._move_selected_node(1)

    def _move_selected_node(self, direction: int):
        if not self.selected_node or not self.current_doc:
            return
        parent = self._find_parent_node(self.current_doc.root, self.selected_node.node_id)
        if not parent:
            return
        ch = parent.children
        idx = next((i for i, c in enumerate(ch) if c.node_id == self.selected_node.node_id), -1)
        new_idx = idx + direction
        if 0 <= new_idx < len(ch):
            ch[idx], ch[new_idx] = ch[new_idx], ch[idx]
            self._refresh_tree()
            item = self._find_tree_item(self.tree_widget.invisibleRootItem(), self.selected_node.node_id)
            if item:
                self.tree_widget.setCurrentItem(item)

    def _find_parent_node(self, node: Node, target_id: str) -> Optional[Node]:
        for child in node.children:
            if child.node_id == target_id:
                return node
            result = self._find_parent_node(child, target_id)
            if result:
                return result
        return None

    def _on_delete_node(self):
        if not self.selected_node or self.selected_node == self.current_doc.root:
            self._status("Δεν είναι δυνατή η διαγραφή του ριζικού κόμβου.")
            return
        if QMessageBox.question(
            self, "Διαγραφή Κόμβου",
            "Διαγραφή αυτού του κόμβου και όλων των παιδιών του;",
            QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No
        ) != QMessageBox.Yes:
            return
        for node in self.current_doc.root.get_all_nodes():
            if node.remove_child(self.selected_node.node_id):
                self.selected_node = None
                while self.form_layout.rowCount() > 0:
                    self.form_layout.removeRow(0)
                self.editor_label.setText("Ο κόμβος διαγράφηκε")
                self._refresh_tree()
                self._status("Ο κόμβος διαγράφηκε.")
                break

    # ── Αυτόματη αρίθμηση ──

    def _auto_number_document(self):
        self._auto_number_children(self.current_doc.root)

    def _auto_number_children(self, node: Node):
        counters: Dict[str, int] = {}
        for child in node.children:
            tpl_id = child.template_id
            if tpl_id:
                counters[tpl_id] = counters.get(tpl_id, 0) + 1
                n = counters[tpl_id]
                if tpl_id == "tpl_article":
                    child.data["article_number"] = n
                elif tpl_id == "tpl_paragraph":
                    child.data["paragraph_number"] = str(n)
                elif tpl_id == "tpl_subparagraph":
                    child.data["number"] = str(n)
            self._auto_number_children(child)

    # ── Αναζήτηση ──

    def _on_search(self):
        query = self.search_input.text().strip().lower()
        if not query or not self.current_doc:
            self._status("Εισάγετε όρο αναζήτησης.")
            return
        matches = [
            node.node_id
            for node in self.current_doc.root.get_all_nodes()
            if any(query in str(v).lower() for v in node.data.values())
        ]
        if not matches:
            self._status(f"Δεν βρέθηκαν αποτελέσματα για '{query}'.")
            return
        self._highlight_node(matches[0])
        self._status(f"{len(matches)} κόμβος/κόμβοι ταιριάζουν με '{query}'. Επισημάνθηκε ο πρώτος.")

    def _highlight_node(self, node_id: str):
        item = self._find_tree_item(self.tree_widget.invisibleRootItem(), node_id)
        if item:
            self.tree_widget.setCurrentItem(item)
            self._on_tree_item_selected(item, 0)

    def _find_tree_item(self, item: QTreeWidgetItem, node_id: str) -> Optional[QTreeWidgetItem]:
        if item.data(0, Qt.UserRole) == node_id:
            return item
        for i in range(item.childCount()):
            result = self._find_tree_item(item.child(i), node_id)
            if result:
                return result
        return None

    # ── Εξαγωγή ──

    def _on_export_html(self):
        path = self._export_path("Αρχεία HTML (*.html)", ".html")
        if not path:
            return
        from ..renderers import HTMLRenderer
        html = HTMLRenderer(self._templates()).render(self.current_doc)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._status(f"HTML εξαγωγή → {path}")

    def _on_export_pdf(self):
        path = self._export_path("Αρχεία PDF (*.pdf)", ".pdf")
        if not path:
            return
        try:
            from ..renderers import PDFRenderer
            pdf = PDFRenderer(self._templates(), use_weasyprint=True).render(self.current_doc)
            with open(path, "wb") as f:
                f.write(pdf)
            self._status(f"PDF εξαγωγή → {path}")
        except Exception as e:
            QMessageBox.warning(self, "Αποτυχία Εξαγωγής PDF",
                                f"{e}\n\nΕναλλακτικά: εξάγετε ως HTML και εκτυπώστε σε PDF από τον browser.")

    def _on_export_latex(self):
        path = self._export_path("Αρχεία LaTeX (*.tex)", ".tex")
        if not path:
            return
        from ..renderers import LaTeXRenderer
        tex = LaTeXRenderer(self._templates()).render(self.current_doc)
        with open(path, "w", encoding="utf-8") as f:
            f.write(tex)
        self._status(f"LaTeX εξαγωγή → {path}")

    def _on_export_xml(self):
        path = self._export_path("Αρχεία XML (*.xml)", ".xml")
        if not path:
            return
        from ..renderers import LegalXMLRenderer
        xml = LegalXMLRenderer(self._templates()).render(self.current_doc)
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)
        self._status(f"XML εξαγωγή → {path}")

    def _export_path(self, filter_str: str, ext: str) -> Optional[str]:
        if not self.current_doc:
            self._status("Δεν υπάρχει ανοιχτό έγγραφο.")
            return None
        default = f"{self.current_doc.title}{ext}"
        path, _ = QFileDialog.getSaveFileName(self, f"Αποθήκευση {ext.upper()}", default, filter_str)
        return path or None

    def _templates(self) -> dict:
        return {t.template_id: t for t in self.template_repo.load_all_templates()}

    # ── Πρότυπα ──

    def _on_manage_templates(self):
        TemplateManagerDialog(self.template_repo, self).exec()

    # ── Ιστορικό ──

    def _on_save_snapshot(self):
        if not self.current_doc:
            self._status("Δεν υπάρχει ανοιχτό έγγραφο.")
            return
        if not self.version_repo:
            self._status("Το ιστορικό εκδόσεων δεν είναι διαθέσιμο.")
            return
        note, ok = QInputDialog.getText(self, "Αποθήκευση Στιγμιοτύπου", "Προαιρετική σημείωση:")
        if ok:
            self._on_save_document()
            self.version_repo.save_version(self.current_doc, note.strip())
            self._status("Το στιγμιότυπο αποθηκεύτηκε.")

    def _on_browse_history(self):
        if not self.current_doc:
            self._status("Δεν υπάρχει ανοιχτό έγγραφο.")
            return
        if not self.version_repo:
            self._status("Το ιστορικό εκδόσεων δεν είναι διαθέσιμο.")
            return
        dlg = HistoryDialog(self.current_doc, self.version_repo, self)
        if dlg.exec() == QDialog.Accepted and dlg.restored_doc:
            restored = dlg.restored_doc
            restored.doc_id = self.current_doc.doc_id
            self.current_doc = restored
            self.doc_title_edit.setText(self.current_doc.title)
            self._refresh_tree()
            self._status("Η έκδοση επαναφέρθηκε — αποθηκεύστε για να γίνει μόνιμη.")
