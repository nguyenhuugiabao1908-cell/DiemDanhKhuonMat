# StudentAttendance/gui/dashboard.py
from __future__ import annotations

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    pass

from gui.attendance import AttendanceFrame
from gui.history import HistoryFrame
from gui.register import RegisterFrame
from gui.schedule import ScheduleFrame
from utils.database import DatabaseManager
from utils.helpers import center_window, modern_theme_colors


class DashboardWindow:
    def __init__(self, db: DatabaseManager, base_dir: Path) -> None:
        self.db = db
        self.base_dir = base_dir
        self.root = tk.Tk()
        self.root.title("Student Attendance Dashboard")
        self.root.geometry("1280x760")
        self.root.minsize(1100, 700)
        center_window(self.root, 1280, 760)

        self.root.state('zoomed')
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)

        self.colors = modern_theme_colors()
        self.root.configure(bg=self.colors["bg"])

        self.content_frame: tk.Frame | None = None
        self.stats_cards: dict[str, tk.Label] = {}
        self.nav_buttons: dict[str, tk.Button] = {}

        self._build_ui()
        self.show_home()

        from utils.ai_assistant import AttendanceAssistant
        self.ai = AttendanceAssistant()

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, bg=self.colors["bg"])
        container.pack(fill="both", expand=True)

        sidebar = tk.Frame(container, bg=self.colors["sidebar"], width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = tk.Label(sidebar, text="ATTENDANCE", bg=self.colors["sidebar"], fg="white", font=("Segoe UI", 18, "bold"))
        logo.pack(pady=(24, 8))

        def on_nav_click(target_key: str, original_command: callable) -> None:
            for key, btn in self.nav_buttons.items():
                btn.configure(font=("Segoe UI", 11, "normal"), fg="#9ca3af")
            if target_key in self.nav_buttons:
                self.nav_buttons[target_key].configure(font=("Segoe UI", 11, "bold"), fg="white")
            original_command()

        menu_items = [
            ("Dashboard", self.show_home, "dashboard"),
            ("Quản lý sinh viên", self.show_register, "students"),
            ("Điểm danh", self.show_attendance, "attendance"),
            ("Lịch sử", self.show_history, "history"),
        ]

        for text, cmd, key in menu_items:
            btn = tk.Button(
                sidebar, text=text, command=lambda k=key, c=cmd: on_nav_click(k, c),
                bg=self.colors["sidebar"], fg="#9ca3af",
                activebackground=self.colors["primary"], activeforeground="white",
                bd=0, relief="flat", font=("Segoe UI", 11), anchor="w", padx=24, pady=12, cursor="hand2"
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn

        bottom_nav = tk.Frame(sidebar, bg=self.colors["sidebar"])
        bottom_nav.pack(side="bottom", fill="x", pady=(0, 20))

        tk.Button(
            bottom_nav, text="🚪 Đăng xuất", command=self.logout,
            bg=self.colors["sidebar"], fg="#ef4444", activebackground="#7f1d1d", activeforeground="white",
            bd=0, relief="flat", font=("Segoe UI", 10, "bold"), anchor="w", padx=24, pady=10, cursor="hand2"
        ).pack(side="bottom", fill="x")

        tk.Button(
            bottom_nav, text="🔑 Đổi mật khẩu", command=self.change_password,
            bg=self.colors["sidebar"], fg="#f59e0b", activebackground="#b45309", activeforeground="white",
            bd=0, relief="flat", font=("Segoe UI", 10), anchor="w", padx=24, pady=10, cursor="hand2"
        ).pack(side="bottom", fill="x")
        
        tk.Button(
            bottom_nav, text="📅 Cài đặt Lịch học", command=self.open_schedule_settings,
            bg=self.colors["sidebar"], fg="#10b981", activebackground="#047857", activeforeground="white",
            bd=0, relief="flat", font=("Segoe UI", 10, "bold"), anchor="w", padx=24, pady=10, cursor="hand2"
        ).pack(side="bottom", fill="x")

        tk.Button(
            bottom_nav, text="🔄 Làm mới thống kê", command=self.refresh_stats,
            bg=self.colors["sidebar"], fg="#9ca3af", activebackground=self.colors["primary"], activeforeground="white",
            bd=0, relief="flat", font=("Segoe UI", 10), anchor="w", padx=24, pady=10, cursor="hand2"
        ).pack(side="bottom", fill="x")

        if "dashboard" in self.nav_buttons:
            self.nav_buttons["dashboard"].configure(font=("Segoe UI", 11, "bold"), fg="white")

        main_area = tk.Frame(container, bg=self.colors["bg"])
        main_area.pack(side="left", fill="both", expand=True)

        topbar = tk.Frame(main_area, bg=self.colors["bg"], height=70)
        topbar.pack(fill="x", padx=20, pady=(16, 8))
        topbar.pack_propagate(False)

        tk.Label(
            topbar, text="Hệ thống điểm danh sinh viên bằng nhận diện khuôn mặt",
            bg=self.colors["bg"], fg=self.colors["text"], font=("Segoe UI", 20, "bold")
        ).pack(anchor="w", pady=8)

        self.content_frame = tk.Frame(main_area, bg=self.colors["bg"])
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def logout(self) -> None:
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc chắn muốn đăng xuất khỏi hệ thống?"):
            self.root.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)

    def change_password(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Đổi mật khẩu Admin")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.configure(bg="white")
        dialog.grab_set()
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 420, self.root.winfo_rooty() + 200))

        tk.Label(dialog, text="Đổi Mật Khẩu Mới", font=("Segoe UI", 15, "bold"), bg="white", fg=self.colors["primary"]).pack(pady=(20, 15))
        frame = tk.Frame(dialog, bg="white")
        frame.pack(fill="both", expand=True, padx=35)

        tk.Label(frame, text="Tên đăng nhập (Username):", bg="white", font=("Segoe UI", 10, "bold"), fg=self.colors["muted"]).pack(anchor="w")
        user_var = tk.StringVar(value="admin")
        ttk.Entry(frame, textvariable=user_var, font=("Segoe UI", 11)).pack(fill="x", pady=(4, 15))

        tk.Label(frame, text="Nhập mật khẩu mới hoàn toàn:", bg="white", font=("Segoe UI", 10, "bold"), fg=self.colors["muted"]).pack(anchor="w")
        pass_var = tk.StringVar()
        ttk.Entry(frame, textvariable=pass_var, show="*", font=("Segoe UI", 11)).pack(fill="x", pady=(4, 20))

        def save_new_password():
            username = user_var.get().strip()
            new_password = pass_var.get().strip()
            if not username or not new_password:
                messagebox.showwarning("Cảnh báo", "Vui lòng không để trống thông tin!", parent=dialog)
                return
            try:
                tables = [row[0] for row in self.db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")]
                target_table = "users"
                for t in ["admin", "users", "accounts", "user"]:
                    if t in tables:
                        target_table = t
                        break
                if target_table not in tables:
                    self.db.execute(f"CREATE TABLE IF NOT EXISTS {target_table} (username TEXT PRIMARY KEY, password TEXT)")
                
                check_user = self.db.fetchone(f"SELECT * FROM {target_table} WHERE username = ?", (username,))
                if check_user:
                    self.db.execute(f"UPDATE {target_table} SET password = ? WHERE username = ?", (new_password, username))
                else:
                    self.db.execute(f"INSERT INTO {target_table} (username, password) VALUES (?, ?)", (username, new_password))
                
                messagebox.showinfo("Thành công", f"Đã lưu mật khẩu thành công cho tài khoản '{username}'!", parent=dialog)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi CSDL", f"Không thể lưu mật khẩu.\nChi tiết: {e}", parent=dialog)

        tk.Button(
            frame, text="Xác nhận đổi mật khẩu", command=save_new_password, 
            bg=self.colors["primary"], fg="white", bd=0, pady=10, font=("Segoe UI", 11, "bold"), cursor="hand2"
        ).pack(fill="x", pady=(5, 20))

    def open_schedule_settings(self) -> None:
        self.clear_content()
        if self.content_frame is None: return
        for btn in self.nav_buttons.values():
            btn.configure(font=("Segoe UI", 11, "normal"), fg="#9ca3af")
        from gui.schedule import ScheduleFrame
        ScheduleFrame(self.content_frame, self.db, self.base_dir)

    def clear_content(self) -> None:
        if self.content_frame is None: return
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_home(self, current_class="Tất cả") -> None:
        self.clear_content()
        if self.content_frame is None: return

        # ==========================================
        # 0. GIAO DIỆN BỘ LỌC LỚP
        # ==========================================
        filter_frame = tk.Frame(self.content_frame, bg=self.colors["bg"])
        filter_frame.pack(fill="x", pady=(0, 10))

        tk.Label(filter_frame, text="Lọc dữ liệu theo lớp:", bg=self.colors["bg"], font=("Segoe UI", 11, "bold"), fg=self.colors["muted"]).pack(side="left")
        
        raw_students = self.db.get_students()
        classes = ["Tất cả"] + sorted(list(set(row["class_name"] for row in raw_students if row["class_name"])))
        
        class_var = tk.StringVar(value=current_class)
        class_cb = ttk.Combobox(filter_frame, textvariable=class_var, values=classes, state="readonly", width=5, font=("Segoe UI", 11))
        class_cb.pack(side="left", padx=10)
        class_cb.bind("<<ComboboxSelected>>", lambda e: self.show_home(current_class=class_var.get()))

        # ==========================================
        # 1. TIỀN XỬ LÝ DỮ LIỆU CHUNG (ĐÃ NÂNG CẤP THUẬT TOÁN ĐẾM NGÀY)
        # ==========================================
        if current_class == "Tất cả":
            all_students = raw_students
            history_rows = self.db.attendance_history()
        else:
            all_students = [s for s in raw_students if s["class_name"] == current_class]
            filtered_ids = [s["student_id"] for s in all_students]
            history_rows = [r for r in self.db.attendance_history() if r["student_id"] in filtered_ids]

        # Nhóm sinh viên theo lớp để tối ưu tốc độ tính toán
        students_by_class = {}
        for s in all_students:
            c = s["class_name"].strip()
            if c not in students_by_class:
                students_by_class[c] = []
            students_by_class[c].append(s)

        expected_total = 0 # Tổng số lượt đáng lẽ phải đi học của toàn bộ sinh viên
        valid_learning_dates = set() 
        classes_learning_today = set()
        
        today_date = datetime.now().date()
        today_str = today_date.strftime("%Y-%m-%d")

        valid_history_rows = []

        for cls_name, students_in_cls in students_by_class.items():
            schedule = self.db.get_class_schedule(cls_name)
            cls_student_ids = [s["student_id"] for s in students_in_cls]
            cls_hist = [r for r in history_rows if r["student_id"] in cls_student_ids]
            
            if schedule and schedule.get("start_date") and schedule.get("learning_days"):
                try:
                    sch_data = dict(schedule)
                    st_date = datetime.strptime(sch_data["start_date"].strip(), "%Y-%m-%d").date()
                    
                    en_date = None
                    if sch_data.get("end_date"):
                        en_date = datetime.strptime(sch_data["end_date"].strip(), "%Y-%m-%d").date()
                        end_bound = min(today_date, en_date)
                    else:
                        end_bound = today_date
                        
                    # Loại bỏ các lượt điểm danh nằm ngoài khung thời gian của lịch học
                    for r in cls_hist:
                        try:
                            r_date = datetime.strptime(r["attendance_date"], "%Y-%m-%d").date()
                            if r_date >= st_date and (not en_date or r_date <= en_date):
                                valid_history_rows.append(r)
                        except:
                            valid_history_rows.append(r)
                            
                    l_days_str = str(sch_data["learning_days"]).strip()
                    l_days = [int(x) for x in l_days_str.split(",") if x] if l_days_str else []
                    
                    curr = st_date
                    class_expected_days = 0
                    
                    while curr <= end_bound:
                        if curr.weekday() in l_days:
                            class_expected_days += 1
                            valid_learning_dates.add(curr.strftime("%Y-%m-%d"))
                            if curr == today_date:
                                classes_learning_today.add(cls_name)
                        curr += timedelta(days=1)
                        
                    expected_total += class_expected_days * len(students_in_cls)
                    
                except Exception:
                    valid_history_rows.extend(cls_hist)
            else:
                valid_history_rows.extend(cls_hist)
                expected_total += len(cls_hist)

        # Ghi đè lại history_rows bằng dữ liệu đã lọc chuẩn
        history_rows = valid_history_rows

        valid_learning_dates = sorted(list(valid_learning_dates))
        total_days_learned = len(valid_learning_dates)
        total_stu_count = len(all_students)

        # Tính chính xác số sinh viên vắng mặt riêng trong ngày hôm nay
        present_today = sum(1 for r in history_rows if r["attendance_date"] == today_str)
        late_today = sum(
            1 for r in history_rows
            if r["attendance_date"] == today_str and r["status"] == "Late"
        )
        students_supposed_to_learn_today = sum(len(students_by_class[c]) for c in classes_learning_today)
        absent_today = max(0, students_supposed_to_learn_today - present_today)
        
        total_att = len(history_rows)
        total_late = sum(1 for r in history_rows if r["status"] == "Late")

        # ==========================================
        # 2. VẼ 4 THẺ THỐNG KÊ TRÊN CÙNG
        # ==========================================
        cards_frame = tk.Frame(self.content_frame, bg=self.colors["bg"])
        cards_frame.pack(fill="x", pady=(0, 16))

        card_specs = [
            ("Tổng sinh viên", "total_students", "#2563eb", str(total_stu_count)),
            ("Tổng số buổi học", "total_days", "#10b981", str(total_days_learned)), 
            ("Vắng mặt h.nay", "absent_today", "#dc2626", str(absent_today)),
            ("Đi muộn h.nay", "late_today", "#d97706", str(late_today)),
            ("Tổng lượt điểm danh", "total_attendance", "#7c3aed", str(total_att)),
        ]

        for idx, (title, key, color, val) in enumerate(card_specs):
            card = tk.Frame(cards_frame, bg="white", highlightthickness=1, highlightbackground=self.colors["border"])
            card.grid(row=0, column=idx, padx=8, sticky="nsew")
            cards_frame.grid_columnconfigure(idx, weight=1)

            tk.Label(card, text=title, bg="white", fg=self.colors["muted"], font=("Segoe UI", 11)).pack(anchor="w", padx=16, pady=(16, 6))
            value_lbl = tk.Label(card, text=val, bg="white", fg=color, font=("Segoe UI", 22, "bold"))
            value_lbl.pack(anchor="w", padx=16, pady=(0, 16))
            self.stats_cards[key] = value_lbl

        bottom_split = tk.Frame(self.content_frame, bg=self.colors["bg"])
        bottom_split.pack(fill="both", expand=True)

        # ==========================================
        # 3. BÊN TRÁI: BIỂU ĐỒ BIẾN HÌNH (DONUT <-> LINE)
        # ==========================================
        chart_section = tk.Frame(bottom_split, bg="white", highlightthickness=1, highlightbackground=self.colors["border"], width=390)
        chart_section.pack(side="left", fill="y", padx=(8, 8))
        chart_section.pack_propagate(False) 

        chart_header = tk.Frame(chart_section, bg="white")
        chart_header.pack(fill="x", padx=16, pady=(16, 0))
        tk.Label(chart_header, text="Phân tích dữ liệu", bg="white", fg=self.colors["text"], font=("Segoe UI", 12, "bold")).pack(side="left")
        
        chart_filter = ttk.Combobox(chart_header, values=["Tổng quan (Tròn)", "7 buổi gần đây", "30 buổi gần đây"], state="readonly", width=16, font=("Segoe UI", 9))
        chart_filter.current(0)
        chart_filter.pack(side="right")

        chart_body = tk.Frame(chart_section, bg="white")
        chart_body.pack(fill="both", expand=True, padx=5, pady=5)

        def render_chart(event=None):
            for widget in chart_body.winfo_children():
                widget.destroy()
                
            mode = chart_filter.get()
            fig = Figure(figsize=(4, 4), dpi=100)
            
            if mode == "Tổng quan (Tròn)":
                fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.2) 
                ax = fig.add_subplot(111)
                
                actual_present = len(history_rows)
                on_time_count = sum(1 for r in history_rows if r["status"] != "Late")
                late_count = sum(1 for r in history_rows if r["status"] == "Late")
                absent_count = max(0, expected_total - actual_present)

                if expected_total == 0:
                    ax.text(0.5, 0.5, "Chưa có dữ liệu\nđiểm danh", ha='center', va='center', fontsize=11, color='#64748b')
                    ax.axis('off')
                else:
                    labels = ['Đúng giờ', 'Đi muộn', 'Vắng mặt']
                    sizes = [on_time_count, late_count, absent_count]
                    colors = ['#10b981', '#f59e0b', '#f43f5e']
                    
                    wedges, texts, autotexts = ax.pie(
                        sizes, labels=None, colors=colors, autopct='%1.1f%%', 
                        pctdistance=0.8, startangle=90, radius=0.85, wedgeprops=dict(width=0.35, edgecolor='w', linewidth=2) 
                    )
                    
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontsize(10)
                        autotext.set_weight('bold')
                        
                    attendance_rate = (actual_present / expected_total) * 100
                    ax.text(0, 0, f"{attendance_rate:.1f}%\nTham dự", ha='center', va='center', fontsize=12, fontweight='bold', color='#334155')
                    ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False, prop={'size': 9})
                    ax.axis('equal') 
                    
            else:
                fig.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.25) 
                ax = fig.add_subplot(111)
                
                limit = 7 if "7" in mode else 30
                recent_dates = valid_learning_dates[-limit:]
                
                if not recent_dates:
                    ax.text(0.5, 0.5, "Chưa đủ dữ liệu\nđể vẽ biểu đồ", ha='center', va='center', fontsize=11, color='#64748b')
                    ax.axis('off')
                else:
                    counts = []
                    display_dates = []
                    for d in recent_dates:
                        c = sum(1 for r in history_rows if r["attendance_date"] == d)
                        counts.append(c)
                        display_dates.append(datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m"))
                        
                    ax.plot(display_dates, counts, marker='o', linestyle='-', color='#3b82f6', linewidth=2, markersize=5)
                    ax.fill_between(display_dates, counts, color='#3b82f6', alpha=0.1)
                    
                    ax.set_ylim(bottom=0, top=total_stu_count + 1)
                    ax.set_ylabel("Số SV đi học", fontsize=9, color='#475569')
                    
                    rotation = 45 if limit == 30 else 0
                    ax.tick_params(axis='x', rotation=rotation, labelsize=8, colors='#475569')
                    ax.tick_params(axis='y', labelsize=8, colors='#475569')
                    ax.grid(True, linestyle='--', alpha=0.5, axis='y')

            canvas = FigureCanvasTkAgg(fig, master=chart_body)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        try:
            render_chart()
            chart_filter.bind("<<ComboboxSelected>>", render_chart)
        except Exception as e:
            tk.Label(chart_body, text="Cần cài đặt matplotlib", bg="white", fg="#ef4444").pack(expand=True)

        # ==========================================
        # 4. BÊN PHẢI: AI PHÂN TÍCH & BẢNG PHONG THẦN
        # ==========================================
        right_section = tk.Frame(bottom_split, bg="white", highlightthickness=1, highlightbackground=self.colors["border"])
        right_section.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ai_frame = tk.Frame(right_section, bg="#fef2f2", highlightthickness=1, highlightbackground="#fecaca") 
        ai_frame.pack(fill="x", padx=16, pady=(16, 10))
        
        ai_header = tk.Frame(ai_frame, bg="#fef2f2")
        ai_header.pack(fill="x", padx=10, pady=(10, 4))
        
        tk.Label(ai_header, text="💡 AI Insight & Phân tích:", bg="#fef2f2", fg="#b91c1c", font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Button(ai_header, text="✨ Phân tích AI Chuyên Sâu", command=self.open_ai_analysis, bg="#8b5cf6", fg="white", bd=0, padx=15, pady=4, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="right")
        
        tk.Label(right_section, text="⚠️ Sinh viên vắng mặt nhiều nhất", bg="white", fg=self.colors["text"], font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=16, pady=(10, 10))
        body = tk.Frame(right_section, bg="white")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        columns = ("student_id", "full_name", "class_name", "absent_count", "late_count", "status")
        self.absent_tree = ttk.Treeview(body, columns=columns, show="headings", height=12)
        tree = self.absent_tree
        
        for col, title, w in zip(columns, ["MSSV", "Họ tên", "Lớp", "Số buổi vắng", "Số buổi muộn", "Mức độ"], [80, 150, 55, 80, 85, 90]):
            tree.heading(col, text=title)
            tree.column(col, width=w, anchor="center")

        scrollbar = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        tree.tag_configure("danger", foreground="#dc2626", font=("Segoe UI", 10, "bold"))
        tree.tag_configure("warning", foreground="#d97706")

        try:
            attendance_counts = {}
            late_counts = {}
            for row in history_rows:
                sid = row["student_id"]
                attendance_counts[sid] = attendance_counts.get(sid, 0) + 1
                if row["status"] == "Late":
                    late_counts[sid] = late_counts.get(sid, 0) + 1
                
            absent_records = []
            danger_3_count = 0
            danger_4_count = 0
            
            for student in all_students:
                sid = student["student_id"]
                present_days = attendance_counts.get(sid, 0)
                
                my_expected = 0
                cls_name = student["class_name"].strip()
                schedule = self.db.get_class_schedule(cls_name)
                
                if schedule and schedule.get("start_date") and schedule.get("learning_days"):
                    try:
                        sch_data = dict(schedule)
                        st_date = datetime.strptime(sch_data["start_date"].strip(), "%Y-%m-%d").date()
                        if sch_data.get("end_date"):
                            en_date = datetime.strptime(sch_data["end_date"].strip(), "%Y-%m-%d").date()
                            end_bound = min(today_date, en_date)
                        else:
                            end_bound = today_date
                            
                        l_days_str = str(sch_data["learning_days"]).strip()
                        l_days = [int(x) for x in l_days_str.split(",") if x] if l_days_str else []
                        
                        curr = st_date
                        while curr <= end_bound:
                            if curr.weekday() in l_days:
                                my_expected += 1
                            curr += timedelta(days=1)
                    except:
                        pass
                else:
                    my_expected = present_days

                absent_days = max(0, my_expected - present_days)
                
                late_days = late_counts.get(sid, 0)
                if absent_days > 0 or late_days > 0:
                    if absent_days >= 4:
                        status = "Cấm thi"
                        tag = "danger"
                        danger_4_count += 1
                    elif absent_days == 3:
                        status = "Nguy cơ cấm thi"
                        tag = "danger"
                        danger_3_count += 1
                    elif absent_days == 2:
                        status = "Cảnh cáo"
                        tag = "warning"
                    elif absent_days == 1:
                        status = "Nhắc nhở"
                        tag = "warning"
                    else:
                        status = "Có đi muộn"
                        tag = "warning"
                        
                    absent_records.append({
                        "id": sid, "name": student["full_name"], "class": student["class_name"], 
                        "absent": absent_days, "late": late_days,
                        "status": status, "tag": tag
                    })
            
            absent_records.sort(key=lambda x: x["absent"], reverse=True)
            for rec in absent_records:
                tree.insert("", "end", values=(rec["id"], rec["name"], rec["class"], f"{rec['absent']} buổi", f"{rec['late']} buổi", rec["status"]), tags=(rec["tag"],))

            attendance_rate = 0
            if expected_total > 0:
                attendance_rate = (len(history_rows) / expected_total) * 100

            ai_text = f"• Tổng số buổi học theo lịch: {total_days_learned} buổi.\n"
            if late_today > 0:
                ai_text += f"• Hôm nay có {late_today} lượt đi muộn.\n"
            if total_late > 0:
                ai_text += f"• Tổng cộng có {total_late} lượt đi muộn trong dữ liệu đang xem.\n"
            if attendance_rate < 70:
                ai_text += f"• Tỷ lệ chuyên cần chung đang ở mức BÁO ĐỘNG ({attendance_rate:.1f}%).\n"
            elif attendance_rate >= 90:
                ai_text += f"• Tỷ lệ chuyên cần chung RẤT TỐT ({attendance_rate:.1f}%).\n"
            else:
                ai_text += f"• Tỷ lệ chuyên cần chung ở mức TRUNG BÌNH ({attendance_rate:.1f}%).\n"
                
            if danger_4_count > 0:
                ai_text += f"• Phát hiện {danger_4_count} sinh viên ĐÃ BỊ CẤM THI (vắng >= 4 buổi)!\n"
            if danger_3_count > 0:
                ai_text += f"• Phát hiện {danger_3_count} sinh viên NGUY CƠ CẤM THI (vắng 3 buổi).\n"
                
            if danger_4_count == 0 and danger_3_count == 0:
                ai_text += "• Chưa phát hiện sinh viên nào vi phạm mốc nguy hiểm (>= 3 buổi)."

            tk.Label(ai_frame, text=ai_text, bg="#fef2f2", fg="#7f1d1d", font=("Segoe UI", 10), justify="left").pack(anchor="w", padx=15, pady=(0, 10))

        except Exception as e:
            tk.Label(ai_frame, text=f"Lỗi phân tích: {e}", bg="#fef2f2", fg="#dc2626").pack()
            
    def refresh_stats(self) -> None:
        if "dashboard" in self.nav_buttons:
            self.nav_buttons["dashboard"].invoke()
        else:
            self.show_home() 

    def show_register(self) -> None:
        self.clear_content()
        if self.content_frame is None: return
        RegisterFrame(self.content_frame, self.db, self.base_dir)

    def show_attendance(self) -> None:
        self.clear_content()
        if self.content_frame is None: return
        AttendanceFrame(self.content_frame, self.db, self.base_dir)

    def show_history(self) -> None:
        self.clear_content()
        if self.content_frame is None: return
        HistoryFrame(self.content_frame, self.db, self.base_dir)

    def confirm_exit(self) -> None:
        if messagebox.askyesno("Xác nhận thoát", "Bạn có chắc chắn muốn thoát phần mềm không?"):
            self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()

    # ==========================================
    # POPUP: REAL AI ANALYSIS
    # ==========================================
    def open_ai_analysis(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Phân tích chuyên sâu bằng AI (Generative AI)")
        dialog.geometry("700x550")
        dialog.configure(bg="white")
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 250, self.root.winfo_rooty() + 50))

        key_frame = tk.Frame(dialog, bg="#f8fafc", pady=10, padx=20, highlightthickness=1, highlightbackground=self.colors["border"])
        key_frame.pack(fill="x")
        
        tk.Label(key_frame, text="OpenRouter API Key:", bg="#f8fafc", font=("Segoe UI", 10, "bold")).pack(side="left")
        key_var = tk.StringVar(value=self.ai.api_key if self.ai.api_key else "")
        key_entry = ttk.Entry(key_frame, textvariable=key_var, font=("Segoe UI", 10), width=45, show="*")
        key_entry.pack(side="left", padx=10)
        
        btn_connect = tk.Button(key_frame, text="Kết nối AI", bg=self.colors["primary"], fg="white", bd=0, padx=15, cursor="hand2", font=("Segoe UI", 9, "bold"))
        btn_connect.pack(side="left")

        result_frame = tk.Frame(dialog, bg="white", padx=20, pady=15)
        result_frame.pack(fill="both", expand=True)
        
        tk.Label(result_frame, text="BÁO CÁO TỪ CHUYÊN GIA AI:", bg="white", fg="#4f46e5", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        result_text = tk.Text(result_frame, font=("Segoe UI", 11), wrap="word", bg="#f1f5f9", relief="flat", padx=15, pady=15)
        result_text.pack(fill="both", expand=True)
        result_text.insert("1.0", "Vui lòng nhập API Key và bấm 'Kết nối AI' để bắt đầu phân tích...")
        result_text.config(state="disabled")

        def connect_and_analyze():
            apikey = key_var.get().strip()
            if not apikey:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập API Key!", parent=dialog)
                return
                
            btn_connect.config(text="Đang xử lý...", state="disabled")
            result_text.config(state="normal")
            result_text.delete("1.0", "end")
            result_text.insert("1.0", "Đang kết nối vệ tinh AI và phân tích dữ liệu... Vui lòng chờ 3-5 giây ⏳")
            result_text.config(state="disabled")
            
            import threading
            def ai_worker():
                if self.ai.api_key != apikey:
                    ok, msg = self.ai.set_key(apikey)
                    if not ok:
                        update_ui(f"❌ Lỗi: {msg}")
                        return

                stats = self.db.get_dashboard_stats()
                stats_str = f"Tổng số sinh viên: {stats.get('total_students', 0)}. Vắng mặt hôm nay: {stats.get('absent_today', 0)}."
                
                absent_list = ""
                if hasattr(self, 'absent_tree') and self.absent_tree:
                    for child in self.absent_tree.get_children():
                        v = self.absent_tree.item(child)["values"]
                        if v: 
                            absent_list += f"- {v[1]} ({v[0]}): vắng {v[3]} ({v[4]})\n"
                
                if not absent_list: 
                    absent_list = "Không có sinh viên nào vắng mặt nguy hiểm."

                answer = self.ai.analyze_attendance(stats_str, absent_list)
                update_ui(answer)

            def update_ui(text):
                dialog.after(0, lambda: _apply_text(text))

            def _apply_text(text):
                btn_connect.config(text="Phân tích lại", state="normal")
                result_text.config(state="normal")
                result_text.delete("1.0", "end")
                result_text.insert("1.0", text)
                result_text.config(state="disabled")

            threading.Thread(target=ai_worker, daemon=True).start()

        btn_connect.config(command=connect_and_analyze)