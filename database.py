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
        blob = psycopg2.Binary(face_encoding_bytes) if DB_URL else face_encoding_bytes
        cursor.execute(f'''
            INSERT INTO employees (employee_id, name, department, phone, email, face_encoding)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p})
        ''', (employee_id, name, department, phone, email, blob))
        conn.commit()
        return True
    except (sqlite3.IntegrityError, psycopg2.IntegrityError):
        return False
    except Exception as e:
        print(f"Error adding employee: {e}")
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
    # Delete child records first to respect Foreign Key constraints
    cursor.execute(f'DELETE FROM attendance WHERE employee_id = {p}', (employee_id,))
    cursor.execute(f'DELETE FROM employees WHERE employee_id = {p}', (employee_id,))
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
        # SQLite row might be a tuple internally if not configured optimally, 
        # but row_factory = sqlite3.Row allows dict access.
        try:
            attendance_id = record['id']
            login_val = record['login_time']
            logout_val = record['logout_time']
        except (TypeError, IndexError):
            attendance_id = record[0]
            login_val = record[1]
            logout_val = record[2]

        # Prevent overwriting manual "Absent" overrides
        if login_val == 'Absent' or logout_val == 'Absent':
            conn.close()
            return "Manual override active. Contact admin."

        current_time = datetime.datetime.strptime(now_time, '%H:%M:%S')

        # 1) Enforce minimum 3 minutes (180s) between Login and first Logout allowed
        if login_val:
            try:
                lt = datetime.datetime.strptime(login_val, '%H:%M:%S')
                if (current_time - lt).total_seconds() < 180:
                    conn.close()
                    return "Already logged in recently."
            except ValueError:
                pass # If parsing fails, proceed

        # 2) Enforce minimum 2 minutes (120s) between consecutive Logout updates
        if logout_val:
            try:
                last_out = datetime.datetime.strptime(logout_val, '%H:%M:%S')
                if (current_time - last_out).total_seconds() < 120:
                    conn.close()
                    return "Already marked recently."
            except ValueError:
                pass

        cursor.execute(f'''
            UPDATE attendance 
            SET logout_time = {p} 
            WHERE id = {p}
        ''', (now_time, attendance_id))
        status = f"Logout recorded at {now_time}"

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
