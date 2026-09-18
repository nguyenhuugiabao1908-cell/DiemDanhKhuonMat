# StudentAttendance/gui/register.py
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk, Toplevel, filedialog
from pathlib import Path
from tkinter import dialog

from PIL import Image, ImageTk
import cv2
import shutil # Thêm thư viện này để xóa thư mục

from utils.camera import Camera
from utils.database import DatabaseManager
from utils.face_encoder import FaceEncoder
from utils.helpers import modern_theme_colors, validate_email, validate_phone
from models.student import Student


class RegisterFrame:
    def __init__(
        self,
        parent: tk.Widget,
        db: DatabaseManager,
        base_dir: Path,
        on_refresh=None,
    ) -> None:
        self.parent = parent
        self.db = db
        self.base_dir = base_dir
        self.on_refresh = on_refresh
        self.colors = modern_theme_colors()

        self.camera = Camera()
        self.camera_running = False
        self.captured_paths: list[Path] = []
        
        # Biến lưu trữ thông tin sinh viên đang được chọn trên bảng
        self.current_student_id: str | None = None
        self.student_id_var = tk.StringVar()
        self.full_name_var = tk.StringVar()
        self.class_name_var = tk.StringVar()
        self.faculty_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        
        self.search_var = tk.StringVar()
        self.selected_student_label_var = tk.StringVar(value="Chưa chọn sinh viên nào")

        self.preview_label: tk.Label | None = None
        self.tree: ttk.Treeview | None = None

        self._build_ui()
        self.load_students()

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.parent, bg=self.colors["bg"])
        wrapper.pack(fill="both", expand=True)

        left = tk.Frame(
            wrapper, bg="white", highlightthickness=1,
            highlightbackground=self.colors["border"], width=400
        )
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        right = tk.Frame(
            wrapper, bg="white", highlightthickness=1,
            highlightbackground=self.colors["border"]
        )
        right.pack(side="left", fill="both", expand=True)

        # ==========================================
        # === BÊN TRÁI: CHỈ CÒN ĐĂNG KÝ KHUÔN MẶT ===
        # ==========================================
        tk.Label(
            left, text="Đăng ký khuôn mặt AI", bg="white",
            fg=self.colors["primary"], font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", padx=16, pady=(16, 5))

        # Hiển thị sinh viên đang được chọn để chụp ảnh
        tk.Label(
            left, textvariable=self.selected_student_label_var, bg="white",
            fg="#dc2626", font=("Segoe UI", 10, "italic")
        ).pack(anchor="w", padx=16, pady=(0, 15))

        camera_btns = tk.Frame(left, bg="white")
        camera_btns.pack(fill="x", padx=16, pady=(0, 10))

        tk.Button(camera_btns, text="Mở Camera", command=self.start_camera, bg="#16a34a", fg="white", bd=0, pady=8, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x", padx=(0, 2))
        tk.Button(camera_btns, text="Chụp ảnh", command=self.capture_face, bg="#2563eb", fg="white", bd=0, pady=8, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(camera_btns, text="Tắt Camera", command=self.stop_camera, bg="#dc2626", fg="white", bd=0, pady=8, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x", padx=(2, 0))

        tk.Button(
            left, text="Mã hóa & Lưu khuôn mặt", command=self.encode_and_save_face,
            bg="#7c3aed", fg="white", bd=0, pady=10, cursor="hand2", font=("Segoe UI", 11, "bold")
        ).pack(fill="x", padx=16, pady=(0, 15))

        # Khung hiển thị Camera (Mở rộng tối đa không gian)
        self.preview_label = tk.Label(left, bg="#e5e7eb", text="Camera Preview\n(Nhấn Mở Camera để bắt đầu)", relief="flat", font=("Segoe UI", 12))
        self.preview_label.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # ==========================================
        # === BÊN PHẢI: QUẢN LÝ DANH SÁCH & NÚT ===
        # ==========================================
        header = tk.Frame(right, bg="white")
        header.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            header, text="Danh sách sinh viên", bg="white",
            fg=self.colors["text"], font=("Segoe UI", 15, "bold")
        ).pack(side="left")

        # Cụm công cụ bên phải header (Bộ lọc & Tìm kiếm)
        search_frame = tk.Frame(header, bg="white")
        search_frame.pack(side="right")

        # 1. Bộ lọc Lớp
        tk.Label(search_frame, text="Lớp:", bg="white", font=("Segoe UI", 10, "bold"), fg=self.colors["muted"]).pack(side="left", padx=(0, 5))
        self.class_filter_var = tk.StringVar(value="Tất cả")
        self.class_combobox = ttk.Combobox(search_frame, textvariable=self.class_filter_var, values=["Tất cả"], state="readonly", width=10, font=("Segoe UI", 10))
        self.class_combobox.pack(side="left", padx=(0, 15))
        self.class_filter_var.trace_add("write", lambda *_: self.load_students())

        # 2. Bộ lọc Trạng thái khuôn mặt
        tk.Label(search_frame, text="Khuôn mặt:", bg="white", font=("Segoe UI", 10, "bold"), fg=self.colors["muted"]).pack(side="left", padx=(0, 5))
        self.status_filter_var = tk.StringVar(value="Tất cả")
        status_combobox = ttk.Combobox(search_frame, textvariable=self.status_filter_var, values=["Tất cả", "Đã đăng ký", "Chưa đăng ký"], state="readonly", width=14, font=("Segoe UI", 10))
        status_combobox.pack(side="left", padx=(0, 15))
        self.status_filter_var.trace_add("write", lambda *_: self.load_students())

        # 3. Thanh tìm kiếm
        tk.Label(search_frame, text="Tìm kiếm:", bg="white", font=("Segoe UI", 10, "bold"), fg=self.colors["muted"]).pack(side="left", padx=5)
        search_box = ttk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 10), width=25)
        search_box.pack(side="left", ipady=3)
        self.search_var.trace_add("write", lambda *_: self.load_students())

        # --- KHÔI PHỤC LẠI THANH NÚT BẤM (BỊ MẤT) ---
        action_bar = tk.Frame(right, bg="white")
        action_bar.pack(fill="x", padx=16, pady=(0, 10))

        tk.Button(action_bar, text="+ Thêm sinh viên", command=lambda: self.open_student_dialog(is_update=False), bg=self.colors["primary"], fg="white", bd=0, padx=15, pady=6, cursor="hand2", font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Button(action_bar, text="Sửa thông tin", command=lambda: self.open_student_dialog(is_update=True), bg="#f59e0b", fg="white", bd=0, padx=15, pady=6, cursor="hand2", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(10, 0))
        tk.Button(action_bar, text="Xóa", command=self.delete_student, bg="#dc2626", fg="white", bd=0, padx=15, pady=6, cursor="hand2", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(10, 0))
        tk.Button(action_bar, text="Điểm danh thủ công", command=self.manual_attendance, bg="#10b981", fg="white", bd=0, padx=15, pady=6, cursor="hand2", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(10, 0))
        tk.Button(action_bar, text="Nhập Excel", command=self.import_from_excel, bg="#8b5cf6", fg="white", bd=0, padx=15, pady=6, cursor="hand2", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(10, 0))
        tk.Button(action_bar, text="🖼️ Quản lý Ảnh AI", command=self.manage_face, bg="#0ea5e9", fg="white", bd=0, padx=15, pady=6, cursor="hand2", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(10, 0))

        # Khung chứa bảng danh sách
        body = tk.Frame(right, bg="white")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        columns = ("student_id", "full_name", "class_name", "faculty", "email", "phone", "face_status")
        
        # 1. TẠO 2 THANH CUỘN (DỌC & NGANG) ĐỂ BẢO VỆ DỮ LIỆU KHÔNG BỊ CHE MẤT
        scrollbar_y = ttk.Scrollbar(body, orient="vertical")
        scrollbar_x = ttk.Scrollbar(body, orient="horizontal")
        
        self.tree = ttk.Treeview(
            body, columns=columns, show="headings", height=22,
            yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set
        )
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # 2. "ÉP CÂN" LẠI ĐỘ RỘNG CÁC CỘT & THIẾT LẬP CHẾ ĐỘ TỰ GIÃN
        widths = [90, 170, 50, 60, 170, 100, 110]
        # Chỉ cho phép cột Họ tên và Email tự động phình to, các cột khác giữ kích thước cố định
        stretches = [False, True, False, False, True, False, False] 
        titles = ["MSSV", "Họ tên", "Lớp", "Khoa", "Email", "SĐT", "Khuôn mặt"]
        
        for col, title, w, is_stretch in zip(columns, titles, widths, stretches):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=w, anchor="center", stretch=is_stretch)

        # 3. GẮN CÁC THÀNH PHẦN VÀO KHUNG (Phải pack thanh cuộn trước)
        scrollbar_x.pack(side="bottom", fill="x")
        scrollbar_y.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_student)

        self.tree.bind("<Control-a>", self.select_all)
        self.tree.bind("<Control-A>", self.select_all)

    # ==========================================
    # === HỘP THOẠI POPUP THÊM/SỬA SINH VIÊN ===
    # ==========================================
    # ==========================================
    # === HỘP THOẠI POPUP THÊM/SỬA SINH VIÊN ===
    # ==========================================
    # ==========================================
    # === HỘP THOẠI POPUP THÊM/SỬA SINH VIÊN ===
    # ==========================================
    def open_student_dialog(self, is_update=False) -> None:
        # --- CHỐT CHẶN BẢO MẬT KHI CHỌN NHIỀU SINH VIÊN ---
        if is_update:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn một sinh viên trên bảng để sửa.")
                return
            if len(selected) > 1:
                messagebox.showwarning("Cảnh báo", "Không thể sửa nhiều người cùng lúc!\nVui lòng chỉ chọn 1 sinh viên duy nhất để cập nhật thông tin.")
                return
                
            # Đảm bảo biến current_student_id khớp chính xác với dòng đang được chọn
            self.current_student_id = str(self.tree.item(selected[0])['values'][0])

        dialog = tk.Toplevel(self.parent)
        dialog.title("Cập nhật thông tin" if is_update else "Thêm sinh viên mới")
        dialog.geometry("400x550")
        dialog.resizable(False, False)
        dialog.configure(bg="white")
        dialog.grab_set()
        
        dialog.geometry("+%d+%d" % (self.parent.winfo_rootx() + 300, self.parent.winfo_rooty() + 50))

        tk.Label(dialog, text="Thông tin sinh viên", bg="white", font=("Segoe UI", 14, "bold"), fg=self.colors["primary"]).pack(pady=(15, 10))

        form_frame = tk.Frame(dialog, bg="white")
        form_frame.pack(fill="both", expand=True, padx=30)

        sid_var = tk.StringVar(value=self.student_id_var.get() if is_update else "")
        name_var = tk.StringVar(value=self.full_name_var.get() if is_update else "")
        class_var = tk.StringVar(value=self.class_name_var.get() if is_update else "")
        fac_var = tk.StringVar(value=self.faculty_var.get() if is_update else "")
        email_var = tk.StringVar(value=self.email_var.get() if is_update else "")
        phone_var = tk.StringVar(value=self.phone_var.get() if is_update else "")

        fields = [("MSSV", sid_var), ("Họ tên", name_var), ("Lớp", class_var), ("Khoa", fac_var), ("Email", email_var), ("SĐT", phone_var)]
        entries = []

        for label_text, var in fields:
            tk.Label(form_frame, text=label_text, bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5, 2))
            entry = ttk.Entry(form_frame, textvariable=var, font=("Segoe UI", 10))
            entry.pack(fill="x", ipady=3)
            entries.append(entry)
            
            if is_update and label_text == "MSSV":
                entry.configure(state="readonly")

        def save_data():
            mssv = sid_var.get().strip()
            name = name_var.get().strip()
            cls = class_var.get().strip()
            fac = fac_var.get().strip()
            email = email_var.get().strip()
            phone = phone_var.get().strip()

            # 1. KIỂM TRA ĐẦY ĐỦ THÔNG TIN
            if not all([mssv, name, cls, fac, email, phone]):
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin vào tất cả các ô.", parent=dialog)
                return
                
            # 2. KIỂM TRA MSSV (Bắt buộc 8 chữ số)
            if not (mssv.isdigit() and len(mssv) == 8):
                messagebox.showwarning("Cảnh báo", "MSSV không hợp lệ!\nBắt buộc phải là một dãy đúng 8 chữ số.", parent=dialog)
                return

            # 3. KIỂM TRA EMAIL (Bắt buộc đuôi @gmail.com)
            # Yêu cầu độ dài > 10 để tránh trường hợp người dùng chỉ gõ mỗi chữ "@gmail.com"
            if not email.endswith("@gmail.com") or len(email) <= 10:
                messagebox.showwarning("Cảnh báo", "Email không hợp lệ!\nBắt buộc phải sử dụng đuôi '@gmail.com'.", parent=dialog)
                return
                
            # 4. KIỂM TRA SĐT (Bắt buộc 10 chữ số, bắt đầu bằng số 0)
            if not (phone.isdigit() and len(phone) == 10 and phone.startswith("0")):
                messagebox.showwarning("Cảnh báo", "Số điện thoại không hợp lệ!\nPhải gồm đúng 10 chữ số và bắt đầu bằng số 0.", parent=dialog)
                return

            try:
                # 5. KIỂM TRA TRÙNG LẶP TRONG DATABASE
                all_students = self.db.get_students()
                for s in all_students:
                    if is_update and s["student_id"] == self.current_student_id:
                        continue
                        
                    if s["student_id"] == mssv:
                        messagebox.showerror("Lỗi Trùng Lặp", f"MSSV '{mssv}' đã được sử dụng bởi sinh viên khác!", parent=dialog)
                        return
                    if s["email"] == email:
                        messagebox.showerror("Lỗi Trùng Lặp", f"Email '{email}' đã được đăng ký bởi sinh viên khác!", parent=dialog)
                        return
                    if s["phone"] == phone:
                        messagebox.showerror("Lỗi Trùng Lặp", f"Số điện thoại '{phone}' đã được đăng ký bởi sinh viên khác!", parent=dialog)
                        return

                # 6. LƯU ĐỐI TƯỢNG VÀO DATABASE
                student = Student(
                    id=None,
                    student_id=mssv,
                    full_name=name,
                    class_name=cls,
                    faculty=fac,
                    email=email, 
                    phone=phone
                )
                
                if is_update:
                    if self.db.update_student(student):
                        messagebox.showinfo("Thành công", "Đã cập nhật thông tin sinh viên thành công!", parent=dialog)
                        dialog.destroy()
                        self.load_students()
                else:
                    if self.db.add_student(student):
                        messagebox.showinfo("Thành công", "Đã thêm sinh viên mới thành công!", parent=dialog)
                        dialog.destroy()
                        self.load_students()
                        if self.on_refresh: self.on_refresh()
                    else:
                        messagebox.showerror("Lỗi Hệ thống", "Không thể thêm vào cơ sở dữ liệu!", parent=dialog)
                        
            except Exception as exc:
                messagebox.showerror("Lỗi", str(exc), parent=dialog)


        tk.Button(dialog, text="Lưu thông tin", command=save_data, bg=self.colors["primary"], fg="white", bd=0, pady=8, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(fill="x", padx=30, pady=20)
        dialog.bind("<Return>", lambda e: save_data())
    # ==========================================
    # === CÁC HÀM XỬ LÝ LOGIC CHÍNH BÊN NGOÀI ===
    # ==========================================
    def load_students(self) -> None:
        if self.tree is None: return
        
        # --- CẤU HÌNH MÀU SẮC CHO BẢNG ---
        self.tree.tag_configure("registered", foreground="#15803d", font=("Segoe UI", 9, "bold")) # Màu Xanh lá
        self.tree.tag_configure("unregistered", foreground="#dc2626", font=("Segoe UI", 9, "bold")) # Màu Đỏ

        for item in self.tree.get_children():
            self.tree.delete(item)

        # Lấy giá trị từ các bộ lọc (Có cơ chế bảo vệ nếu UI chưa kịp render)
        keyword = self.search_var.get().strip().lower()
        class_filter = getattr(self, "class_filter_var", tk.StringVar(value="Tất cả")).get()
        status_filter = getattr(self, "status_filter_var", tk.StringVar(value="Tất cả")).get()

        students = self.db.get_students()
        
        # --- TỰ ĐỘNG CẬP NHẬT DANH SÁCH LỚP VÀO DROPDOWN ---
        if hasattr(self, "class_combobox") and students:
            classes = sorted(list(set(row["class_name"] for row in students if row["class_name"])))
            self.class_combobox['values'] = ["Tất cả"] + classes

        for row in students:
            mssv = str(row["student_id"])
            cls_name = row["class_name"]
            
            # 1. Áp dụng Bộ lọc Lớp
            if class_filter != "Tất cả" and cls_name != class_filter:
                continue

            # --- THUẬT TOÁN KIỂM TRA TRẠNG THÁI KHUÔN MẶT ---
            faces_dir = self.base_dir / "data" / "faces" / mssv
            is_registered = False
            if faces_dir.exists() and any(faces_dir.glob("*.jpg")):
                is_registered = True

            # 2. Áp dụng Bộ lọc Trạng thái
            if status_filter == "Đã đăng ký" and not is_registered:
                continue
            if status_filter == "Chưa đăng ký" and is_registered:
                continue

            # 3. Gắn nhãn trạng thái và Tag màu
            if is_registered:
                face_status = "✅ Đã đăng ký"
                row_tag = "registered"
            else:
                face_status = "❌ Chưa đăng ký"
                row_tag = "unregistered"

            # Đưa dữ liệu hiển thị vào hàng
            display_row = (mssv, row["full_name"], cls_name, dict(row).get("faculty") or "", row["email"], row["phone"], face_status)

            # 4. Áp dụng ô Tìm kiếm chữ
            if keyword and keyword not in str(display_row).lower(): 
                continue
                
            # Đẩy lên bảng kèm theo màu sắc (tags)
            self.tree.insert("", "end", values=display_row, tags=(row_tag,))

    def on_select_student(self, _: object) -> None:
        if self.tree is None: return
        selected = self.tree.selection()
        if not selected: return
        
        values = self.tree.item(selected[0], "values")
        self.student_id_var.set(values[0])
        self.full_name_var.set(values[1])
        self.class_name_var.set(values[2])
        self.faculty_var.set(values[3])
        self.email_var.set(values[4])
        self.phone_var.set(values[5])
        
        self.current_student_id = values[0]
        self.selected_student_label_var.set(f"Đang chọn: {values[0]} - {values[1]}")

    def delete_student(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn sinh viên cần xóa!\n(Mẹo: Nhấn giữ phím Ctrl hoặc Shift để chọn nhiều sinh viên cùng lúc)")
            return

        count = len(selected)
        if count == 1:
            item = self.tree.item(selected[0])
            msg = f"Bạn có chắc chắn muốn xóa sinh viên {item['values'][1]} (MSSV: {item['values'][0]})?"
        else:
            msg = f"CẢNH BÁO: Bạn đang chọn XÓA HÀNG LOẠT {count} sinh viên!\nBạn có chắc chắn muốn thực hiện?"

        if messagebox.askyesno("Xác nhận", msg + "\n\nHành động này sẽ xóa toàn bộ dữ liệu khuôn mặt và lịch sử điểm danh trong ổ cứng!"):
            import shutil
            
            for sel in selected:
                item = self.tree.item(sel)
                mssv = str(item['values'][0])

                # 1. Xóa thông tin khỏi Database
                self.db.delete_student(mssv)
                try:
                    self.db.execute("DELETE FROM attendance WHERE student_id = ?", (mssv,))
                    self.db.execute("DELETE FROM attendance_history WHERE student_id = ?", (mssv,))
                except: pass

                # 2. Xóa thư mục ảnh
                faces_dir = self.base_dir / "data" / "faces" / mssv
                if faces_dir.exists():
                    try: shutil.rmtree(faces_dir)
                    except: pass

            messagebox.showinfo("Thành công", f"Đã xóa triệt để {count} sinh viên thành công.")
            self.load_students()

    def show_camera_instruction(self) -> None:
        # Lấy cửa sổ chính của phần mềm làm điểm tựa (thay vì dùng self)
        main_window = self.tree.winfo_toplevel()
        
        # 1. Tạo một nhãn (Label) nổi lên trên giao diện
        toast = tk.Label(
            main_window, 
            text="📸 HÃY NHÌN THẲNG VÀO CAMERA\nĐể chụp được bức ảnh sinh trắc học rõ nét nhất nhé!",
            bg="#0ea5e9",        
            fg="white", 
            font=("Segoe UI", 11, "bold"),
            padx=20, pady=10, 
            bd=2, relief="ridge"
        )
        
        # 2. Hàm tạo hiệu ứng trượt xuống (Slide-down animation)
        def slide(y):
            if y <= 40: # Trượt đến tọa độ Y = 40 thì dừng lại
                toast.place(relx=0.5, y=y, anchor="n")
                main_window.after(15, lambda: slide(y + 2)) # Gọi hàm after từ main_window
            else:
                # 3. Dừng lại 3.5 giây (3500ms) rồi tự động xóa thông báo
                main_window.after(3500, toast.destroy)
        
        # Bắt đầu gọi hiệu ứng trượt từ trên cùng (Y = 0)
        slide(0)

    def manual_attendance(self) -> None:
        # 1. LẤY DANH SÁCH NHIỀU SINH VIÊN TỪ BẢNG
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một sinh viên để điểm danh.\n(Mẹo: Lọc theo lớp, rồi bấm Shift + Click để chọn cả lớp)")
            return

        count = len(selected)
        selected_data = [(str(self.tree.item(s)['values'][0]), str(self.tree.item(s)['values'][2])) for s in selected]

        # 2. TẠO HỘP THOẠI CHỌN NGÀY GIỜ & MÔN HỌC
        dialog = tk.Toplevel(self.parent)
        dialog.title("Điểm danh thủ công (Hàng loạt)")
        dialog.geometry("400x380")
        dialog.resizable(False, False)
        dialog.configure(bg="white")
        dialog.grab_set()
        
        dialog.geometry("+%d+%d" % (self.parent.winfo_rootx() + 450, self.parent.winfo_rooty() + 150))

        tk.Label(dialog, text=f"Điểm danh cho: {count} sinh viên", bg="white", font=("Segoe UI", 12, "bold"), fg=self.colors["primary"], justify="center").pack(pady=(20, 15))

        # --- Khung chọn Môn học ---
        sub_frame = tk.Frame(dialog, bg="white")
        sub_frame.pack(fill="x", padx=30, pady=5)
        
        tk.Label(sub_frame, text="Chọn môn:", bg="white", font=("Segoe UI", 10, "bold")).pack(side="left")
        
        subjects = self.db.get_subjects()
        sub_list = [f"{sub['subject_id']} - {sub['subject_name']}" for sub in subjects]
        
        sub_var = tk.StringVar()
        cb_sub = ttk.Combobox(sub_frame, textvariable=sub_var, values=sub_list, state="readonly", font=("Segoe UI", 10), width=20)
        cb_sub.pack(side="right")
        if sub_list:
            cb_sub.current(0)
        else:
            cb_sub.set("Chưa có môn học")

        # --- Khung chọn Ngày (TRẢ LẠI GIAO DIỆN CHUẨN ĐỒNG BỘ) ---
        date_frame = tk.Frame(dialog, bg="white")
        date_frame.pack(fill="x", padx=30, pady=15)
        
        tk.Label(date_frame, text="Chọn ngày:", bg="white", font=("Segoe UI", 10, "bold")).pack(side="left")
        
        try:
            from tkcalendar import DateEntry
            date_var = tk.StringVar()
            date_picker = DateEntry(
                date_frame, textvariable=date_var, font=("Segoe UI", 10), width=15,
                date_pattern='yyyy-mm-dd', background=self.colors["primary"], 
                foreground='white', borderwidth=1, cursor="hand2",
                showweeknumbers=False
            )
            date_picker.pack(side="right")
        except ImportError:
            from datetime import datetime
            date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
            date_picker = ttk.Entry(date_frame, textvariable=date_var, font=("Segoe UI", 10), width=17)
            date_picker.pack(side="right")

        # --- Khung chọn Giờ ---
        time_frame = tk.Frame(dialog, bg="white")
        time_frame.pack(fill="x", padx=30, pady=(5, 20))
        
        tk.Label(time_frame, text="Giờ (HH:MM):", bg="white", font=("Segoe UI", 10, "bold")).pack(side="left")
        
        from datetime import datetime
        now = datetime.now()
        
        spin_frame = tk.Frame(time_frame, bg="white")
        spin_frame.pack(side="right")
        
        hour_var = tk.StringVar(value=now.strftime("%H"))
        hour_spin = ttk.Spinbox(spin_frame, from_=0, to=23, textvariable=hour_var, width=3, format="%02.0f", font=("Segoe UI", 11, "bold"))
        hour_spin.pack(side="left")
        
        tk.Label(spin_frame, text=":", bg="white", font=("Segoe UI", 11, "bold")).pack(side="left")
        
        minute_var = tk.StringVar(value=now.strftime("%M"))
        minute_spin = ttk.Spinbox(spin_frame, from_=0, to=59, textvariable=minute_var, width=3, format="%02.0f", font=("Segoe UI", 11, "bold"))
        minute_spin.pack(side="left")

        # --- Hàm thực thi ghi HÀNG LOẠT vào CSDL ---
        def save_manual_record():
            target_date = date_var.get().strip()
            subject_raw = sub_var.get()
            
            if not subject_raw or subject_raw == "Chưa có môn học":
                messagebox.showwarning("Lỗi", "Vui lòng tạo ít nhất 1 Môn học trong Cài đặt Lịch học trước khi điểm danh!", parent=dialog)
                return
                
            subject_id = subject_raw.split(" - ")[0]
            
            h = int(hour_var.get() or 0)
            m = int(minute_var.get() or 0)
            target_time = f"{h:02d}:{m:02d}:00"
            
            try:
                success_count = 0
                skip_count = 0
                
                # VÒNG LẶP DUYỆT QUA TỪNG SINH VIÊN
                for mssv, class_name in selected_data:
                    existing = self.db.fetchone(
                        "SELECT id FROM attendance WHERE student_id = ? AND attendance_date = ? AND subject_id = ?",
                        (mssv, target_date, subject_id)
                    )
                    
                    if existing:
                        skip_count += 1
                        continue 

                    status = self.db.get_attendance_status(
                        class_name, subject_id, target_date, target_time, manual=True
                    )
                    if status == "Closed":
                        skip_count += 1
                        continue
                    self.db.execute(
                        "INSERT INTO attendance (student_id, subject_id, attendance_date, attendance_time, status) VALUES (?, ?, ?, ?, ?)",
                        (mssv, subject_id, target_date, target_time, status)
                    )
                    success_count += 1
                
                msg = f"Cập nhật hàng loạt hoàn tất!\n\n- Thành công: {success_count} lượt\n- Bỏ qua (đã điểm danh môn này): {skip_count} lượt"
                messagebox.showinfo("Thành công", msg, parent=dialog)
                dialog.destroy()
                
                if self.on_refresh: self.on_refresh() 
                
            except Exception as exc:
                messagebox.showerror("Lỗi CSDL", str(exc), parent=dialog)

        # NÚT LƯU
        tk.Button(dialog, text="Lưu điểm danh", command=save_manual_record, bg="#10b981", fg="white", bd=0, pady=8, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(fill="x", padx=30, pady=10)

    # ==========================================
    # === TÍCH HỢP CAMERA VÀ AI ===
    # ==========================================
    def start_camera(self) -> None:
        # GỌI HIỆU ỨNG THÔNG BÁO TRƯỢT XUỐNG
        self.show_camera_instruction()
        if self.camera_running: return
        if not self.camera.start():
            messagebox.showerror("Lỗi", "Không mở được camera.")
            return
        self.camera_running = True
        self._update_preview()

    def _update_preview(self) -> None:
        if not self.camera_running or self.preview_label is None: return
        frame = self.camera.read()
        if frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # --- THUẬT TOÁN KÉO DÃN FULL KHUNG (FULL-FRAME AUTO-RESIZE) ---
            target_w = self.preview_label.winfo_width()
            target_h = self.preview_label.winfo_height()
            
            # Đảm bảo phần mềm đã load xong giao diện thì mới kéo giãn
            if target_w > 10 and target_h > 10:
                rgb = cv2.resize(rgb, (target_w, target_h))
            # -------------------------------------------------------------
            
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.preview_label.configure(image=imgtk, text="")
            self.preview_label.image = imgtk
        self.preview_label.after(30, self._update_preview)

    def capture_face(self) -> None:
        if not self.current_student_id:
            messagebox.showwarning("Cảnh báo", "Bạn phải chọn một sinh viên ở bảng bên phải trước khi chụp.")
            return
        if not self.camera_running:
            messagebox.showwarning("Cảnh báo", "Bạn phải Mở Camera trước.")
            return

        faces_dir = self.base_dir / "data" / "faces" / self.current_student_id
        faces_dir.mkdir(parents=True, exist_ok=True)
        file_path = faces_dir / f"{self.current_student_id}_{len(list(faces_dir.glob('*.jpg'))) + 1}.jpg"

        if self.camera.save_frame(str(file_path)):
            self.captured_paths.append(file_path)
            messagebox.showinfo("Thành công", f"Đã chụp ảnh thành công.\nHãy bấm [Mã hóa & Lưu] để hệ thống AI kiểm duyệt.")
        else:
            messagebox.showerror("Lỗi", "Không thể lưu ảnh.")

    def encode_and_save_face(self) -> None:
        if not self.current_student_id:
            messagebox.showwarning("Cảnh báo", "Bạn chưa chọn sinh viên nào.")
            return

        faces_dir = self.base_dir / "data" / "faces" / self.current_student_id
        image_files = list(faces_dir.glob("*.jpg"))
        
        if not image_files:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy ảnh nào! Vui lòng bấm 'Chụp ảnh' trước.")
            return

        # ==========================================
        # 1. TẠO POPUP GIAO DIỆN (MAIN THREAD)
        # ==========================================
        progress_dialog = tk.Toplevel(self.tree.winfo_toplevel())
        progress_dialog.title("AI Engine Processing")
        progress_dialog.geometry("380x160")
        progress_dialog.resizable(False, False)
        progress_dialog.configure(bg="white")
        progress_dialog.grab_set() 
        
        tk.Label(progress_dialog, text="🤖 ĐANG PHÂN TÍCH SINH TRẮC HỌC", bg="white", fg="#4f46e5", font=("Segoe UI", 11, "bold")).pack(pady=(20, 10))
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_dialog, variable=progress_var, maximum=100, length=300)
        progress_bar.pack(pady=5)
        
        status_label = tk.Label(progress_dialog, text="Khởi động engine AI... 0%", bg="white", fg="#64748b", font=("Segoe UI", 9))
        status_label.pack()

        # HÀM BẢO VỆ GIAO DIỆN: Chỉ cập nhật UI thông qua Main Thread
        def update_ui_safe(value, text):
            progress_var.set(value)
            status_label.config(text=text)

        # ==========================================
        # 2. HÀM CHẠY NGẦM (CHỈ TÍNH TOÁN, KHÔNG ĐỤNG VÀO UI)
        # ==========================================
        def process_ai():
            import time
            import cv2
            
            try:
                encoder = FaceEncoder()
                count = 0
                error_msg = ""
                duplicate_owner_id = None # Biến lưu kẻ gian lận
                
                # Giao tiếp với Main Thread để đổi chữ
                progress_dialog.after(0, lambda: update_ui_safe(5, "Đang tải dữ liệu an ninh..."))
                known_encodings, known_ids = encoder.load_all_encodings()
                
                for img_path in image_files:
                    progress_dialog.after(0, lambda: update_ui_safe(15, "Đang đọc dữ liệu điểm ảnh..."))
                    time.sleep(0.2) 
                    
                    image = cv2.imread(str(img_path))
                    if image is None: continue
                        
                    progress_dialog.after(0, lambda: update_ui_safe(35, "Đang kiểm tra độ sắc nét (Blur Check)..."))
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
                    
                    if blur_score < 70: 
                        error_msg = f"Ảnh quá mờ (Điểm chất lượng: {blur_score:.1f}/70).\nVui lòng giữ chắc tay và chụp lại!"
                        break
                        
                    progress_dialog.after(0, lambda: update_ui_safe(55, "Quét không gian khuôn mặt 3D..."))
                    try:
                        import face_recognition
                        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        face_locations = face_recognition.face_locations(rgb_image)
                        
                        if len(face_locations) == 0:
                            error_msg = "AI không tìm thấy khuôn mặt nào trong ảnh!"
                            break
                        elif len(face_locations) > 1:
                            error_msg = f"Phát hiện {len(face_locations)} người trong khung hình!"
                            break
                    except ImportError: pass 
                        
                    progress_dialog.after(0, lambda: update_ui_safe(75, "Đang phân tích & đối chiếu an ninh..."))
                    encoding = encoder.get_face_encoding(image)
                    
                    if encoding is not None:
                        is_duplicate = False
                        if known_encodings:
                            import face_recognition
                            face_distances = face_recognition.face_distance(known_encodings, encoding)
                            for i, distance in enumerate(face_distances):
                                if distance < 0.45:
                                    owner_id = known_ids[i]
                                    if owner_id != self.current_student_id:
                                        # Nắm cổ kẻ gian lận, chuyển về Main Thread xử lý Database
                                        duplicate_owner_id = owner_id 
                                        is_duplicate = True
                                        break
                                        
                        if is_duplicate: break 
                            
                        progress_dialog.after(0, lambda: update_ui_safe(90, "Kiểm duyệt thành công! Đang lưu DB..."))
                        if encoder.save_encoding(self.current_student_id, encoding, str(img_path)):
                            count += 1
                    else:
                        error_msg = "Không thể mã hóa khuôn mặt này!"
                        break
                
                progress_dialog.after(0, lambda: update_ui_safe(100, "Hoàn tất!"))
                
                # Trả kết quả về Main Thread an toàn
                progress_dialog.after(300, lambda: finish_process(count, error_msg, duplicate_owner_id))
                
            except Exception as exc:
                progress_dialog.after(0, lambda: handle_error(str(exc)))

        # ==========================================
        # 3. XỬ LÝ KẾT QUẢ VÀ DATABASE (MAIN THREAD)
        # ==========================================
        def finish_process(count, error_msg, duplicate_owner_id):
            progress_dialog.destroy()
            
            # Luồng chính tự do gọi Database mà không sợ bị chặn
            if duplicate_owner_id:
                owner_info = self.db.fetchone("SELECT full_name FROM students WHERE student_id = ?", (duplicate_owner_id,))
                owner_name = owner_info["full_name"] if owner_info else duplicate_owner_id
                error_msg = f"🚫 PHÁT HIỆN GIAN LẬN 🚫\nKhuôn mặt này đã được đăng ký bởi sinh viên:\n{owner_name} ({duplicate_owner_id})\n\nVui lòng không sử dụng khuôn mặt của người khác!"

            if error_msg:
                messagebox.showerror("AI Reject (Từ chối duyệt)", error_msg)
                
                # Dọn rác triệt để
                import os
                for img_path in image_files:
                    try: os.remove(str(img_path)) 
                    except: pass
                try: faces_dir.rmdir() 
                except: pass
                
                self.load_students() 
                
            elif count > 0:
                messagebox.showinfo("Thành công", f"Đã mã hóa 100% thành công cho sinh viên {self.current_student_id}.")
                self.load_students() 
            else:
                messagebox.showwarning("Cảnh báo", "Xử lý thất bại. Vui lòng thử lại.")

        def handle_error(err):
            progress_dialog.destroy()
            messagebox.showerror("Lỗi hệ thống", f"Tiến trình bị gián đoạn:\n{err}")

        # KÍCH HOẠT LUỒNG CHẠY NGẦM
        import threading
        threading.Thread(target=process_ai, daemon=True).start()

    def stop_camera(self) -> None:
        if not self.camera_running: return
        self.camera_running = False
        self.camera.stop()
        if self.preview_label is not None:
            self.preview_label.configure(image="", text="Camera Preview\n(Nhấn Mở Camera để bắt đầu)")
            self.preview_label.image = None

    # ==========================================
    # TÍNH NĂNG IMPORT TỪ EXCEL/CSV (BẢN PRO)
    # ==========================================
    def import_from_excel(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Chọn file danh sách sinh viên",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
        )
        if not file_path:
            return
            
        try:
            import pandas as pd
            
            # 1. Bí quyết 1: Ép pandas đọc tất cả dưới dạng chữ (str) ngay từ đầu để giữ nguyên định dạng
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, dtype=str)
            else:
                df = pd.read_excel(file_path, dtype=str)
                
            # Làm sạch tên cột
            df.columns = df.columns.astype(str).str.strip().str.lower()
            
            if not any(col in df.columns for col in ['mssv', 'student_id', 'mã sinh viên']):
                messagebox.showerror("Lỗi File", "File Excel phải có ít nhất cột 'MSSV' hoặc 'Mã sinh viên'")
                return
                
            success_count = 0
            skip_count = 0
            
            for index, row in df.iterrows():
                # Bí quyết 2: Hàm dọn rác do Excel tự sinh ra
                def clean_val(val):
                    if pd.isna(val): return ""
                    v = str(val).strip()
                    if v.lower() == 'nan': return ""
                    if v.endswith('.0'): v = v[:-2] # Cắt đuôi .0 nếu Excel tự nhận là số thập phân
                    return v

                mssv = clean_val(row.get('mssv', row.get('student_id', row.get('mã sinh viên'))))
                name = clean_val(row.get('họ tên', row.get('full_name', row.get('tên', row.get('họ và tên')))))
                class_name = clean_val(row.get('lớp', row.get('class', row.get('class_name'))))
                faculty = clean_val(row.get('khoa', row.get('faculty', row.get('department'))))
                email = clean_val(row.get('email'))
                phone = clean_val(row.get('sđt', row.get('số điện thoại', row.get('phone'))))
                
                # Bí quyết 3: Tự động đắp lại số 0 cho SĐT nếu Excel đã lỡ xóa
                if phone and len(phone) == 9 and not phone.startswith('0'):
                    phone = '0' + phone
                
                if not mssv:
                    continue
                    
                existing = self.db.fetchone("SELECT student_id FROM students WHERE student_id = ?", (mssv,))
                if existing:
                    skip_count += 1
                    continue
                    
                # Đã gỡ bỏ cột Khoa để khớp 100% với file init_db.py của bạn
                # Đưa cột Khoa (faculty) trở lại để chèn vào DB
                self.db.execute(
                    "INSERT INTO students (student_id, full_name, class_name, faculty, email, phone) VALUES (?, ?, ?, ?, ?, ?)",
                    (mssv, name, class_name, faculty, email, phone)
                )
                success_count += 1
                
            if hasattr(self, 'load_data'):
                self.load_data()
            elif hasattr(self, 'load_students'):
                self.load_students()
                
            messagebox.showinfo("Hoàn tất", f"✅ Đã nhập thành công: {success_count} sinh viên.\n⚠️ Bỏ qua: {skip_count} sinh viên (do trùng MSSV).")
            
        except Exception as e:
            messagebox.showerror("Lỗi xử lý", f"Không thể đọc file:\n{e}")

    def manage_face(self):
        # 1. Kiểm tra xem đã chọn sinh viên trên bảng chưa
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng click chọn một sinh viên trên bảng trước!")
            return
            
        item = self.tree.item(selected[0])
        mssv = str(item['values'][0])
        name = str(item['values'][1])
        status = str(item['values'][6])
        
        # 2. Nếu chưa đăng ký thì không có ảnh để xem
        if "Chưa" in status:
            messagebox.showinfo("Thông báo", f"Sinh viên {name} chưa có dữ liệu khuôn mặt!")
            return
            
        faces_dir = self.base_dir / "data" / "faces" / mssv
        image_files = list(faces_dir.glob("*.jpg"))
        
        if not image_files:
            messagebox.showerror("Lỗi", "Không tìm thấy file ảnh vật lý trong thư mục!")
            return
            
        # 3. Tạo Popup hiển thị
        dialog = tk.Toplevel(self.tree.winfo_toplevel())
        dialog.title(f"Quản lý ảnh AI - {name}")
        dialog.geometry("400x480")
        dialog.resizable(False, False)
        dialog.configure(bg="white")
        dialog.grab_set()
        
        tk.Label(dialog, text=f"Dữ liệu sinh trắc học", bg="white", font=("Segoe UI", 13, "bold"), fg="#334155").pack(pady=(20, 5))
        tk.Label(dialog, text=f"Sinh viên: {name}\nMSSV: {mssv}", bg="white", font=("Segoe UI", 10), fg="#64748b", justify="center").pack(pady=(0, 15))
        
        # 4. Hiển thị ảnh bằng thư viện PIL
        try:
            from PIL import Image, ImageTk
            img_path = image_files[0] # Lấy ảnh đầu tiên đang lưu
            img = Image.open(img_path)
            # Crop/Resize ảnh về hình vuông cho đẹp
            img = img.resize((220, 220), Image.Resampling.LANCZOS) 
            photo = ImageTk.PhotoImage(img)
            
            img_label = tk.Label(dialog, image=photo, bg="#f1f5f9", bd=2, relief="groove")
            img_label.image = photo # Giữ reference để ảnh không bị mất
            img_label.pack(pady=10)
        except Exception as e:
            tk.Label(dialog, text=f"Lỗi hiển thị ảnh: {e}", bg="white", fg="red").pack()
            
        # 5. Hàm thực thi lệnh XÓA
        def delete_face():
            if messagebox.askyesno("Xác nhận nguy hiểm", f"Bạn có chắc chắn muốn XÓA ảnh khuôn mặt của {name} không?\n\nHành động này không thể hoàn tác, sinh viên sẽ phải đứng trước camera để chụp lại.", parent=dialog):
                import shutil
                try:
                    shutil.rmtree(faces_dir) # Xóa sạch thư mục chứa ảnh của SV này
                    messagebox.showinfo("Thành công", f"Đã xóa dữ liệu khuôn mặt của {name}.", parent=dialog)
                    dialog.destroy()
                    self.load_students() # Load lại bảng để Trạng thái chuyển thành màu Đỏ
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể xóa dữ liệu: {e}", parent=dialog)
                    
        # Nút Xóa
        tk.Button(dialog, text="🗑️ Xóa khuôn mặt (Chụp lại)", command=delete_face, bg="#ef4444", fg="white", activebackground="#b91c1c", activeforeground="white", bd=0, padx=20, pady=10, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(pady=(15, 10))

    def select_all(self, event=None):
        """Hàm tự động bôi đen toàn bộ các dòng đang hiển thị trên bảng"""
        all_items = self.tree.get_children()
        if all_items:
            self.tree.selection_set(all_items)
        return "break"