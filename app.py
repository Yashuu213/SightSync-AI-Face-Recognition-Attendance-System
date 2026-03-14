from flask import Flask, render_template, request, jsonify, send_file
import face_recognition
import cv2
import numpy as np
import os
import pandas as pd
from datetime import datetime
import base64

from database import init_db, add_employee, get_all_employees, delete_employee, mark_attendance, get_attendance_logs
from face_utils import encode_face_from_image, serialize_encoding, deserialize_encoding, match_face

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fas-secret-2026'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

# ─── Database Init ────────────────────────────────────────────────────────────
init_db()

# ─── In-memory face cache ─────────────────────────────────────────────────────
known_encodings = []
known_ids = []
id_to_name = {}

def reload_faces():
    global known_encodings, known_ids, id_to_name
    known_encodings, known_ids = [], []
    id_to_name = {}
    for emp in get_all_employees():
        eid = emp['employee_id']
        name = emp['name']
        known_ids.append(eid)
        id_to_name[eid] = name
        known_encodings.append(deserialize_encoding(emp['face_encoding']))

reload_faces()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def b64_to_bytes(b64str):
    if ',' in b64str:
        b64str = b64str.split(',', 1)[1]
    return base64.b64decode(b64str)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    # If this service is meant only for users, redirect home to the user panel
    if os.getenv('APP_MODE') == 'USER':
        return redirect(url_for('user_panel'))
        
    employees = get_all_employees()
    all_logs   = get_attendance_logs()
    today      = datetime.now().strftime('%Y-%m-%d')
    today_logs = [l for l in all_logs if l['date'] == today]
    
    return render_template('index.html', 
                           total_employees=len(employees),
                           present_today=len(today_logs),
                           recent_logs=all_logs[:8])

@app.route('/employees')
def view_employees():
    return render_template('employees.html', employees=get_all_employees())

@app.route('/add_employee')
def add_employee_route():
    return render_template('add_employee.html')

@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

@app.route('/history')
def history():
    return render_template('history.html', logs=get_attendance_logs())

@app.route('/user')
def user_panel():
    return render_template('user_attendance.html')

@app.route('/manifest.json')
def serve_manifest():
    return send_file('static/manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_file('static/sw.js')

# ─── API: Add employee with live face samples ──────────────────────────────────
@app.route('/api/add_employee', methods=['POST'])
def api_add_employee():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return jsonify(success=False, message=f'Invalid request: {e}')

    eid        = (data.get('employee_id') or '').strip()
    name       = (data.get('name') or '').strip()
    department = data.get('department', 'IT')
    phone      = data.get('phone', '')
    email      = data.get('email', '')
    frames_b64 = data.get('frames', [])   # list of base64 strings

    if not eid or not name:
        return jsonify(success=False, message='Employee ID and Name are required.')
    if not frames_b64:
        return jsonify(success=False, message='No face frames received.')

    # Extract encodings from each captured frame
    good_encodings = []
    for b64 in frames_b64:
        enc = encode_face_from_image(b64_to_bytes(b64))
        if enc is not None:
            good_encodings.append(enc)

    if len(good_encodings) < 3:
        return jsonify(success=False,
                       message=f'Only {len(good_encodings)} valid face frames detected out of {len(frames_b64)}. '
                               'Ensure good lighting and face is fully visible.')

    # Average the encodings → robust single representation
    avg_encoding = np.mean(good_encodings, axis=0)
    blob = serialize_encoding(avg_encoding)

    ok = add_employee(eid, name, department, phone, email, blob)
    if not ok:
        return jsonify(success=False, message='Employee ID already exists. Use a different ID.')

    reload_faces()
    return jsonify(success=True,
                   message=f'✅ {name} registered with {len(good_encodings)} face samples!')

# ─── API: Delete employee ──────────────────────────────────────────────────────
@app.route('/api/delete_employee/<eid>', methods=['POST'])
def api_delete_employee(eid):
    delete_employee(eid)
    reload_faces()
    return jsonify(success=True)


# ─── API: Recognise a single frame ────────────────────────────────────────────
@app.route('/api/recognise', methods=['POST'])
def api_recognise():
    data = request.get_json(force=True)
    img_b64 = data.get('frame', '')
    if not img_b64:
        return jsonify(success=False, faces=[])

    img_bytes = b64_to_bytes(img_b64)
    nparr = np.frombuffer(img_bytes, np.uint8)
    bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if bgr is None:
        return jsonify(success=False, faces=[])

    # Shrink for speed
    small = cv2.resize(bgr, (0, 0), fx=0.25, fy=0.25)
    rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    locs  = face_recognition.face_locations(rgb, model='hog')
    encs  = face_recognition.face_encodings(rgb, locs)

    results = []
    for (top, right, bottom, left), enc in zip(locs, encs):
        mid = match_face(known_encodings, known_ids, enc)
        name = id_to_name.get(mid, 'Unknown') if mid else 'Unknown'
        results.append({
            'id':  mid if mid else 'Unknown',
            'name': name,
            'box': {'top': top*4, 'right': right*4, 'bottom': bottom*4, 'left': left*4}
        })

    return jsonify(success=True, faces=results)


# ─── API: Mark attendance ─────────────────────────────────────────────────────
@app.route('/api/mark', methods=['POST'])
def api_mark():
    data = request.get_json(force=True)
    eid  = (data.get('employee_id') or '').strip()
    if not eid:
        return jsonify(success=False, message='No employee_id')
    status = mark_attendance(eid)
    return jsonify(success=True, message=status)


# ─── Export Excel ─────────────────────────────────────────────────────────────
@app.route('/export_excel')
def export_excel():
    logs = get_attendance_logs()
    rows = []
    for l in logs:
        hours = ''
        if l['login_time'] and l['logout_time']:
            fmt = '%H:%M:%S'
            diff = datetime.strptime(l['logout_time'], fmt) - datetime.strptime(l['login_time'], fmt)
            hours = str(diff)
        rows.append({
            'Employee ID': l['employee_id'],
            'Name': l['name'],
            'Department': l['department'],
            'Date': l['date'],
            'Login': l['login_time'],
            'Logout': l['logout_time'],
            'Total Hours': hours
        })
    df = pd.DataFrame(rows)
    path = os.path.join(os.path.dirname(__file__), 'data', 'attendance.xlsx')
    df.to_excel(path, index=False, engine='openpyxl')
    return send_file(path, as_attachment=True, download_name='Attendance_Report.xlsx')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
