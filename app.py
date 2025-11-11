from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
import sqlite3
import csv
import os
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'medical-appointment-secret-key-2024'

# ==================== CẤU HÌNH EMAIL ====================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hoangcanh1233214@gmail.com'
app.config['MAIL_PASSWORD'] = 'dihf fjgz rsyp jgwj'
app.config['MAIL_DEFAULT_SENDER'] = 'hoangcanh1233214@gmail.com'

mail = Mail(app)

# Flask-Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'

class User(UserMixin):
    def __init__(self, id, username, role, name=None, email=None):
        self.id = id
        self.username = username
        self.role = role
        self.name = name
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['role'], user['name'], user['email'])
    return None

# Database configuration
DATABASE = 'medical_appointment.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialize database with tables and import doctors from CSV"""
    conn = get_db_connection()
    
    # Create tables
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT,
            phone TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT,
            date_of_birth DATE,
            gender TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            available_days TEXT,
            available_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date DATE NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT DEFAULT 'Scheduled',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    ''')
    
    # Insert default users với password đã hash
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        admin_password = hash_password('admin123')
        reception_password = hash_password('reception123')
        
        conn.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)", 
                    ('admin', admin_password, 'admin', 'Quản Trị Viên'))
        conn.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)", 
                    ('reception', reception_password, 'receptionist', 'Nhân Viên Lễ Tân'))
        print("✅ Đã thêm user mặc định: admin/admin123, reception/reception123")
    
    # Import doctors from CSV
    cursor.execute("SELECT COUNT(*) FROM doctors")
    doctor_count_before = cursor.fetchone()[0]
    
    if doctor_count_before == 0 and os.path.exists('doctors.csv'):
        print("📁 Đang import dữ liệu bác sĩ từ doctors.csv...")
        imported_count = 0
        
        try:
            with open('doctors.csv', 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                
                for row_num, row in enumerate(csv_reader, 1):
                    try:
                        name = row.get('name', '').strip()
                        specialization = row.get('specialization', '').strip()
                        phone = row.get('phone', '').strip()
                        email = row.get('email', '').strip()
                        available_days = row.get('available_days', 'Thứ 2 - Thứ 6').strip()
                        available_time = row.get('available_time', '08:00-17:00').strip()
                        
                        if not name or not specialization or not phone:
                            print(f"⚠️ Dòng {row_num}: Thiếu thông tin, bỏ qua")
                            continue
                        
                        conn.execute('''
                            INSERT INTO doctors (name, specialization, phone, email, available_days, available_time)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (name, specialization, phone, email, available_days, available_time))
                        
                        imported_count += 1
                        print(f"✅ Đã import bác sĩ {row_num}: {name} - {specialization}")
                        
                    except Exception as e:
                        print(f"❌ Lỗi khi import dòng {row_num}: {str(e)}")
            
            print(f"🎉 Đã import thành công {imported_count} bác sĩ từ CSV")
            
        except Exception as e:
            print(f"❌ Lỗi khi đọc file CSV: {str(e)}")
    
    cursor.execute("SELECT COUNT(*) FROM doctors")
    doctor_count_after = cursor.fetchone()[0]
    print(f"👨‍⚕️ Tổng số bác sĩ trong database: {doctor_count_after}")
    
    conn.commit()
    conn.close()

def check_users():
    """Kiểm tra users trong database"""
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    print("=== USERS IN DATABASE ===")
    for user in users:
        print(f"ID: {user['id']}, Username: {user['username']}, Role: {user['role']}, Name: {user['name']}")
    conn.close()

# ==================== DECORATORS PHÂN QUYỀN ====================

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Bạn không có quyền truy cập trang này!', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def staff_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'receptionist']:
            flash('Bạn không có quyền truy cập trang này!', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def patient_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'patient':
            flash('Bạn không có quyền truy cập trang này!', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ==================== ROUTES CÔNG KHAI ====================

@app.route('/')
def index():
    """Trang chủ công khai"""
    return render_template('public_index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Đăng ký tài khoản bệnh nhân"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự!', 'error')
            return render_template('register.html')
        
        conn = get_db_connection()
        try:
            # Kiểm tra username đã tồn tại chưa
            existing_user = conn.execute(
                'SELECT id FROM users WHERE username = ?', (username,)
            ).fetchone()
            
            if existing_user:
                flash('Tên đăng nhập đã tồn tại!', 'error')
                return render_template('register.html')
            
            # Thêm user mới
            cursor = conn.cursor()
            hashed_password = hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, password, role, name, phone, email)
                VALUES (?, ?, 'patient', ?, ?, ?)
            ''', (username, hashed_password, name, phone, email))
            
            user_id = cursor.lastrowid
            
            # Thêm vào bảng patients
            cursor.execute('''
                INSERT INTO patients (name, phone, email, user_id)
                VALUES (?, ?, ?, ?)
            ''', (name, phone, email, user_id))
            
            conn.commit()
            conn.close()
            
            flash('Đăng ký tài khoản thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            conn.close()
            flash(f'Lỗi khi đăng ký: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Đăng nhập cho cả admin và bệnh nhân"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?', 
            (username, hashed_password)
        ).fetchone()
        conn.close()
        
        if user:
            user_obj = User(user['id'], user['username'], user['role'], user['name'], user['email'])
            login_user(user_obj)
            flash(f'Đăng nhập thành công! Chào mừng {user["name"]}', 'success')
            
            # Redirect dựa trên role
            if user['role'] == 'patient':
                return redirect(url_for('patient_dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'error')
    
    return render_template('login.html')

@app.route('/public/appointment', methods=['GET', 'POST'])
def public_appointment():
    """Trang đăng ký lịch hẹn công khai (không cần đăng nhập)"""
    conn = get_db_connection()
    doctors = conn.execute('SELECT * FROM doctors ORDER BY name').fetchall()
    conn.close()
    
    if request.method == 'POST':
        patient_name = request.form['patient_name']
        patient_phone = request.form['patient_phone']
        patient_email = request.form['patient_email']
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        notes = request.form.get('notes', '')
        
        print(f"📝 Đang xử lý đăng ký lịch hẹn:")
        print(f"   👤 Bệnh nhân: {patient_name}")
        print(f"   📞 SĐT: {patient_phone}")
        print(f"   📧 Email: {patient_email}")
        
        conn = get_db_connection()
        try:
            # Thêm bệnh nhân mới
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO patients (name, phone, email, created_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', (patient_name, patient_phone, patient_email))
            patient_id = cursor.lastrowid
            
            print(f"✅ Đã thêm bệnh nhân mới - ID: {patient_id}")
            
            # Tạo lịch hẹn
            cursor.execute('''
                INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, notes)
                VALUES (?, ?, ?, ?, 'Scheduled', ?)
            ''', (patient_id, doctor_id, appointment_date, appointment_time, notes))
            appointment_id = cursor.lastrowid
            
            # Lấy thông tin bác sĩ
            doctor = conn.execute('SELECT name, specialization FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
            
            print(f"👨‍⚕️ Thông tin bác sĩ: {doctor['name']} - {doctor['specialization']}")
            
            # Gửi email xác nhận TRƯỚC KHI commit
            if patient_email:
                print(f"📧 Đang gửi email xác nhận đến: {patient_email}")
                email_sent = send_appointment_email(patient_email, patient_name, doctor['name'], 
                                                  appointment_date, appointment_time, appointment_id)
                if email_sent:
                    print(f"✅ Đã gửi email xác nhận thành công!")
                else:
                    print(f"❌ Gửi email thất bại!")
            else:
                print("⚠️ Không có email để gửi xác nhận")
            
            conn.commit()
            print(f"✅ Đã tạo lịch hẹn - ID: {appointment_id}")
            
            conn.close()
            
            flash('Đăng ký lịch hẹn thành công! Chúng tôi đã gửi email xác nhận.', 'success')
            return redirect(url_for('public_appointment_success', appointment_id=appointment_id))
            
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"❌ Lỗi khi đăng ký lịch hẹn: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Lỗi khi đăng ký lịch hẹn: {str(e)}', 'error')
    
    return render_template('public_appointment.html', doctors=doctors, today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/public/appointment/success/<int:appointment_id>')
def public_appointment_success(appointment_id):
    """Trang thông báo đăng ký thành công"""
    conn = get_db_connection()
    appointment = conn.execute('''
        SELECT a.*, p.name as patient_name, d.name as doctor_name, d.specialization
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.id = ?
    ''', (appointment_id,)).fetchone()
    conn.close()
    
    if appointment:
        return render_template('appointment_success.html', 
                             appointment=appointment,
                             appointment_id=appointment_id)
    else:
        flash('Không tìm thấy lịch hẹn!', 'error')
        return redirect(url_for('public_appointment'))

# ==================== ROUTES SAU ĐĂNG NHẬP ====================

@app.route('/home')
@login_required
def home():
    """Trang chủ sau khi đăng nhập - phân theo role"""
    if current_user.role == 'patient':
        return redirect(url_for('patient_dashboard'))
    else:
        # Lấy dữ liệu thống kê cho admin/receptionist
        conn = get_db_connection()
        
        total_patients = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
        total_doctors = conn.execute('SELECT COUNT(*) FROM doctors').fetchone()[0]
        total_appointments = conn.execute('SELECT COUNT(*) FROM appointments').fetchone()[0]
        
        # Lấy lịch hẹn gần đây
        recent_appointments = conn.execute('''
            SELECT a.*, p.name as patient_name, d.name as doctor_name 
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            ORDER BY a.created_at DESC LIMIT 5
        ''').fetchall()
        
        conn.close()
        
        return render_template('home.html', 
                             total_patients=total_patients,
                             total_doctors=total_doctors,
                             total_appointments=total_appointments,
                             recent_appointments=recent_appointments)

@app.route('/patient/dashboard')
@patient_required
def patient_dashboard():
    """Dashboard dành cho bệnh nhân"""
    conn = get_db_connection()
    
    # Lấy thông tin bệnh nhân
    patient = conn.execute('''
        SELECT p.* FROM patients p 
        WHERE p.user_id = ?
    ''', (current_user.id,)).fetchone()
    
    if not patient:
        # Nếu chưa có patient record, tạo mới
        user_info = conn.execute('SELECT name, phone, email FROM users WHERE id = ?', (current_user.id,)).fetchone()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO patients (name, phone, email, user_id)
            VALUES (?, ?, ?, ?)
        ''', (user_info['name'], user_info['phone'], user_info['email'], current_user.id))
        patient_id = cursor.lastrowid
        conn.commit()
        patient = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    
    # Lấy lịch sử lịch hẹn
    appointments = conn.execute('''
        SELECT a.*, d.name as doctor_name, d.specialization
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    ''', (patient['id'],)).fetchall()
    
    doctors = conn.execute('SELECT * FROM doctors ORDER BY name').fetchall()
    conn.close()
    
    return render_template('patient_dashboard.html', 
                         patient=patient, 
                         appointments=appointments, 
                         doctors=doctors,
                         today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/patient/book_appointment', methods=['POST'])
@patient_required
def patient_book_appointment():
    """Bệnh nhân đặt lịch hẹn - GỬI EMAIL VỀ EMAIL ĐÃ ĐĂNG KÝ"""
    data = request.get_json()
    conn = get_db_connection()
    
    try:
        # Lấy patient_id từ user_id
        patient = conn.execute('SELECT id, name, email FROM patients WHERE user_id = ?', (current_user.id,)).fetchone()
        
        if not patient:
            return jsonify({'success': False, 'message': 'Không tìm thấy thông tin bệnh nhân'})
        
        # Tạo lịch hẹn
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, notes)
            VALUES (?, ?, ?, ?, 'Scheduled', ?)
        ''', (patient['id'], data['doctor_id'], data['date'], data['time'], data.get('notes', '')))
        
        appointment_id = cursor.lastrowid
        
        # Lấy thông tin bác sĩ
        doctor = conn.execute('SELECT name, specialization FROM doctors WHERE id = ?', (data['doctor_id'],)).fetchone()
        
        # GỬI EMAIL VỀ EMAIL ĐÃ ĐĂNG KÝ CỦA BỆNH NHÂN
        if patient['email']:
            print(f"📧 Đang gửi email xác nhận đến: {patient['email']}")
            email_sent = send_appointment_email(
                patient['email'], 
                patient['name'], 
                doctor['name'], 
                data['date'], 
                data['time'], 
                appointment_id
            )
            if email_sent:
                print(f"✅ Đã gửi email xác nhận thành công!")
            else:
                print(f"❌ Gửi email thất bại!")
        else:
            print("⚠️ Bệnh nhân không có email để gửi xác nhận")
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Đặt lịch hẹn thành công! Email xác nhận đã được gửi.'})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

# ==================== ROUTES MỚI CHO BỆNH NHÂN ====================

@app.route('/patient/update_appointment', methods=['POST'])
@patient_required
def patient_update_appointment():
    """Bệnh nhân cập nhật lịch hẹn"""
    data = request.get_json()
    conn = get_db_connection()
    
    try:
        # Kiểm tra xem lịch hẹn có thuộc về bệnh nhân này không
        appointment = conn.execute('''
            SELECT a.*, p.user_id 
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.id 
            WHERE a.id = ? AND p.user_id = ?
        ''', (data['appointment_id'], current_user.id)).fetchone()
        
        if not appointment:
            return jsonify({'success': False, 'message': 'Không tìm thấy lịch hẹn!'})
        
        # Kiểm tra trạng thái lịch hẹn
        if appointment['status'] not in ['Scheduled', 'Confirmed']:
            return jsonify({'success': False, 'message': 'Không thể chỉnh sửa lịch hẹn này!'})
        
        # Cập nhật lịch hẹn
        conn.execute('''
            UPDATE appointments 
            SET appointment_date = ?, appointment_time = ?, notes = ?
            WHERE id = ?
        ''', (data['date'], data['time'], data['notes'], data['appointment_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Cập nhật lịch hẹn thành công!'})
        
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/patient/cancel_appointment/<int:appointment_id>')
@patient_required
def patient_cancel_appointment(appointment_id):
    """Bệnh nhân hủy lịch hẹn"""
    conn = get_db_connection()
    
    try:
        # Kiểm tra xem lịch hẹn có thuộc về bệnh nhân này không
        appointment = conn.execute('''
            SELECT a.*, p.user_id 
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.id 
            WHERE a.id = ? AND p.user_id = ?
        ''', (appointment_id, current_user.id)).fetchone()
        
        if not appointment:
            return jsonify({'success': False, 'message': 'Không tìm thấy lịch hẹn!'})
        
        # Kiểm tra trạng thái lịch hẹn
        if appointment['status'] not in ['Scheduled', 'Confirmed']:
            return jsonify({'success': False, 'message': 'Không thể hủy lịch hẹn này!'})
        
        # Hủy lịch hẹn
        conn.execute('''
            UPDATE appointments 
            SET status = 'Cancelled'
            WHERE id = ?
        ''', (appointment_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Hủy lịch hẹn thành công!'})
        
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/patient/update_info', methods=['POST'])
@patient_required
def patient_update_info():
    """Bệnh nhân cập nhật thông tin cá nhân"""
    data = request.get_json()
    conn = get_db_connection()
    
    try:
        # Cập nhật thông tin bệnh nhân
        conn.execute('''
            UPDATE patients 
            SET name = ?, phone = ?, email = ?, address = ?, date_of_birth = ?, gender = ?
            WHERE user_id = ?
        ''', (data['name'], data['phone'], data['email'], data['address'], 
              data['date_of_birth'], data['gender'], current_user.id))
        
        # Cập nhật thông tin user
        conn.execute('''
            UPDATE users 
            SET name = ?, phone = ?, email = ?
            WHERE id = ?
        ''', (data['name'], data['phone'], data['email'], current_user.id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Cập nhật thông tin thành công!'})
        
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

# ==================== ROUTES QUẢN LÝ (STAFF) ====================

@app.route('/patients')
@staff_required
def patients():
    """Quản lý bệnh nhân - chỉ staff"""
    conn = get_db_connection()
    patients_data = conn.execute('SELECT * FROM patients ORDER BY created_at DESC').fetchall()
    
    patients_with_appointments = []
    for patient in patients_data:
        appointments = conn.execute('''
            SELECT a.*, d.name as doctor_name 
            FROM appointments a 
            JOIN doctors d ON a.doctor_id = d.id 
            WHERE a.patient_id = ? 
            ORDER BY a.appointment_date DESC
        ''', (patient['id'],)).fetchall()
        patients_with_appointments.append({
            **dict(patient), 
            'appointments': appointments
        })
    
    conn.close()
    return render_template('patients.html', patients=patients_with_appointments)

@app.route('/add_patient', methods=['POST'])
@staff_required
def add_patient():
    """Thêm bệnh nhân - chỉ staff"""
    data = request.get_json()
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO patients (name, phone, email, address, date_of_birth, gender)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['phone'], data['email'], data['address'], data['dob'], data['gender']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Thêm bệnh nhân thành công!'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/delete_patient/<int:patient_id>')
@staff_required
def delete_patient(patient_id):
    """Xóa bệnh nhân - chỉ staff"""
    conn = get_db_connection()
    try:
        # Kiểm tra xem bệnh nhân có lịch hẹn không
        appointments = conn.execute('SELECT COUNT(*) FROM appointments WHERE patient_id = ?', (patient_id,)).fetchone()[0]
        if appointments > 0:
            return jsonify({'success': False, 'message': 'Không thể xóa bệnh nhân đã có lịch hẹn!'})
        
        conn.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Xóa bệnh nhân thành công!'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/doctors')
@staff_required
def doctors():
    """Quản lý bác sĩ - chỉ staff"""
    conn = get_db_connection()
    doctors = conn.execute('SELECT * FROM doctors ORDER BY name').fetchall()
    conn.close()
    return render_template('doctors.html', doctors=doctors)

@app.route('/add_doctor', methods=['POST'])
@staff_required
def add_doctor():
    """Thêm bác sĩ - chỉ staff"""
    data = request.get_json()
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO doctors (name, specialization, phone, email, available_days, available_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['specialization'], data['phone'], data['email'], data['days'], data['time']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Thêm bác sĩ thành công!'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/delete_doctor/<int:doctor_id>')
@staff_required
def delete_doctor(doctor_id):
    """Xóa bác sĩ - chỉ staff"""
    conn = get_db_connection()
    try:
        # Kiểm tra xem bác sĩ có lịch hẹn không
        appointments = conn.execute('SELECT COUNT(*) FROM appointments WHERE doctor_id = ?', (doctor_id,)).fetchone()[0]
        if appointments > 0:
            return jsonify({'success': False, 'message': 'Không thể xóa bác sĩ đã có lịch hẹn!'})
        
        conn.execute('DELETE FROM doctors WHERE id = ?', (doctor_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Xóa bác sĩ thành công!'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/appointments')
@staff_required
def appointments():
    """Quản lý lịch hẹn - chỉ staff"""
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT a.*, p.name as patient_name, p.phone as patient_phone, d.name as doctor_name, d.specialization
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    ''').fetchall()
    
    patients = conn.execute('SELECT id, name, phone FROM patients').fetchall()
    doctors = conn.execute('SELECT * FROM doctors').fetchall()
    conn.close()
    
    return render_template('appointments.html', 
                         appointments=appointments, 
                         patients=patients, 
                         doctors=doctors)

@app.route('/add_appointment', methods=['POST'])
@staff_required
def add_appointment():
    """Thêm lịch hẹn - chỉ staff"""
    data = request.get_json()
    conn = get_db_connection()
    try:
        patient_id = data.get('patient_id')
        
        # Nếu là bệnh nhân mới
        if not patient_id and 'new_patient' in data:
            new_patient = data['new_patient']
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO patients (name, phone, email, created_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', (new_patient['name'], new_patient['phone'], new_patient.get('email')))
            patient_id = cursor.lastrowid
        
        # Tạo lịch hẹn
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (patient_id, data['doctor_id'], data['date'], data['time'], data['status'], data['notes']))
        
        appointment_id = cursor.lastrowid
        
        # Lấy thông tin bệnh nhân và bác sĩ để gửi email
        patient = conn.execute('SELECT name, email FROM patients WHERE id = ?', (patient_id,)).fetchone()
        doctor = conn.execute('SELECT name FROM doctors WHERE id = ?', (data['doctor_id'],)).fetchone()
        
        # Gửi email xác nhận nếu bệnh nhân có email
        if patient and patient['email']:
            print(f"📧 Đang gửi email xác nhận đến: {patient['email']}")
            email_sent = send_appointment_email(
                patient['email'], 
                patient['name'], 
                doctor['name'], 
                data['date'], 
                data['time'], 
                appointment_id
            )
            if email_sent:
                print(f"✅ Đã gửi email xác nhận thành công!")
            else:
                print(f"❌ Gửi email thất bại!")
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Đặt lịch hẹn thành công!'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/update_appointment_status', methods=['POST'])
@staff_required
def update_appointment_status():
    """Cập nhật trạng thái lịch hẹn - chỉ staff"""
    data = request.get_json()
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE appointments SET status = ? WHERE id = ?
        ''', (data['status'], data['appointment_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Cập nhật trạng thái thành công!'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/delete_appointment/<int:appointment_id>')
@staff_required
def delete_appointment(appointment_id):
    """Xóa lịch hẹn - chỉ staff"""
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Xóa lịch hẹn thành công!'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

# ==================== ROUTES QUẢN TRỊ (ADMIN ONLY) ====================

@app.route('/users')
@admin_required
def users():
    """Quản lý người dùng - chỉ admin"""
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('users.html', users=users)

# ==================== DASHBOARD DATA ====================

@app.route('/dashboard_data')
@login_required
def dashboard_data():
    """Dữ liệu dashboard - cho tất cả user đã đăng nhập"""
    conn = get_db_connection()
    
    total_patients = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
    total_doctors = conn.execute('SELECT COUNT(*) FROM doctors').fetchone()[0]
    total_appointments = conn.execute('SELECT COUNT(*) FROM appointments').fetchone()[0]
    today_appointments = conn.execute('''
        SELECT COUNT(*) FROM appointments 
        WHERE appointment_date = date('now')
    ''').fetchone()[0]
    
    recent_appointments = conn.execute('''
        SELECT a.*, p.name as patient_name, d.name as doctor_name 
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.created_at DESC LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'recent_appointments': [
            {
                'id': app['id'],
                'patient_name': app['patient_name'],
                'doctor_name': app['doctor_name'],
                'date': app['appointment_date'],
                'time': app['appointment_time'],
                'status': app['status']
            }
            for app in recent_appointments
        ]
    })

# ==================== UTILITY FUNCTIONS ====================

def send_appointment_email(patient_email, patient_name, doctor_name, date, time, appointment_id):
    """Gửi email xác nhận lịch hẹn"""
    try:
        # Kiểm tra email có hợp lệ không
        if not patient_email or '@' not in patient_email:
            print(f"❌ Email không hợp lệ: {patient_email}")
            return False
            
        subject = f"Xác nhận lịch hẹn khám bệnh - Mã #{appointment_id}"
        
        # Format ngày giờ đẹp hơn
        appointment_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ 
                    font-family: 'Arial', sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    margin: 0;
                    padding: 0;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 0 auto; 
                    padding: 20px;
                    background: #f9f9f9;
                }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 30px; 
                    text-align: center; 
                    border-radius: 10px 10px 0 0; 
                }}
                .content {{ 
                    padding: 30px; 
                    background: white;
                    border-radius: 0 0 10px 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .info {{ 
                    background: #f8f9fa; 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 8px; 
                    border-left: 4px solid #667eea;
                }}
                .footer {{ 
                    text-align: center; 
                    margin-top: 30px; 
                    padding: 20px; 
                    color: #666;
                    font-size: 14px;
                }}
                .success-badge {{
                    background: #28a745;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                ul {{
                    padding-left: 20px;
                }}
                li {{
                    margin-bottom: 8px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏥 MEDICAL APPOINTMENT</h1>
                    <p>Hệ thống đặt lịch khám bệnh trực tuyến</p>
                </div>
                <div class="content">
                    <h2>XÁC NHẬN LỊCH HẸN THÀNH CÔNG</h2>
                    
                    <p>Kính chào <strong>{patient_name}</strong>,</p>
                    <p>Cảm ơn bạn đã đăng ký lịch hẹn khám bệnh tại Phòng khám MEDICAL.</p>
                    
                    <div class="info">
                        <h3>📋 THÔNG TIN LỊCH HẸN</h3>
                        <p><strong>Mã lịch hẹn:</strong> <span style="color: #667eea; font-weight: bold; font-size: 18px;">#{appointment_id}</span></p>
                        <p><strong>Bác sĩ:</strong> {doctor_name}</p>
                        <p><strong>Ngày hẹn:</strong> {appointment_date}</p>
                        <p><strong>Giờ hẹn:</strong> {time}</p>
                        <p><strong>Trạng thái:</strong> <span class="success-badge">ĐÃ XÁC NHẬN</span></p>
                    </div>
                    
                    <div class="info">
                        <h3>📝 HƯỚNG DẪN & LƯU Ý</h3>
                        <ul>
                            <li>⏰ <strong>Vui lòng có mặt trước 15 phút</strong> để làm thủ tục</li>
                            <li>🆔 <strong>Mang theo CMND/CCCD</strong> và thẻ BHYT (nếu có)</li>
                            <li>💰 Chuẩn bị phí khám bệnh theo quy định</li>
                            <li>📞 <strong>Hotline hỗ trợ: 1900-1234</strong> (7:00-20:00)</li>
                            <li>📍 <strong>Địa chỉ:</strong> 123 Nguyễn Trãi, Quận 1, TP.HCM</li>
                            <li>🔄 Nếu không thể đến, vui lòng hủy lịch trước 24h</li>
                        </ul>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                        <h4 style="color: #856404; margin-top: 0;">💡 Lời khuyên sức khỏe</h4>
                        <p style="margin-bottom: 0;">Nghỉ ngơi đầy đủ, uống đủ nước và ăn nhẹ trước khi khám bệnh.</p>
                    </div>
                    
                    <p style="margin-top: 30px;">Trân trọng,<br>
                    <strong>Đội ngũ Phòng khám Đa khoa MEDICAL</strong><br>
                    <em>"Vì sức khỏe cộng đồng"</em></p>
                </div>
                <div class="footer">
                    <p>© 2024 Phòng khám Đa khoa MEDICAL. All rights reserved.</p>
                    <p>Hotline: 1900-1234 | Email: info@medical.com | Website: www.medical.com</p>
                    <p><em>Đây là email tự động, vui lòng không trả lời.</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject=subject,
            recipients=[patient_email],
            html=html_body
        )
        
        mail.send(msg)
        print(f"✅ Đã gửi email xác nhận thành công đến: {patient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi gửi email đến {patient_email}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/test-email-detailed')
def test_email_detailed():
    """Route test gửi email chi tiết"""
    try:
        test_email = "anhnguyen0934422067@gmail.com"  # Thay bằng email thật của bạn để test
        
        # Test với dữ liệu mẫu
        email_sent = send_appointment_email(
            test_email, 
            "Nguyễn Văn Test", 
            "BS. Nguyễn Văn A - Khoa Nội", 
            "2024-12-25", 
            "14:30", 
            999
        )
        
        if email_sent:
            return f'''
            <h1>✅ Email sent successfully!</h1>
            <p>Check your email: <strong>{test_email}</strong></p>
            <p>Check spam folder if not in inbox.</p>
            <a href="/" class="btn btn-primary">Back to Home</a>
            '''
        else:
            return f'''
            <h1>❌ Failed to send email</h1>
            <p>Could not send to: <strong>{test_email}</strong></p>
            <p>Check your email configuration and try again.</p>
            <a href="/" class="btn btn-primary">Back to Home</a>
            '''
            
    except Exception as e:
        return f'''
        <h1>❌ Error in test</h1>
        <p>Error: {str(e)}</p>
        <p>Check your email configuration in app.py</p>
        <a href="/" class="btn btn-primary">Back to Home</a>
        '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # CHỈ TẠO DATABASE MỚI NẾU CHƯA TỒN TẠI - KHÔNG XÓA DATABASE CŨ
    if not os.path.exists(DATABASE):
        print("📦 Đang khởi tạo database mới...")
        init_db()
    else:
        print("✅ Đang sử dụng database hiện có:", DATABASE)
    
    check_users()  # Kiểm tra users trong database
    print("🚀 Starting Flask application...")
    print("🏠 Trang chủ: http://localhost:5000")
    print("🔐 Đăng ký: http://localhost:5000/register") 
    print("🔐 Đăng nhập: http://localhost:5000/login")
    print("📧 Email test: http://localhost:5000/test-email-detailed")
    print("🌐 Public appointment: http://localhost:5000/public/appointment")
    print("👨‍💼 Admin: admin/admin123")
    print("👩‍💼 Reception: reception/reception123")
    print("💾 Database file:", DATABASE)
    app.run(debug=True, host='0.0.0.0', port=5000)