# StudentAttendance/gui/login.py
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from gui.dashboard import DashboardWindow
from utils.database import DatabaseManager
from utils.helpers import (
    center_window,
    modern_theme_colors,
    safe_showerror,
)

class LoginWindow:
    def __init__(self, db: DatabaseManager, base_dir: Path):
        self.db = db
        self.base_dir = base_dir

        self.root = tk.Tk()
        self.root.title("Student Attendance - Login")
        self.root.geometry("750x450")
        self.root.resizable(False, False)

        self.colors = modern_theme_colors()
        self.root.configure(bg="white")
        center_window(self.root, 750, 450)

        # Mật khẩu điền sẵn
        self.username_var = tk.StringVar(value="admin")
        self.password_var = tk.StringVar(value="admin123") # Chú ý: Đổi lại thành mật khẩu của bạn
        self.show_pass_var = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        # ==========================================
        # ĐỒNG BỘ MÀU SẮC THƯƠNG HIỆU (EAUT Cyan)
        # ==========================================
        brand_color = "#00a1e4" # Nền xanh lơ của logo
        brand_color_dark = "#0288d1" # Màu khi bấm nút

        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(fill="both", expand=True)

        # --- NỬA TRÁI (Branding / Banner) ---
        # Đổi màu nền của cột bên trái thành màu brand_color
        left_panel = tk.Frame(main_frame, bg=brand_color, width=320)
        left_panel.pack(side="left", fill="y")
        left_panel.pack_propagate(False)

        img_loaded = False
        try:
            from PIL import Image, ImageTk
            
            img_path_png = self.base_dir / "assets" / "logo.png"
            img_path_jpg = self.base_dir / "assets" / "logo.jpg"
            img_path = img_path_png if img_path_png.exists() else (img_path_jpg if img_path_jpg.exists() else None)
            
            if img_path:
                img = Image.open(img_path)
                img = img.resize((140, 140), Image.Resampling.LANCZOS)
                
                self.logo_image = ImageTk.PhotoImage(img) 
                
                # Label chứa ảnh cũng được hòa màu nền brand_color
                tk.Label(left_panel, image=self.logo_image, bg=brand_color).pack(pady=(50, 15))
                img_loaded = True
        except Exception:
            pass

        if not img_loaded:
            tk.Label(left_panel, text="🎓", font=("Segoe UI", 60), bg=brand_color, fg="white").pack(pady=(50, 15))

        tk.Label(left_panel, text="ATTENDANCE\nSYSTEM", font=("Segoe UI", 22, "bold"), bg=brand_color, fg="white", justify="center").pack(pady=(0, 10))
        tk.Label(left_panel, text="Quản lý sinh viên thông minh\nbằng công nghệ nhận diện", font=("Segoe UI", 11), bg=brand_color, fg="#f0f9ff", justify="center").pack()

        # --- NỬA PHẢI (Form Đăng nhập) ---
        right_panel = tk.Frame(main_frame, bg="white")
        right_panel.pack(side="right", fill="both", expand=True)

        form_container = tk.Frame(right_panel, bg="white")
        form_container.place(relx=0.5, rely=0.5, anchor="center", width=300)

        tk.Label(form_container, text="Đăng nhập", font=("Segoe UI", 24, "bold"), bg="white", fg=self.colors["text"]).pack(anchor="w", pady=(0, 5))
        tk.Label(form_container, text="Vui lòng nhập tài khoản quản trị viên", font=("Segoe UI", 10), bg="white", fg=self.colors["muted"]).pack(anchor="w", pady=(0, 30))

        tk.Label(form_container, text="Tên đăng nhập", bg="white", fg=self.colors["text"], font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Entry(form_container, textvariable=self.username_var, font=("Segoe UI", 12)).pack(fill="x", pady=(5, 20), ipady=5)

        tk.Label(form_container, text="Mật khẩu", bg="white", fg=self.colors["text"], font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.pwd_entry = ttk.Entry(form_container, textvariable=self.password_var, show="*", font=("Segoe UI", 12))
        self.pwd_entry.pack(fill="x", pady=(5, 10), ipady=5)

        def toggle_password():
            if self.show_pass_var.get():
                self.pwd_entry.config(show="")
            else:
                self.pwd_entry.config(show="*")

        tk.Checkbutton(
            form_container, text="Hiển thị mật khẩu", variable=self.show_pass_var, command=toggle_password,
            bg="white", fg=self.colors["muted"], font=("Segoe UI", 9), activebackground="white", cursor="hand2"
        ).pack(anchor="w", pady=(0, 25))

        # Đổi màu Nút bấm thành màu brand_color để tone-sur-tone với logo
        tk.Button(
            form_container, text="ĐĂNG NHẬP", bg=brand_color, fg="white",
            activebackground=brand_color_dark, activeforeground="white",
            relief="flat", cursor="hand2", font=("Segoe UI", 11, "bold"), command=self._login,
        ).pack(fill="x", ipady=10)

        self.root.bind("<Return>", lambda e: self._login())

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if username == "" or password == "":
            messagebox.showwarning("Thông báo", "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
            return

        try:
            ok = False
            tables = [row[0] for row in self.db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")]
            target_table = None
            for t in ["admin", "users", "accounts", "user"]:
                if t in tables:
                    target_table = t
                    break
            
            if target_table:
                user_data = self.db.fetchone(f"SELECT * FROM {target_table} WHERE username = ? AND password = ?", (username, password))
                if user_data:
                    ok = True

            if not ok:
                ok = self.db.verify_admin(username, password)

            if not ok:
                messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu.")
                return

            self.root.destroy()
            DashboardWindow(self.db, self.base_dir).run()

        except Exception as exc:
            safe_showerror("Lỗi", f"Không thể đăng nhập:\n{exc}")

    def run(self):
        self.root.mainloop()