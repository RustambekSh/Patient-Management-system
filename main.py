import psycopg2
import logging
from typing import Optional, List, Dict, Any, Tuple
import os
from datetime import datetime, timedelta
import json
from psycopg2 import pool
import google.generativeai as genai
from dotenv import load_dotenv  
import uuid
import sys

# Loading environment variables  
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_operations.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Database schema definitions - separated from code
SCHEMAS = {
    "extensions": [
        "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
    ],
    "tables": {
        "patients": """
            CREATE TABLE IF NOT EXISTS patients (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                dob DATE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "appointments": """
            CREATE TABLE IF NOT EXISTS appointments (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                patient_id INTEGER REFERENCES patients(id),
                appointment_date TIMESTAMP NOT NULL,
                purpose TEXT,
                status VARCHAR(20) DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "treatments": """
            CREATE TABLE IF NOT EXISTS treatments (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                patient_id INTEGER REFERENCES patients(id),
                condition TEXT NOT NULL,
                symptoms TEXT,
                ai_analysis JSONB,
                treatment_plan JSONB,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "medical_history": """
            CREATE TABLE IF NOT EXISTS medical_history (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                patient_id INTEGER REFERENCES patients(id),
                visit_date TIMESTAMP NOT NULL,
                diagnosis TEXT,
                treatment TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
    }
}

class ConfigManager:
    """Manages application configuration with fallbacks and validation"""
    
    @staticmethod
    def get_db_config() -> Dict[str, str]:
        """Get database configuration from environment variables or config file"""
        # Priority: ENV vars > config file > defaults somthing like this
        config = {
            "dbname": os.getenv("DB_NAME", "postgres"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "Rustamking1+"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432")
        }
        
        # Checking for config file as fallback
        config_file = os.getenv("CONFIG_FILE", "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    # Only using file values for keys that aren't set in env vars
                    for key, value in file_config.items():
                        if key in config and not os.getenv(f"DB_{key.upper()}"):
                            config[key] = value
            except Exception as e:
                logger.warning(f"Failed to load config file: {str(e)}")
        
        return config
    
    @staticmethod
    def get_ai_config() -> Dict[str, str]:
        """Get AI configuration from environment variables"""
        api_key = os.getenv("GEMINI_API_KEY") #I have deleted my gemini api key purposefully not to show it here
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
        
        return {
            "api_key": api_key,
            "model_name": model_name
        }
    
    @staticmethod
    def validate_config(config: Dict[str, Any], required_keys: List[str]) -> Tuple[bool, str]:
        """Validate that all required keys exist in config"""
        missing = [key for key in required_keys if not config.get(key)]
        if missing:
            return False, f"Missing required configuration: {', '.join(missing)}"
        return True, ""

class DatabaseConnection:
    """Single database connection handler with reconnection logic"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.conn = None
        self._connect()
    
    def _connect(self) -> bool:
        """Establish database connection with retry logic"""
        try:
            if self.conn and not self.conn.closed:
                return True
                
            self.conn = psycopg2.connect(**self.config)
            self.conn.autocommit = False
            return True
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            return False
    
    def get_connection(self):
        """Get the connection, reconnecting if necessary"""
        if not self.conn or self.conn.closed:
            if not self._connect():
                raise Exception("Failed to establish database connection")
        return self.conn
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[tuple]]:
        """Execute a database query with error handling and auto-reconnect"""
        max_retries = 3
        retries = 0
        
        while retries < max_retries:
            try:
                conn = self.get_connection()
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    if cursor.description:  # If query returns results
                        result = cursor.fetchall()
                    else:
                        result = None
                    conn.commit()
                    return result
            except psycopg2.OperationalError as e:
                # Connection issue - attempts reconnect
                logger.warning(f"Database connection lost, reconnecting... ({retries+1}/{max_retries})")
                self.conn = None
                retries += 1
                if retries >= max_retries:
                    raise
            except Exception as e:
                conn.rollback()
                logger.error(f"Query execution error: {str(e)}")
                logger.error(f"Failed query: {query}")
                if params:
                    logger.error(f"Query parameters: {params}")
                raise
        
        return None
    
    def close(self):
        """Close the database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Database connection closed")

class DatabaseManager:
    """Database management class with connection pooling"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            self.db.execute_query("SELECT 1;")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    def setup_database(self) -> bool:
        """Set up database schema"""
        try:
            # 1. Test connection
            if not self.test_connection():
                return False
                
            # 2. Enabling extensions
            for extension_query in SCHEMAS["extensions"]:
                try:
                    self.db.execute_query(extension_query)
                    logger.info(f"Extension enabled: {extension_query}")
                except Exception as e:
                    logger.error(f"Failed to enable extension: {str(e)}")
                    return False
            
            # 3. Creating tables in order (respecting dependencies)
            table_order = ["patients", "appointments", "treatments", "medical_history"]
            
            for table_name in table_order:
                query = SCHEMAS["tables"][table_name]
                try:
                    self.db.execute_query(query)
                    logger.info(f"Table created or verified: {table_name}")
                except Exception as e:
                    logger.error(f"Failed to create table {table_name}: {str(e)}")
                    return False
            
            # 4. Verifing tables exist
            verify_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('patients', 'appointments', 'treatments', 'medical_history');
            """
            result = self.db.execute_query(verify_query)
            
            if result and len(result) == 4:
                logger.info("All tables created and verified successfully")
                return True
            else:
                found_tables = [row[0] for row in (result or [])]
                missing = set(table_order) - set(found_tables)
                logger.error(f"Table verification failed. Missing tables: {missing}")
                return False
                
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            return False

class AIService:
    """Handles AI-related operations"""
    
    def __init__(self, config: Dict[str, str]):
        """Initialize AI service with configuration"""
        self.api_key = config.get("api_key")
        self.model_name = config.get("model_name", "gemini-2.0-flash")
        self.timeout = 30  # Set a timeout for API calls
        
        # Configure Gemini API if API key is available
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"AI service initialized with model: {self.model_name}")
        else:
            self.model = None
            logger.warning("AI service initialized without API key - analysis functions will be limited")
    
    def analyze_patient_symptoms(self, symptoms: str) -> Dict[str, Any]:
        """Analyze patient symptoms using Gemini AI"""
        if not self.model:
            logger.warning("AI analysis requested but no API key configured")
            return {
                'analysis': "AI analysis unavailable - no API key configured",
                'timestamp': datetime.now().isoformat()
            }
            
        try:
            prompt = f"""
            As a medical AI assistant, analyze these symptoms and provide YOUR OWN original analysis with:
            1. Three possible conditions that might cause these symptoms (general possibilities only, not specific diagnoses)
            2. Two general categories of tests that might be appropriate (not specific branded tests)
            3. General lifestyle recommendations (not specific medications or treatments)
            
            Be brief and general, avoiding specific medical literature references.
            
            Symptoms: {symptoms}
            """
            
            # Adding timeout to prevent hanging
            import threading
            import time
            from concurrent.futures import ThreadPoolExecutor, TimeoutError
            
            # Function to generate content with a model
            def generate_with_timeout():
                try:
                    return self.model.generate_content(prompt)
                except Exception as e:
                    logger.error(f"Error in AI generation: {str(e)}")
                    return None
            
            # Using a thread pool to implement a timeout
            with ThreadPoolExecutor() as executor:
                future = executor.submit(generate_with_timeout)
                try:
                    response = future.result(timeout=self.timeout)
                    if response:
                        return {
                            'analysis': response.text if hasattr(response, 'text') else str(response),
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'analysis': "AI analysis could not be generated due to an error with the AI service.",
                            'timestamp': datetime.now().isoformat()
                        }
                except TimeoutError:
                    logger.error(f"AI analysis timed out after {self.timeout} seconds")
                    return {
                        'analysis': f"AI analysis timed out after {self.timeout} seconds. Please try again later.",
                        'timestamp': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'analysis': "AI analysis could not be generated due to an error."
            }

    def generate_treatment_plan(self, condition: str, patient_history: str) -> Dict[str, Any]:
        """Generate a treatment plan using Gemini AI"""
        if not self.model:
            logger.warning("Treatment plan generation requested but no API key configured")
            return {
                'treatment_plan': "AI treatment plan unavailable - no API key configured",
                'timestamp': datetime.now().isoformat()
            }
            
        try:
            prompt = f"""
            Create a brief, general treatment approach for:
            Condition: {condition}
            Patient History: {patient_history}
            
            Please provide YOUR OWN original recommendations including:
            1. General wellness approaches (not specific treatment protocols)
            2. Types of lifestyle modifications (not specific brand names or medications)
            3. General follow-up timeframes
            4. General self-care suggestions
            
            Be brief and completely generic, avoiding any specific commercial products, brand names, or references to medical literature.
            """
            
            # Add timeout to prevent hanging
            import threading
            import time
            from concurrent.futures import ThreadPoolExecutor, TimeoutError
            
            # Function to generate content with a model
            def generate_with_timeout():
                try:
                    return self.model.generate_content(prompt)
                except Exception as e:
                    logger.error(f"Error in AI generation: {str(e)}")
                    return None
            
            # Using a thread pool to implement a timeout
            with ThreadPoolExecutor() as executor:
                future = executor.submit(generate_with_timeout)
                try:
                    response = future.result(timeout=self.timeout)
                    if response:
                        return {
                            'treatment_plan': response.text if hasattr(response, 'text') else str(response),
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'treatment_plan': "AI treatment plan could not be generated due to an error with the AI service.",
                            'timestamp': datetime.now().isoformat()
                        }
                except TimeoutError:
                    logger.error(f"Treatment plan generation timed out after {self.timeout} seconds")
                    return {
                        'treatment_plan': f"Treatment plan generation timed out after {self.timeout} seconds. Please try again later.",
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"Treatment plan generation failed: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'treatment_plan': "Treatment plan could not be generated due to an error."
            }

class PatientRepository:
    """Data access layer for patient-related operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def add_patient(self, patient_data: Dict[str, Any]) -> Optional[int]:
        """Add a new patient record"""
        query = """
        INSERT INTO patients (first_name, last_name, dob, phone, email)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """
        try:
            params = (
                patient_data['first_name'],
                patient_data['last_name'],
                patient_data['dob'],
                patient_data['phone'],
                patient_data.get('email')
            )
            result = self.db.db.execute_query(query, params)
            if result and result[0]:
                patient_id = result[0][0]
                logger.info(f"Patient added successfully with ID: {patient_id}")
                return patient_id
            return None
        except Exception as e:
            logger.error(f"Failed to add patient: {str(e)}")
            return None
    
    def get_patient(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a patient by ID"""
        query = "SELECT * FROM patients WHERE id = %s;"
        try:
            result = self.db.db.execute_query(query, (patient_id,))
            if result and result[0]:
                return {
                    'id': result[0][0],
                    'first_name': result[0][1],
                    'last_name': result[0][2],
                    'dob': result[0][3],
                    'phone': result[0][4],
                    'email': result[0][5]
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get patient: {str(e)}")
            return None
    
    def update_patient(self, patient_id: int, update_data: Dict[str, Any]) -> bool:
        """Update patient information"""
        try:
            set_clauses = []
            params = []
            for key, value in update_data.items():
                if key in ['first_name', 'last_name', 'dob', 'phone', 'email']:
                    set_clauses.append(f"{key} = %s")
                    params.append(value)
            
            if not set_clauses:
                return False

            params.append(patient_id)
            query = f"""
            UPDATE patients 
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id;
            """
            
            result = self.db.db.execute_query(query, tuple(params))
            if result:
                logger.info(f"Patient {patient_id} updated successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update patient: {str(e)}")
            return False
    
    def delete_patient(self, patient_id: int) -> bool:
        """Delete a patient record"""
        query = "DELETE FROM patients WHERE id = %s RETURNING id;"
        try:
            result = self.db.db.execute_query(query, (patient_id,))
            if result:
                logger.info(f"Patient {patient_id} deleted successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete patient: {str(e)}")
            return False
    
    def list_patients(self) -> List[Dict[str, Any]]:
        """List all patients"""
        query = "SELECT * FROM patients ORDER BY last_name, first_name;"
        try:
            result = self.db.db.execute_query(query)
            if result:
                return [{
                    'id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'dob': row[3],
                    'phone': row[4],
                    'email': row[5]
                } for row in result]
            return []
        except Exception as e:
            logger.error(f"Failed to list patients: {str(e)}")
            return []

class AppointmentRepository:
    """Data access layer for appointment-related operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def schedule_appointment(self, patient_id: int, appointment_data: Dict[str, Any]) -> bool:
        """Schedule a new appointment"""
        query = """
        INSERT INTO appointments (patient_id, appointment_date, purpose)
        VALUES (%s, %s, %s)
        RETURNING id;
        """
        try:
            params = (
                patient_id,
                appointment_data['appointment_date'],
                appointment_data.get('purpose', '')
            )
            result = self.db.db.execute_query(query, params)
            if result:
                logger.info(f"Appointment scheduled successfully with ID: {result[0][0]}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to schedule appointment: {str(e)}")
            return False
    
    def get_patient_appointments(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get all appointments for a patient"""
        query = """
        SELECT id, appointment_date, purpose, status
        FROM appointments
        WHERE patient_id = %s
        ORDER BY appointment_date;
        """
        try:
            result = self.db.db.execute_query(query, (patient_id,))
            if result:
                return [{
                    'id': row[0],
                    'appointment_date': row[1],
                    'purpose': row[2],
                    'status': row[3]
                } for row in result]
            return []
        except Exception as e:
            logger.error(f"Failed to get appointments: {str(e)}")
            return []

class TreatmentRepository:
    """Data access layer for treatment-related operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def add_treatment(self, patient_id: int, condition: str, symptoms: str, 
                     ai_analysis: Dict[str, Any], treatment_plan: Dict[str, Any]) -> bool:
        """Add a new treatment record with AI analysis"""
        try:
            # Convert dictionary to JSON string if needed
            ai_analysis_json = json.dumps(ai_analysis) if isinstance(ai_analysis, dict) else ai_analysis
            treatment_plan_json = json.dumps(treatment_plan) if isinstance(treatment_plan, dict) else treatment_plan
            
            query = """
            INSERT INTO treatments (
                patient_id, condition, symptoms, ai_analysis, treatment_plan
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """
            
            params = (
                patient_id,
                condition,
                symptoms,
                ai_analysis_json,
                treatment_plan_json
            )
            
            result = self.db.db.execute_query(query, params)
            if result:
                logger.info(f"Treatment added successfully with ID: {result[0][0]}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to add treatment: {str(e)}")
            return False
    
    def get_patient_treatments(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get all treatments for a patient"""
        query = """
        SELECT id, condition, symptoms, ai_analysis, treatment_plan, status, created_at
        FROM treatments
        WHERE patient_id = %s
        ORDER BY created_at DESC;
        """
        try:
            result = self.db.db.execute_query(query, (patient_id,))
            if result:
                treatments = []
                for row in result:
                    # Safely parse JSON data
                    try:
                        ai_analysis = json.loads(row[3]) if row[3] else None
                    except Exception as e:
                        logger.warning(f"Failed to parse AI analysis JSON: {str(e)}")
                        ai_analysis = {"error": "Failed to parse AI analysis data"}
                    
                    try:
                        treatment_plan = json.loads(row[4]) if row[4] else None
                    except Exception as e:
                        logger.warning(f"Failed to parse treatment plan JSON: {str(e)}")
                        treatment_plan = {"error": "Failed to parse treatment plan data"}
                    
                    treatments.append({
                        'id': row[0],
                        'condition': row[1],
                        'symptoms': row[2],
                        'ai_analysis': ai_analysis,
                        'treatment_plan': treatment_plan,
                        'status': row[5],
                        'created_at': row[6]
                    })
                return treatments
            return []
        except Exception as e:
            logger.error(f"Failed to get treatments: {str(e)}")
            return []

class MedicalHistoryRepository:
    """Data access layer for medical history operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def add_medical_history(self, patient_id: int, history_data: Dict[str, Any]) -> bool:
        """Add medical history record"""
        query = """
        INSERT INTO medical_history (
            patient_id, visit_date, diagnosis, treatment, notes
        ) VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """
        try:
            params = (
                patient_id,
                history_data['visit_date'],
                history_data.get('diagnosis', ''),
                history_data.get('treatment', ''),
                history_data.get('notes', '')
            )
            result = self.db.db.execute_query(query, params)
            if result:
                logger.info(f"Medical history added successfully with ID: {result[0][0]}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to add medical history: {str(e)}")
            return False
    
    def get_patient_medical_history(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get medical history for a patient"""
        query = """
        SELECT id, visit_date, diagnosis, treatment, notes
        FROM medical_history
        WHERE patient_id = %s
        ORDER BY visit_date DESC;
        """
        try:
            result = self.db.db.execute_query(query, (patient_id,))
            if result:
                return [{
                    'id': row[0],
                    'visit_date': row[1],
                    'diagnosis': row[2],
                    'treatment': row[3],
                    'notes': row[4]
                } for row in result]
            return []
        except Exception as e:
            logger.error(f"Failed to get medical history: {str(e)}")
            return []

class PatientService:
    """Business logic layer for patient-related operations"""
    
    def __init__(self, 
                 patient_repo: PatientRepository,
                 appointment_repo: AppointmentRepository,
                 treatment_repo: TreatmentRepository,
                 medical_history_repo: MedicalHistoryRepository,
                 ai_service: AIService):
        self.patient_repo = patient_repo
        self.appointment_repo = appointment_repo
        self.treatment_repo = treatment_repo
        self.medical_history_repo = medical_history_repo
        self.ai = ai_service
    
    def add_patient(self, patient_data: Dict[str, Any]) -> bool:
        """Add a new patient"""
        patient_id = self.patient_repo.add_patient(patient_data)
        return patient_id is not None
    
    def get_patient(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """Get patient details"""
        return self.patient_repo.get_patient(patient_id)
    
    def update_patient(self, patient_id: int, update_data: Dict[str, Any]) -> bool:
        """Update patient information"""
        return self.patient_repo.update_patient(patient_id, update_data)
    
    def delete_patient(self, patient_id: int) -> bool:
        """Delete a patient"""
        return self.patient_repo.delete_patient(patient_id)
    
    def list_patients(self) -> List[Dict[str, Any]]:
        """List all patients"""
        return self.patient_repo.list_patients()
    
    def schedule_appointment(self, patient_id: int, appointment_data: Dict[str, Any]) -> bool:
        """Schedule a new appointment"""
        return self.appointment_repo.schedule_appointment(patient_id, appointment_data)
    
    def get_patient_appointments(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get all appointments for a patient"""
        return self.appointment_repo.get_patient_appointments(patient_id)
    
    def add_treatment(self, patient_id: int, treatment_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
        """Add a new treatment with AI analysis and return the AI responses"""
        ai_analysis = {"analysis": "No analysis available", "timestamp": datetime.now().isoformat()}
        treatment_plan = {"treatment_plan": "No treatment plan available", "timestamp": datetime.now().isoformat()}
        
        try:
            # Get AI analysis
            logger.info(f"Generating AI analysis for patient {patient_id}")
            print("\nGenerating AI analysis of symptoms...")
            ai_analysis = self.ai.analyze_patient_symptoms(treatment_data['symptoms'])
            
            # Check if analysis was successful
            if 'error' in ai_analysis:
                logger.warning(f"AI analysis returned an error: {ai_analysis.get('error')}")
            
            # Get treatment plan
            logger.info(f"Generating AI treatment plan for patient {patient_id}")
            print("\nGenerating AI treatment plan...")
            treatment_plan = self.ai.generate_treatment_plan(
                treatment_data['condition'],
                treatment_data.get('patient_history', '')
            )
            
            # Check if treatment plan was successful
            if 'error' in treatment_plan:
                logger.warning(f"AI treatment plan returned an error: {treatment_plan.get('error')}")
            
            # Store AI responses in the database
            logger.info(f"Saving treatment data to database for patient {patient_id}")
            success = self.treatment_repo.add_treatment(
                patient_id,
                treatment_data['condition'],
                treatment_data['symptoms'],
                ai_analysis,
                treatment_plan
            )
            
            if not success:
                logger.error(f"Failed to save treatment data for patient {patient_id}")
            
            # Return the success status and the AI responses
            return success, ai_analysis, treatment_plan
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in add_treatment service: {error_msg}")
            
            # Provide helpful error messages in the analysis and treatment plan
            ai_analysis = {
                "error": f"Analysis failed: {error_msg}",
                "analysis": "Analysis could not be completed due to a system error.",
                "timestamp": datetime.now().isoformat()
            }
            
            treatment_plan = {
                "error": f"Treatment plan failed: {error_msg}",
                "treatment_plan": "Treatment plan could not be generated due to a system error.",
                "timestamp": datetime.now().isoformat()
            }
            
            return False, ai_analysis, treatment_plan
    
    def get_patient_treatments(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get all treatments for a patient"""
        return self.treatment_repo.get_patient_treatments(patient_id)
    
    def add_medical_history(self, patient_id: int, history_data: Dict[str, Any]) -> bool:
        """Add medical history record"""
        return self.medical_history_repo.add_medical_history(patient_id, history_data)
    
    def get_patient_medical_history(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get medical history for a patient"""
        return self.medical_history_repo.get_patient_medical_history(patient_id)

class UserInterface:
    """Handles user interaction"""
    def __init__(self, patient_service: PatientService):
        self.service = patient_service

    def display_menu(self):
        """Display the main menu"""
        print("\n=== Advanced Patient Management System ===")
        print("1. Patient Management")
        print("2. Appointment Management")
        print("3. Treatment Management")
        print("4. Medical History")
        print("5. Exit")
        return input("Enter your choice (1-5): ")

    def patient_management_menu(self):
        """Display patient management menu"""
        print("\n=== Patient Management ===")
        print("1. Add Patient")
        print("2. View Patient")
        print("3. Update Patient")
        print("4. Delete Patient")
        print("5. List All Patients")
        print("6. Back to Main Menu")
        return input("Enter your choice (1-6): ")

    def appointment_management_menu(self):
        """Display appointment management menu"""
        print("\n=== Appointment Management ===")
        print("1. Schedule Appointment")
        print("2. View Appointments")
        print("3. Back to Main Menu")
        return input("Enter your choice (1-3): ")

    def treatment_management_menu(self):
        """Display treatment management menu"""
        print("\n=== Treatment Management ===")
        print("1. Add Treatment")
        print("2. View Treatments")
        print("3. Back to Main Menu")
        return input("Enter your choice (1-3): ")

    def medical_history_menu(self):
        """Display medical history menu"""
        print("\n=== Medical History ===")
        print("1. Add Medical Record")
        print("2. View Medical History")
        print("3. Back to Main Menu")
        return input("Enter your choice (1-3): ")

    def get_patient_data(self) -> Dict[str, Any]:
        """Get patient information from user"""
        return {
            'first_name': input("Enter first name: "),
            'last_name': input("Enter last name: "),
            'dob': input("Enter date of birth (YYYY-MM-DD): "),
            'phone': input("Enter phone number: "),
            'email': input("Enter email (optional): ")
        }

    def get_appointment_data(self) -> Dict[str, Any]:
        """Get appointment information from user"""
        return {
            'appointment_date': input("Enter appointment date and time (YYYY-MM-DD HH:MM): "),
            'purpose': input("Enter appointment purpose: ")
        }

    def get_treatment_data(self) -> Dict[str, Any]:
        """Get treatment information from user"""
        return {
            'condition': input("Enter medical condition: "),
            'symptoms': input("Enter symptoms (comma-separated): "),
            'patient_history': input("Enter relevant patient history (optional): ")
        }

    def get_medical_history_data(self) -> Dict[str, Any]:
        """Get medical history information from user"""
        return {
            'visit_date': input("Enter visit date (YYYY-MM-DD): "),
            'diagnosis': input("Enter diagnosis: "),
            'treatment': input("Enter treatment: "),
            'notes': input("Enter additional notes: ")
        }

    def display_ai_analysis(self, ai_analysis: Dict[str, Any]):
        """Display AI analysis in a structured way"""
        print("\n" + "="*60)
        print(" "*20 + "AI SYMPTOM ANALYSIS")
        print("="*60)
        
        if 'error' in ai_analysis:
            print(f"Error generating analysis: {ai_analysis['error']}")
            return
            
        if 'analysis' in ai_analysis:
            # Format the analysis text
            analysis_text = ai_analysis['analysis']
            
            # Try to structure the output by looking for numbered points
            import re
            
            # Split by lines
            lines = analysis_text.strip().split('\n')
            
            # Print each line with proper formatting
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this is a header or a numbered point
                if re.match(r'^\d+\.', line):
                    # This is a numbered point
                    print(f"\n  {line}")
                elif ':' in line:
                    # This might be a header
                    print(f"\n{line}")
                else:
                    # Regular text
                    print(f"  {line}")
            
            if 'timestamp' in ai_analysis:
                timestamp = datetime.fromisoformat(ai_analysis['timestamp'])
                print(f"\nAnalysis generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("No AI analysis data available.")
        
        print("="*60)
    
    def display_treatment_plan(self, treatment_plan: Dict[str, Any]):
        """Display treatment plan in a structured way"""
        print("\n" + "="*60)
        print(" "*20 + "AI TREATMENT PLAN")
        print("="*60)
        
        if 'error' in treatment_plan:
            print(f"Error generating treatment plan: {treatment_plan['error']}")
            return
            
        if 'treatment_plan' in treatment_plan:
            # Format the treatment plan text
            plan_text = treatment_plan['treatment_plan']
            
            # Try to structure the output by looking for numbered points
            import re
            
            # Split by lines
            lines = plan_text.strip().split('\n')
            
            # Print each line with proper formatting
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this is a header or a numbered point
                if re.match(r'^\d+\.', line):
                    # This is a numbered point
                    print(f"\n  {line}")
                elif ':' in line:
                    # This might be a header
                    print(f"\n{line}")
                else:
                    # Regular text
                    print(f"  {line}")
            
            if 'timestamp' in treatment_plan:
                timestamp = datetime.fromisoformat(treatment_plan['timestamp'])
                print(f"\nPlan generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("No treatment plan data available.")
        
        print("="*60)
    
    def run(self):
        """Main program loop"""
        while True:
            choice = self.display_menu()

            if choice == '1':  # Patient Management
                self.handle_patient_management()
            elif choice == '2':  # Appointment Management
                self.handle_appointment_management()
            elif choice == '3':  # Treatment Management
                self.handle_treatment_management()
            elif choice == '4':  # Medical History
                self.handle_medical_history()
            elif choice == '5':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
    
    def handle_patient_management(self):
        """Handle patient management menu interactions"""
        while True:
            sub_choice = self.patient_management_menu()
            if sub_choice == '1':
                patient_data = self.get_patient_data()
                if self.service.add_patient(patient_data):
                    print("Patient added successfully!")
                else:
                    print("Failed to add patient.")
            elif sub_choice == '2':
                patient_id = int(input("Enter patient ID: "))
                patient = self.service.get_patient(patient_id)
                if patient:
                    print("\nPatient Details:")
                    for key, value in patient.items():
                        print(f"{key}: {value}")
                else:
                    print("Patient not found.")
            elif sub_choice == '3':
                patient_id = int(input("Enter patient ID to update: "))
                patient = self.service.get_patient(patient_id)
                if patient:
                    print("\nCurrent patient details:")
                    for key, value in patient.items():
                        print(f"{key}: {value}")
                    print("\nEnter new values (press Enter to keep current value):")
                    update_data = {}
                    for field in ['first_name', 'last_name', 'dob', 'phone', 'email']:
                        new_value = input(f"New {field}: ")
                        if new_value:
                            update_data[field] = new_value
                    if self.service.update_patient(patient_id, update_data):
                        print("Patient updated successfully!")
                    else:
                        print("Failed to update patient.")
                else:
                    print("Patient not found.")
            elif sub_choice == '4':
                patient_id = int(input("Enter patient ID to delete: "))
                if self.service.delete_patient(patient_id):
                    print("Patient deleted successfully!")
                else:
                    print("Failed to delete patient or patient not found.")
            elif sub_choice == '5':
                patients = self.service.list_patients()
                if patients:
                    print("\nAll Patients:")
                    for patient in patients:
                        print(f"\nID: {patient['id']}")
                        print(f"Name: {patient['first_name']} {patient['last_name']}")
                        print(f"DOB: {patient['dob']}")
                        print(f"Phone: {patient['phone']}")
                        print(f"Email: {patient['email']}")
                else:
                    print("No patients found.")
            elif sub_choice == '6':
                break
    
    def handle_appointment_management(self):
        """Handle appointment management menu interactions"""
        while True:
            sub_choice = self.appointment_management_menu()
            if sub_choice == '1':
                patient_id = int(input("Enter patient ID: "))
                if not self.service.get_patient(patient_id):
                    print("Patient not found.")
                    continue
                    
                appointment_data = self.get_appointment_data()
                if self.service.schedule_appointment(patient_id, appointment_data):
                    print("Appointment scheduled successfully!")
                else:
                    print("Failed to schedule appointment.")
            elif sub_choice == '2':
                patient_id = int(input("Enter patient ID: "))
                appointments = self.service.get_patient_appointments(patient_id)
                if appointments:
                    print("\nAppointments:")
                    for appt in appointments:
                        print(f"\nID: {appt['id']}")
                        print(f"Date: {appt['appointment_date']}")
                        print(f"Purpose: {appt['purpose']}")
                        print(f"Status: {appt['status']}")
                else:
                    print("No appointments found.")
            elif sub_choice == '3':
                break
    
    def handle_treatment_management(self):
        """Handle treatment management menu interactions"""
        while True:
            sub_choice = self.treatment_management_menu()
            if sub_choice == '1':
                patient_id = int(input("Enter patient ID: "))
                if not self.service.get_patient(patient_id):
                    print("Patient not found.")
                    continue
                    
                treatment_data = self.get_treatment_data()
                print("\nProcessing AI analysis... please wait.")
                
                # Get back the success status and AI responses
                success, ai_analysis, treatment_plan = self.service.add_treatment(patient_id, treatment_data)
                
                if success:
                    print("Treatment added successfully!")
                    
                    # Display the AI responses in a structured way
                    self.display_ai_analysis(ai_analysis)
                    self.display_treatment_plan(treatment_plan)
                else:
                    print("Failed to add treatment.")
            elif sub_choice == '2':
                patient_id = int(input("Enter patient ID: "))
                treatments = self.service.get_patient_treatments(patient_id)
                if treatments:
                    print("\nTreatments:")
                    for treatment in treatments:
                        print(f"\n{'='*50}")
                        print(f"ID: {treatment['id']}")
                        print(f"Condition: {treatment['condition']}")
                        print(f"Symptoms: {treatment['symptoms']}")
                        print(f"Status: {treatment['status']}")
                        print(f"Created: {treatment['created_at']}")
                        
                        if treatment['ai_analysis']:
                            self.display_ai_analysis(treatment['ai_analysis'])
                                
                        if treatment['treatment_plan']:
                            self.display_treatment_plan(treatment['treatment_plan'])
                        
                        print(f"{'='*50}")
                else:
                    print("No treatments found.")
            elif sub_choice == '3':
                break
    
    def handle_medical_history(self):
        """Handle medical history menu interactions"""
        while True:
            sub_choice = self.medical_history_menu()
            if sub_choice == '1':
                patient_id = int(input("Enter patient ID: "))
                if not self.service.get_patient(patient_id):
                    print("Patient not found.")
                    continue
                    
                history_data = self.get_medical_history_data()
                if self.service.add_medical_history(patient_id, history_data):
                    print("Medical history added successfully!")
                else:
                    print("Failed to add medical history.")
            elif sub_choice == '2':
                patient_id = int(input("Enter patient ID: "))
                history = self.service.get_patient_medical_history(patient_id)
                if history:
                    print("\nMedical History:")
                    for record in history:
                        print(f"\nVisit Date: {record['visit_date']}")
                        print(f"Diagnosis: {record['diagnosis']}")
                        print(f"Treatment: {record['treatment']}")
                        print(f"Notes: {record['notes']}")
                else:
                    print("No medical history found.")
            elif sub_choice == '3':
                break

def main():
    """Main program entry point"""
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
            logger.error(f"Invalid database configuration: {error_msg}")
            print(f"Configuration error: {error_msg}")
            print("Please check your environment variables or config.json file.")
            return
        
        # Setup database connection
        db_connection = DatabaseConnection(db_config)
        
        # Setup database manager
        db_manager = DatabaseManager(db_connection)
        
        # Initialize the database schema
        if not db_manager.setup_database():
            logger.error("Failed to set up database schema")
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
        
        # Initialize and run UI
        ui = UserInterface(patient_service)
        ui.run()
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print(f"An error occurred: {str(e)}")
    finally:
        # Cleanup resources
        if 'db_connection' in locals():
            db_connection.close()

if __name__ == "__main__":
    main()
