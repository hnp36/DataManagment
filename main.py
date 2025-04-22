from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import mysql.connector
from mysql.connector import Error
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Connection
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='medical_db',
            user='medical_user',
            password='medical_password'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        logger.error(f"MySQL connection error: {e}")
    return None

# Table Creation
def create_tables():
    connection = create_connection()
    if not connection:
        return

    try:
        cursor = connection.cursor()

        # Patients Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                age INT NOT NULL,
                gender VARCHAR(10) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(100) NOT NULL,
                address VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Appointments Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT NOT NULL,
                doctor VARCHAR(100) NOT NULL,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        ''')

        # Diagnoses Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diagnoses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT NOT NULL,
                diagnosis TEXT NOT NULL,
                diagnosis_date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        ''')

        connection.commit()
        logger.info("Tables created or already exist.")
    except Error as e:
        logger.error(f"Error creating tables: {e}")
    finally:
        cursor.close()
        connection.close()

@app.on_event("startup")
async def on_startup():
    create_tables()

# Schemas
class Patient(BaseModel):
    name: str
    age: int
    gender: str
    phone: str
    email: str
    address: str

class Appointment(BaseModel):
    patient_id: int
    doctor: str
    appointment_date: str  # Format: YYYY-MM-DD
    appointment_time: str  # Format: HH:MM:SS

class Diagnosis(BaseModel):
    patient_id: int
    diagnosis: str

# Routes
@app.post("/api/patients")
async def add_patient(patient: Patient):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO patients (name, age, gender, phone, email, address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (patient.name, patient.age, patient.gender, patient.phone, patient.email, patient.address))
        connection.commit()
        return {"message": "Patient added", "success": True}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/api/patients")
async def get_patients():
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM patients")
        return {"patients": cursor.fetchall()}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.post("/api/appointments")
async def schedule_appointment(appointment: Appointment):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO appointments (patient_id, doctor, appointment_date, appointment_time)
            VALUES (%s, %s, %s, %s)
        """, (appointment.patient_id, appointment.doctor, appointment.appointment_date, appointment.appointment_time))
        connection.commit()
        return {"message": "Appointment scheduled", "success": True}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/api/appointments")
async def get_appointments(doctor: Optional[str] = None, date: Optional[str] = None):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM appointments"
        filters = []
        params = []

        if doctor:
            filters.append("doctor = %s")
            params.append(doctor)
        if date:
            filters.append("appointment_date = %s")
            params.append(date)
        if filters:
            query += " WHERE " + " AND ".join(filters)

        cursor.execute(query, params)
        return {"appointments": cursor.fetchall()}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/api/patient-id")
async def get_patient_id(name: str):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM patients WHERE name = %s", (name,))
        result = cursor.fetchone()
        if result:
            return {"patient_id": result[0]}
        else:
            raise HTTPException(status_code=404, detail="Patient not found")
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.post("/api/diagnoses")
async def add_diagnosis(diag: Diagnosis):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO diagnoses (patient_id, diagnosis)
            VALUES (%s, %s)
        """, (diag.patient_id, diag.diagnosis))
        connection.commit()
        return {"message": "Diagnosis recorded", "success": True}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/api/diagnoses/{patient_id}")
async def get_diagnoses(patient_id: int):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM diagnoses WHERE patient_id = %s", (patient_id,))
        return {"diagnoses": cursor.fetchall()}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Newark Medical Associates API is running"}
