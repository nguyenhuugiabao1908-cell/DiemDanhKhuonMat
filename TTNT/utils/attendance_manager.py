    # utils/attendance_manager.py

from __future__ import annotations

from typing import List, Tuple

from utils.database import DatabaseManager
from utils.helpers import (
    current_date,
    current_time,
    export_csv,
    export_excel,
    logger,
    save_attendance_csv,
)


class AttendanceManager:
    """
    Attendance manager.
    """

    def __init__(self) -> None:
        self.db = DatabaseManager()

    def mark_attendance(
        self,
        student_id: str,
        subject_id: str | None = None,
    ) -> Tuple[bool, str]:
        """
        Mark attendance once per day.
        """

        try:
            today = current_date()
            attendance_time = current_time()
            student = self.db.get_student(student_id)

            if student is None:
                return False, "Không tìm thấy sinh viên."

            if subject_id is None:
                subject_id = self.db.get_current_subject(student["class_name"])
            if subject_id is None:
                return False, "Hiện không có môn học đang diễn ra."

            if self.db.attendance_exists(student_id, today, subject_id):
                return False, "Đã điểm danh môn học này hôm nay."

            status = self.db.get_attendance_status(
                student["class_name"], subject_id, today, attendance_time
            )
            if status == "Closed":
                return False, "Đã hết thời gian điểm danh."

            self.db.mark_attendance(
                student_id=student_id,
                subject_id=subject_id,
                attendance_date=today,
                attendance_time=attendance_time,
                status=status,
            )

            save_attendance_csv(
                student_id=student["student_id"],
                full_name=student["full_name"],
                class_name=student["class_name"],
                status=status,
            )

            logger.info(
                "Attendance success: %s",
                student_id,
            )

            message = "Điểm danh muộn." if status == "Late" else "Điểm danh thành công."
            return True, message

        except Exception as exc:

            logger.exception(exc)

            return False, "Có lỗi xảy ra."

    # -----------------------------------------------------

    def get_history(self) -> List:
        """
        Get attendance history.
        """

        return self.db.attendance_history()

    # -----------------------------------------------------

    def export_to_excel(
        self,
        output_path: str,
    ) -> None:

        rows = self.get_history()

        data = [
            (
                row["student_id"],
                row["full_name"],
                row["class_name"],
                row["attendance_date"],
                row["attendance_time"],
                row["status"],
            )
            for row in rows
        ]

        export_excel(
            data,
            output_path,
        )

        logger.info(
            "Export Excel: %s",
            output_path,
        )

    # -----------------------------------------------------

    def export_to_csv(
        self,
        output_path: str,
    ) -> None:

        rows = self.get_history()

        data = [
            (
                row["student_id"],
                row["full_name"],
                row["class_name"],
                row["attendance_date"],
                row["attendance_time"],
                row["status"],
            )
            for row in rows
        ]

        export_csv(
            data,
            output_path,
        )

        logger.info(
            "Export CSV: %s",
            output_path,
        )

    # -----------------------------------------------------

    def total_attendance(self) -> int:
        """
        Total attendance records.
        """

        return self.db.total_attendance()

    # -----------------------------------------------------

    def today_attendance(self) -> int:
        """
        Number of students attended today.
        """

        rows = self.db.fetchall(
            """
            SELECT COUNT(*) AS total
            FROM attendance
            WHERE attendance_date = ?
            """,
            (current_date(),),
        )

        return int(rows[0]["total"])