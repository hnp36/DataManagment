from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow frontend (HTML) to access backend - more permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MySQL Connection Configuration
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='medical_db',
            user='medical_user',
            password='medical_password'
        )
        if connection.is_connected():
            logger.info("MySQL connection successful")
            return connection
        else:
            logger.error("MySQL connection failed")
            return None
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None

# Create patients table if it doesn't exist
def create_patients_table():
    connection = create_connection()
    if not connection:
        logger.error("Skipping table creation due to failed DB connection")
        return

    try:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                age INT NOT NULL,
                gender VARCHAR(10) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        connection.commit()
        logger.info("Patients table created or already exists")
    except Error as e:
        logger.error(f"Error creating table: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Call this on startup
@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application starting up")
    create_patients_table()

# Pydantic model for request body
class Patient(BaseModel):
    name: str
    age: int
    gender: str
    phone: str

# POST endpoint to add a patient
@app.post("/api/patients")
async def add_patient(patient: Patient):
    logger.info(f"Received patient data: {patient}")
    connection = create_connection()
    if not connection:
        logger.error("Database connection failed when adding patient")
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = connection.cursor()
        sql = "INSERT INTO patients (name, age, gender, phone) VALUES (%s, %s, %s, %s)"
        values = (patient.name, patient.age, patient.gender, patient.phone)
        
        # Log the query and values to be inserted
        logger.info(f"Executing SQL: {sql} with values: {values}")
        
        cursor.execute(sql, values)
        connection.commit()
        logger.info(f"Patient added successfully: {patient.name}")
        return {"message": "Patient successfully added", "success": True}
    except Error as e:
        logger.error(f"Error adding patient: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding patient: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Newark Medical Associates API is running"}
