import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'attendance.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Employees table
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

    # Create Attendance table
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

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Helper functions
def add_employee(employee_id, name, department, phone, email, face_encoding_bytes):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO employees (employee_id, name, department, phone, email, face_encoding)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (employee_id, name, department, phone, email, face_encoding_bytes))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_employees():
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees').fetchall()
    conn.close()
    return employees

def delete_employee(employee_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM employees WHERE employee_id = ?', (employee_id,))
    # Optionally delete attendance logs as well
    conn.execute('DELETE FROM attendance WHERE employee_id = ?', (employee_id,))
    conn.commit()
    conn.close()

def mark_attendance(employee_id):
    """
    Marks attendance for an employee. 
    First scan of the day marks login. Subsequent scans mark/update logout time.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.date.today().strftime('%Y-%m-%d')
    now_time = datetime.datetime.now().strftime('%H:%M:%S')

    # Check if there is already a record for today
    cursor.execute('''
        SELECT id, login_time, logout_time FROM attendance 
        WHERE employee_id = ? AND date = ?
    ''', (employee_id, today))
    
    record = cursor.fetchone()

    status = ""
    if not record:
        # First scan -> Mark Login
        cursor.execute('''
            INSERT INTO attendance (employee_id, date, login_time, logout_time)
            VALUES (?, ?, ?, ?)
        ''', (employee_id, today, now_time, ""))
        status = f"Login recorded at {now_time}"
    else:
        # Second scan -> Mark Logout
        attendance_id = record['id']
        login_time = record['login_time']

        # To prevent spam, check if last update was very recent (e.g. within 1 minute)
        # Assuming we don't need strict cooldown for simplicity, just update logout
        if record['logout_time']:
            last_logout_time = datetime.datetime.strptime(record['logout_time'], '%H:%M:%S')
            current_time = datetime.datetime.strptime(now_time, '%H:%M:%S')
            if (current_time - last_logout_time).total_seconds() < 60:
                conn.close()
                return "Already marked recently."

         # Calculate time diff between now and login if we wanted to enforce strict > 1 min logout
        cursor.execute('''
            UPDATE attendance 
            SET logout_time = ? 
            WHERE id = ?
        ''', (now_time, attendance_id))
        status = f"Logout updated at {now_time}"

    conn.commit()
    conn.close()
    return status

def get_attendance_logs(date=None):
    conn = get_db_connection()
    if date:
        query = '''
            SELECT a.id, a.employee_id, e.name, e.department, a.date, a.login_time, a.logout_time 
            FROM attendance a 
            JOIN employees e ON a.employee_id = e.employee_id
            WHERE a.date = ?
            ORDER BY a.login_time DESC
        '''
        logs = conn.execute(query, (date,)).fetchall()
    else:
        query = '''
            SELECT a.id, a.employee_id, e.name, e.department, a.date, a.login_time, a.logout_time 
            FROM attendance a 
            JOIN employees e ON a.employee_id = e.employee_id
            ORDER BY a.date DESC, a.login_time DESC
        '''
        logs = conn.execute(query).fetchall()
    conn.close()
    return logs
