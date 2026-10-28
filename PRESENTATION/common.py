from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QHeaderView, QFileDialog, QMessageBox)
from PERSISTENCE.text_files import write_tsv

# Ejecuta una función sin bloquear la ventana. Nunca manipula widgets.
class Task(QThread):
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, function, parent=None):
        super().__init__(parent)
        self.function = function

    def run(self):
        try:
            self.completed.emit(self.function())
        except Exception as error:
            self.failed.emit(f'{type(error).__name__}: {error}')

# Muestra una tabla elegida por el usuario y permite exportarla a TSV.
# set_results recibe {titulo: [[encabezados...], [fila...], ...]}.
class ResultsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = {}
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.selector = QComboBox()
        self.export_button = QPushButton('Guardar tabla TSV')
        controls.addWidget(self.selector, 1)
        controls.addWidget(self.export_button)
        layout.addLayout(controls)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.selector.currentTextChanged.connect(self._show_table)
        self.export_button.clicked.connect(self.export)
        self.set_results({})

    def set_results(self, results):
        self.results = results
        self.selector.blockSignals(True)
        self.selector.clear()
        self.selector.addItems(results)
        self.selector.blockSignals(False)
        self.selector.setEnabled(bool(results))
        self.export_button.setEnabled(bool(results))
        self._show_table(self.selector.currentText())

    def _show_table(self, name):
        rows = self.results.get(name, [])
        self.table.clear()
        self.table.setRowCount(max(0, len(rows) - 1))
        self.table.setColumnCount(len(rows[0]) if rows else 0)
        if not rows:
            return
        self.table.setHorizontalHeaderLabels([str(x) for x in rows[0]])
        for i, row in enumerate(rows[1:]):
            for j, value in enumerate(row[:len(rows[0])]):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

    def export(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Guardar tabla', 'resultado.tsv', 'TSV (*.tsv)')
        if path:
            try:
                write_tsv(path, self.results[self.selector.currentText()])
            except OSError as error:
                QMessageBox.warning(self, 'No se pudo guardar', str(error))
