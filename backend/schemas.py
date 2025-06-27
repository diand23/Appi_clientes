from pydantic import BaseModel, constr
from typing import Optional

class UsuarioIn(BaseModel):
    nombre: str
    apellidos: str
    email: constr(strip_whitespace=True, min_length=5)
    telefono: Optional[str] = None
    direccion: Optional[str] = None

class UsuarioOut(UsuarioIn):
    id_cliente: int
    fecha_registro: str
