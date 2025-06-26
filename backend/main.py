import sqlite3
from datetime import datetime
import re

class ConexionDB:
    def __init__(self, db_path):
        self.conexion = sqlite3.connect(db_path)
        self.conexion.row_factory = sqlite3.Row
        self.cursor = self.conexion.cursor()

    def cerrar(self):
        self.cursor.close()
        self.conexion.close()


class Usuario:
    def __init__(self, db):
        self.db = db

    def email_valido(self, email):
        return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)

    def email_existe(self, email):
        self.db.cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        return self.db.cursor.fetchone() is not None

    def registrar(self):
        print("\n=== REGISTRO DE NUEVO USUARIO ===")
        nombre = input("Ingrese nombre: ").strip()
        apellidos = input("Ingrese apellidos: ").strip()
        email = input("Ingrese email: ").strip()
        telefono = input("Ingrese teléfono (opcional): ").strip() or None
        direccion = input("Ingrese dirección (opcional): ").strip() or None

        if not (nombre and apellidos and email):
            print("Todos los campos obligatorios deben estar completos.")
            return
        if not self.email_valido(email):
            print("Email no tiene un formato válido.")
            return
        if self.email_existe(email):
            print("Ese email ya está registrado.")
            return

        self.db.cursor.execute("""
            INSERT INTO usuarios (nombre, apellidos, email, telefono, direccion)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, apellidos, email, telefono, direccion))
        self.db.conexion.commit()

        id_cliente = self.db.cursor.lastrowid
        print("\nUsuario registrado exitosamente!")
        print(f"ID asignado: USR{id_cliente:03}")
        print("Fecha de registro: " + datetime.today().strftime('%d/%m/%Y'))

    def buscar(self):
        print("\n=== BUSCAR USUARIO ===")
        metodo = input("1. Buscar por email\n2. Buscar por nombre\nSeleccione método: ").strip()
        if metodo == "1":
            email = input("Ingrese email: ").strip()
            self.db.cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        elif metodo == "2":
            nombre = input("Ingrese nombre: ").strip()
            self.db.cursor.execute("SELECT * FROM usuarios WHERE nombre LIKE ?", (f"%{nombre}%",))
        else:
            print("Opción inválida.")
            return

        usuario = self.db.cursor.fetchone()
        if usuario:
            print(f"\nID: USR{usuario['id_cliente']:03}")
            print(f"Nombre: {usuario['nombre']} {usuario['apellidos']}")
            print(f"Email: {usuario['email']}")
            print(f"Teléfono: {usuario['telefono'] or 'No especificado'}")
            print(f"Dirección: {usuario['direccion'] or 'No especificada'}")
            print(f"Fecha de registro: {usuario['fecha_registro']}")
        else:
            print("Usuario no encontrado.")

    def mostrar_todos(self):
        print("\n=== LISTA DE USUARIOS ===")
        self.db.cursor.execute("SELECT * FROM usuarios")
        usuarios = self.db.cursor.fetchall()
        for i, usuario in enumerate(usuarios, 1):
            print(f"\nUsuario #{i} - USR{usuario['id_cliente']:03}")
            print(f"Nombre: {usuario['nombre']} {usuario['apellidos']}")
            print(f"Email: {usuario['email']}")
            print(f"Teléfono: {usuario['telefono'] or 'No especificado'}")
            fecha = usuario['fecha_registro']
            fecha_fmt = fecha.strftime('%d/%m/%Y') if isinstance(fecha, datetime) else str(fecha)
            print(f"Fecha de registro: {fecha_fmt}")
        print(f"\nTotal usuarios: {len(usuarios)}")


class Factura:
    def __init__(self, db):
        self.db = db

    def crear(self):
        print("\n=== CREAR FACTURA ===")
        email = input("Ingrese email del usuario: ").strip()
        self.db.cursor.execute("SELECT id_cliente, nombre, apellidos FROM usuarios WHERE email = ?", (email,))
        usuario = self.db.cursor.fetchone()

        if not usuario:
            print("Usuario no encontrado.")
            return

        descripcion = input("Ingrese descripción del servicio/producto: ").strip()
        try:
            monto = float(input("Ingrese monto: "))
            if monto <= 0:
                raise ValueError
        except ValueError:
            print("Monto inválido.")
            return

        print("Seleccione estado:\n1. Pendiente\n2. Pagada\n3. Cancelada")
        estado = {"1": "Pendiente", "2": "Pagada", "3": "Cancelada"}.get(input("Estado: "))
        if not estado:
            print("Estado inválido.")
            return

        self.db.cursor.execute("""
            INSERT INTO facturas (id_cliente, descripcion, monto, estado)
            VALUES (?, ?, ?, ?)
        """, (usuario['id_cliente'], descripcion, monto, estado))
        self.db.conexion.commit()

        print("Factura creada con éxito.")

    def mostrar_por_usuario(self):
        email = input("Ingrese email del usuario: ").strip()
        self.db.cursor.execute("SELECT id_cliente, nombre, apellidos FROM usuarios WHERE email = ?", (email,))
        usuario = self.db.cursor.fetchone()
        if not usuario:
            print("Usuario no encontrado.")
            return

        self.db.cursor.execute("SELECT * FROM facturas WHERE id_cliente = ?", (usuario['id_cliente'],))
        facturas = self.db.cursor.fetchall()
        total = sum(f['monto'] for f in facturas)
        pendientes = sum(f['monto'] for f in facturas if f['estado'] == "Pendiente")

        for i, f in enumerate(facturas, 1):
            print(f"\nFactura #{i}: FAC{f['numero_factura']:03}, {f['fecha_emision']}, {f['descripcion']}, ${f['monto']:.2f}, Estado: {f['estado']}")
        print(f"\nTotal: ${total:.2f}, Pendiente: ${pendientes:.2f}")

    def resumen_financiero(self):
        self.db.cursor.execute("SELECT * FROM usuarios")
        usuarios = self.db.cursor.fetchall()
        total_facturas = total_ingresos = total_pendientes = 0

        for u in usuarios:
            self.db.cursor.execute("SELECT estado, monto FROM facturas WHERE id_cliente = ?", (u['id_cliente'],))
            facturas = self.db.cursor.fetchall()
            monto_total = sum(f['monto'] for f in facturas)
            pagadas = sum(f['monto'] for f in facturas if f['estado'] == "Pagada")
            pendientes = sum(f['monto'] for f in facturas if f['estado'] == "Pendiente")

            print(f"\n{u['nombre']} {u['apellidos']} ({u['email']}):\n - Total: ${monto_total:.2f}\n - Pagadas: ${pagadas:.2f}\n - Pendientes: ${pendientes:.2f}")

            total_facturas += len(facturas)
            total_ingresos += pagadas
            total_pendientes += pendientes

        print(f"\n--- RESUMEN GENERAL ---\nFacturas: {total_facturas}, Ingresos: ${total_ingresos:.2f}, Pendientes: ${total_pendientes:.2f}")


class CRM:
    def __init__(self, db_path):
        self.db = ConexionDB(db_path)
        self.usuario = Usuario(self.db)
        self.factura = Factura(self.db)

    def menu(self):
        while True:
            print("\n=== SISTEMA CRM ===")
            print("1. Registrar nuevo usuario")
            print("2. Buscar usuario")
            print("3. Crear factura para usuario")
            print("4. Mostrar todos los usuarios")
            print("5. Mostrar facturas de un usuario")
            print("6. Resumen financiero por usuario")
            print("7. Salir")
            opcion = input("Seleccione una opción: ")

            if opcion == "1":
                self.usuario.registrar()
            elif opcion == "2":
                self.usuario.buscar()
            elif opcion == "3":
                self.factura.crear()
            elif opcion == "4":
                self.usuario.mostrar_todos()
            elif opcion == "5":
                self.factura.mostrar_por_usuario()
            elif opcion == "6":
                self.factura.resumen_financiero()
            elif opcion == "7":
                break
            else:
                print("Opción inválida.")
        self.db.cerrar()


if __name__ == "__main__":
    db_path = r"C:/Users/merlo/OneDrive/Desktop/Appi_clientes/data/datos_clientes.db"
    crm = CRM(db_path)
    crm.menu()