
import os
import json
import random
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_FILE = "db.json"

# ==========================================
# CAPA DE ACCESO A DATOS (Preparada para MySQL)
# ==========================================
class DataRepository:
    def __init__(self, filepath):
        self.filepath = filepath
        self._init_db()

    def _init_db(self):
        if not os.path.exists(self.filepath):
            initial_data = {
                "users": [
                    {"id": 1, "username": "admin", "password": "123", "name": "Administrador", "role": "admin"},
                    {"id": 2, "username": "profe1", "password": "123", "name": "Prof. García", "role": "teacher"},
                    {"id": 3, "username": "alumno1", "password": "123", "name": "Juan Pérez", "role": "student"}
                ],
                "classes": [],
                "enrollments": [] # {"student_id": 3, "class_code": "1234"}
            }
            self._write(initial_data)

    def _read(self):
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def authenticate(self, username, password):
        data = self._read()
        for u in data["users"]:
            if u["username"] == username and u["password"] == password:
                return {"id": u["id"], "username": u["username"], "name": u["name"], "role": u["role"]}
        return None

    def get_user_by_id(self, user_id):
        data = self._read()
        return next((u for u in data["users"] if u["id"] == user_id), None)

    def get_users(self, role=None):
        data = self._read()
        users = [{"id": u["id"], "username": u["username"], "name": u["name"], "role": u["role"]} for u in data["users"]]
        if role:
            return [u for u in users if u["role"] == role]
        return users

    def create_user(self, username, password, name, role):
        data = self._read()
        if any(u["username"] == username for u in data["users"]):
            return None
        new_id = max([u["id"] for u in data["users"]], default=0) + 1
        new_user = {"id": new_id, "username": username, "password": password, "name": name, "role": role}
        data["users"].append(new_user)
        self._write(data)
        return {"id": new_id, "username": username, "name": name, "role": role}

    def create_class(self, class_name, teacher_id):
        data = self._read()
        # Generar código único de 4 dígitos
        existing_codes = {c["code"] for c in data["classes"]}
        while True:
            code = f"{random.randint(0, 9999):04d}"
            if code not in existing_codes:
                break
        
        new_id = max([c["id"] for c in data["classes"]], default=0) + 1
        new_class = {"id": new_id, "name": class_name, "teacher_id": teacher_id, "code": code}
        data["classes"].append(new_class)
        self._write(data)
        return new_class

    def enroll_student(self, student_id, class_code):
        data = self._read()
        target_class = next((c for c in data["classes"] if c["code"] == class_code), None)
        if not target_class:
            return "NOT_FOUND", None
        
        if any(e["student_id"] == student_id and e["class_code"] == class_code for e in data["enrollments"]):
            return "ALREADY_ENROLLED", None

        data["enrollments"].append({"student_id": student_id, "class_code": class_code})
        self._write(data)
        return "OK", target_class

    def get_classes_by_role(self, user):
        data = self._read()
        users_map = {u["id"]: u["name"] for u in data["users"]}
        role = user["role"]
        
        if role == "admin":
            result = []
            for c in data["classes"]:
                students = [users_map.get(e["student_id"], "Desconocido") for e in data["enrollments"] if e["class_code"] == c["code"]]
                result.append({**c, "teacher_name": users_map.get(c["teacher_id"], "N/A"), "students": students})
            return result
            
        elif role == "teacher":
            result = []
            for c in data["classes"]:
                if c["teacher_id"] == user["id"]:
                    students = [users_map.get(e["student_id"], "Desconocido") for e in data["enrollments"] if e["class_code"] == c["code"]]
                    result.append({**c, "students": students})
            return result
            
        elif role == "student":
            enrolled_codes = {e["class_code"] for e in data["enrollments"] if e["student_id"] == user["id"]}
            result = []
            for c in data["classes"]:
                if c["code"] in enrolled_codes:
                    result.append({**c, "teacher_name": users_map.get(c["teacher_id"], "N/A")})
            return result
        return []

    def get_class_by_code(self, code):
        data = self._read()
        target = next((c for c in data["classes"] if c["code"] == code), None)
        if not target:
            return None
        users_map = {u["id"]: u["name"] for u in data["users"]}
        students = [{"id": e["student_id"], "name": users_map.get(e["student_id"], "N/A")} 
                    for e in data["enrollments"] if e["class_code"] == code]
        return {**target, "teacher_name": users_map.get(target["teacher_id"], "N/A"), "students": students}

    def unenroll_student(self, student_id, class_code):
        data = self._read()
        initial_len = len(data["enrollments"])
        data["enrollments"] = [e for e in data["enrollments"] if not (e["student_id"] == student_id and e["class_code"] == class_code)]
        if len(data["enrollments"]) == initial_len:
            return False
        self._write(data)
        return True

db = DataRepository(DB_FILE)

# Helper para validar usuario desde headers
def get_current_user():
    user_id = request.headers.get("X-User-Id")
    if not user_id or not user_id.isdigit():
        return None
    return db.get_user_by_id(int(user_id))

# ==========================================
# ENDPOINTS REST
# ==========================================

@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json() or {}
    username = body.get("username")
    password = body.get("password")
    if not username or not password:
        return jsonify({"error": "Faltan credenciales"}), 400
    
    user = db.authenticate(username, password)
    if not user:
        return jsonify({"error": "Credenciales inválidas"}), 401
    return jsonify({"message": "Login exitoso", "user": user}), 200

@app.route("/api/users", methods=["POST"])
def register_user():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    if current_user["role"] != "admin":
        return jsonify({"error": "No autorizado. Solo administradores pueden registrar usuarios"}), 403

    body = request.get_json() or {}
    username = body.get("username")
    password = body.get("password")
    name = body.get("name")
    role = body.get("role")

    if not all([username, password, name, role]) or role not in ["student", "teacher", "admin"]:
        return jsonify({"error": "Datos inválidos o rol incorrecto"}), 400

    new_user = db.create_user(username, password, name, role)
    if not new_user:
        return jsonify({"error": "El nombre de usuario ya existe"}), 409
    return jsonify(new_user), 201

@app.route("/api/users", methods=["GET"])
def list_users():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    if current_user["role"] != "admin":
        return jsonify({"error": "Solo el admin puede listar usuarios"}), 403

    role_filter = request.args.get("role")
    return jsonify(db.get_users(role_filter)), 200

@app.route("/api/classes", methods=["POST"])
def create_class():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    if current_user["role"] not in ["admin", "teacher"]:
        return jsonify({"error": "Solo profesores o administradores pueden crear clases"}), 403

    body = request.get_json() or {}
    class_name = body.get("name")
    teacher_id = body.get("teacher_id") if current_user["role"] == "admin" else current_user["id"]

    if not class_name or not teacher_id:
        return jsonify({"error": "Nombre de clase y teacher_id son requeridos"}), 400

    teacher = db.get_user_by_id(int(teacher_id))
    if not teacher or teacher["role"] != "teacher":
        return jsonify({"error": "Profesor no encontrado o rol inválido"}), 404

    new_class = db.create_class(class_name, int(teacher_id))
    return jsonify(new_class), 201

@app.route("/api/classes", methods=["GET"])
def get_classes():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    classes = db.get_classes_by_role(current_user)
    return jsonify(classes), 200

@app.route("/api/classes/<string:code>", methods=["GET"])
def get_class_detail(code):
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    if len(code) != 4 or not code.isdigit():
        return jsonify({"error": "El código debe ser de 4 dígitos numéricos"}), 400

    cls_info = db.get_class_by_code(code)
    if not cls_info:
        return jsonify({"error": "Clase no encontrada"}), 404
    return jsonify(cls_info), 200

@app.route("/api/classes/join", methods=["POST"])
def join_class():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    if current_user["role"] != "student":
        return jsonify({"error": "Solo los alumnos pueden unirse a clases por código"}), 403

    body = request.get_json() or {}
    code = str(body.get("code", "")).strip()
    if len(code) != 4 or not code.isdigit():
        return jsonify({"error": "El código debe tener exactamente 4 números"}), 400

    status, cls_obj = db.enroll_student(current_user["id"], code)
    if status == "NOT_FOUND":
        return jsonify({"error": "No existe ninguna clase con ese código"}), 404
    if status == "ALREADY_ENROLLED":
        return jsonify({"error": "El alumno ya está inscrito en esta clase"}), 409

    return jsonify({"message": "Inscripción exitosa", "class": cls_obj}), 200

@app.route("/api/classes/<string:code>/students/<int:student_id>", methods=["DELETE"])
def remove_student_from_class(code, student_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    if current_user["role"] not in ["admin", "teacher"]:
        return jsonify({"error": "No tienes permisos para dar de baja alumnos"}), 403

    deleted = db.unenroll_student(student_id, code)
    if not deleted:
        return jsonify({"error": "Registro de inscripción no encontrado"}), 404
    return jsonify({"message": "Alumno dado de baja de la clase"}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)