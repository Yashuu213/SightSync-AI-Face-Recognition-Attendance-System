import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv('DATABASE_URL')
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'attendance.db')

def get_db_connection():
    if DB_URL:
        # PostgreSQL (Supabase)
        conn = psycopg2.connect(DB_URL)
        return conn
    else:
        # Local SQLite
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def get_cursor(conn):
    if DB_URL:
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()

def get_placeholder():
    return "%s" if DB_URL else "?"

def init_db():
    conn = get_db_connection()
    cursor = get_cursor(conn)
    p = get_placeholder()

    # Create Employees table
    if DB_URL:
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT,
                phone TEXT,
                email TEXT,
                face_encoding BYTEA NOT NULL
            )
        ''')
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                employee_id TEXT NOT NULL,
                date TEXT NOT NULL,
                login_time TEXT,
                logout_time TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT,
                phone TEXT,
                email TEXT,
                face_encoding BLOB NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                date TEXT NOT NULL,
                login_time TEXT,
                logout_time TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            )
        ''')

    conn.commit()
    conn.close()

# Helper functions
def add_employee(employee_id, name, department, phone, email, face_encoding_bytes):
    conn = get_db_connection()
    cursor = get_cursor(conn)
    p = get_placeholder()
    try:
        cursor.execute(f'''
            INSERT INTO employees (employee_id, name, department, phone, email, face_encoding)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p})
        ''', (employee_id, name, department, phone, email, face_encoding_bytes))
        conn.commit()
        return True
    except (sqlite3.IntegrityError, psycopg2.IntegrityError):
        return False
    finally:
        conn.close()

def get_all_employees():
    conn = get_db_connection()
    cursor = get_cursor(conn)
    cursor.execute('SELECT * FROM employees')
    employees = cursor.fetchall()
    conn.close()
    return employees

def delete_employee(employee_id):
    conn = get_db_connection()
    cursor = get_cursor(conn)
    p = get_placeholder()
    cursor.execute(f'DELETE FROM employees WHERE employee_id = {p}', (employee_id,))
    cursor.execute(f'DELETE FROM attendance WHERE employee_id = {p}', (employee_id,))
    conn.commit()
    conn.close()

def mark_attendance(employee_id):
    conn = get_db_connection()
    cursor = get_cursor(conn)
    p = get_placeholder()
    today = datetime.date.today().strftime('%Y-%m-%d')
    now_time = datetime.datetime.now().strftime('%H:%M:%S')

    cursor.execute(f'''
        SELECT id, login_time, logout_time FROM attendance 
        WHERE employee_id = {p} AND date = {p}
    ''', (employee_id, today))
    
    record = cursor.fetchone()

    status = ""
    if not record:
        cursor.execute(f'''
            INSERT INTO attendance (employee_id, date, login_time, logout_time)
            VALUES ({p}, {p}, {p}, {p})
        ''', (employee_id, today, now_time, ""))
        status = f"Login recorded at {now_time}"
    else:
        attendance_id = record['id']
        if record['logout_time']:
            last_logout_time = datetime.datetime.strptime(record['logout_time'], '%H:%M:%S')
            current_time = datetime.datetime.strptime(now_time, '%H:%M:%S')
            if (current_time - last_logout_time).total_seconds() < 60:
                conn.close()
                return "Already marked recently."

        cursor.execute(f'''
            UPDATE attendance 
            SET logout_time = {p} 
            WHERE id = {p}
        ''', (now_time, attendance_id))
        status = f"Logout updated at {now_time}"

    conn.commit()
    conn.close()
    return status

def get_attendance_logs(date=None):
    conn = get_db_connection()
    cursor = get_cursor(conn)
    p = get_placeholder()
    if date:
        query = f'''
            SELECT a.id, a.employee_id, e.name, e.department, a.date, a.login_time, a.logout_time 
            FROM attendance a 
            JOIN employees e ON a.employee_id = e.employee_id
            WHERE a.date = {p}
            ORDER BY a.login_time DESC
        '''
        cursor.execute(query, (date,))
    else:
        query = '''
            SELECT a.id, a.employee_id, e.name, e.department, a.date, a.login_time, a.logout_time 
            FROM attendance a 
            JOIN employees e ON a.employee_id = e.employee_id
            ORDER BY a.date DESC, a.login_time DESC
        '''
        cursor.execute(query)
    logs = cursor.fetchall()
    conn.close()
    return logs
