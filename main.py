from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import mysql.connector
from mysql.connector import Error
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import List

# Logging configuration
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

# Database connection helper
@contextmanager
def get_db_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='medical_db',
            user='medical_user',
            password='medical_password'
        )
        yield connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")
    finally:
        if connection and connection.is_connected():
            connection.close()

# Database cursor helper
@contextmanager
def get_db_cursor(connection):
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        yield cursor
    except Error as e:
        logger.error(f"Database cursor error: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    finally:
        if cursor:
            cursor.close()

# Table creation function
def create_tables():
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
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
                        diagnosis_date DATE NOT NULL DEFAULT (CURRENT_DATE),
                        FOREIGN KEY (patient_id) REFERENCES patients(id)
                    )
                ''')

                # Staff Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS staff (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        first_name VARCHAR(50) NOT NULL,
                        last_name VARCHAR(50) NOT NULL,
                        age INT NOT NULL,
                        employment_no VARCHAR(20) UNIQUE NOT NULL,
                        ssn VARCHAR(20) UNIQUE NOT NULL,
                        street VARCHAR(100) NOT NULL,
                        city VARCHAR(50) NOT NULL,
                        state VARCHAR(50) NOT NULL,
                        zip VARCHAR(20) NOT NULL,
                        gender VARCHAR(10) NOT NULL,
                        phone VARCHAR(20) NOT NULL,
                        emp_type VARCHAR(20) NOT NULL,
                        role VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Room Assignments Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS room_assignments (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        patient_id INT NOT NULL,
                        admission_date DATE NOT NULL,
                        nursing_unit VARCHAR(20) NOT NULL,
                        room_number VARCHAR(20) NOT NULL,
                        bed_number VARCHAR(10) NOT NULL,
                        number_of_days INT NOT NULL,
                        assigned_nurse VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (patient_id) REFERENCES patients(id)
                    )
                ''')

                # Shifts Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS shifts (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        staff_id INT NOT NULL,
                        shift_type VARCHAR(20) NOT NULL,
                        shift_date DATE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (staff_id) REFERENCES staff(id)
                    )
                ''')

                connection.commit()
                logger.info("Tables created successfully")
            except Error as e:
                connection.rollback()
                logger.error(f"Error creating tables: {e}")
                raise HTTPException(status_code=500, detail="Table creation failed")


            # Doctor Assignments Table
            cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctor_assignments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT NOT NULL,
        doctor_id INT NOT NULL,
        assignment_date DATE NOT NULL,
        reason TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES staff(id)
    )
''')
            
            # Nurse Assignments Table:
            cursor.execute('''
    CREATE TABLE IF NOT EXISTS nurse_assignments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT NOT NULL,
        nurse_id INT NOT NULL,
        assignment_date DATE NOT NULL,
        shift VARCHAR(20) NOT NULL,
        responsibilities TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (nurse_id) REFERENCES staff(id)
    )
''')
# Models
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
    appointment_date: str
    appointment_time: str

class Diagnosis(BaseModel):
    patient_id: int
    diagnosis: str

class Staff(BaseModel):
    first_name: str
    last_name: str
    age: int
    employment_no: str
    ssn: str
    street: str
    city: str
    state: str
    zip: str
    gender: str
    phone: str
    emp_type: str
    role: str

class RoomAssignment(BaseModel):
    patient_id: int
    admission_date: str
    nursing_unit: str
    room_number: str
    bed_number: str
    number_of_days: int
    assigned_nurse: str

class Shift(BaseModel):
    staff_id: int
    shift_type: str
    shift_date: str

class DoctorAssignment(BaseModel):
    patient_id: int
    doctor_id: int
    assignment_date: str
    reason: str

class NurseAssignment(BaseModel):
    patient_id: int
    nurse_id: int
    assignment_date: str
    shift: str
    responsibilities: str

class Surgery(BaseModel):
    patient_id: int
    surgeon_id: int
    surgery_type: str
    room_number: str
    surgery_date: str
    start_time: str
    end_time: str
    notes: Optional[str] = None

class SurgeryUpdate(BaseModel):
    status: str
# Startup event
@app.on_event("startup")
async def startup_event():
    create_tables()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Newark Medical Associates API is running"}

# Routes

# Patient Routes
@app.post("/api/patients")
async def add_patient(patient: Patient):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    INSERT INTO patients (name, age, gender, phone, email, address)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (patient.name, patient.age, patient.gender, patient.phone, patient.email, patient.address))
                connection.commit()
                return {"message": "Patient added", "success": True}
            except Error as e:
                connection.rollback()
                raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/patients")
async def get_patients():
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("SELECT * FROM patients")
                return {"patients": cursor.fetchall()}
            except Error as e:
                raise HTTPException(status_code=500, detail=str(e))
            
# Add these to your existing FastAPI code

# Update Patient Route
@app.put("/api/patients/{patient_id}")
async def update_patient(patient_id: int, patient: Patient):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                # First check if patient exists
                cursor.execute("SELECT id FROM patients WHERE id = %s", (patient_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Patient not found")
                
                # Update patient information
                cursor.execute("""
                    UPDATE patients 
                    SET name = %s, age = %s, gender = %s, phone = %s, email = %s, address = %s
                    WHERE id = %s
                """, (
                    patient.name, patient.age, patient.gender, 
                    patient.phone, patient.email, patient.address, 
                    patient_id
                ))
                connection.commit()
                
                # Check if update was successful
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=500, detail="Failed to update patient")
                    
                return {"message": "Patient updated successfully", "success": True}
            except Error as e:
                connection.rollback()
                logger.error(f"Error updating patient: {e}")
                raise HTTPException(status_code=500, detail=str(e))
                
# Delete Patient Route
@app.delete("/api/patients/{patient_id}")
async def delete_patient(patient_id: int):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                # Check for related records in other tables
                related_tables = []
                
                # Check appointments
                cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE patient_id = %s", (patient_id,))
                if cursor.fetchone()['count'] > 0:
                    related_tables.append("appointments")
                
                # Check diagnoses
                cursor.execute("SELECT COUNT(*) as count FROM diagnoses WHERE patient_id = %s", (patient_id,))
                if cursor.fetchone()['count'] > 0:
                    related_tables.append("diagnoses")
                    
                # Check room_assignments
                cursor.execute("SELECT COUNT(*) as count FROM room_assignments WHERE patient_id = %s", (patient_id,))
                if cursor.fetchone()['count'] > 0:
                    related_tables.append("room_assignments")
                
                # Check doctor_assignments
                cursor.execute("SELECT COUNT(*) as count FROM doctor_assignments WHERE patient_id = %s", (patient_id,))
                if cursor.fetchone()['count'] > 0:
                    related_tables.append("doctor_assignments")
                
                # Check nurse_assignments
                cursor.execute("SELECT COUNT(*) as count FROM nurse_assignments WHERE patient_id = %s", (patient_id,))
                if cursor.fetchone()['count'] > 0:
                    related_tables.append("nurse_assignments")
                
                # Check surgeries if the table exists
                try:
                    cursor.execute("SHOW TABLES LIKE 'surgeries'")
                    if cursor.fetchone():
                        cursor.execute("SELECT COUNT(*) as count FROM surgeries WHERE patient_id = %s", (patient_id,))
                        if cursor.fetchone()['count'] > 0:
                            related_tables.append("surgeries")
                except:
                    pass  # Table doesn't exist, continue
                
                # If there are related records, return an error
                if related_tables:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Cannot delete patient because they have records in: {', '.join(related_tables)}. Delete those records first."
                    )
                
                # First check if patient exists
                cursor.execute("SELECT id FROM patients WHERE id = %s", (patient_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Patient not found")
                
                # Delete the patient
                cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
                connection.commit()
                
                # Check if deletion was successful
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=500, detail="Failed to delete patient")
                    
                return {"message": "Patient deleted successfully", "success": True}
            except HTTPException:
                connection.rollback()
                raise
            except Error as e:
                connection.rollback()
                logger.error(f"Error deleting patient: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# Appointment Routes
@app.post("/api/appointments")
async def schedule_appointment(appointment: Appointment):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    INSERT INTO appointments (patient_id, doctor, appointment_date, appointment_time)
                    VALUES (%s, %s, %s, %s)
                """, (appointment.patient_id, appointment.doctor, appointment.appointment_date, appointment.appointment_time))
                connection.commit()
                return {"message": "Appointment scheduled", "success": True}
            except Error as e:
                connection.rollback()
                raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/appointments")
async def get_appointments(doctor: Optional[str] = None, date: Optional[str] = None):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
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

# Diagnosis Routes
@app.post("/api/diagnoses")
async def add_diagnosis(diag: Diagnosis):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    INSERT INTO diagnoses (patient_id, diagnosis)
                    VALUES (%s, %s)
                """, (diag.patient_id, diag.diagnosis))
                connection.commit()
                return {"message": "Diagnosis recorded", "success": True}
            except Error as e:
                connection.rollback()
                raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diagnoses/{patient_id}")
async def get_diagnoses(patient_id: int):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("SELECT * FROM diagnoses WHERE patient_id = %s", (patient_id,))
                return {"diagnoses": cursor.fetchall()}
            except Error as e:
                raise HTTPException(status_code=500, detail=str(e))

# Staff Routes
@app.post("/api/staff")
async def add_staff(staff: Staff):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    INSERT INTO staff (
                        first_name, last_name, age, employment_no, ssn,
                        street, city, state, zip, gender, phone, emp_type, role
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    staff.first_name, staff.last_name, staff.age, staff.employment_no, staff.ssn,
                    staff.street, staff.city, staff.state, staff.zip, staff.gender,
                    staff.phone, staff.emp_type, staff.role
                ))
                connection.commit()
                return {"message": "Staff added successfully", "success": True}
            except Error as e:
                connection.rollback()
                logger.error(f"Error adding staff: {e}")
                raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/staff")
async def get_staff():
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("SELECT * FROM staff")
                return {"staff": cursor.fetchall()}
            except Error as e:
                raise HTTPException(status_code=500, detail=str(e))
            

@app.delete("/api/staff/{staff_id}")
async def delete_staff(staff_id: int):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                # First check if staff exists
                cursor.execute("SELECT id FROM staff WHERE id = %s", (staff_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Staff member not found")
                
                # Delete the staff member
                cursor.execute("DELETE FROM staff WHERE id = %s", (staff_id,))
                connection.commit()
                
                # Check if deletion was successful
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=500, detail="Failed to delete staff member")
                    
                return {"message": "Staff member deleted successfully", "success": True}
            except Error as e:
                connection.rollback()
                logger.error(f"Error deleting staff: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            
@app.get("/api/staff/{staff_id}")
async def get_staff_by_id(staff_id: int):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("SELECT * FROM staff WHERE id = %s", (staff_id,))
                staff = cursor.fetchone()
                if not staff:
                    raise HTTPException(status_code=404, detail="Staff member not found")
                return {"staff": staff}
            except Error as e:
                raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/staff/{staff_id}")
async def update_staff(staff_id: int, updated_staff: Staff):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    UPDATE staff SET
                        first_name = %s,
                        last_name = %s,
                        age = %s,
                        employment_no = %s,
                        ssn = %s,
                        street = %s,
                        city = %s,
                        state = %s,
                        zip = %s,
                        gender = %s,
                        phone = %s,
                        emp_type = %s,
                        role = %s
                    WHERE id = %s
                """, (
                    updated_staff.first_name, updated_staff.last_name, updated_staff.age,
                    updated_staff.employment_no, updated_staff.ssn, updated_staff.street,
                    updated_staff.city, updated_staff.state, updated_staff.zip,
                    updated_staff.gender, updated_staff.phone, updated_staff.emp_type,
                    updated_staff.role, staff_id
                ))
                connection.commit()
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Staff member not found")
                return {"message": "Staff member updated successfully", "success": True}
            except Error as e:
                connection.rollback()
                logger.error(f"Error updating staff: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# Room Assignment Routes
@app.post("/api/room-assignments")
async def assign_room(assignment: RoomAssignment):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    INSERT INTO room_assignments (
                        patient_id, admission_date, nursing_unit,
                        room_number, bed_number, number_of_days, assigned_nurse
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    assignment.patient_id, assignment.admission_date, assignment.nursing_unit,
                    assignment.room_number, assignment.bed_number, assignment.number_of_days,
                    assignment.assigned_nurse
                ))
                connection.commit()
                return {"message": "Room assigned successfully", "success": True}
            except Error as e:
                connection.rollback()
                raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/room-assignments")
async def get_room_assignments(patient_id: Optional[int] = None):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                base_query = """
                    SELECT 
                        ra.id, ra.patient_id, ra.admission_date, 
                        ra.nursing_unit, ra.room_number, ra.bed_number,
                        ra.number_of_days, ra.assigned_nurse, ra.created_at,
                        p.name AS patient_name,
                        DATE_FORMAT(ra.admission_date, '%Y-%m-%d') AS formatted_date
                    FROM room_assignments ra
                    JOIN patients p ON ra.patient_id = p.id
                """

                params = []
                where_clause = ""
                if patient_id is not None:
                    where_clause = "WHERE ra.patient_id = %s"
                    params.append(patient_id)

                final_query = f"""
                    {base_query}
                    {where_clause}
                    ORDER BY ra.admission_date DESC
                """

                logger.info(f"Executing SQL: {final_query.strip()} | Params: {params}")

                cursor.execute(final_query, params)
                assignments = cursor.fetchall()

                if not assignments:
                    logger.warning("No room assignments found.")
                return {"assignments": assignments}

            except Error as e:
                logger.error(f"Error fetching room assignments: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to fetch room assignments. Please try again later."
                )
# Utility Routes
@app.get("/api/patient-id")
async def get_patient_id(name: str):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("SELECT id FROM patients WHERE name = %s", (name,))
                result = cursor.fetchone()
                if result:
                    return {"patient_id": result[0]}
                else:
                    raise HTTPException(status_code=404, detail="Patient not found")
            except Error as e:
                raise HTTPException(status_code=500, detail=str(e))
            
#  endpoint for deleting room assignments
@app.delete("/api/room-assignments/{assignment_id}")
async def delete_room_assignment(assignment_id: int):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                # First check if assignment exists
                cursor.execute("SELECT id FROM room_assignments WHERE id = %s", (assignment_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Room assignment not found")
                
                # Delete the assignment
                cursor.execute("DELETE FROM room_assignments WHERE id = %s", (assignment_id,))
                connection.commit()
                
                # Check if deletion was successful
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=500, detail="Failed to delete room assignment")
                    
                return {"message": "Room assignment removed successfully", "success": True}
            except Error as e:
                connection.rollback()
                logger.error(f"Error deleting room assignment: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# Shifts Routes
@app.post("/api/shifts")
async def schedule_shift(shift: Shift):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    INSERT INTO shifts (staff_id, shift_type, shift_date)
                    VALUES (%s, %s, %s)
                """, (shift.staff_id, shift.shift_type, shift.shift_date))
                connection.commit()
                return {"message": "Shift scheduled successfully", "success": True}
            except Error as e:
                connection.rollback()
                logger.error(f"Error scheduling shift: {e}")
                raise HTTPException(status_code=500, detail="Failed to schedule shift")

@app.get("/api/shifts")
async def get_shifts():
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    SELECT s.id, s.staff_id, 
                           CONCAT(st.first_name, ' ', st.last_name) AS staff_name,
                           st.role, s.shift_type, s.shift_date
                    FROM shifts s
                    JOIN staff st ON s.staff_id = st.id
                    ORDER BY s.shift_date DESC
                """)
                shifts = cursor.fetchall()
                
                # Format dates properly
                for shift in shifts:
                    if shift['shift_date']:
                        shift['formatted_date'] = shift['shift_date'].strftime('%m/%d/%Y')
                
                return {"shifts": shifts}
            except Error as e:
                logger.error(f"Error fetching shifts: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch shifts")
            
@app.delete("/api/shifts/{shift_id}")
async def delete_shift(shift_id: int):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("DELETE FROM shifts WHERE id = %s", (shift_id,))
                connection.commit()
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Shift not found")
                return {"message": "Shift deleted successfully", "success": True}
            except Error as e:
                connection.rollback()
                logger.error(f"Error deleting shift: {e}")
                raise HTTPException(status_code=500, detail="Failed to delete shift")

@app.post("/api/doctor-assignments")
async def assign_doctor(assignment: DoctorAssignment):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    INSERT INTO doctor_assignments (
                        patient_id, doctor_id, assignment_date, reason
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    assignment.patient_id, assignment.doctor_id, 
                    assignment.assignment_date, assignment.reason
                ))
                connection.commit()
                return {"message": "Doctor assigned successfully", "success": True}
            except Error as e:
                connection.rollback()
                raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/doctor-assignments")
async def get_doctor_assignments():
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    SELECT da.*, 
                           p.name as patient_name,
                           CONCAT(s.first_name, ' ', s.last_name) as doctor_name
                    FROM doctor_assignments da
                    JOIN patients p ON da.patient_id = p.id
                    JOIN staff s ON da.doctor_id = s.id
                    ORDER BY da.assignment_date DESC
                """)
                return {"assignments": cursor.fetchall()}
            except Error as e:
                raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/doctor-assignments/{assignment_id}")
async def delete_doctor_assignment(assignment_id: int):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("DELETE FROM doctor_assignments WHERE id = %s", (assignment_id,))
                connection.commit()
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Assignment not found")
                return {"message": "Assignment deleted successfully", "success": True}
            except Error as e:
                connection.rollback()
                raise HTTPException(status_code=500, detail=str(e))
            
@app.post("/api/nurse-assignments")
async def assign_nurse(assignment: NurseAssignment):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    INSERT INTO nurse_assignments (
                        patient_id, nurse_id, assignment_date, shift, responsibilities
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    assignment.patient_id, assignment.nurse_id, 
                    assignment.assignment_date, assignment.shift,
                    assignment.responsibilities
                ))
                connection.commit()
                return {"message": "Nurse assigned successfully", "success": True}
            except Error as e:
                connection.rollback()
                raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nurse-assignments")
async def get_nurse_assignments():
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    SELECT na.*, 
                           p.name as patient_name,
                           CONCAT(s.first_name, ' ', s.last_name) as nurse_name
                    FROM nurse_assignments na
                    JOIN patients p ON na.patient_id = p.id
                    JOIN staff s ON na.nurse_id = s.id
                    ORDER BY na.assignment_date DESC
                """)
                return {"assignments": cursor.fetchall()}
            except Error as e:
                raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/nurse-assignments/{assignment_id}")
async def delete_nurse_assignment(assignment_id: int):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("DELETE FROM nurse_assignments WHERE id = %s", (assignment_id,))
                connection.commit()
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Assignment not found")
                return {"message": "Assignment deleted successfully", "success": True}
            except Error as e:
                connection.rollback()
                raise HTTPException(status_code=500, detail=str(e))
# Nurse data
@app.get("/api/nurses")
async def get_nurses():
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    SELECT id, first_name, last_name, employment_no
                    FROM staff
                    WHERE role = 'Nurse'
                    ORDER BY last_name, first_name
                """)
                return {"nurses": cursor.fetchall()}
            except Error as e:
                logger.error(f"Error fetching nurses: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch nurses")
            
@app.get("/api/doctors")
async def get_doctors():
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                cursor.execute("""
                    SELECT id, first_name, last_name, role 
                    FROM staff 
                    WHERE role IN ('Physician', 'Surgeon')
                    ORDER BY last_name, first_name
                """)
                return {"doctors": cursor.fetchall()}
            except Error as e:
                logger.error(f"Error fetching doctors: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch doctors")
            
@app.post("/api/surgeries", status_code=201)
async def create_surgery(surgery: Surgery):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                # Verify patient exists
                cursor.execute("SELECT name FROM patients WHERE id = %s", (surgery.patient_id,))
                patient = cursor.fetchone()
                if not patient:
                    raise HTTPException(status_code=404, detail="Patient not found")
                
                # Verify surgeon exists
                cursor.execute("SELECT first_name, last_name FROM staff WHERE id = %s AND role IN ('Surgeon', 'Physician')", 
                              (surgery.surgeon_id,))
                surgeon = cursor.fetchone()
                if not surgeon:
                    raise HTTPException(status_code=404, detail="Surgeon not found or not a valid surgeon")
                
                # Insert the surgery
                cursor.execute("""
                    INSERT INTO surgeries (
                        patient_id, surgeon_id, surgery_type, room_number,
                        surgery_date, start_time, end_time, notes, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Scheduled')
                """, (
                    surgery.patient_id, surgery.surgeon_id, surgery.surgery_type,
                    surgery.room_number, surgery.surgery_date, surgery.start_time,
                    surgery.end_time, surgery.notes
                ))
                
                # Get the inserted surgery ID
                surgery_id = cursor.lastrowid
                
                # Create a complete surgery record to return
                surgery_record = {
                    "id": surgery_id,
                    "patient_id": surgery.patient_id,
                    "patient_name": patient['name'],
                    "surgeon_id": surgery.surgeon_id,
                    "surgeon_name": f"{surgeon['first_name']} {surgeon['last_name']}",
                    "surgery_type": surgery.surgery_type,
                    "room_number": surgery.room_number,
                    "surgery_date": surgery.surgery_date,
                    "start_time": surgery.start_time,
                    "end_time": surgery.end_time,
                    "notes": surgery.notes,
                    "status": "Scheduled"
                }
                
                connection.commit()
                return {"message": "Surgery scheduled successfully", "surgery": surgery_record}
                
            except Error as e:
                connection.rollback()
                logger.error(f"Error scheduling surgery: {e}")
                raise HTTPException(status_code=500, detail="Failed to schedule surgery")

@app.get("/api/surgeries")
async def get_surgeries(
    patient_id: Optional[int] = None,
    surgeon_id: Optional[int] = None,
    room_number: Optional[str] = None,
    date: Optional[str] = None,
    status: Optional[str] = None
):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                base_query = """
                    SELECT 
                        s.id, s.patient_id, p.name AS patient_name,
                        s.surgeon_id, CONCAT(st.first_name, ' ', st.last_name) AS surgeon_name,
                        s.surgery_type, s.room_number, 
                        DATE_FORMAT(s.surgery_date, '%%Y-%%m-%%d') AS surgery_date,
                        TIME_FORMAT(s.start_time, '%%H:%%i') AS start_time,
                        TIME_FORMAT(s.end_time, '%%H:%%i') AS end_time,
                        s.notes, s.status,
                        CONCAT(TIME_FORMAT(s.start_time, '%%H:%%i'), ' - ', TIME_FORMAT(s.end_time, '%%H:%%i')) AS time_range
                    FROM surgeries s
                    JOIN patients p ON s.patient_id = p.id
                    JOIN staff st ON s.surgeon_id = st.id
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
                if status:
                    conditions.append("s.status = %s")
                    params.append(status)
                
                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)
                
                base_query += " ORDER BY s.surgery_date, s.start_time"
                
                cursor.execute(base_query, params)
                surgeries = cursor.fetchall()
                
                return {"surgeries": surgeries}
                
            except Error as e:
                logger.error(f"Error fetching surgeries: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch surgeries")

@app.patch("/api/surgeries/{surgery_id}")
async def update_surgery_status(surgery_id: int, update: SurgeryUpdate):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                # Verify surgery exists
                cursor.execute("SELECT id FROM surgeries WHERE id = %s", (surgery_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Surgery not found")
                
                # Update status
                cursor.execute("""
                    UPDATE surgeries SET status = %s WHERE id = %s
                """, (update.status, surgery_id))
                
                connection.commit()
                return {"message": "Surgery status updated successfully"}
                
            except Error as e:
                connection.rollback()
                logger.error(f"Error updating surgery status: {e}")
                raise HTTPException(status_code=500, detail="Failed to update surgery status")

@app.delete("/api/surgeries/{surgery_id}")
async def cancel_surgery(surgery_id: int):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                # Verify surgery exists
                cursor.execute("SELECT id FROM surgeries WHERE id = %s", (surgery_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Surgery not found")
                
                # Update status to Cancelled rather than deleting
                cursor.execute("""
                    UPDATE surgeries SET status = 'Cancelled' WHERE id = %s
                """, (surgery_id,))
                
                connection.commit()
                return {"message": "Surgery cancelled successfully"}
                
            except Error as e:
                connection.rollback()
                logger.error(f"Error cancelling surgery: {e}")
                raise HTTPException(status_code=500, detail="Failed to cancel surgery")

# Add this to your create_tables() function
def create_tables():
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            try:
                # ... (your existing table creation code)

                # Surgeries Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS surgeries (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        patient_id INT NOT NULL,
                        surgeon_id INT NOT NULL,
                        surgery_type VARCHAR(100) NOT NULL,
                        room_number VARCHAR(20) NOT NULL,
                        surgery_date DATE NOT NULL,
                        start_time TIME NOT NULL,
                        end_time TIME NOT NULL,
                        notes TEXT,
                        status VARCHAR(20) NOT NULL DEFAULT 'Scheduled',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (patient_id) REFERENCES patients(id),
                        FOREIGN KEY (surgeon_id) REFERENCES staff(id)
                    )
                ''')

                connection.commit()
                logger.info("Tables created successfully")
            except Error as e:
                connection.rollback()
                logger.error(f"Error creating tables: {e}")
                raise HTTPException(status_code=500, detail="Table creation failed")