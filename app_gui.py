import sys
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, 
    QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, 
    QDateEdit, QDateTimeEdit, QTableWidget, QTableWidgetItem,
    QDialog, QMessageBox, QComboBox, QScrollArea, QSpinBox,
    QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, QDate, QDateTime, QTimer
from PyQt6.QtGui import QFont, QIcon

# Importing from main.py
from main import (
    ConfigManager, DatabaseConnection, DatabaseManager,
    PatientRepository, AppointmentRepository, TreatmentRepository,
    MedicalHistoryRepository, AIService, PatientService
)

# Importing styles
from styles import MAIN_STYLE, PATIENT_FORM_STYLE, TREATMENT_DETAIL_STYLE

class MainWindow(QMainWindow):
    """Main application window with tab-based navigation"""
    
    def __init__(self, patient_service):
        super().__init__()
        self.patient_service = patient_service
        self.setWindowTitle("Advanced Patient Management System")
        self.setMinimumSize(1000, 700)
        
        # Apply main stylesheet
        self.setStyleSheet(MAIN_STYLE)
        
        # Create central widget with tab layout
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create tabs
        self.create_patients_tab()
        self.create_appointments_tab()
        self.create_treatments_tab()
        self.create_medical_history_tab()
        
        # Set the first tab as active
        self.central_widget.setCurrentIndex(0)
        
        # Status bar
        self.statusBar().showMessage("Ready - Green Theme Applied")
    
    def create_patients_tab(self):
        """Create and configure the patients management tab"""
        patients_tab = QWidget()
        main_layout = QHBoxLayout()
        patients_tab.setLayout(main_layout)
        
        # Left side - List of patients
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Search and refresh controls
        search_layout = QHBoxLayout()
        self.patient_search = QLineEdit()
        self.patient_search.setPlaceholderText("Search patients...")
        refresh_button = QPushButton("Refresh")
        search_layout.addWidget(self.patient_search)
        search_layout.addWidget(refresh_button)
        left_layout.addLayout(search_layout)
        
        # Patients table
        self.patients_table = QTableWidget(0, 4)
        self.patients_table.setHorizontalHeaderLabels(["ID", "Name", "DOB", "Phone"])
        self.patients_table.horizontalHeader().setStretchLastSection(True)
        self.patients_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.patients_table.setAlternatingRowColors(True)
        left_layout.addWidget(self.patients_table)
        
        # Add patient button
        add_patient_button = QPushButton("Add New Patient")
        add_patient_button.clicked.connect(self.show_add_patient_dialog)
        left_layout.addWidget(add_patient_button)
        
        # Right side - Patient details
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Patient details section
        details_group = QGroupBox("Patient Details")
        details_layout = QFormLayout()
        details_group.setLayout(details_layout)
        
        self.patient_id_field = QLabel("N/A")
        self.first_name_field = QLabel("N/A")
        self.last_name_field = QLabel("N/A")
        self.dob_field = QLabel("N/A")
        self.phone_field = QLabel("N/A")
        self.email_field = QLabel("N/A")
        
        details_layout.addRow("Patient ID:", self.patient_id_field)
        details_layout.addRow("First Name:", self.first_name_field)
        details_layout.addRow("Last Name:", self.last_name_field)
        details_layout.addRow("Date of Birth:", self.dob_field)
        details_layout.addRow("Phone:", self.phone_field)
        details_layout.addRow("Email:", self.email_field)
        
        right_layout.addWidget(details_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        edit_button = QPushButton("Edit Patient")
        edit_button.clicked.connect(self.show_edit_patient_dialog)
        delete_button = QPushButton("Delete Patient")
        delete_button.setObjectName("deleteButton")  # Apply specific style
        delete_button.clicked.connect(self.delete_patient)
        actions_layout.addWidget(edit_button)
        actions_layout.addWidget(delete_button)
        right_layout.addLayout(actions_layout)
        
        # Add a spacer to push everything up
        right_layout.addStretch()
        
        # Add panels to the main layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)
        
        # Connect events
        self.patients_table.itemClicked.connect(self.on_patient_selected)
        refresh_button.clicked.connect(self.refresh_patients)
        self.patient_search.textChanged.connect(self.filter_patients)
        
        # Add tab to main widget
        self.central_widget.addTab(patients_tab, "Patients")
        
        # Load patients initially
        self.refresh_patients()
    
    def create_appointments_tab(self):
        """Create and configure the appointments management tab"""
        appointments_tab = QWidget()
        main_layout = QVBoxLayout()
        appointments_tab.setLayout(main_layout)
        
        # Patient selection
        form_layout = QFormLayout()
        self.appointment_patient_combo = QComboBox()
        form_layout.addRow("Select Patient:", self.appointment_patient_combo)
        main_layout.addLayout(form_layout)
        
        # Appointments table
        self.appointments_table = QTableWidget(0, 4)
        self.appointments_table.setHorizontalHeaderLabels(["ID", "Date", "Purpose", "Status"])
        self.appointments_table.horizontalHeader().setStretchLastSection(True)
        self.appointments_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.appointments_table)
        
        # Add appointment section
        appointment_group = QGroupBox("Schedule New Appointment")
        appointment_layout = QFormLayout()
        appointment_group.setLayout(appointment_layout)
        
        self.appointment_datetime = QDateTimeEdit()
        self.appointment_datetime.setDateTime(QDateTime.currentDateTime())
        self.appointment_datetime.setCalendarPopup(True)
        
        self.appointment_purpose = QLineEdit()
        
        appointment_layout.addRow("Date & Time:", self.appointment_datetime)
        appointment_layout.addRow("Purpose:", self.appointment_purpose)
        
        schedule_button = QPushButton("Schedule Appointment")
        schedule_button.clicked.connect(self.schedule_appointment)
        appointment_layout.addRow("", schedule_button)
        
        main_layout.addWidget(appointment_group)
        main_layout.addStretch()
        
        # Connect events
        self.appointment_patient_combo.currentIndexChanged.connect(self.load_patient_appointments)
        
        # Add tab to main widget
        self.central_widget.addTab(appointments_tab, "Appointments")
        
        # Load patients for the combobox
        self.load_patients_for_combo(self.appointment_patient_combo)
    
    def create_treatments_tab(self):
        """Create and configure the treatments management tab"""
        treatments_tab = QWidget()
        main_layout = QVBoxLayout()
        treatments_tab.setLayout(main_layout)
        
        # Patient selection
        form_layout = QFormLayout()
        self.treatment_patient_combo = QComboBox()
        form_layout.addRow("Select Patient:", self.treatment_patient_combo)
        main_layout.addLayout(form_layout)
        
        # Treatments table
        self.treatments_table = QTableWidget(0, 3)
        self.treatments_table.setHorizontalHeaderLabels(["ID", "Condition", "Status"])
        self.treatments_table.horizontalHeader().setStretchLastSection(True)
        self.treatments_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.treatments_table)
        
        # Treatment details when selected
        self.treatment_details = QTextEdit()
        self.treatment_details.setReadOnly(True)
        self.treatment_details.setStyleSheet(TREATMENT_DETAIL_STYLE)
        main_layout.addWidget(self.treatment_details)
        
        # Add treatment section
        treatment_group = QGroupBox("Add New Treatment")
        treatment_layout = QFormLayout()
        treatment_group.setLayout(treatment_layout)
        
        self.treatment_condition = QLineEdit()
        self.treatment_symptoms = QTextEdit()
        self.treatment_symptoms.setMaximumHeight(100)
        self.treatment_history = QTextEdit()
        self.treatment_history.setMaximumHeight(100)
        
        treatment_layout.addRow("Condition:", self.treatment_condition)
        treatment_layout.addRow("Symptoms:", self.treatment_symptoms)
        treatment_layout.addRow("Patient History:", self.treatment_history)
        
        add_treatment_button = QPushButton("Add Treatment & Generate AI Analysis")
        add_treatment_button.clicked.connect(self.add_treatment)
        treatment_layout.addRow("", add_treatment_button)
        
        main_layout.addWidget(treatment_group)
        
        # Connect events
        self.treatment_patient_combo.currentIndexChanged.connect(self.load_patient_treatments)
        self.treatments_table.itemClicked.connect(self.show_treatment_details)
        
        # Add tab to main widget
        self.central_widget.addTab(treatments_tab, "Treatments")
        
        # Load patients for the combobox
        self.load_patients_for_combo(self.treatment_patient_combo)
    
    def create_medical_history_tab(self):
        """Create and configure the medical history tab"""
        history_tab = QWidget()
        main_layout = QVBoxLayout()
        history_tab.setLayout(main_layout)
        
        # Patient selection
        form_layout = QFormLayout()
        self.history_patient_combo = QComboBox()
        form_layout.addRow("Select Patient:", self.history_patient_combo)
        main_layout.addLayout(form_layout)
        
        # Medical history table
        self.history_table = QTableWidget(0, 3)
        self.history_table.setHorizontalHeaderLabels(["Date", "Diagnosis", "Treatment"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.history_table)
        
        # Add medical history record section
        history_group = QGroupBox("Add Medical Record")
        history_layout = QFormLayout()
        history_group.setLayout(history_layout)
        
        self.visit_date = QDateEdit()
        self.visit_date.setDate(QDate.currentDate())
        self.visit_date.setCalendarPopup(True)
        
        self.history_diagnosis = QLineEdit()
        self.history_treatment = QLineEdit()
        self.history_notes = QTextEdit()
        self.history_notes.setMaximumHeight(100)
        
        history_layout.addRow("Visit Date:", self.visit_date)
        history_layout.addRow("Diagnosis:", self.history_diagnosis)
        history_layout.addRow("Treatment:", self.history_treatment)
        history_layout.addRow("Notes:", self.history_notes)
        
        add_history_button = QPushButton("Add Medical Record")
        add_history_button.clicked.connect(self.add_medical_record)
        history_layout.addRow("", add_history_button)
        
        main_layout.addWidget(history_group)
        
        # Connect events
        self.history_patient_combo.currentIndexChanged.connect(self.load_patient_medical_history)
        
        # Add tab to main widget
        self.central_widget.addTab(history_tab, "Medical History")
        
        # Load patients for the combobox
        self.load_patients_for_combo(self.history_patient_combo)
    
    def refresh_patients(self):
        """Refresh the patients table with data from service"""
        patients = self.patient_service.list_patients()
        self.patients_table.setRowCount(0)  # Clear table
        
        for i, patient in enumerate(patients):
            self.patients_table.insertRow(i)
            self.patients_table.setItem(i, 0, QTableWidgetItem(str(patient['id'])))
            self.patients_table.setItem(i, 1, QTableWidgetItem(f"{patient['first_name']} {patient['last_name']}"))
            self.patients_table.setItem(i, 2, QTableWidgetItem(str(patient['dob'])))
            self.patients_table.setItem(i, 3, QTableWidgetItem(patient['phone']))
        
        self.statusBar().showMessage(f"Loaded {len(patients)} patients")
    
    def filter_patients(self):
        """Filter patients table based on search input"""
        search_text = self.patient_search.text().lower()
        for row in range(self.patients_table.rowCount()):
            show_row = False
            for col in range(1, self.patients_table.columnCount()):  # Skip ID column
                item = self.patients_table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            self.patients_table.setRowHidden(row, not show_row)
    
    def on_patient_selected(self, item):
        """Handle patient selection in the table"""
        if not item:
            return
            
        row = item.row()
        patient_id = int(self.patients_table.item(row, 0).text())
        
        # Load patient details
        patient = self.patient_service.get_patient(patient_id)
        if patient:
            self.patient_id_field.setText(str(patient['id']))
            self.first_name_field.setText(patient['first_name'])
            self.last_name_field.setText(patient['last_name'])
            self.dob_field.setText(str(patient['dob']))
            self.phone_field.setText(patient['phone'])
            self.email_field.setText(patient['email'] or "N/A")
    
    def show_add_patient_dialog(self):
        """Show dialog to add a new patient"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Patient")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(PATIENT_FORM_STYLE)
        
        layout = QFormLayout()
        dialog.setLayout(layout)
        
        # Form fields
        first_name = QLineEdit()
        last_name = QLineEdit()
        dob = QDateEdit()
        dob.setCalendarPopup(True)
        dob.setDate(QDate(2000, 1, 1))  # Default date
        phone = QLineEdit()
        email = QLineEdit()
        
        layout.addRow("First Name*:", first_name)
        layout.addRow("Last Name*:", last_name)
        layout.addRow("Date of Birth*:", dob)
        layout.addRow("Phone*:", phone)
        layout.addRow("Email:", email)
        
        # Buttons
        button_box = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.setFixedWidth(120)
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedWidth(120)
        
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        layout.addRow("", button_box)
        
        # Connect events
        save_button.clicked.connect(lambda: self.save_new_patient(
            dialog, first_name.text(), last_name.text(), 
            dob.date().toString("yyyy-MM-dd"), phone.text(), email.text()
        ))
        cancel_button.clicked.connect(dialog.reject)
        
        # Show dialog
        dialog.exec()
    
    def save_new_patient(self, dialog, first_name, last_name, dob, phone, email):
        """Save a new patient to the database"""
        # Validate required fields
        if not first_name or not last_name or not dob or not phone:
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields.")
            return
        
        patient_data = {
            'first_name': first_name,
            'last_name': last_name,
            'dob': dob,
            'phone': phone,
            'email': email if email else None
        }
        
        if self.patient_service.add_patient(patient_data):
            QMessageBox.information(self, "Success", "Patient added successfully!")
            dialog.accept()
            
            # Refresh patient lists
            self.refresh_patients()
            self.load_patients_for_combo(self.appointment_patient_combo)
            self.load_patients_for_combo(self.treatment_patient_combo)
            self.load_patients_for_combo(self.history_patient_combo)
        else:
            QMessageBox.critical(self, "Error", "Failed to add patient.")
    
    def show_edit_patient_dialog(self):
        """Show dialog to edit selected patient"""
        if not self.patient_id_field.text() or self.patient_id_field.text() == "N/A":
            QMessageBox.warning(self, "No Selection", "Please select a patient to edit.")
            return
            
        patient_id = int(self.patient_id_field.text())
        patient = self.patient_service.get_patient(patient_id)
        
        if not patient:
            QMessageBox.critical(self, "Error", "Failed to load patient details.")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Patient: {patient['first_name']} {patient['last_name']}")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(PATIENT_FORM_STYLE)
        
        layout = QFormLayout()
        dialog.setLayout(layout)
        
        # Form fields with current values
        first_name = QLineEdit(patient['first_name'])
        last_name = QLineEdit(patient['last_name'])
        
        dob = QDateEdit()
        dob.setCalendarPopup(True)
        if patient['dob']:
            try:
                if isinstance(patient['dob'], str):
                    date_parts = patient['dob'].split('-')
                    date = QDate(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                else:  # Assuming it's a datetime.date object
                    date = QDate(patient['dob'].year, patient['dob'].month, patient['dob'].day)
                dob.setDate(date)
            except:
                dob.setDate(QDate.currentDate())
        
        phone = QLineEdit(patient['phone'])
        email = QLineEdit(patient['email'] if patient['email'] else "")
        
        layout.addRow("First Name*:", first_name)
        layout.addRow("Last Name*:", last_name)
        layout.addRow("Date of Birth*:", dob)
        layout.addRow("Phone*:", phone)
        layout.addRow("Email:", email)
        
        # Buttons
        button_box = QHBoxLayout()
        save_button = QPushButton("Save Changes")
        save_button.setFixedWidth(140)
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedWidth(120)
        
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        layout.addRow("", button_box)
        
        # Connect events
        save_button.clicked.connect(lambda: self.save_edited_patient(
            dialog, patient_id, first_name.text(), last_name.text(), 
            dob.date().toString("yyyy-MM-dd"), phone.text(), email.text()
        ))
        cancel_button.clicked.connect(dialog.reject)
        
        # Show dialog
        dialog.exec()
    
    def save_edited_patient(self, dialog, patient_id, first_name, last_name, dob, phone, email):
        """Save edited patient information"""
        # Validate required fields
        if not first_name or not last_name or not dob or not phone:
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields.")
            return
        
        update_data = {
            'first_name': first_name,
            'last_name': last_name,
            'dob': dob,
            'phone': phone,
            'email': email if email else None
        }
        
        if self.patient_service.update_patient(patient_id, update_data):
            QMessageBox.information(self, "Success", "Patient updated successfully!")
            dialog.accept()
            
            # Refresh patient data
            self.refresh_patients()
            self.on_patient_selected(self.patients_table.item(
                self.patients_table.currentRow(), 0
            ))
            
            # Also refresh patient combos
            self.load_patients_for_combo(self.appointment_patient_combo)
            self.load_patients_for_combo(self.treatment_patient_combo)
            self.load_patients_for_combo(self.history_patient_combo)
        else:
            QMessageBox.critical(self, "Error", "Failed to update patient.")
    
    def delete_patient(self):
        """Delete the selected patient"""
        if not self.patient_id_field.text() or self.patient_id_field.text() == "N/A":
            QMessageBox.warning(self, "No Selection", "Please select a patient to delete.")
            return
            
        patient_id = int(self.patient_id_field.text())
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to delete patient {self.first_name_field.text()} {self.last_name_field.text()}?\n\nThis will also delete all associated records.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.patient_service.delete_patient(patient_id):
                QMessageBox.information(self, "Success", "Patient deleted successfully!")
                
                # Reset patient details
                self.patient_id_field.setText("N/A")
                self.first_name_field.setText("N/A")
                self.last_name_field.setText("N/A")
                self.dob_field.setText("N/A")
                self.phone_field.setText("N/A")
                self.email_field.setText("N/A")
                
                # Refresh patients
                self.refresh_patients()
                self.load_patients_for_combo(self.appointment_patient_combo)
                self.load_patients_for_combo(self.treatment_patient_combo)
                self.load_patients_for_combo(self.history_patient_combo)
            else:
                QMessageBox.critical(self, "Error", "Failed to delete patient.")
    
    def load_patients_for_combo(self, combo_box):
        """Load patients into a combo box"""
        combo_box.clear()
        combo_box.addItem("-- Select Patient --", -1)
        
        patients = self.patient_service.list_patients()
        for patient in patients:
            display_text = f"{patient['id']}: {patient['first_name']} {patient['last_name']}"
            combo_box.addItem(display_text, patient['id'])
    
    def get_selected_patient_id(self, combo_box):
        """Get the selected patient ID from a combo box"""
        patient_id = combo_box.currentData()
        # Ensure we have a valid patient ID
        if patient_id is None or patient_id == -1:
            return -1
        return patient_id
    
    def load_patient_appointments(self):
        """Load appointments for the selected patient"""
        patient_id = self.get_selected_patient_id(self.appointment_patient_combo)
        if patient_id == -1:
            self.appointments_table.setRowCount(0)
            return
            
        # Show a status message while loading
        self.statusBar().showMessage("Loading appointments...")
        
        appointments = self.patient_service.get_patient_appointments(patient_id)
        
        self.appointments_table.setRowCount(0)
        for i, appt in enumerate(appointments):
            self.appointments_table.insertRow(i)
            self.appointments_table.setItem(i, 0, QTableWidgetItem(str(appt['id'])))
            self.appointments_table.setItem(i, 1, QTableWidgetItem(str(appt['appointment_date'])))
            self.appointments_table.setItem(i, 2, QTableWidgetItem(appt['purpose']))
            self.appointments_table.setItem(i, 3, QTableWidgetItem(appt['status']))
        
        self.statusBar().showMessage(f"Loaded {len(appointments)} appointments for selected patient")
    
    def schedule_appointment(self):
        """Schedule a new appointment for the selected patient"""
        patient_id = self.get_selected_patient_id(self.appointment_patient_combo)
        if patient_id == -1:
            QMessageBox.warning(self, "No Selection", "Please select a patient.")
            return
            
        appointment_data = {
            'appointment_date': self.appointment_datetime.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            'purpose': self.appointment_purpose.text()
        }
        
        if not appointment_data['purpose']:
            QMessageBox.warning(self, "Validation Error", "Please enter a purpose for the appointment.")
            return
            
        if self.patient_service.schedule_appointment(patient_id, appointment_data):
            QMessageBox.information(self, "Success", "Appointment scheduled successfully!")
            
            # Clear form
            self.appointment_purpose.clear()
            
            # Reload appointments
            self.load_patient_appointments()
        else:
            QMessageBox.critical(self, "Error", "Failed to schedule appointment.")
    
    def load_patient_treatments(self):
        """Load treatments for the selected patient"""
        patient_id = self.get_selected_patient_id(self.treatment_patient_combo)
        if patient_id == -1:
            self.treatments_table.setRowCount(0)
            self.treatment_details.clear()
            return
            
        # Show a status message while loading
        self.statusBar().showMessage("Loading treatments...")
        
        treatments = self.patient_service.get_patient_treatments(patient_id)
        
        self.treatments_table.setRowCount(0)
        for i, treatment in enumerate(treatments):
            self.treatments_table.insertRow(i)
            self.treatments_table.setItem(i, 0, QTableWidgetItem(str(treatment['id'])))
            self.treatments_table.setItem(i, 1, QTableWidgetItem(treatment['condition']))
            self.treatments_table.setItem(i, 2, QTableWidgetItem(treatment['status']))
            
            # Store the full treatment data in the first cell for later retrieval
            self.treatments_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, treatment)
        
        self.statusBar().showMessage(f"Loaded {len(treatments)} treatments for selected patient")
    
    def show_treatment_details(self, item):
        """Show details of the selected treatment"""
        row = item.row()
        treatment_data = self.treatments_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if not treatment_data:
            return
            
        details = f"""<h2>Treatment Details</h2>
        <p><b>Condition:</b> {treatment_data['condition']}</p>
        <p><b>Symptoms:</b> {treatment_data['symptoms']}</p>
        <p><b>Status:</b> {treatment_data['status']}</p>
        <p><b>Created:</b> {treatment_data['created_at']}</p>
        
        <h3>AI Analysis</h3>
        <div>
        {treatment_data['ai_analysis'].get('analysis', 'No analysis available')}
        </div>
        
        <h3>Treatment Plan</h3>
        <div>
        {treatment_data['treatment_plan'].get('treatment_plan', 'No treatment plan available')}
        </div>
        """
        
        self.treatment_details.setHtml(details)
    
    def add_treatment(self):
        """Add a new treatment for the selected patient"""
        patient_id = self.get_selected_patient_id(self.treatment_patient_combo)
        if patient_id == -1:
            QMessageBox.warning(self, "No Selection", "Please select a patient.")
            return
            
        condition = self.treatment_condition.text()
        symptoms = self.treatment_symptoms.toPlainText()
        
        if not condition or not symptoms:
            QMessageBox.warning(self, "Validation Error", "Please enter both condition and symptoms.")
            return
            
        treatment_data = {
            'condition': condition,
            'symptoms': symptoms,
            'patient_history': self.treatment_history.toPlainText()
        }
        
        # Creating a custom progress dialog instead of a simple message box
        wait_dialog = QDialog(self)
        wait_dialog.setWindowTitle("Processing AI Analysis")
        wait_dialog.setModal(True)
        wait_dialog.setFixedSize(400, 100)
        
        # Creating layout and message
        layout = QVBoxLayout()
        message = QLabel("Generating AI analysis and treatment plan...\nThis may take up to 30 seconds.")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        wait_dialog.setLayout(layout)
        
        # Showing the dialog without blocking
        wait_dialog.show()
        
        # Creating a timer to process events while waiting
        timer = QTimer()
        timer.start(100)  # Process events every 100ms
        timer.timeout.connect(QApplication.processEvents)
        
        # Update status bar
        self.statusBar().showMessage("Processing AI analysis, please wait...")
        
        success = False
        ai_analysis = {}
        treatment_plan = {}
        
        try:
            # Get AI analysis
            success, ai_analysis, treatment_plan = self.patient_service.add_treatment(patient_id, treatment_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during AI processing: {str(e)}")
            success = False
        finally:
            # Stop the timer
            timer.stop()
            # Ensure the wait dialog is closed
            wait_dialog.close()
            # Force UI update
            QApplication.processEvents()
        
        if success:
            QMessageBox.information(self, "Success", "Treatment added successfully with AI analysis!")
            
            # Clear form
            self.treatment_condition.clear()
            self.treatment_symptoms.clear()
            self.treatment_history.clear()
            
            # Show AI analysis results
            details = f"""<h2>AI Analysis Results</h2>
            
            <h3>Symptom Analysis</h3>
            <div>
            {ai_analysis.get('analysis', 'No analysis available')}
            </div>
            
            <h3>Treatment Plan</h3>
            <div>
            {treatment_plan.get('treatment_plan', 'No treatment plan available')}
            </div>
            """
            
            self.treatment_details.setHtml(details)
            
            # Reload treatments
            self.load_patient_treatments()
            self.statusBar().showMessage("Treatment added successfully")
        else:
            error_msg = "Failed to add treatment."
            if ai_analysis.get('error'):
                error_msg += f"\nAnalysis error: {ai_analysis.get('error')}"
            if treatment_plan.get('error'):
                error_msg += f"\nTreatment plan error: {treatment_plan.get('error')}"
                
            QMessageBox.critical(self, "Error", error_msg)
            self.statusBar().showMessage("Failed to add treatment")
    
    def load_patient_medical_history(self):
        """Load medical history for the selected patient"""
        patient_id = self.get_selected_patient_id(self.history_patient_combo)
        if patient_id == -1:
            self.history_table.setRowCount(0)
            return
            
        # Show a status message while loading
        self.statusBar().showMessage("Loading medical history...")
        
        history = self.patient_service.get_patient_medical_history(patient_id)
        
        self.history_table.setRowCount(0)
        for i, record in enumerate(history):
            self.history_table.insertRow(i)
            self.history_table.setItem(i, 0, QTableWidgetItem(str(record['visit_date'])))
            self.history_table.setItem(i, 1, QTableWidgetItem(record['diagnosis']))
            self.history_table.setItem(i, 2, QTableWidgetItem(record['treatment']))
            
            # Store full record in the first cell
            self.history_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, record)
        
        self.statusBar().showMessage(f"Loaded {len(history)} medical records for selected patient")
    
    def add_medical_record(self):
        """Add a new medical history record for the selected patient"""
        patient_id = self.get_selected_patient_id(self.history_patient_combo)
        if patient_id == -1:
            QMessageBox.warning(self, "No Selection", "Please select a patient.")
            return
            
        history_data = {
            'visit_date': self.visit_date.date().toString("yyyy-MM-dd"),
            'diagnosis': self.history_diagnosis.text(),
            'treatment': self.history_treatment.text(),
            'notes': self.history_notes.toPlainText()
        }
        
        if not history_data['diagnosis'] or not history_data['treatment']:
            QMessageBox.warning(self, "Validation Error", "Please enter both diagnosis and treatment.")
            return
            
        if self.patient_service.add_medical_history(patient_id, history_data):
            QMessageBox.information(self, "Success", "Medical record added successfully!")
            
            # Clear form
            self.history_diagnosis.clear()
            self.history_treatment.clear()
            self.history_notes.clear()
            
            # Reload history
            self.load_patient_medical_history()
        else:
            QMessageBox.critical(self, "Error", "Failed to add medical record.")

def main():
    """Application entry point"""
    try:
        # Load configurations
        db_config = ConfigManager.get_db_config()
        ai_config = ConfigManager.get_ai_config()
        
        # Validate configurations
        is_valid, error_msg = ConfigManager.validate_config(
            db_config, 
            ['dbname', 'user', 'password', 'host', 'port']
        )
        
        if not is_valid:
            print(f"Configuration error: {error_msg}")
            print("Please check your environment variables or config.json file.")
            return
        
        # Setup database connection
        db_connection = DatabaseConnection(db_config)
        
        # Setup database manager
        db_manager = DatabaseManager(db_connection)
        
        # Initialize the database schema
        if not db_manager.setup_database():
            print("Database setup failed. See logs for details.")
            return
        
        # Initialize repositories
        patient_repo = PatientRepository(db_manager)
        appointment_repo = AppointmentRepository(db_manager)
        treatment_repo = TreatmentRepository(db_manager)
        medical_history_repo = MedicalHistoryRepository(db_manager)
        
        # Initialize AI service
        ai_service = AIService(ai_config)
        
        # Initialize service layer
        patient_service = PatientService(
            patient_repo,
            appointment_repo,
            treatment_repo,
            medical_history_repo,
            ai_service
        )
        
        # Create and run the application
        app = QApplication(sys.argv)
        app.setStyle("Fusion")  # Use Fusion style for consistent cross-platform look
        
        # Set application font
        font = QFont("Segoe UI", 9)
        app.setFont(font)
        
        window = MainWindow(patient_service)
        window.show()
        sys.exit(app.exec())
    
    except Exception as e:
        print(f"Application error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup resources
        if 'db_connection' in locals():
            db_connection.close()

if __name__ == "__main__":
    main() 
