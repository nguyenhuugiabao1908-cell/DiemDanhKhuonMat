# StudentAttendance/gui/schedule.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

from utils.helpers import modern_theme_colors

class ScheduleFrame:
    def __init__(self, parent: tk.Widget, db, base_dir=None) -> None:
        self.parent = parent
        self.db = db
        self.colors = modern_theme_colors()
        
        self.days_map = {
            "T2": 0, "T3": 1, "T4": 2, 
            "T5": 3, "T6": 4, "T7": 5, "CN": 6
        }
        self.days_reverse = {v: k for k, v in self.days_map.items()}
        self.day_vars = {} 
        
        self._build_ui()
        self.load_subjects()
        self.load_classes() 
        self.load_schedules()

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.parent, bg=self.colors["bg"])
        wrapper.pack(fill="both", expand=True)

        tk.Label(
            wrapper, text="Quản lý Môn học & Thời khóa biểu", 
            bg=self.colors["bg"], fg=self.colors["text"], font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.notebook = ttk.Notebook(wrapper)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.tab_subjects = tk.Frame(self.notebook, bg="white")
        self.tab_schedules = tk.Frame(self.notebook, bg="white")
        
        self.notebook.add(self.tab_subjects, text="📚 Quản lý Môn học")
        self.notebook.add(self.tab_schedules, text="📅 Thời khóa biểu")

        self._build_subjects_tab()
        self._build_schedules_tab()

    # ==========================================
    # TAB 1: MÔN HỌC
    # ==========================================
    def _build_subjects_tab(self):
        form_frame = tk.Frame(self.tab_subjects, bg="#f8fafc", highlightthickness=1, highlightbackground=self.colors["border"])
        form_frame.pack(fill="x", padx=15, pady=15)
        
        tk.Label(form_frame, text="Mã môn học (VD: IT123):", bg="#f8fafc", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.sub_id_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.sub_id_var, font=("Segoe UI", 10), width=20).grid(row=0, column=1, padx=10, pady=10)

        tk.Label(form_frame, text="Tên môn học (VD: Python):", bg="#f8fafc", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.sub_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.sub_name_var, font=("Segoe UI", 10), width=35).grid(row=0, column=3, padx=10, pady=10)

        btn_frame = tk.Frame(form_frame, bg="#f8fafc")
        btn_frame.grid(row=0, column=4, padx=20, pady=10)
        
        tk.Button(btn_frame, text="Thêm môn học", command=self.add_subject, bg="#16a34a", fg="white", bd=0, padx=15, pady=6, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Xóa dòng chọn", command=self.delete_subject, bg="#dc2626", fg="white", bd=0, padx=15, pady=6, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)

        self.tree_sub = ttk.Treeview(self.tab_subjects, columns=("subject_id", "subject_name"), show="headings", height=15)
        self.tree_sub.heading("subject_id", text="Mã môn học")
        self.tree_sub.heading("subject_name", text="Tên môn học")
        
        # Đã chỉnh anchor="center" cho cột Tên môn học
        self.tree_sub.column("subject_id", width=150, anchor="center")
        self.tree_sub.column("subject_name", width=500, anchor="center")
        
        self.tree_sub.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    # ==========================================
    # TAB 2: LỊCH HỌC
    # ==========================================
    def _build_schedules_tab(self):
        form_frame = tk.Frame(self.tab_schedules, bg="#f8fafc", highlightthickness=1, highlightbackground=self.colors["border"])
        form_frame.pack(fill="x", padx=15, pady=15)
        
        # --- HÀNG 1: Lớp | Môn Học | Khung giờ ---
        tk.Label(form_frame, text="Lớp:", bg="#f8fafc", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=(15,5), pady=10, sticky="w")
        self.sch_class_var = tk.StringVar()
        self.cb_classes = ttk.Combobox(form_frame, textvariable=self.sch_class_var, state="readonly", font=("Segoe UI", 10), width=15)
        self.cb_classes.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        self.cb_classes.bind("<<ComboboxSelected>>", self.on_class_select)

        tk.Label(form_frame, text="Môn học:", bg="#f8fafc", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=(15,5), pady=10, sticky="w")
        self.sch_sub_var = tk.StringVar()
        self.cb_subjects = ttk.Combobox(form_frame, textvariable=self.sch_sub_var, state="readonly", font=("Segoe UI", 10), width=25)
        self.cb_subjects.grid(row=0, column=3, padx=5, pady=10, sticky="w")

        tk.Label(form_frame, text="Khung giờ:", bg="#f8fafc", font=("Segoe UI", 10, "bold")).grid(row=0, column=4, padx=(15,5), pady=10, sticky="w")
        time_frame = tk.Frame(form_frame, bg="#f8fafc")
        time_frame.grid(row=0, column=5, padx=5, pady=10, sticky="w")
        
        self.start_h_var, self.start_m_var = tk.StringVar(value="07"), tk.StringVar(value="00")
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.start_h_var, width=3, format="%02.0f").pack(side="left")
        tk.Label(time_frame, text=":", bg="#f8fafc", font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.start_m_var, width=3, format="%02.0f").pack(side="left")
        tk.Label(time_frame, text=" - ", bg="#f8fafc", font=("Segoe UI", 10, "bold")).pack(side="left", padx=2)
        
        self.end_h_var, self.end_m_var = tk.StringVar(value="09"), tk.StringVar(value="30")
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.end_h_var, width=3, format="%02.0f").pack(side="left")
        tk.Label(time_frame, text=":", bg="#f8fafc", font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.end_m_var, width=3, format="%02.0f").pack(side="left")

        # --- HÀNG 2: Khai giảng | Kết thúc | Ngày học ---
        tk.Label(form_frame, text="Khai giảng:", bg="#f8fafc", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, padx=(15,5), pady=(0,15), sticky="w")
        self.start_date_var = tk.StringVar()
        if DateEntry:
            DateEntry(form_frame, textvariable=self.start_date_var, font=("Segoe UI", 10), width=12, date_pattern='yyyy-mm-dd', background=self.colors["primary"], foreground='white').grid(row=1, column=1, padx=5, pady=(0,15), sticky="w")
        else:
            self.start_date_var.set(datetime.now().strftime("%Y-%m-%d"))
            ttk.Entry(form_frame, textvariable=self.start_date_var, width=14).grid(row=1, column=1, padx=5, pady=(0,15), sticky="w")

        tk.Label(form_frame, text="Kết thúc:", bg="#f8fafc", font=("Segoe UI", 10, "bold")).grid(row=1, column=2, padx=(15,5), pady=(0,15), sticky="w")
        self.end_date_var = tk.StringVar()
        if DateEntry:
            DateEntry(form_frame, textvariable=self.end_date_var, font=("Segoe UI", 10), width=12, date_pattern='yyyy-mm-dd', background=self.colors["primary"], foreground='white').grid(row=1, column=3, padx=5, pady=(0,15), sticky="w")
        else:
            self.end_date_var.set(datetime.now().strftime("%Y-%m-%d"))
            ttk.Entry(form_frame, textvariable=self.end_date_var, width=14).grid(row=1, column=3, padx=5, pady=(0,15), sticky="w")

        tk.Label(form_frame, text="Ngày học:", bg="#f8fafc", font=("Segoe UI", 10, "bold")).grid(row=1, column=4, padx=(15,5), pady=(0,15), sticky="e")
        days_frame = tk.Frame(form_frame, bg="#f8fafc")
        days_frame.grid(row=1, column=5, padx=5, pady=(0,15), sticky="w")
        for text, val in self.days_map.items():
            var = tk.IntVar()
            self.day_vars[val] = var
            tk.Checkbutton(days_frame, text=text, variable=var, bg="#f8fafc", font=("Segoe UI", 10), cursor="hand2").pack(side="left", padx=(0,5))

        # --- HÀNG 3: Nút điều khiển ---
        btn_frame = tk.Frame(form_frame, bg="#f8fafc")
        btn_frame.grid(row=2, column=0, columnspan=6, padx=15, pady=(0,15), sticky="e")
        tk.Button(btn_frame, text="Thêm lịch học", command=self.add_schedule, bg="#2563eb", fg="white", bd=0, padx=20, pady=8, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Button(btn_frame, text="Sửa lịch chọn", command=self.edit_schedule, bg="#f59e0b", fg="white", bd=0, padx=20, pady=8, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Xóa lịch chọn", command=self.delete_schedule, bg="#dc2626", fg="white", bd=0, padx=20, pady=8, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="left")

        # -- Bảng dữ liệu (ĐÃ THÊM CỘT THỜI GIAN HỌC) --
        self.tree_sch = ttk.Treeview(self.tab_schedules, columns=("id", "class", "subject", "date_range", "day", "time"), show="headings", height=15)
        
        self.tree_sch.heading("id", text="ID")
        self.tree_sch.heading("class", text="Lớp")
        self.tree_sch.heading("subject", text="Môn học")
        self.tree_sch.heading("date_range", text="Thời gian học")
        self.tree_sch.heading("day", text="Thứ")
        self.tree_sch.heading("time", text="Khung giờ")
        
        self.tree_sch.column("id", width=40, anchor="center")
        self.tree_sch.column("class", width=80, anchor="center")
        self.tree_sch.column("subject", width=250, anchor="center")
        self.tree_sch.column("date_range", width=200, anchor="center")
        self.tree_sch.column("day", width=80, anchor="center")
        self.tree_sch.column("time", width=150, anchor="center")
        
        self.tree_sch.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.tree_sch.bind("<<TreeviewSelect>>", self.on_schedule_select)

    # ==========================================
    # LOGIC XỬ LÝ
    # ==========================================
    def load_subjects(self):
        for item in self.tree_sub.get_children(): self.tree_sub.delete(item)
        subjects = self.db.get_subjects()
        for sub in subjects: self.tree_sub.insert("", "end", values=(sub["subject_id"], sub["subject_name"]))
        cb_values = [f"{sub['subject_id']} - {sub['subject_name']}" for sub in subjects]
        self.cb_subjects['values'] = cb_values
        if cb_values: self.cb_subjects.current(0)
            
    def load_classes(self):
        students = self.db.get_students()
        classes = sorted(list(set([s["class_name"] for s in students if s["class_name"]])))
        self.cb_classes['values'] = classes
        if classes:
            self.cb_classes.current(0)
            self.on_class_select() 
        else:
            self.cb_classes.set("Chưa có lớp")

    def on_class_select(self, event=None):
        cls = self.sch_class_var.get().strip()
        schedule = self.db.get_class_schedule(cls)
        if schedule:
            if "start_date" in schedule and schedule["start_date"]: 
                self.start_date_var.set(schedule["start_date"])
            if "end_date" in schedule and schedule["end_date"]: 
                self.end_date_var.set(schedule["end_date"])

    def on_schedule_select(self, event=None):
        selected = self.tree_sch.selection()
        if not selected: return
        
        vals = self.tree_sch.item(selected[0])["values"]
        
        # 1. Lớp
        self.sch_class_var.set(str(vals[1]))
        self.on_class_select() 
        
        # 2. Môn
        sub_name = str(vals[2])
        for sub in self.cb_subjects['values']:
            if sub_name in sub:
                self.cb_subjects.set(sub)
                break
                
        # 3. Khung giờ (Index đã thay đổi do thêm cột date_range)
        time_str = str(vals[5])
        if " - " in time_str:
            st, en = time_str.split(" - ")
            self.start_h_var.set(st.split(":")[0])
            self.start_m_var.set(st.split(":")[1])
            self.end_h_var.set(en.split(":")[0])
            self.end_m_var.set(en.split(":")[1])
            
        # 4. Thứ
        day_str = str(vals[4])
        day_int = self.days_map.get(day_str)
        for val, var in self.day_vars.items():
            var.set(1 if val == day_int else 0)

    def add_subject(self):
        sub_id = self.sub_id_var.get().strip().upper()
        sub_name = self.sub_name_var.get().strip()
        if not sub_id or not sub_name:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ Mã môn và Tên môn!")
            return
        if self.db.add_subject(sub_id, sub_name):
            messagebox.showinfo("Thành công", f"Đã thêm môn: {sub_name}")
            self.sub_id_var.set("")
            self.sub_name_var.set("")
            self.load_subjects()
        else:
            messagebox.showerror("Lỗi", "Mã môn học này đã tồn tại hoặc có lỗi CSDL!")

    def delete_subject(self):
        selected = self.tree_sub.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn môn học cần xóa!")
            return
        if messagebox.askyesno("Xác nhận", "Xóa môn học này sẽ xóa TOÀN BỘ lịch học liên quan. Chắc chắn xóa?"):
            for item in selected:
                sub_id = self.tree_sub.item(item, "values")[0]
                self.db.delete_subject(sub_id)
            self.load_subjects()
            self.load_schedules()

    def load_schedules(self):
        for item in self.tree_sch.get_children(): self.tree_sch.delete(item)
        schedules = self.db.get_schedules()
        subjects_dict = {sub["subject_id"]: sub["subject_name"] for sub in self.db.get_subjects()}
        
        for sch in schedules:
            cls_name = sch["class_name"]
            sub_name = subjects_dict.get(sch["subject_id"], sch["subject_id"])
            day_str = self.days_reverse.get(sch["day_of_week"], "Unknown")
            time_str = f"{sch['start_time']} - {sch['end_time']}"
            
            # Tính toán chuỗi hiển thị Thời gian học
            cls_sch = self.db.get_class_schedule(cls_name)
            date_range = "Chưa thiết lập"
            if cls_sch:
                # Ép kiểu sang Dictionary chuẩn để có thể dùng hàm .get() an toàn
                sch_data = dict(cls_sch) 
                
                st = sch_data.get("start_date", "")
                en = sch_data.get("end_date", "")
                
                if st and en:
                    date_range = f"{st} đến {en}"
                elif st:
                    date_range = f"Từ {st}"
                    
            self.tree_sch.insert("", "end", values=(sch["id"], cls_name, sub_name, date_range, day_str, time_str))

    def add_schedule(self):
        class_name = self.sch_class_var.get().strip()
        subject_raw = self.sch_sub_var.get()
        start_date = self.start_date_var.get().strip()
        end_date = self.end_date_var.get().strip()
        
        try:
            start_time = f"{int(self.start_h_var.get() or 0):02d}:{int(self.start_m_var.get() or 0):02d}"
            end_time = f"{int(self.end_h_var.get() or 0):02d}:{int(self.end_m_var.get() or 0):02d}"
        except ValueError:
            messagebox.showwarning("Sai định dạng", "Khung giờ phải là số hợp lệ!")
            return
        
        selected_days = [val for val, var in self.day_vars.items() if var.get() == 1]
        
        if not class_name or class_name == "Chưa có lớp" or not subject_raw:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn Lớp và Môn học!")
            return
            
        if start_date > end_date:
            messagebox.showwarning("Lỗi logic", "Ngày khai giảng không thể lớn hơn Ngày kết thúc!")
            return
            
        if not selected_days:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng tích chọn ít nhất 1 ngày học trong tuần!")
            return
            
        subject_id = subject_raw.split(" - ")[0]
        success = True
        
        for day_int in selected_days:
            if not self.db.add_schedule(class_name, subject_id, day_int, start_time, end_time):
                success = False
                
        if success:
            old_sch = self.db.get_class_schedule(class_name)
            all_learning_days = set(selected_days)
            
            if old_sch and old_sch["learning_days"]:
                try:
                    all_learning_days.update([int(x.strip()) for x in str(old_sch["learning_days"]).split(",") if x.strip()])
                except: pass
                    
            learning_days_str = ",".join(map(str, sorted(list(all_learning_days))))
            self.db.save_class_schedule(class_name, start_date, end_date, learning_days_str)

            messagebox.showinfo("Thành công", "Đã lưu thời khóa biểu thành công!")
            for var in self.day_vars.values(): var.set(0)
            self.load_schedules()
        else:
            messagebox.showerror("Lỗi", "Có lỗi xảy ra khi thêm lịch học!")

    def edit_schedule(self):
        selected = self.tree_sch.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng bấm chọn 1 lịch học trong bảng bên dưới để sửa!")
            return
        if len(selected) > 1:
            messagebox.showwarning("Cảnh báo", "Chỉ được sửa từng lịch học một!")
            return
            
        sch_id = self.tree_sch.item(selected[0], "values")[0]
        old_class = str(self.tree_sch.item(selected[0], "values")[1])
        
        class_name = self.sch_class_var.get().strip()
        subject_raw = self.sch_sub_var.get()
        start_date = self.start_date_var.get().strip()
        end_date = self.end_date_var.get().strip()
        
        try:
            start_time = f"{int(self.start_h_var.get() or 0):02d}:{int(self.start_m_var.get() or 0):02d}"
            end_time = f"{int(self.end_h_var.get() or 0):02d}:{int(self.end_m_var.get() or 0):02d}"
        except ValueError:
            messagebox.showwarning("Sai định dạng", "Khung giờ phải là số hợp lệ!")
            return
            
        selected_days = [val for val, var in self.day_vars.items() if var.get() == 1]
        
        if not class_name or class_name == "Chưa có lớp" or not subject_raw:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn Lớp và Môn học!")
            return
        if start_date > end_date:
            messagebox.showwarning("Lỗi logic", "Ngày khai giảng không thể lớn hơn Ngày kết thúc!")
            return
        if not selected_days:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng tích chọn ít nhất 1 ngày học trong tuần!")
            return
            
        subject_id = subject_raw.split(" - ")[0]
        
        self.db.delete_schedule(sch_id)
        success = True
        for day_int in selected_days:
            if not self.db.add_schedule(class_name, subject_id, day_int, start_time, end_time):
                success = False
                
        if success:
            old_sch = self.db.get_class_schedule(class_name)
            all_learning_days = set(selected_days)
            if old_sch and old_sch["learning_days"]:
                try:
                    all_learning_days.update([int(x.strip()) for x in str(old_sch["learning_days"]).split(",") if x.strip()])
                except: pass
            self.db.save_class_schedule(class_name, start_date, end_date, ",".join(map(str, sorted(list(all_learning_days)))))
            
            if class_name != old_class:
                remaining = self.db.get_schedules(old_class)
                if remaining:
                    rem_days = set(int(r["day_of_week"]) for r in remaining)
                    old_c_sch = self.db.get_class_schedule(old_class)
                    st = old_c_sch["start_date"] if old_c_sch else datetime.now().strftime("%Y-%m-%d")
                    en = old_c_sch["end_date"] if old_c_sch and "end_date" in old_c_sch else st
                    self.db.save_class_schedule(old_class, st, en, ",".join(map(str, sorted(list(rem_days)))))
                else:
                    self.db.execute("DELETE FROM class_schedules WHERE class_name=?", (old_class,))
            
            messagebox.showinfo("Thành công", "Đã cập nhật lịch học thành công!")
            for var in self.day_vars.values(): var.set(0)
            self.load_schedules()
        else:
            messagebox.showerror("Lỗi", "Có lỗi xảy ra khi cập nhật lịch học!")

    def delete_schedule(self):
        selected = self.tree_sch.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn lịch học cần xóa!")
            return
            
        if messagebox.askyesno("Xác nhận", f"Chắc chắn muốn xóa {len(selected)} lịch học đã chọn?"):
            for item in selected:
                sch_id = self.tree_sch.item(item, "values")[0]
                class_name = str(self.tree_sch.item(item, "values")[1])
                self.db.delete_schedule(sch_id)
                
                remaining = self.db.get_schedules(class_name)
                if remaining:
                    rem_days = set(int(r["day_of_week"]) for r in remaining)
                    old_sch = self.db.get_class_schedule(class_name)
                    st = old_sch["start_date"] if old_sch else datetime.now().strftime("%Y-%m-%d")
                    en = old_sch["end_date"] if old_sch and "end_date" in old_sch else st
                    self.db.save_class_schedule(class_name, st, en, ",".join(map(str, sorted(list(rem_days)))))
                else:
                    self.db.execute("DELETE FROM class_schedules WHERE class_name=?", (class_name,))
                    
            self.load_schedules()