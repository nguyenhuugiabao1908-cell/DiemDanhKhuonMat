# StudentAttendance/gui/attendance.py
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox
import cv2
import time
from datetime import datetime
from PIL import Image, ImageTk

from utils.attendance_manager import AttendanceManager
from utils.camera import Camera
from utils.database import DatabaseManager
from utils.helpers import modern_theme_colors, current_date, current_time
from utils.recognizer import Recognizer
from utils.face_encoder import FaceEncoder


class AttendanceFrame:
    def __init__(
        self,
        parent: tk.Widget,
        db: DatabaseManager,
        base_dir: Path,
        on_marked=None,
    ) -> None:
        self.parent = parent
        self.db = db
        self.base_dir = base_dir
        self.on_marked = on_marked
        self.colors = modern_theme_colors()

        self.camera = Camera()
        
        encoder = FaceEncoder()
        known_encodings, known_student_ids = encoder.load_all_encodings()
        
        self.recognizer = Recognizer(known_encodings, known_student_ids)
        self.attendance_manager = AttendanceManager()

        self.running = False
        self.preview_label: tk.Label | None = None
        
        self.status_var = tk.StringVar(value="Sẵn sàng")
        self.cam_status_var = tk.StringVar(value="Camera: ✗")
        self.detected_var = tk.StringVar(value="Phát hiện: 0")
        self.recognized_var = tk.StringVar(value="Nhận diện: 0")

        self.session_cache = {}
        self.frame_count = 0        
        self.current_faces = []     

        self._build_ui()

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.parent, bg=self.colors["bg"])
        wrapper.pack(fill="both", expand=True)

        left = tk.Frame(wrapper, bg="white", highlightthickness=1, highlightbackground=self.colors["border"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = tk.Frame(wrapper, bg="white", highlightthickness=1, highlightbackground=self.colors["border"], width=320)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)

        tk.Label(left, text="Điểm danh realtime", bg="white", fg=self.colors["text"], font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=16, pady=(16, 8))

        self.preview_label = tk.Label(left, bg="#111827")
        self.preview_label.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        tk.Label(right, text="Điều khiển", bg="white", fg=self.colors["text"], font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(16, 12))

        tk.Button(right, text="Start", command=self.start, bg="#16a34a", fg="white", bd=0, padx=10, pady=10, cursor="hand2", font=("Segoe UI", 10, "bold")).pack(fill="x", padx=16, pady=4)
        tk.Button(right, text="Stop", command=self.stop, bg="#dc2626", fg="white", bd=0, padx=10, pady=10, cursor="hand2", font=("Segoe UI", 10, "bold")).pack(fill="x", padx=16, pady=4)
        tk.Button(right, text="Reload Encodings", command=self.reload_encodings, bg="#2563eb", fg="white", bd=0, padx=10, pady=10, cursor="hand2", font=("Segoe UI", 10, "bold")).pack(fill="x", padx=16, pady=4)

        stats_box = tk.Frame(right, bg="#f0f9ff", highlightthickness=1, highlightbackground="#bae6fd")
        stats_box.pack(fill="x", padx=16, pady=(15, 5))

        tk.Label(stats_box, textvariable=self.cam_status_var, bg="#f0f9ff", fg="#0369a1", font=("Consolas", 11, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        tk.Label(stats_box, textvariable=self.detected_var, bg="#f0f9ff", fg="#0369a1", font=("Consolas", 11, "bold")).pack(anchor="w", padx=15, pady=2)
        tk.Label(stats_box, textvariable=self.recognized_var, bg="#f0f9ff", fg="#0369a1", font=("Consolas", 11, "bold")).pack(anchor="w", padx=15, pady=(2, 10))

        tk.Label(right, text="Trạng thái", bg="white", fg=self.colors["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(20, 4))
        tk.Label(right, textvariable=self.status_var, bg="white", fg=self.colors["text"], justify="left", wraplength=280, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16)

    def start(self) -> None:
        if self.running: return
        self.session_cache = {} 
        if not self.camera.start():
            messagebox.showerror("Lỗi", "Không thể kết nối với Camera.")
            return
        self.running = True
        self.cam_status_var.set("Camera: ✓")
        self.status_var.set("Camera đang mở...")
        self._update_frame()

    def stop(self) -> None:
        if not self.running: return
        self.running = False
        if hasattr(self.camera, 'stop'): self.camera.stop()
        elif hasattr(self.camera, 'release'): self.camera.release()
        if self.preview_label is not None:
            self.preview_label.configure(image="")
            self.preview_label.image = None
        self.cam_status_var.set("Camera: ✗") 
        self.detected_var.set("Phát hiện: 0")
        self.recognized_var.set("Nhận diện: 0")
        self.status_var.set("Đã dừng")

    def reload_encodings(self) -> None:
        encoder = FaceEncoder()
        encodings, student_ids = encoder.load_all_encodings()
        self.recognizer.update_database(encodings, student_ids)
        self.status_var.set(f"Đã cập nhật {len(student_ids)} khuôn mặt")
        
    def _update_frame(self) -> None:
        if not self.running: return
        frame = self.camera.read()

        if frame is not None:
            self.frame_count += 1
            if self.frame_count % 5 == 0:
                self.current_faces = self.recognizer.recognize(frame)
                num_detected = len(self.current_faces)
                num_recognized = sum(1 for s_id, _, _ in self.current_faces if s_id != "Unknown")
                self.detected_var.set(f"Phát hiện: {num_detected}")
                self.recognized_var.set(f"Nhận diện: {num_recognized}")

            for student_id, confidence, (top, right, bottom, left) in self.current_faces:
                if student_id == "Unknown":
                    color = (0, 0, 255)
                    label = "Unknown"
                    status_msg = "Phát hiện người lạ!"
                else:
                    if student_id not in self.session_cache:
                        student_info = self.db.fetchone("SELECT full_name, class_name FROM students WHERE student_id = ?", (student_id,))
                        full_name = student_info["full_name"] if student_info else "Không rõ tên"
                        class_name = student_info["class_name"] if student_info else ""
                        
                        state = "blocked"
                        msg = ""
                        
                        if class_name:
                            # GỌI NÃO AI KIỂM TRA LỊCH HỌC
                            schedule = self.db.get_current_schedule(class_name.strip())
                            subject_id = schedule["subject_id"] if schedule else None
                            
                            if not subject_id:
                                state = "blocked"
                                msg = f"Lớp {class_name} không có lịch học lúc này!"
                            else:
                                today = current_date()
                                current_time_str = current_time()
                                
                                # KIỂM TRA ĐIỂM DANH TRÙNG MÔN
                                if self.db.attendance_exists(student_id, today, subject_id):
                                    state = "already"
                                    msg = f"Môn: {subject_id}"
                                else:
                                    # LƯU ĐIỂM DANH TRỰC TIẾP VÀO DB
                                    status = self.db.get_attendance_status(
                                        class_name.strip(), subject_id, today, current_time_str
                                    )
                                    if status == "Closed":
                                        state = "blocked"
                                        msg = "Đã hết thời gian điểm danh bằng camera."
                                    else:
                                        success = self.db.mark_attendance(
                                            student_id, subject_id, today, current_time_str, status
                                        )
                                    if status != "Closed" and success:
                                        state = "success"
                                        msg = f"Môn: {subject_id} - {'Đi muộn' if status == 'Late' else 'Đúng giờ'}"
                                    elif status != "Closed":
                                        state = "blocked"
                                        msg = "Lỗi lưu dữ liệu DB!"
                        else:
                            msg = "Không tìm thấy dữ liệu lớp."

                        self.session_cache[student_id] = {
                            "full_name": full_name,
                            "state": state,
                            "msg": msg,
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "timestamp": time.time()
                        }

                    cache_data = self.session_cache[student_id]
                    elapsed_time = time.time() - cache_data["timestamp"]
                    
                    if cache_data["state"] == "blocked":
                        color = (0, 0, 255)
                        label = "SAI LICH HOC"
                        status_msg = f"❌ TỪ CHỐI ĐIỂM DANH\n{cache_data['full_name']} ({student_id})\nLý do: {cache_data['msg']}"
                    elif cache_data["state"] == "success" and elapsed_time < 3.0:
                        color = (0, 255, 0) 
                        label = f"{student_id} ({confidence}%)"
                        status_msg = f"✓ ĐIỂM DANH THÀNH CÔNG\n{cache_data['full_name']}\nMSSV: {student_id}\n{cache_data['msg']} - Lúc {cache_data['time']}"
                    else:
                        color = (0, 255, 255)
                        label = f"Da diem danh ({confidence}%)"
                        status_msg = f"⏳ Đã điểm danh hôm nay\n{cache_data['full_name']}\nMSSV: {student_id}\n{cache_data['msg']}"

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                self.status_var.set(status_msg)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if getattr(self, "target_w", 0) < 10:
                self.target_w = self.preview_label.winfo_width()
                self.target_h = self.preview_label.winfo_height()
            
            if self.target_w > 10 and self.target_h > 10:
                rgb_frame = cv2.resize(rgb_frame, (self.target_w, self.target_h))
            
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.preview_label.imgtk = imgtk
            self.preview_label.configure(image=imgtk)

        if self.preview_label:
            self.preview_label.after(30, self._update_frame)