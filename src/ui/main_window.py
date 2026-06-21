"""Main application window (PySide6/Qt)."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit, QScrollArea, QFormLayout
)
from PySide6.QtCore import Qt, QSize

from ..models import Document, Node, Template
from ..db import DocumentRepository, TemplateRepository


class MainWindow(QMainWindow):
    """Main application window with document editor."""

    def __init__(self, doc_repo: DocumentRepository, template_repo: TemplateRepository):
        super().__init__()
        self.doc_repo = doc_repo
        self.template_repo = template_repo
        self.current_doc: Document = None
        self.selected_node: Node = None

        self.setWindowTitle("Isokratis - Legislature Builder")
        self.setGeometry(100, 100, 1400, 900)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout: splitter between document tree and editor panel
        main_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)

        # Left: Document tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Document Structure")
        self.tree_widget.itemClicked.connect(self._on_tree_item_selected)

        # Right: Editor panel (scrollable form)
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        self.editor_title_label = QLabel("Select a node to edit")
        right_layout.addWidget(self.editor_title_label)

        # Form area for template parameters
        self.form_layout = QFormLayout()
        form_widget = QWidget()
        form_widget.setLayout(self.form_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidget(form_widget)
        scroll_area.setWidgetResizable(True)

        right_layout.addWidget(scroll_area)

        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Child Node")
        add_button.clicked.connect(self._on_add_child)
        delete_button = QPushButton("Delete Node")
        delete_button.clicked.connect(self._on_delete_node)
        save_button = QPushButton("Save Document")
        save_button.clicked.connect(self._on_save_document)

        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(save_button)
        right_layout.addLayout(button_layout)

        right_panel.setLayout(right_layout)

        # Add to splitter
        splitter.addWidget(self.tree_widget)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

        # Create menu bar
        self._setup_menu()

    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        new_action = file_menu.addAction("New Document")
        new_action.triggered.connect(self._on_new_document)
        open_action = file_menu.addAction("Open Document")
        open_action.triggered.connect(self._on_open_document)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Export menu
        export_menu = menubar.addMenu("Export")
        html_action = export_menu.addAction("Export as HTML")
        html_action.triggered.connect(self._on_export_html)
        pdf_action = export_menu.addAction("Export as PDF")
        pdf_action.triggered.connect(self._on_export_pdf)
        latex_action = export_menu.addAction("Export as LaTeX")
        latex_action.triggered.connect(self._on_export_latex)
        xml_action = export_menu.addAction("Export as Legal XML")
        xml_action.triggered.connect(self._on_export_xml)

        # Templates menu
        templates_menu = menubar.addMenu("Templates")
        manage_action = templates_menu.addAction("Manage Templates")
        manage_action.triggered.connect(self._on_manage_templates)

    def load_document(self, doc_id: str):
        """Load a document from the database."""
        self.current_doc = self.doc_repo.load_document(doc_id)
        if self.current_doc:
            self._refresh_tree()

    def _refresh_tree(self):
        """Refresh the document tree widget."""
        self.tree_widget.clear()
        if self.current_doc:
            root_item = self._node_to_tree_item(self.current_doc.root)
            self.tree_widget.addTopLevelItem(root_item)
            root_item.setExpanded(True)

    def _node_to_tree_item(self, node: Node) -> QTreeWidgetItem:
        """Convert a node to a tree widget item."""
        label = f"{node.node_type}"
        if node.template_id:
            template = self.template_repo.load_template(node.template_id)
            if template:
                label = f"{template.name} (instance)"
        elif node.data.get('content'):
            label += f": {node.data['content'][:50]}"

        item = QTreeWidgetItem([label])
        item.setData(0, Qt.UserRole, node.node_id)

        for child in node.children:
            item.addChild(self._node_to_tree_item(child))

        return item

    def _on_tree_item_selected(self, item: QTreeWidgetItem, column: int):
        """Handle tree item selection."""
        node_id = item.data(0, Qt.UserRole)
        self.selected_node = self.current_doc.root.find_node(node_id)
        self._load_node_form()

    def _load_node_form(self):
        """Load the form for the selected node."""
        # Clear existing form
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)

        if not self.selected_node:
            self.editor_title_label.setText("No node selected")
            return

        self.editor_title_label.setText(f"Editing: {self.selected_node.node_type}")

        # If it's a template instance, show template fields
        if self.selected_node.template_id:
            template = self.template_repo.load_template(self.selected_node.template_id)
            if template:
                for field in template.fields:
                    value = self.selected_node.data.get(field.field_id, field.default_value or "")
                    input_widget = QLineEdit()
                    input_widget.setText(str(value))
                    input_widget.editingFinished.connect(
                        lambda v=value, fid=field.field_id: self._on_field_changed(fid, v)
                    )
                    self.form_layout.addRow(field.label, input_widget)
        else:
            # For raw nodes, show basic data
            content = self.selected_node.data.get('content', '')
            input_widget = QLineEdit()
            input_widget.setText(content)
            input_widget.editingFinished.connect(
                lambda v=content: self._on_field_changed('content', v)
            )
            self.form_layout.addRow("Content", input_widget)

    def _on_field_changed(self, field_id: str, value: str):
        """Handle form field change."""
        if self.selected_node:
            self.selected_node.data[field_id] = value

    def _on_add_child(self):
        """Add a child node to the selected node."""
        if not self.selected_node:
            return

        new_node = Node()
        self.selected_node.add_child(new_node)
        self._refresh_tree()

    def _on_delete_node(self):
        """Delete the selected node."""
        if not self.selected_node or self.selected_node == self.current_doc.root:
            return

        # Find parent and remove
        for node in self.current_doc.root.get_all_nodes():
            if node.remove_child(self.selected_node.node_id):
                self.selected_node = None
                self._refresh_tree()
                break

    def _on_save_document(self):
        """Save the current document."""
        if self.current_doc:
            self.current_doc.update_modified_time()
            self.doc_repo.save_document(self.current_doc)
            self.editor_title_label.setText("Document saved!")

    def _on_new_document(self):
        """Create a new document."""
        from ..models import Document
        self.current_doc = Document(title="Untitled")
        self._refresh_tree()

    def _on_open_document(self):
        """Open an existing document (placeholder)."""
        # This would open a dialog to select a document
        pass

    def _on_export_html(self):
        """Export document as HTML."""
        if not self.current_doc:
            return
        from ..renderers import HTMLRenderer
        templates = {t.template_id: t for t in self.template_repo.load_all_templates()}
        renderer = HTMLRenderer(templates)
        html = renderer.render(self.current_doc)
        # Save to file (placeholder)
        with open("export.html", "w", encoding="utf-8") as f:
            f.write(html)
        self.editor_title_label.setText("Exported to export.html")

    def _on_export_pdf(self):
        """Export document as PDF."""
        if not self.current_doc:
            return
        try:
            from ..renderers import PDFRenderer
            templates = {t.template_id: t for t in self.template_repo.load_all_templates()}
            renderer = PDFRenderer(templates, use_weasyprint=True)
            pdf_bytes = renderer.render(self.current_doc)
            with open("export.pdf", "wb") as f:
                f.write(pdf_bytes)
            self.editor_title_label.setText("Exported to export.pdf")
        except ImportError as e:
            self.editor_title_label.setText(f"Error: {e}")

    def _on_export_latex(self):
        """Export document as LaTeX."""
        if not self.current_doc:
            return
        from ..renderers import LaTeXRenderer
        templates = {t.template_id: t for t in self.template_repo.load_all_templates()}
        renderer = LaTeXRenderer(templates)
        latex = renderer.render(self.current_doc)
        with open("export.tex", "w", encoding="utf-8") as f:
            f.write(latex)
        self.editor_title_label.setText("Exported to export.tex")

    def _on_export_xml(self):
        """Export document as legal XML."""
        if not self.current_doc:
            return
        from ..renderers import LegalXMLRenderer
        templates = {t.template_id: t for t in self.template_repo.load_all_templates()}
        renderer = LegalXMLRenderer(templates)
        xml = renderer.render(self.current_doc)
        with open("export.xml", "w", encoding="utf-8") as f:
            f.write(xml)
        self.editor_title_label.setText("Exported to export.xml")

    def _on_manage_templates(self):
        """Open template management dialog (placeholder)."""
        self.editor_title_label.setText("Template manager: not yet implemented")
