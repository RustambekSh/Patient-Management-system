"""
Stylesheet definitions for the PyQt6 Patient Management System with green and black theme
"""

# Main application style
MAIN_STYLE = """
QMainWindow {
    background-color: #0a0a0a;
    color: #a0ffa0;
}

QTabWidget::pane {
    border: 1px solid #1e1e1e;
    background: #121212;
}

QTabBar::tab {
    background: #0a0a0a;
    border: 1px solid #1e1e1e;
    border-bottom-color: #121212;
    min-width: 8ex;
    padding: 8px 14px;
    color: #20c020;
}

QTabBar::tab:selected {
    background: #121212;
    border-bottom-color: #121212;
    color: #50ff50;
}

QGroupBox {
    border: 1px solid #1e1e1e;
    border-radius: 5px;
    margin-top: 1.5ex;
    padding-top: 1.5ex;
    background-color: #121212;
    color: #a0ffa0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 5px;
    background-color: #121212;
    color: #50ff50;
}

QPushButton {
    background-color: #006400;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #008800;
}

QPushButton:pressed {
    background-color: #004000;
}

QPushButton:disabled {
    background-color: #2a2a2a;
    color: #5a5a5a;
}

QLineEdit, QTextEdit, QDateEdit, QDateTimeEdit, QComboBox {
    border: 1px solid #1e1e1e;
    border-radius: 3px;
    padding: 4px;
    background-color: #0a0a0a;
    color: #a0ffa0;
    selection-background-color: #006400;
    selection-color: white;
}

QTableWidget {
    alternate-background-color: #0f0f0f;
    gridline-color: #1e1e1e;
    background-color: #121212;
    color: #a0ffa0;
    selection-background-color: #006400;
    selection-color: white;
}

QTableWidget::item {
    padding: 5px;
}

QHeaderView::section {
    background-color: #006400;
    padding: 5px;
    border: 1px solid #1e1e1e;
    font-weight: bold;
    color: white;
}

QLabel {
    color: #a0ffa0;
}

QStatusBar {
    background-color: #0a0a0a;
    color: #a0ffa0;
}

QMessageBox {
    background-color: #121212;
    color: #a0ffa0;
}

QPushButton#deleteButton {
    background-color: #800000;
}

QPushButton#deleteButton:hover {
    background-color: #a00000;
}

QScrollArea {
    background-color: #121212;
    border: 1px solid #1e1e1e;
}

QScrollBar:vertical {
    background: #0a0a0a;
    width: 10px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background: #006400;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar:horizontal {
    background: #0a0a0a;
    height: 10px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:horizontal {
    background: #006400;
    min-width: 20px;
    border-radius: 5px;
}

QSplitter::handle {
    background-color: #006400;
}

QComboBox QAbstractItemView {
    border: 1px solid #1e1e1e;
    background-color: #0a0a0a;
    color: #a0ffa0;
    selection-background-color: #006400;
}

QCalendarWidget {
    background-color: #121212;
    color: #a0ffa0;
}

QCalendarWidget QWidget {
    alternate-background-color: #0a0a0a;
    color: #a0ffa0;
}

QCalendarWidget QAbstractItemView {
    background-color: #121212;
    color: #a0ffa0;
    selection-background-color: #006400;
    selection-color: white;
}

QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #0a0a0a;
}

QCalendarWidget QToolButton {
    color: #a0ffa0;
    background-color: #0a0a0a;
    border: 1px solid #1e1e1e;
}

QDialog QDialogButtonBox {
    button-layout: 0;
}
"""

# Patient form style
PATIENT_FORM_STYLE = """
QDialog {
    background-color: #121212;
    color: #a0ffa0;
}

QLabel {
    font-weight: bold;
    color: #a0ffa0;
}

QPushButton {
    min-width: 100px;
}
"""

# Treatment detail style
TREATMENT_DETAIL_STYLE = """
QTextEdit {
    font-family: 'Segoe UI', Arial, sans-serif;
    border: 1px solid #1e1e1e;
    border-radius: 4px;
    padding: 10px;
    background-color: #0a0a0a;
    color: #a0ffa0;
}

QTextEdit h2, QTextEdit h3 {
    color: #50ff50;
}

QTextEdit b {
    color: #50ff50;
}

QTextEdit div {
    background-color: #121212 !important;
    color: #a0ffa0 !important;
    padding: 10px;
    border-radius: 5px;
    border: 1px solid #1e1e1e;
    margin: 5px 0;
}
""" 