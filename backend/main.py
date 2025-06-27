from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import sqlite3
from datetime import datetime

app = FastAPI()


# === MODELOS Pydantic ===
class UsuarioIn(BaseModel):
    nombre: str
    apellidos: str
    email: EmailStr
    telefono: Optional[str] = None
    direccion: Optional[str] = None


class UsuarioOut(UsuarioIn):
    id_cliente: int
    fecha_registro: Optional[str]


class FacturaIn(BaseModel):
    email: EmailStr
    descripcion: str
    monto: float
    estado: str


class FacturaOut(BaseModel):
    numero_factura: int
    descripcion: str
    monto: float
    estado: str
    fecha_emision: str


# === CONEXIÓN DB ===
class ConexionDB:
    def __init__(self, db_path="data/datos_clientes.db"):
        self.db_path = db_path

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()

    def commit(self):
        self.conn.commit()


# === ENDPOINTS ===

@app.post("/usuarios/", response_model=UsuarioOut)
def registrar_usuario(usuario: UsuarioIn):
    with ConexionDB() as db:
        # Validación de email existente
        db.cursor.execute("SELECT * FROM usuarios WHERE email = ?", (usuario.email,))
        if db.cursor.fetchone():
            raise HTTPException(status_code=400, detail="El email ya está registrado")

        db.cursor.execute("""
            INSERT INTO usuarios (nombre, apellidos, email, telefono, direccion)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario.nombre, usuario.apellidos, usuario.email, usuario.telefono, usuario.direccion))
        db.commit()
        id_cliente = db.cursor.lastrowid
        fecha_registro = datetime.today().strftime('%d/%m/%Y')

        return UsuarioOut(id_cliente=id_cliente, fecha_registro=fecha_registro, **usuario.dict())


@app.get("/usuarios/", response_model=List[UsuarioOut])
def listar_usuarios():
    with ConexionDB() as db:
        db.cursor.execute("SELECT * FROM usuarios")
        usuarios = db.cursor.fetchall()
        return [UsuarioOut(
            id_cliente=u["id_cliente"],
            nombre=u["nombre"],
            apellidos=u["apellidos"],
            email=u["email"],
            telefono=u["telefono"],
            direccion=u["direccion"],
            fecha_registro=u["fecha_registro"]
        ) for u in usuarios]


@app.get("/usuarios/{email}", response_model=UsuarioOut)
def buscar_usuario(email: EmailStr):
    with ConexionDB() as db:
        db.cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        u = db.cursor.fetchone()
        if not u:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return UsuarioOut(
            id_cliente=u["id_cliente"],
            nombre=u["nombre"],
            apellidos=u["apellidos"],
            email=u["email"],
            telefono=u["telefono"],
            direccion=u["direccion"],
            fecha_registro=u["fecha_registro"]
        )


@app.post("/facturas/")
def crear_factura(factura: FacturaIn):
    if factura.estado not in ["Pendiente", "Pagada", "Cancelada"]:
        raise HTTPException(status_code=400, detail="Estado no válido")

    with ConexionDB() as db:
        db.cursor.execute("SELECT id_cliente FROM usuarios WHERE email = ?", (factura.email,))
        usuario = db.cursor.fetchone()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        db.cursor.execute("""
            INSERT INTO facturas (id_cliente, descripcion, monto, estado)
            VALUES (?, ?, ?, ?)
        """, (usuario["id_cliente"], factura.descripcion, factura.monto, factura.estado))
        db.commit()
        return {"mensaje": "Factura creada exitosamente"}


@app.get("/facturas/{email}", response_model=List[FacturaOut])
def facturas_por_usuario(email: EmailStr):
    with ConexionDB() as db:
        db.cursor.execute("SELECT id_cliente FROM usuarios WHERE email = ?", (email,))
        usuario = db.cursor.fetchone()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        db.cursor.execute("SELECT * FROM facturas WHERE id_cliente = ?", (usuario["id_cliente"],))
        facturas = db.cursor.fetchall()

        return [FacturaOut(
            numero_factura=f["numero_factura"],
            descripcion=f["descripcion"],
            monto=f["monto"],
            estado=f["estado"],
            fecha_emision=f["fecha_emision"]
        ) for f in facturas]
