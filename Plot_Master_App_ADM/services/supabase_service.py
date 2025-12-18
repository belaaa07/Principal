import os
from supabase import create_client, Client
from dotenv import load_dotenv
import hashlib
import hmac
import secrets
from datetime import datetime

# --- CONFIGURACIÓN INICIAL DEL CLIENTE SUPABASE ---

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def init_supabase_client():
    """
    Inicializa y devuelve el cliente de Supabase usando variables de entorno.
    Retorna None si las variables no están configuradas.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("Error: Las variables de entorno SUPABASE_URL y SUPABASE_KEY no están configuradas.")
        return None

    try:
        supabase: Client = create_client(url, key)
        print("Conexión con Supabase establecida correctamente.")
        return supabase
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")
        return None

# Inicializar el cliente una sola vez para ser usado en todo el módulo
supabase = init_supabase_client()


# --- FUNCIONES PARA INTERACTUAR CON LA BASE DE DATOS ---

def get_next_ot_number():
    """Obtiene el último número de OT de la base de datos y devuelve el siguiente."""
    if not supabase: return 1001 # Valor por defecto si no hay conexión

    try:
        response = supabase.table('ordenes_trabajo').select('ot_nro').order('ot_nro', desc=True).limit(1).execute()
        if response.data:
            last_ot_number = response.data[0]['ot_nro']
            return last_ot_number + 1
        else:
            return 1001 # Si no hay OTs, empezar desde 1001
    except Exception as e:
        print(f"Error al obtener el siguiente número de OT: {e}")
        return 1001 # Fallback

def get_next_client_number():
    """Obtiene el último ID de cliente de la base de datos y devuelve el siguiente."""
    if not supabase: return 1 # Valor por defecto si no hay conexión

    try:
        # La columna de ID en la tabla clientes se llama 'id'
        response = supabase.table('clientes').select('id').order('id', desc=True).limit(1).execute()
        if response.data:
            last_client_id = response.data[0]['id']
            return last_client_id + 1
        else:
            return 1 # Si no hay clientes, empezar desde 1
    except Exception as e:
        print(f"Error al obtener el siguiente número de cliente: {e}")
        return 1 # Fallback

def find_client_by_ci_ruc(ci_ruc: str):
    """Busca un cliente por su CI/RUC y devuelve un dict {nombre, telefono, email} o None."""
    if not supabase: return None

    try:
        response = supabase.table('clientes').select('nombre, telefono, email').eq('ci_ruc', ci_ruc).limit(1).execute()
        if response.data:
            row = response.data[0]
            return {
                'nombre': row.get('nombre'),
                'telefono': row.get('telefono'),
                'email': row.get('email')
            }
        return None
    except Exception as e:
        print(f"Error al buscar cliente: {e}")
        return None

def insert_client(nombre: str, ci_ruc: str, telefono: str, zona: str, email: str = None):
    """Inserta un nuevo cliente en la base de datos."""
    if not supabase: return False, "No hay conexión con la base de datos."

    try:
        data, count = supabase.table('clientes').insert({
            'nombre': nombre,
            'ci_ruc': ci_ruc,
            'telefono': telefono,
            'zona': zona,
            'email': email
        }).execute()
        return True, "Cliente guardado correctamente."
    except Exception as e:
        # Manejar error de duplicado de CI/RUC
        if 'duplicate key value violates unique constraint "clientes_ci_ruc_key"' in str(e):
            return False, f"El CI/RUC '{ci_ruc}' ya está registrado."
        print(f"Error al insertar cliente: {e}")
        return False, f"Error inesperado al guardar: {e}"

# --- FUNCIONES PARA ADMINISTRADORES (USAR SOLO LA TABLA administradores) ---

def get_admin_by_ci_ruc(ci_ruc: str):
    if not supabase: return None
    try:
        response = supabase.table('administradores').select('*').eq('ci_ruc', ci_ruc).limit(1).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error al obtener administrador: {e}")
        return None


def _hash_password(password: str, salt: str = None) -> tuple:
    """Devuelve (salt, password_hash) usando PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = secrets.token_hex(16)
    pw_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    hash_digest = hashlib.pbkdf2_hmac('sha256', pw_bytes, salt_bytes, 100_000)
    return salt, hash_digest.hex()


def _verify_password(password: str, salt: str, password_hash: str) -> bool:
    _, new_hash = _hash_password(password, salt)
    return hmac.compare_digest(new_hash, password_hash)


def verify_admin_credentials(ci_ruc: str, password: str):
    """Verifica credenciales contra la tabla `administradores`. Retorna (True, nombre) o (False, mensaje)."""
    if not supabase:
        return False, "No hay conexión con la base de datos."
    try:
        admin = get_admin_by_ci_ruc(ci_ruc)
        if not admin:
            return False, "Administrador no encontrado."
        salt = admin.get('salt')
        pw_hash = admin.get('password_hash')
        if not salt or not pw_hash:
            return False, "Credenciales incompletas para el administrador."
        if _verify_password(password, salt, pw_hash):
            return True, admin.get('nombre')
        return False, "Contraseña incorrecta."
    except Exception as e:
        print(f"Error al verificar credenciales admin: {e}")
        return False, f"Error al verificar credenciales: {e}"


def create_admin(nombre: str, ci_ruc: str, password: str, email: str = None, estado: str = 'activo'):
    """Crea un administrador en la tabla 'administradores'. Retorna (True, mensaje) o (False, mensaje)."""
    if not supabase:
        return False, "No hay conexión con la base de datos."

    salt, pw_hash = _hash_password(password)
    try:
        data = {
            'nombre': nombre,
            'ci_ruc': ci_ruc,
            'password_hash': pw_hash,
            'salt': salt,
            'email': email,
            'fecha_registro': datetime.utcnow().isoformat(),
            'estado': estado
        }
        response = supabase.table('administradores').insert(data).execute()
        if hasattr(response, 'error') and response.error:
            raise Exception(response.error)
        return True, "Administrador registrado correctamente."
    except Exception as e:
        err_str = str(e).lower()
        if 'duplicate' in err_str or 'unique' in err_str:
            return False, f"El administrador con CI/RUC '{ci_ruc}' ya existe."
        if 'row-level security' in err_str or 'violates row-level security' in err_str or '42501' in err_str:
            return False, "Permiso denegado por Row-Level Security (RLS). Configura una policy o usa la service_role key para realizar inserts." 
        print(f"Error al crear administrador: {e}")
        return False, f"Error inesperado al crear administrador: {e}"


# --- FUNCIONES RELACIONADAS A ORDENES DE TRABAJO PARA ADMIN ---
def get_all_work_orders():
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('ordenes_trabajo').select('*').order('fecha_creacion', desc=True).execute()
        return True, (response.data or [])
    except Exception as e:
        print(f"Error al obtener las órdenes de trabajo: {e}")
        return False, f"Error inesperado al obtener las órdenes de trabajo: {e}"


def get_work_order_by_ot(ot_nro):
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('ordenes_trabajo').select('*').eq('ot_nro', ot_nro).limit(1).execute()
        return True, (response.data[0] if response.data else None)
    except Exception as e:
        print(f"Error al obtener OT: {e}")
        return False, f"Error inesperado al obtener la OT: {e}"


def update_work_order_status(ot_nro, status):
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('ordenes_trabajo').update({'status': status}).eq('ot_nro', ot_nro).execute()
        return True, "Estado actualizado"
    except Exception as e:
        print(f"Error al actualizar estado OT: {e}")
        return False, f"Error al actualizar estado: {e}"


def update_work_order_value(ot_nro, valor_total):
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('ordenes_trabajo').update({'valor_total': valor_total}).eq('ot_nro', ot_nro).execute()
        return True, "Valor actualizado"
    except Exception as e:
        print(f"Error al actualizar valor OT: {e}")
        return False, f"Error al actualizar valor: {e}"


def delete_work_order(ot_nro):
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('ordenes_trabajo').delete().eq('ot_nro', ot_nro).execute()
        return True, "Orden eliminada"
    except Exception as e:
        print(f"Error al eliminar OT: {e}")
        return False, f"Error al eliminar OT: {e}"


# --- FUNCIONES PARA CLIENTES ---
def get_all_clients():
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('clientes').select('*').order('created_at', desc=True).execute()
        return True, (response.data or [])
    except Exception as e:
        print(f"Error al obtener clientes: {e}")
        return False, f"Error inesperado al obtener clientes: {e}"


def update_client(ci_ruc, updates: dict):
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('clientes').update(updates).eq('ci_ruc', ci_ruc).execute()
        return True, "Cliente actualizado"
    except Exception as e:
        print(f"Error al actualizar cliente: {e}")
        return False, f"Error al actualizar cliente: {e}"


def delete_client(ci_ruc: str):
    """Elimina un cliente por su CI/RUC."""
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('clientes').delete().eq('ci_ruc', ci_ruc).execute()
        return True, "Cliente eliminado"
    except Exception as e:
        print(f"Error al eliminar cliente: {e}")
        return False, f"Error al eliminar cliente: {e}"


def get_work_orders_by_client(ci_ruc: str):
    """Devuelve las órdenes de trabajo asociadas al CI/RUC del cliente."""
    if not supabase:
        return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('ordenes_trabajo').select('ot_nro, fecha_creacion, status').eq('cliente_ci_ruc', ci_ruc).order('fecha_creacion', desc=True).execute()
        return True, (response.data or [])
    except Exception as e:
        print(f"Error al obtener OTs por cliente: {e}")
        return False, f"Error inesperado al obtener OTs: {e}"


# Note: usuario-related helper functions removed. Use administradores table and the admin functions above.