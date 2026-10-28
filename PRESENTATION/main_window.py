from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QStackedWidget, QMessageBox, QButtonGroup, QSizePolicy,
)

from .pythonLexer_tab import PythonLexerTab
from .flexLexer_tab import FlexLexerTab
from .firstFollow_tab import FirstFollowTab
from .canonicalCollection_tab import CanonicalCollectionTab
from .syntactic_table_tab import SyntacticTableTab
from .style import STYLE
from .lrParser_tab import LRParserTab


SECTIONS = [
    {
        "key": "lexico",
        "label": "Analizador Léxico",
        "pages": [
            ("lexico_python", "Python"),
            ("lexico_flex",   "Flex"),
        ],
    },
    {
        "key": "sintactico",
        "label": "Analizador Sintáctico",
        "pages": [
            ("first_follow", "PRIMEROS y SIGUIENTES"),
            ("canonical",    "Colección canónica LR(0)"),
            ("lr_table",     "Tabla de análisis LR"),
            ("lr_parser",    "Analizador sintáctico LR"),   # NUEVA
        ],
    },
    {
        "key": "semantico",
        "label": "Analizador Semántico",
        "pages": [],
    },
]


class SectionTab(QPushButton):
    """Botón tipo pestaña de ribbon."""

    def __init__(self, label, parent=None):
        super().__init__(label, parent)
        self.setObjectName("sectionTab")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compilador · Equipo 6")
        self.resize(1280, 860)
        self.setMinimumSize(1000, 700)
        self.setStyleSheet(STYLE)

        # Páginas por submenú
        self.pages = {
            "lexico_python": PythonLexerTab(),
            "lexico_flex":   FlexLexerTab(),
            "first_follow":  FirstFollowTab(),
            "canonical":     CanonicalCollectionTab(),
            "lr_table":      SyntacticTableTab(),
            "lr_parser":     LRParserTab(),
        }

        # Placeholder para "Semántico"
        self.placeholder = QWidget()
        ph_layout = QVBoxLayout(self.placeholder)
        ph_layout.setContentsMargins(60, 60, 60, 60)
        title = QLabel("Analizador Semántico")
        title.setObjectName("heading")
        hint = QLabel("Disponible en una próxima entrega.")
        hint.setObjectName("subheading")
        ph_layout.addWidget(title)
        ph_layout.addWidget(hint)
        ph_layout.addStretch()

        # ---------------- Contenedor raíz ----------------
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---------------- Ribbon superior ----------------
        ribbon = QWidget()
        ribbon.setObjectName("ribbon")
        ribbon_layout = QHBoxLayout(ribbon)
        ribbon_layout.setContentsMargins(16, 6, 16, 6)
        ribbon_layout.setSpacing(4)

        self.top_group = QButtonGroup(self)
        self.top_group.setExclusive(True)
        self.section_tabs = {}
        for section in SECTIONS:
            tab = SectionTab(section["label"])
            self.section_tabs[section["key"]] = tab
            self.top_group.addButton(tab)
            ribbon_layout.addWidget(tab)
            tab.clicked.connect(
                lambda _=False, k=section["key"]: self._select_section(k)
            )
        ribbon_layout.addStretch()
        outer.addWidget(ribbon)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setObjectName("ribbonSeparator")
        outer.addWidget(sep)

        # ---------------- Body: sidebar + stack ----------------
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        self.sidebar.itemClicked.connect(self._on_sidebar_clicked)

        self.stack = QStackedWidget()
        for page in self.pages.values():
            self.stack.addWidget(page)
        self.stack.addWidget(self.placeholder)

        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.stack, 1)
        outer.addWidget(body, 1)

        self.setCentralWidget(central)

        self._build_menu()
        self._select_section("lexico")

        self.statusBar().showMessage("Selecciona una sección para comenzar.")

    # ---------------- Navegación ----------------

    def _select_section(self, key):
        section = next(s for s in SECTIONS if s["key"] == key)

        # Focus en la pestaña del ribbon
        self.section_tabs[key].setChecked(True)

        self.sidebar.blockSignals(True)
        self.sidebar.clear()

        if not section["pages"]:
            self.sidebar.setEnabled(False)
            self.stack.setCurrentWidget(self.placeholder)
        else:
            self.sidebar.setEnabled(True)
            for page_key, label in section["pages"]:
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, page_key)
                self.sidebar.addItem(item)

            # Auto-seleccionar el primero (doble focus)
            self.sidebar.setCurrentRow(0)
            first_key = section["pages"][0][0]
            self.stack.setCurrentWidget(self.pages[first_key])

        self.sidebar.blockSignals(False)
        self.statusBar().showMessage(f"Sección: {section['label']}")

    def _on_sidebar_clicked(self, item):
        key = item.data(Qt.ItemDataRole.UserRole)
        if key and key in self.pages:
            self.stack.setCurrentWidget(self.pages[key])
            self.statusBar().showMessage(f"  ·  {item.text()}")

    # ---------------- Menú clásico ----------------

    def _build_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Archivo")
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("Ayuda")
        about = QAction("Acerca de…", self)
        about.triggered.connect(self._show_about)
        help_menu.addAction(about)

    def _show_about(self):
        QMessageBox.information(
            self, "Acerca de",
            "Compilador · Equipo 6\n\n"
            "Analizadores léxico y sintáctico · UTM",
        )

    # ---------------- Cierre ----------------

    def closeEvent(self, event):
        for tab in self.pages.values():
            win = getattr(tab, "results_window", None)
            if win is not None:
                try:
                    win.close()
                except RuntimeError:
                    pass

        if any(getattr(t, "busy", False) for t in self.pages.values()):
            self.statusBar().showMessage(
                "Espera a que termine la operación antes de cerrar."
            )
            event.ignore()
            return
        event.accept()