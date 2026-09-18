import bcrypt
from database import Database

db = Database()
conn = db.connect()
cursor = conn.cursor()

# 1. BẢNG QUẢN TRỊ VIÊN
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# 2. BẢNG SINH VIÊN
cursor.execute("""
CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    class_name TEXT NOT NULL,
    faculty TEXT,
    gender TEXT,
    birthday TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 3. BẢNG KHUÔN MẶT
cursor.execute("""
CREATE TABLE IF NOT EXISTS face_encodings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT UNIQUE NOT NULL,
    encoding BLOB NOT NULL,
    image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE
)
""")

# ==========================================
# CÁC BẢNG MỚI ĐƯỢC THÊM VÀO CHO TÍNH NĂNG MÔN HỌC
# ==========================================

# 4. BẢNG MÔN HỌC (MỚI)
cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects(
    subject_id TEXT PRIMARY KEY,
    subject_name TEXT NOT NULL
)
""")

# 5. BẢNG LỊCH HỌC / THỜI KHÓA BIỂU (MỚI)
cursor.execute("""
CREATE TABLE IF NOT EXISTS schedules(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    day_of_week INTEGER NOT NULL, /* 0: Thứ 2, 1: Thứ 3, ..., 6: Chủ Nhật */
    start_time TEXT NOT NULL, /* VD: '07:00' */
    end_time TEXT NOT NULL,   /* VD: '09:30' */
    FOREIGN KEY(subject_id) 
        REFERENCES subjects(subject_id) 
        ON DELETE CASCADE
)
""")

# 6. BẢNG LỊCH SỬ ĐIỂM DANH (ĐÃ ĐƯỢC NÂNG CẤP)
# Bỏ UNIQUE(student_id, date) cũ, thêm cột subject_id
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject_id TEXT NOT NULL, 
    attendance_date TEXT NOT NULL,
    attendance_time TEXT NOT NULL,
    status TEXT DEFAULT 'Present',
    UNIQUE(student_id, attendance_date, subject_id), /* 1 ngày học 2 môn khác nhau thì được */
    FOREIGN KEY(student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,
    FOREIGN KEY(subject_id)
        REFERENCES subjects(subject_id)
        ON DELETE CASCADE
)
""")

# ==========================================
# KHỞI TẠO TÀI KHOẢN ADMIN MẶC ĐỊNH
# ==========================================
cursor.execute(
    "SELECT * FROM admins WHERE username=?",
    ("admin",)
)

admin = cursor.fetchone()

if admin is None:
    password = bcrypt.hashpw(
        "admin123".encode(),
        bcrypt.gensalt()
    ).decode()

    cursor.execute(
        """
        INSERT INTO admins(username,password)
        VALUES(?,?)
        """,
        ("admin", password)
    )

conn.commit()
conn.close()

print("Database initialized successfully with Subject & Schedule modules.")