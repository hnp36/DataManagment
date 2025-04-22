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
# Add these to main.py after the existing code

# Room/Bed Management
class Room(BaseModel):
    room_number: str
    room_type: str
    status: str  # Available, Occupied, Maintenance

class AssignRoom(BaseModel):
    patient_id: int
    room_number: str
    admission_date: str
    discharge_date: Optional[str] = None

class StaffAssignment(BaseModel):
    patient_id: int
    staff_id: int
    staff_type: str  # doctor or nurse

class Surgery(BaseModel):
    patient_id: int
    surgeon_id: int
    room_number: str
    surgery_date: str
    surgery_time: str
    procedure: str

# Create tables for new functionality
def create_tables():
    connection = create_connection()
    if not connection:
        return

    try:
        cursor = connection.cursor()

        # Existing tables...

        # Rooms Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_number VARCHAR(10) PRIMARY KEY,
                room_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'Available'
            )
        ''')

        # Patient Rooms Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT NOT NULL,
                room_number VARCHAR(10) NOT NULL,
                admission_date DATE NOT NULL,
                discharge_date DATE,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (room_number) REFERENCES rooms(room_number)
            )
        ''')

        # Staff Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                role VARCHAR(50) NOT NULL,
                department VARCHAR(50) NOT NULL,
                contact_number VARCHAR(20) NOT NULL
            )
        ''')

        # Patient Staff Assignments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_staff (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT NOT NULL,
                staff_id INT NOT NULL,
                staff_type VARCHAR(20) NOT NULL,
                assignment_date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (staff_id) REFERENCES staff(id)
            )
        ''')

        # Surgeries Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS surgeries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT NOT NULL,
                surgeon_id INT NOT NULL,
                room_number VARCHAR(10) NOT NULL,
                surgery_date DATE NOT NULL,
                surgery_time TIME NOT NULL,
                procedure TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'Scheduled',
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (surgeon_id) REFERENCES staff(id),
                FOREIGN KEY (room_number) REFERENCES rooms(room_number)
            )
        ''')

        connection.commit()
        logger.info("Tables created or already exist.")
    except Error as e:
        logger.error(f"Error creating tables: {e}")
    finally:
        cursor.close()
        connection.close()

# Room Management Endpoints
@app.post("/api/rooms")
async def add_room(room: Room):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO rooms (room_number, room_type, status)
            VALUES (%s, %s, %s)
        """, (room.room_number, room.room_type, room.status))
        connection.commit()
        return {"message": "Room added", "success": True}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/api/rooms")
async def get_rooms(status: Optional[str] = None):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM rooms"
        if status:
            query += " WHERE status = %s"
            cursor.execute(query, (status,))
        else:
            cursor.execute(query)
        return {"rooms": cursor.fetchall()}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.post("/api/assign-room")
async def assign_room(assignment: AssignRoom):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor()
        
        # Check if room is available
        cursor.execute("SELECT status FROM rooms WHERE room_number = %s", (assignment.room_number,))
        room = cursor.fetchone()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        if room[0] != "Available":
            raise HTTPException(status_code=400, detail="Room is not available")
        
        # Assign room to patient
        cursor.execute("""
            INSERT INTO patient_rooms (patient_id, room_number, admission_date, discharge_date)
            VALUES (%s, %s, %s, %s)
        """, (assignment.patient_id, assignment.room_number, assignment.admission_date, assignment.discharge_date))
        
        # Update room status
        cursor.execute("""
            UPDATE rooms SET status = 'Occupied' WHERE room_number = %s
        """, (assignment.room_number,))
        
        connection.commit()
        return {"message": "Room assigned successfully", "success": True}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.post("/api/discharge-patient")
async def discharge_patient(patient_id: int = Query(...)):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor()
        
        # Get current room assignment
        cursor.execute("""
            SELECT room_number FROM patient_rooms 
            WHERE patient_id = %s AND discharge_date IS NULL
        """, (patient_id,))
        assignment = cursor.fetchone()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="No active room assignment found for patient")
        
        room_number = assignment[0]
        
        # Update discharge date
        cursor.execute("""
            UPDATE patient_rooms 
            SET discharge_date = CURRENT_DATE 
            WHERE patient_id = %s AND discharge_date IS NULL
        """, (patient_id,))
        
        # Update room status
        cursor.execute("""
            UPDATE rooms SET status = 'Available' WHERE room_number = %s
        """, (room_number,))
        
        connection.commit()
        return {"message": "Patient discharged and room made available", "success": True}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

# Staff Management Endpoints
@app.post("/api/staff")
async def add_staff(staff: dict):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO staff (name, role, department, contact_number)
            VALUES (%s, %s, %s, %s)
        """, (staff['name'], staff['role'], staff['department'], staff['contact_number']))
        connection.commit()
        return {"message": "Staff added", "success": True, "staff_id": cursor.lastrowid}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/api/staff")
async def get_staff(role: Optional[str] = None):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM staff"
        if role:
            query += " WHERE role = %s"
            cursor.execute(query, (role,))
        else:
            cursor.execute(query)
        return {"staff": cursor.fetchall()}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.post("/api/assign-staff")
async def assign_staff(assignment: StaffAssignment):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO patient_staff (patient_id, staff_id, staff_type)
            VALUES (%s, %s, %s)
        """, (assignment.patient_id, assignment.staff_id, assignment.staff_type))
        connection.commit()
        return {"message": "Staff assigned to patient", "success": True}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.delete("/api/remove-staff")
async def remove_staff(assignment_id: int = Query(...)):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM patient_staff WHERE id = %s", (assignment_id,))
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return {"message": "Staff assignment removed", "success": True}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

# Surgery Management Endpoints
@app.post("/api/surgeries")
async def schedule_surgery(surgery: Surgery):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO surgeries (patient_id, surgeon_id, room_number, surgery_date, surgery_time, procedure)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            surgery.patient_id, surgery.surgeon_id, surgery.room_number,
            surgery.surgery_date, surgery.surgery_time, surgery.procedure
        ))
        connection.commit()
        return {"message": "Surgery scheduled", "success": True}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/api/surgeries")
async def get_surgeries(
    patient_id: Optional[int] = None,
    surgeon_id: Optional[int] = None,
    room_number: Optional[str] = None,
    date: Optional[str] = None
):
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT s.*, p.name as patient_name, st.name as surgeon_name, r.room_type
            FROM surgeries s
            JOIN patients p ON s.patient_id = p.id
            JOIN staff st ON s.surgeon_id = st.id
            JOIN rooms r ON s.room_number = r.room_number
        """
        conditions = []
        params = []
        
        if patient_id:
            conditions.append("s.patient_id = %s")
            params.append(patient_id)
        if surgeon_id:
            conditions.append("s.surgeon_id = %s")
            params.append(surgeon_id)
        if room_number:
            conditions.append("s.room_number = %s")
            params.append(room_number)
        if date:
            conditions.append("s.surgery_date = %s")
            params.append(date)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY s.surgery_date, s.surgery_time"
        cursor.execute(query, params)
        return {"surgeries": cursor.fetchall()}
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
