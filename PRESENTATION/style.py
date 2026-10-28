"""Hoja de estilos global. Tema claro con acento azul."""

STYLE = """
QWidget {
    background: #f4f7fc;
    color: #15263f;
    font-size: 13px;
}

/* ---- Menú clásico ---- */
QMenuBar {
    background: #ffffff;
    border-bottom: 1px solid #e1e7f0;
    padding: 2px 6px;
}
QMenuBar::item { padding: 6px 12px; border-radius: 4px; }
QMenuBar::item:selected { background: #eaf0fb; color: #174b97; }
QMenu {
    background: #ffffff;
    border: 1px solid #e1e7f0;
    padding: 6px;
}
QMenu::item { padding: 7px 28px 7px 12px; border-radius: 4px; }
QMenu::item:selected { background: #2456a6; color: white; }

/* ---- Ribbon superior ---- */
QWidget#ribbon {
    background: #ffffff;
    border-bottom: none;
}
QPushButton#sectionTab {
    background: transparent;
    color: #4d6485;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 10px 22px;
    font-size: 14px;
    font-weight: 500;
    text-align: center;
    border-radius: 6px;
}
QPushButton#sectionTab:hover {
    background: #eaf0fb;
    color: #1a3a6d;
}
QPushButton#sectionTab:checked {
    background: #eaf0fb;
    color: #2456a6;
    border-bottom: 3px solid #2456a6;
    font-weight: 600;
}
QWidget#ribbonSeparator {
    background: #e1e7f0;
}

/* ---- Sidebar ---- */
QListWidget#sidebar {
    background: #ffffff;
    border: none;
    border-right: 1px solid #e1e7f0;
    padding: 10px 8px;
    outline: 0;
}
QListWidget#sidebar::item {
    padding: 10px 14px;
    border-radius: 6px;
    margin: 2px 0;
    color: #344e73;
}
QListWidget#sidebar::item:hover {
    background: #eaf0fb;
}
QListWidget#sidebar::item:selected {
    background: #2456a6;
    color: white;
    font-weight: 500;
}
QListWidget#sidebar:disabled {
    background: #f8fafd;
}

/* ---- Títulos ---- */
QLabel#heading {
    font-size: 22px;
    font-weight: bold;
    padding: 4px 0 8px 0;
    color: #1a2f55;
}
QLabel#subheading { color: #4d6485; }

/* ---- Botones ---- */
QPushButton {
    background: #2456a6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 9px 16px;
    font-weight: 500;
}
QPushButton:hover   { background: #1d4788; }
QPushButton:pressed { background: #163765; }
QPushButton:disabled{ background: #c4ccd9; color: #6b7a8f; }
QPushButton#secondary {
    background: #e8eef9;
    color: #1a3a6d;
}
QPushButton#secondary:hover { background: #d8e3f5; }

/* ---- Editores y tablas ---- */
QPlainTextEdit, QTableWidget {
    background: white;
    alternate-background-color: #f5f8fd;
    border: 1px solid #d0dbe8;
    border-radius: 6px;
    selection-background-color: #2456a6;
    selection-color: white;
}
QHeaderView::section {
    background: #e4ecfa;
    color: #15263f;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #d0dbe8;
    border-bottom: 1px solid #d0dbe8;
    font-weight: 600;
}

/* ---- Tabs (Resultados) ---- */
QTabWidget::pane {
    border: 1px solid #d0dbe8;
    border-radius: 6px;
    background: white;
}
QTabBar::tab {
    padding: 10px 22px;
    background: #eaf0fb;
    color: #1a3a6d;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
}
QTabBar::tab:selected {
    background: white;
    color: #174b97;
    font-weight: bold;
    border-bottom: 2px solid #2456a6;
}
QTabBar::tab:hover:!selected { background: #d8e3f5; }

/* ---- Combo ---- */
QComboBox {
    background: white;
    border: 1px solid #d0dbe8;
    border-radius: 6px;
    padding: 7px 10px;
    color: #15263f;
}
QComboBox:hover { border-color: #2456a6; }
QComboBox QAbstractItemView {
    background: white;
    color: #15263f;
    selection-background-color: #2456a6;
    selection-color: white;
    border: 1px solid #d0dbe8;
}

/* ---- Status bar ---- */
QStatusBar {
    background: #f4f7fc;
    color: #4d6485;
    border-top: 1px solid #e1e7f0;
}

/* ---- Scrollbars ---- */
QScrollBar:vertical { background: transparent; width: 12px; margin: 0; }
QScrollBar::handle:vertical {
    background: #c4d1e8; border-radius: 6px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #a8b9d8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QScrollBar:horizontal { background: transparent; height: 12px; margin: 0; }
QScrollBar::handle:horizontal {
    background: #c4d1e8; border-radius: 6px; min-width: 24px;
}
QScrollBar::handle:horizontal:hover { background: #a8b9d8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
"""