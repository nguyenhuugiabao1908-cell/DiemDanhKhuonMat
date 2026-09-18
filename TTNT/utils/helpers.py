# utils/helpers.py

from __future__ import annotations

import csv
import logging
import os
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Iterable

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
FACE_DIR = DATA_DIR / "faces"
LOG_DIR = BASE_DIR / "logs"
ASSET_DIR = BASE_DIR / "assets"

CSV_FILE = DATA_DIR / "attendance.csv"


def ensure_project_structure(base_dir=None) -> None:
    """
    Tạo cấu trúc thư mục của dự án (Tích hợp luôn ensure_directories).
    """
    if base_dir is None:
        base_dir = BASE_DIR
    else:
        base_dir = Path(base_dir)

    (base_dir / "data").mkdir(parents=True, exist_ok=True)
    (base_dir / "data" / "faces").mkdir(parents=True, exist_ok=True)
    (base_dir / "logs").mkdir(parents=True, exist_ok=True)
    (base_dir / "assets").mkdir(parents=True, exist_ok=True)

    csv_file = base_dir / "data" / "attendance.csv"

    if not csv_file.exists():
        with open(csv_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "Student ID",
                    "Full Name",
                    "Class",
                    "Date",
                    "Time",
                    "Status",
                ]
            )

# Hỗ trợ tên hàm cũ nếu có nơi khác gọi
ensure_directories = ensure_project_structure

def setup_logging(log_dir=None) -> logging.Logger:
    """
    Khởi tạo logging và trả về logger.
    """
    if log_dir is None:
        log_dir = LOG_DIR
    else:
        log_dir = Path(log_dir)
        
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("attendance")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    log_file = log_dir / (
        datetime.now().strftime("%Y-%m-%d") + ".log"
    )

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Tạo sẵn logger cho các module khác import trực tiếp
logger = setup_logging()

def current_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def current_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def student_face_folder(student_id: str) -> Path:
    folder = FACE_DIR / student_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_attendance_csv(
    student_id: str,
    full_name: str,
    class_name: str,
    status: str = "Present",
) -> None:
    """
    Ghi điểm danh ra CSV.
    """
    ensure_directories()

    with open(
        CSV_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                student_id,
                full_name,
                class_name,
                current_date(),
                current_time(),
                status,
            ]
        )


def export_excel(
    rows: Iterable,
    output_path: str,
) -> None:
    """
    Xuất Excel.
    """
    dataframe = pd.DataFrame(
        rows,
        columns=[
            "Student ID",
            "Full Name",
            "Class",
            "Date",
            "Time",
            "Status",
        ],
    )
    dataframe.to_excel(
        output_path,
        index=False,
    )


def export_csv(
    rows: Iterable,
    output_path: str,
) -> None:
    dataframe = pd.DataFrame(
        rows,
        columns=[
            "Student ID",
            "Full Name",
            "Class",
            "Date",
            "Time",
            "Status",
        ],
    )
    dataframe.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )


def resource_path(*paths: str) -> str:
    """
    Lấy đường dẫn tuyệt đối.
    """
    return str(BASE_DIR.joinpath(*paths))


def image_path(
    student_id: str,
    image_name: str,
) -> str:
    folder = student_face_folder(student_id)
    return str(folder / image_name)


def clear_student_images(
    student_id: str,
) -> None:
    folder = student_face_folder(student_id)
    for file in folder.glob("*"):
        try:
            file.unlink()
        except Exception as exc:
            logger.exception(exc)


def delete_file(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def is_email(email: str) -> bool:
    return (
        "@" in email
        and "." in email
        and len(email) >= 5
    )


def is_phone(phone: str) -> bool:
    return phone.isdigit() and 9 <= len(phone) <= 12


def today() -> datetime:
    return datetime.now()


def format_datetime(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def modern_theme_colors() -> dict:
    """
    Trả về bảng màu giao diện.
    Đã được bổ sung thuộc tính 'sidebar' bị thiếu.
    """
    return {
        # Background
        "bg": "#F5F7FA",
        "background": "#F5F7FA",
        "surface": "#FFFFFF",
        "card": "#FFFFFF",

        # Primary
        "primary": "#1976D2",
        "primary_dark": "#1565C0",
        "primary_light": "#42A5F5",

        # Secondary
        "secondary": "#455A64",
        "secondary_dark": "#263238",
        "secondary_light": "#78909C",

        # Accent
        "accent": "#1976D2",

        # Text
        "text": "#212121",
        "text_light": "#757575",
        "muted": "#6C757D",
        "white": "#FFFFFF",
        "black": "#000000",

        # Status
        "success": "#2E7D32",
        "danger": "#D32F2F",
        "error": "#D32F2F",
        "warning": "#ED6C02",
        "info": "#0288D1",

        # Border
        "border": "#D0D7DE",
        "border_light": "#E5E7EB",

        # Button
        "button_fg": "#FFFFFF",
        "hover": "#1565C0",
        "disabled": "#BDBDBD",

        # Misc
        "shadow": "#DDDDDD",
        "light": "#F8F9FA",
        "dark": "#212121",
        
        # SỬA LỖI Ở ĐÂY: Thêm màu cho thanh menu bên trái
        "sidebar": "#263238",
    }


# ==========================
# Giao diện (GUI) & Tương thích API
# ==========================

def validate_email(email: str) -> bool:
    return is_email(email)


def validate_phone(phone: str) -> bool:
    return is_phone(phone)


def center_window(window: tk.Tk | tk.Toplevel, width: int = 900, height: int = 600) -> None:
    """
    Căn giữa cửa sổ trên màn hình.
    """
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def safe_showinfo(title: str, message: str) -> None:
    try:
        messagebox.showinfo(title, message)
    except Exception:
        print(f"[INFO] {title}: {message}")


def safe_showwarning(title: str, message: str) -> None:
    try:
        messagebox.showwarning(title, message)
    except Exception:
        print(f"[WARNING] {title}: {message}")


def safe_showerror(title: str, message: str) -> None:
    try:
        messagebox.showerror(title, message)
    except Exception:
        print(f"[ERROR] {title}: {message}")