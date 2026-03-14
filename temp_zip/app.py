from flask import Flask, render_template, request, jsonify, Response, send_file
import cv2
import face_recognition
import numpy as np
import os
import pandas as pd
from datetime import datetime
import json

from database import init_db, add_employee, get_all_employees, delete_employee, mark_attendance, get_attendance_logs
from face_utils import encode_face_from_image, serialize_encoding, deserialize_encoding, match_face

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-123'

# Initialize database
init_db()

# Caching encodings to speed up matching
known_face_encodings = []
known_face_ids = []

def load_known_faces():
    global known_face_encodings, known_face_ids
    employees = get_all_employees()
    known_face_encodings = []
    known_face_ids = []
    for emp in employees:
        known_face_ids.append(emp['employee_id'])
        encoding_bytes = emp['face_encoding']
        encoding_array = deserialize_encoding(encoding_bytes)
        known_face_encodings.append(encoding_array)

load_known_faces()

@app.route('/')
def dashboard():
    employees = get_all_employees()
    attendance_logs = get_attendance_logs()
    
    # Calculate some stats
    total_employees = len(employees)
    today = datetime.now().strftime('%Y-%m-%d')
    today_logs = [log for log in attendance_logs if log['date'] == today]
    present_today = len(today_logs)
    
    return render_template('index.html', 
                          total_employees=total_employees, 
                          present_today=present_today,
                          recent_logs=attendance_logs[:5])

@app.route('/employees')
def view_employees():
    employees = get_all_employees()
    return render_template('employees.html', employees=employees)

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee_route():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        name = request.form.get('name')
        department = request.form.get('department')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        # Handle file upload for face capture
        if 'face_image' not in request.files:
            return jsonify({'success': False, 'message': 'No face image provided'})
            
        file = request.files['face_image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'})
            
        image_bytes = file.read()
        encoding = encode_face_from_image(image_bytes)
        
        if encoding is None:
            return jsonify({'success': False, 'message': 'No face found in the image. Please try again with a clearer photo.'})
            
        # Serialize encoding
        encoding_bytes = serialize_encoding(encoding)
        
        # Save to database
        success = add_employee(employee_id, name, department, phone, email, encoding_bytes)
        
        if success:
            # Reload known faces in memory
            load_known_faces()
            return jsonify({'success': True, 'message': 'Employee added successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Employee ID already exists.'})
            
    return render_template('add_employee.html')

@app.route('/delete_employee/<employee_id>', methods=['POST'])
def delete_employee_route(employee_id):
    delete_employee(employee_id)
    load_known_faces() # Reload cache
    return jsonify({'success': True})

@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

def gen_frames():
    """ Video streaming generator function for attendance recognition """
    camera = cv2.VideoCapture(0)
    
    # Frame skipping to reduce CPU load
    process_this_frame = True
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Resize frame for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Convert the image from BGR color (which OpenCV uses) to RGB color
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_names = []
            
            if process_this_frame:
                # Find all the faces and face encodings in the current frame of video
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                for face_encoding in face_encodings:
                    # See if the face is a match for the known face(s)
                    matched_id = match_face(known_face_encodings, known_face_ids, face_encoding)
                    
                    name = "Unknown"
                    if matched_id:
                        # Log attendance
                        status = mark_attendance(matched_id)
                        name = f"{matched_id} ({status})"
                    
                    face_names.append(name)
            
            process_this_frame = not process_this_frame

            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                color = (0, 255, 0) if "Unknown" not in name else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/history')
def history():
    logs = get_attendance_logs()
    return render_template('history.html', logs=logs)

@app.route('/export_excel')
def export_excel():
    logs = get_attendance_logs()
    
    # Process logs to calculate total hours
    export_data = []
    for log in logs:
        login = log['login_time']
        logout = log['logout_time']
        total_hours = ""
        
        if login and logout:
            fmt = '%H:%M:%S'
            t1 = datetime.strptime(login, fmt)
            t2 = datetime.strptime(logout, fmt)
            diff = t2 - t1
            # Convert to hours
            total_hours = str(diff)
            
        export_data.append({
            'Employee ID': log['employee_id'],
            'Employee Name': log['name'],
            'Department': log['department'],
            'Date': log['date'],
            'Login Time': login,
            'Logout Time': logout,
            'Total Working Hours': total_hours
        })
        
    df = pd.DataFrame(export_data)
    
    # Generate Excel file
    excel_path = os.path.join(os.path.dirname(__file__), 'data', 'attendance_report.xlsx')
    df.to_excel(excel_path, index=False, engine='openpyxl')
    
    return send_file(excel_path, as_attachment=True)

if __name__ == '__main__':
    # Ensure correct permissions / port
    app.run(host='0.0.0.0', port=5000, debug=True)
