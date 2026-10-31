import tkinter as tk
from tkinter import ttk, messagebox
import requests

API_URL = "http://127.0.0.1:5000/api"

class SchoolClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión Escolar")
        self.root.geometry("680x500")
        self.current_user = None
        self.show_login()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def get_headers(self):
        if self.current_user:
            return {"X-User-Id": str(self.current_user["id"])}
        return {}

    # ==========================================
    # PANTALLA DE LOGIN
    # ==========================================
    def show_login(self):
        self.clear_window()
        self.current_user = None

        frame = ttk.Frame(self.root, padding=25)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(frame, text="Iniciar Sesión", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=15)

        ttk.Label(frame, text="Usuario:").grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.ent_user = ttk.Entry(frame, width=25)
        self.ent_user.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Contraseña:").grid(row=2, column=0, sticky="e", pady=5, padx=5)
        self.ent_pass = ttk.Entry(frame, show="*", width=25)
        self.ent_pass.grid(row=2, column=1, pady=5)

        btn_login = ttk.Button(frame, text="Ingresar", command=self.do_login)
        btn_login.grid(row=3, column=0, columnspan=2, pady=15, ipadx=10)

        hint = "Usuarios de prueba (pass: 123):\nadmin | profe1 | alumno1"
        ttk.Label(frame, text=hint, foreground="gray", justify="center").grid(row=4, column=0, columnspan=2, pady=5)

    def do_login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pass.get().strip()
        try:
            res = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
            if res.status_code == 200:
                self.current_user = res.json()["user"]
                role = self.current_user["role"]
                if role == "admin":
                    self.show_admin_dashboard()
                elif role == "teacher":
                    self.show_teacher_dashboard()
                elif role == "student":
                    self.show_student_dashboard()
            else:
                messagebox.showerror("Error", res.json().get("error", "Error al iniciar sesión"))
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Error de Red", "No se pudo conectar con server.py en el puerto 5000")

    # ==========================================
    # PANEL DE ADMINISTRADOR
    # ==========================================
    def show_admin_dashboard(self):
        self.clear_window()
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text=f"Panel Admin: {self.current_user['name']}", font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(top, text="Cerrar Sesión", command=self.show_login).pack(side="right")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: Registrar Usuarios
        tab_users = ttk.Frame(notebook, padding=15)
        notebook.add(tab_users, text="Registrar Alumnos / Profesores")

        ttk.Label(tab_users, text="Nombre Completo:").grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.adm_name = ttk.Entry(tab_users, width=30)
        self.adm_name.grid(row=0, column=1, pady=5)

        ttk.Label(tab_users, text="Username:").grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.adm_user = ttk.Entry(tab_users, width=30)
        self.adm_user.grid(row=1, column=1, pady=5)

        ttk.Label(tab_users, text="Contraseña:").grid(row=2, column=0, sticky="e", pady=5, padx=5)
        self.adm_pass = ttk.Entry(tab_users, width=30)
        self.adm_pass.grid(row=2, column=1, pady=5)

        ttk.Label(tab_users, text="Rol:").grid(row=3, column=0, sticky="e", pady=5, padx=5)
        self.adm_role = ttk.Combobox(tab_users, values=["student", "teacher"], state="readonly", width=27)
        self.adm_role.current(0)
        self.adm_role.grid(row=3, column=1, pady=5)

        ttk.Button(tab_users, text="Registrar Usuario", command=self.admin_create_user).grid(row=4, column=0, columnspan=2, pady=15)

        # Tab 2: Crear Clases y Asignar Profesor
        tab_classes = ttk.Frame(notebook, padding=15)
        notebook.add(tab_classes, text="Crear y Ver Clases")

        frm_create = ttk.LabelFrame(tab_classes, text="Nueva Clase", padding=10)
        frm_create.pack(fill="x", pady=5)

        ttk.Label(frm_create, text="Materia:").grid(row=0, column=0, padx=5, pady=5)
        self.adm_cls_name = ttk.Entry(frm_create, width=22)
        self.adm_cls_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frm_create, text="Profesor:").grid(row=0, column=2, padx=5, pady=5)
        self.adm_teacher_cb = ttk.Combobox(frm_create, state="readonly", width=22)
        self.adm_teacher_cb.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(frm_create, text="Generar Clase", command=self.admin_create_class).grid(row=0, column=4, padx=10, pady=5)

        self.adm_cls_list = tk.Listbox(tab_classes, height=12)
        self.adm_cls_list.pack(fill="both", expand=True, pady=10)

        self.load_admin_data()

    def load_admin_data(self):
        # Cargar profesores en combobox
        res_t = requests.get(f"{API_URL}/users?role=teacher", headers=self.get_headers())
        if res_t.status_code == 200:
            self.teachers_list = res_t.json()
            self.adm_teacher_cb["values"] = [f"{t['id']} - {t['name']}" for t in self.teachers_list]
            if self.teachers_list:
                self.adm_teacher_cb.current(0)

        # Cargar clases
        res_c = requests.get(f"{API_URL}/classes", headers=self.get_headers())
        if res_c.status_code == 200:
            self.adm_cls_list.delete(0, tk.END)
            for c in res_c.json():
                alumnos_str = ", ".join(c["students"]) if c["students"] else "Sin alumnos"
                self.adm_cls_list.insert(tk.END, f"[{c['code']}] {c['name']} | Prof: {c['teacher_name']} | Alumnos: {alumnos_str}")

    def admin_create_user(self):
        payload = {
            "name": self.adm_name.get().strip(),
            "username": self.adm_user.get().strip(),
            "password": self.adm_pass.get().strip(),
            "role": self.adm_role.get()
        }
        res = requests.post(f"{API_URL}/users", json=payload, headers=self.get_headers())
        if res.status_code == 201:
            messagebox.showinfo("Éxito", f"Usuario '{payload['username']}' creado con éxito.")
            self.adm_name.delete(0, tk.END)
            self.adm_user.delete(0, tk.END)
            self.adm_pass.delete(0, tk.END)
            self.load_admin_data()
        else:
            messagebox.showerror("Error", res.json().get("error", "Error al crear"))

    def admin_create_class(self):
        if not getattr(self, "teachers_list", None) or not self.adm_teacher_cb.get():
            messagebox.showwarning("Atención", "Primero registra al menos un profesor.")
            return
        teacher_id = int(self.adm_teacher_cb.get().split(" - ")[0])
        name = self.adm_cls_name.get().strip()
        res = requests.post(f"{API_URL}/classes", json={"name": name, "teacher_id": teacher_id}, headers=self.get_headers())
        if res.status_code == 201:
            cls_data = res.json()
            messagebox.showinfo("Clase Creada", f"Clase '{cls_data['name']}' creada.\nCódigo de acceso: {cls_data['code']}")
            self.adm_cls_name.delete(0, tk.END)
            self.load_admin_data()
        else:
            messagebox.showerror("Error", res.json().get("error", "No se pudo crear la clase"))

    # ==========================================
    # PANEL DE PROFESOR
    # ==========================================
    def show_teacher_dashboard(self):
        self.clear_window()
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text=f"Panel Profesor: {self.current_user['name']}", font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(top, text="Cerrar Sesión", command=self.show_login).pack(side="right")

        frm = ttk.Frame(self.root, padding=15)
        frm.pack(fill="both", expand=True)

        frm_new = ttk.LabelFrame(frm, text="Crear Nueva Clase", padding=10)
        frm_new.pack(fill="x", pady=5)
        ttk.Label(frm_new, text="Nombre de la Materia:").pack(side="left", padx=5)
        self.tch_cls_name = ttk.Entry(frm_new, width=30)
        self.tch_cls_name.pack(side="left", padx=5)
        ttk.Button(frm_new, text="Generar Código de 4 Dígitos", command=self.teacher_create_class).pack(side="left", padx=10)

        ttk.Label(frm, text="Mis Clases y Alumnos Inscritos:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(15, 5))
        self.tch_cls_list = tk.Listbox(frm, height=14)
        self.tch_cls_list.pack(fill="both", expand=True)

        self.load_teacher_classes()

    def teacher_create_class(self):
        name = self.tch_cls_name.get().strip()
        res = requests.post(f"{API_URL}/classes", json={"name": name}, headers=self.get_headers())
        if res.status_code == 201:
            data = res.json()
            messagebox.showinfo("Código Generado", f"Clase: {data['name']}\nCódigo para alumnos: {data['code']}")
            self.tch_cls_name.delete(0, tk.END)
            self.load_teacher_classes()
        else:
            messagebox.showerror("Error", res.json().get("error", "Error"))

    def load_teacher_classes(self):
        res = requests.get(f"{API_URL}/classes", headers=self.get_headers())
        if res.status_code == 200:
            self.tch_cls_list.delete(0, tk.END)
            for c in res.json():
                alumnos = ", ".join(c["students"]) if c["students"] else "Ningún alumno inscrito aún"
                self.tch_cls_list.insert(tk.END, f"Código: {c['code']} | Materia: {c['name']} | Inscritos: {alumnos}")

    # ==========================================
    # PANEL DE ALUMNO
    # ==========================================
    def show_student_dashboard(self):
        self.clear_window()
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text=f"Panel Alumno: {self.current_user['name']}", font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(top, text="Cerrar Sesión", command=self.show_login).pack(side="right")

        frm = ttk.Frame(self.root, padding=15)
        frm.pack(fill="both", expand=True)

        frm_join = ttk.LabelFrame(frm, text="Unirse a una Clase", padding=10)
        frm_join.pack(fill="x", pady=5)
        ttk.Label(frm_join, text="Código de 4 dígitos:").pack(side="left", padx=5)
        self.std_code = ttk.Entry(frm_join, width=15)
        self.std_code.pack(side="left", padx=5)
        ttk.Button(frm_join, text="Vincularme a la Clase", command=self.student_join_class).pack(side="left", padx=10)

        ttk.Label(frm, text="Mis Clases Inscritas:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(15, 5))
        self.std_cls_list = tk.Listbox(frm, height=14)
        self.std_cls_list.pack(fill="both", expand=True)

        self.load_student_classes()

    def student_join_class(self):
        code = self.std_code.get().strip()
        res = requests.post(f"{API_URL}/classes/join", json={"code": code}, headers=self.get_headers())
        if res.status_code == 200:
            cls_info = res.json()["class"]
            messagebox.showinfo("Inscripción Exitosa", f"Te has unido a: {cls_info['name']}")
            self.std_code.delete(0, tk.END)
            self.load_student_classes()
        else:
            messagebox.showerror("Error", res.json().get("error", "No fue posible unirse"))

    def load_student_classes(self):
        res = requests.get(f"{API_URL}/classes", headers=self.get_headers())
        if res.status_code == 200:
            self.std_cls_list.delete(0, tk.END)
            for c in res.json():
                self.std_cls_list.insert(tk.END, f"[{c['code']}] {c['name']} - Profesor: {c['teacher_name']}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SchoolClientApp(root)
    root.mainloop()