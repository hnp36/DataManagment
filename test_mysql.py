import mysql.connector

try:
    # Try connection with your new credentials
    conn = mysql.connector.connect(
        host='localhost',
        user='medical_user',
        password='medical_password',
        database='medical_db'
    )
    
    if conn.is_connected():
        print("Connection successful!")
        
        # Test creating a table
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100)
            )
        ''')
        print("Table created successfully!")
        
        cursor.close()
        conn.close()
except Exception as e:
    print(f"Error: {e}")