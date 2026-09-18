# utils/database.py

from __future__ import annotations

import pickle
from datetime import datetime, timedelta
from typing import Any, Optional

from database.database import Database
from models.student import Student
from utils.helpers import logger


class DatabaseManager:
    """
    Database helper class.
    """

    def __init__(self) -> None:
        self.db = Database()
        self.conn = self.db.connect()
        self._create_extra_tables()

    def _create_extra_tables(self) -> None:
        """Tạo bảng class_schedules để lưu cấu hình lịch học"""
        try:
            self.execute(
                """
                CREATE TABLE IF NOT EXISTS class_schedules (
                    class_name TEXT PRIMARY KEY,
                    start_date TEXT,
                    learning_days TEXT
                )
                """
            )
            # Tự động chèn thêm cột end_date nếu bảng cũ chưa có
            try:
                self.execute("ALTER TABLE class_schedules ADD COLUMN end_date TEXT")
            except:
                pass # Cột đã tồn tại, bỏ qua
        except Exception as exc:
            from utils.helpers import logger
            logger.exception("Could not create extra tables: %s", exc)

    # ==========================================================
    # Generic
    # ==========================================================

    def execute(
        self,
        query: str,
        params: tuple = (),
    ) -> None:
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()

    def fetchone(
        self,
        query: str,
        params: tuple = (),
    ) -> Optional[Any]:
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def fetchall(
        self,
        query: str,
        params: tuple = (),
    ) -> list[Any]:
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    # ==========================================================
    # Admin
    # ==========================================================

    def get_admin(
        self,
        username: str,
    ):
        return self.fetchone(
            """
            SELECT *
            FROM admins
            WHERE username=?
            """,
            (username,),
        )

    # ==========================================================
    # Student CRUD
    # ==========================================================

    def add_student(
        self,
        student: Student,
    ) -> bool:
        try:
            self.execute(
                """
                INSERT INTO students(
                    student_id,
                    full_name,
                    class_name,
                    faculty,
                    email,
                    phone
                )
                VALUES(?,?,?,?,?,?)
                """,
                (
                    student.student_id,
                    student.full_name,
                    student.class_name,
                    student.faculty,
                    student.email,
                    student.phone,
                ),
            )

            logger.info(
                "Added student %s",
                student.student_id,
            )
            return True

        except Exception as exc:
            logger.exception(exc)
            return False

    # ----------------------------------------------------------

    def update_student(
        self,
        student: Student,
    ) -> bool:
        try:
            self.execute(
                """
                UPDATE students
                SET
                    full_name=?,
                    class_name=?,
                    faculty=?,
                    email=?,
                    phone=?
                WHERE student_id=?
                """,
                (
                    student.full_name,
                    student.class_name,
                    student.faculty,
                    student.email,
                    student.phone,
                    student.student_id,
                ),
            )
            return True

        except Exception as exc:
            logger.exception(exc)
            return False

    # ----------------------------------------------------------

    def delete_student(
        self,
        student_id: str,
    ) -> bool:

        try:

            self.execute(
                """
                DELETE FROM students
                WHERE student_id=?
                """,
                (student_id,),
            )

            logger.info(
                "Deleted student %s",
                student_id,
            )

            return True

        except Exception as exc:

            logger.exception(exc)

            return False

    # ----------------------------------------------------------

    def get_student(
        self,
        student_id: str,
    ):

        return self.fetchone(
            """
            SELECT *
            FROM students
            WHERE student_id=?
            """,
            (student_id,),
        )

    # ----------------------------------------------------------

    def get_students(self):

        return self.fetchall(
            """
            SELECT *
            FROM students
            ORDER BY full_name
            """
        )

    # ==========================================================
    # Face Encoding
    # ==========================================================

    def save_encoding(
        self,
        student_id: str,
        encoding,
        image_path: str,
    ) -> bool:

        try:

            binary = pickle.dumps(encoding)

            if self.fetchone(
                """
                SELECT id
                FROM face_encodings
                WHERE student_id=?
                """,
                (student_id,),
            ):

                self.execute(
                    """
                    UPDATE face_encodings
                    SET
                        encoding=?,
                        image_path=?
                    WHERE student_id=?
                    """,
                    (
                        binary,
                        image_path,
                        student_id,
                    ),
                )

            else:

                self.execute(
                    """
                    INSERT INTO face_encodings(
                        student_id,
                        encoding,
                        image_path
                    )
                    VALUES(?,?,?)
                    """,
                    (
                        student_id,
                        binary,
                        image_path,
                    ),
                )

            logger.info(
                "Saved encoding %s",
                student_id,
            )

            return True

        except Exception as exc:

            logger.exception(exc)

            return False

    # ----------------------------------------------------------

    def load_encodings(self):

        rows = self.fetchall(
            """
            SELECT *
            FROM face_encodings
            """
        )

        encodings = []

        for row in rows:

            encodings.append(
                {
                    "student_id": row["student_id"],
                    "encoding": pickle.loads(
                        row["encoding"]
                    ),
                    "image_path": row["image_path"],
                }
            )

        return encodings

    # ==========================================================
    # Attendance (Đã nâng cấp để hỗ trợ Môn học)
    # ==========================================================

    def attendance_exists(
        self,
        student_id: str,
        attendance_date: str,
        subject_id: str,
    ) -> bool:
        row = self.fetchone(
            """
            SELECT id
            FROM attendance
            WHERE student_id=?
            AND attendance_date=?
            AND subject_id=?
            """,
            (student_id, attendance_date, subject_id),
        )
        return row is not None

    # ----------------------------------------------------------

    def mark_attendance(
        self,
        student_id: str,
        subject_id: str,
        attendance_date: str,
        attendance_time: str,
        status: str = "Present",
    ) -> bool:
        try:
            self.execute(
                """
                INSERT INTO attendance(
                    student_id,
                    subject_id,
                    attendance_date,
                    attendance_time,
                    status
                )
                VALUES(?,?,?,?,?)
                """,
                (student_id, subject_id, attendance_date, attendance_time, status),
            )
            logger.info("Attendance: %s for subject %s", student_id, subject_id)
            return True
        except Exception as exc:
            logger.exception(exc)
            return False

    # ----------------------------------------------------------

    def attendance_history(self):
        return self.fetchall(
            """
            SELECT
                attendance.student_id,
                students.full_name,
                students.class_name,
                subjects.subject_name,
                attendance.attendance_date,
                attendance.attendance_time,
                attendance.status
            FROM attendance
            INNER JOIN students ON students.student_id = attendance.student_id
            INNER JOIN subjects ON subjects.subject_id = attendance.subject_id
            ORDER BY attendance.id DESC
            """
        )

    # ==========================================================
    # Dashboard
    # ==========================================================

    def total_students(self) -> int:

        row = self.fetchone(
            """
            SELECT COUNT(*) AS total
            FROM students
            """
        )

        return int(row["total"])

    def total_attendance(self) -> int:

        row = self.fetchone(
            """
            SELECT COUNT(*) AS total
            FROM attendance
            """
        )

        return int(row["total"])

    def total_registered_faces(self) -> int:

        row = self.fetchone(
            """
            SELECT COUNT(*) AS total
            FROM face_encodings
            """
        )

        return int(row["total"])

    def get_dashboard_stats(self) -> dict:
        # Import hàm lấy ngày hiện tại từ helpers
        from utils.helpers import current_date
        
        # Lấy các tổng số sẵn có
        total_stu = self.total_students()
        total_att = self.total_attendance()
        
        # Đếm số sinh viên ĐÃ điểm danh hôm nay (tránh đếm trùng)
        row = self.fetchone(
            """
            SELECT COUNT(DISTINCT student_id) AS total 
            FROM attendance 
            WHERE attendance_date = ?
            """,
            (current_date(),)
        )
        attended_today = int(row["total"]) if row else 0
        
        # Số sinh viên CHƯA điểm danh = Tổng số - Đã điểm danh
        absent_today = max(0, total_stu - attended_today)
        
        # Trả về từ điển khớp với yêu cầu của dashboard.py
        return {
            "total_students": total_stu,
            "attended_today": attended_today,
            "absent_today": absent_today,
            "total_attendance": total_att
        }

    # ==========================
    # Admin Authentication
    # ==========================

    def verify_admin(self, username: str, password: str) -> bool:
        """
        Kiểm tra tài khoản quản trị.
        Mặc định: admin / admin123
        """
        return username == "admin" and password == "admin123"

    def change_admin_password(self, old_password: str, new_password: str) -> bool:
        """
        Đổi mật khẩu admin (demo).
        """
        if old_password == "admin123":
            return True
        return False

    # ==========================================================
    # Class Schedules (Cấu hình Lịch học)
    # ==========================================================

    def save_class_schedule(self, class_name: str, start_date: str, end_date: str, learning_days: str) -> bool:
        """Lưu lịch học của một lớp kèm Ngày bắt đầu và Ngày kết thúc"""
        try:
            from utils.helpers import logger
            self.execute(
                """
                REPLACE INTO class_schedules (class_name, start_date, end_date, learning_days)
                VALUES (?, ?, ?, ?)
                """,
                (class_name, start_date, end_date, learning_days)
            )
            return True
        except Exception as e:
            logger.exception("Error saving schedule: %s", e)
            return False

    def get_class_schedule(self, class_name: str) -> dict | None:
        """Lấy lịch học của một lớp"""
        row = self.fetchone(
            "SELECT * FROM class_schedules WHERE class_name = ?",
            (class_name,),
        )
        return dict(row) if row else None

    # ==========================================================
    # Quản lý Môn học (Subjects)
    # ==========================================================
    def get_subjects(self):
        """Lấy danh sách tất cả môn học"""
        return self.fetchall("SELECT * FROM subjects")

    def add_subject(self, subject_id: str, subject_name: str) -> bool:
        """Thêm môn học mới"""
        try:
            self.execute(
                "INSERT INTO subjects (subject_id, subject_name) VALUES (?, ?)",
                (subject_id, subject_name)
            )
            return True
        except Exception as e:
            logger.exception(f"Lỗi thêm môn học: {e}")
            return False

    def delete_subject(self, subject_id: str):
        """Xóa môn học"""
        self.execute("DELETE FROM subjects WHERE subject_id = ?", (subject_id,))

    # ==========================================================
    # Quản lý Lịch học (Schedules)
    # ==========================================================
    def get_schedules(self, class_name: str = None):
        """Lấy lịch học. Nếu truyền class_name thì chỉ lấy của lớp đó."""
        if class_name:
            return self.fetchall("SELECT * FROM schedules WHERE class_name = ?", (class_name,))
        return self.fetchall("SELECT * FROM schedules")

    def add_schedule(self, class_name: str, subject_id: str, day_of_week: int, start_time: str, end_time: str) -> bool:
        """Thêm lịch học vào thời khóa biểu"""
        try:
            self.execute(
                "INSERT INTO schedules (class_name, subject_id, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
                (class_name, subject_id, day_of_week, start_time, end_time)
            )
            return True
        except Exception as e:
            logger.exception(f"Lỗi thêm lịch học: {e}")
            return False

    def delete_schedule(self, schedule_id: int):
        """Xóa một lịch học"""
        self.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))

    # ==========================================================
    # HÀM AI NỘI SOI: TÌM MÔN HỌC ĐANG DIỄN RA
    # ==========================================================
    def get_current_subject(self, class_name: str) -> str | None:
        """
        AI sẽ gọi hàm này và truyền vào Tên Lớp.
        Hệ thống tự động soi đồng hồ xem ngay giây phút này lớp đó đang học môn gì.
        Trả về: subject_id (Mã môn) hoặc None (Nếu đang rảnh/Không có lịch).
        """
        schedule = self.get_current_schedule(class_name)
        return schedule["subject_id"] if schedule else None

    def get_current_schedule(self, class_name: str):
        """Trả về lịch học đang diễn ra của một lớp."""
        now = datetime.now()
        schedules = self.fetchall(
            "SELECT * FROM schedules WHERE class_name = ? AND day_of_week = ?",
            (class_name, now.weekday()),
        )

        current_time = now.strftime("%H:%M:%S")
        return next(
            (
                schedule
                for schedule in schedules
                if schedule["start_time"] <= current_time[:5] <= schedule["end_time"]
            ),
            None,
        )

    def get_attendance_status(
        self,
        class_name: str,
        subject_id: str,
        attendance_date: str,
        attendance_time: str,
        late_minutes: int = 10,
        manual: bool = False,
    ) -> str:
        """Trả về Present, Late hoặc Closed theo khung điểm danh của buổi học."""
        date_value = datetime.strptime(attendance_date, "%Y-%m-%d")
        schedules = self.fetchall(
            """
            SELECT start_time
            FROM schedules
            WHERE class_name = ? AND subject_id = ? AND day_of_week = ?
            """,
            (class_name, subject_id, date_value.weekday()),
        )

        actual_time = datetime.strptime(
            f"{attendance_date} {attendance_time}", "%Y-%m-%d %H:%M:%S"
        )
        for schedule in schedules:
            start_time = datetime.strptime(
                f"{attendance_date} {schedule['start_time']}", "%Y-%m-%d %H:%M"
            )
            if actual_time < start_time:
                continue
            if actual_time <= start_time + timedelta(minutes=5):
                return "Present"
            if actual_time <= start_time + timedelta(minutes=late_minutes + 5):
                return "Late"
            if manual:
                return "Late"

        return "Closed"