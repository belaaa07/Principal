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
    """Busca un cliente por su CI/RUC y devuelve su nombre si lo encuentra."""
    if not supabase: return None

    try:
        response = supabase.table('clientes').select('nombre').eq('ci_ruc', ci_ruc).limit(1).execute()
        if response.data:
            return response.data[0]['nombre']
        return None
    except Exception as e:
        print(f"Error al buscar cliente: {e}")
        return None

def insert_client(nombre: str, ci_ruc: str, telefono: str, zona: str):
    """Inserta un nuevo cliente en la base de datos."""
    if not supabase: return False, "No hay conexión con la base de datos."

    try:
        data, count = supabase.table('clientes').insert({
            'nombre': nombre,
            'ci_ruc': ci_ruc,
            'telefono': telefono,
            'zona': zona
        }).execute()
        return True, "Cliente guardado correctamente."
    except Exception as e:
        # Manejar error de duplicado de CI/RUC
        if 'duplicate key value violates unique constraint "clientes_ci_ruc_key"' in str(e):
            return False, f"El CI/RUC '{ci_ruc}' ya está registrado."
        print(f"Error al insertar cliente: {e}")
        return False, f"Error inesperado al guardar: {e}"

def insert_work_order(ot_data: dict):
    """Inserta una nueva orden de trabajo en la base de datos."""
    if not supabase: return False, "No hay conexión con la base de datos."

    try:
        data, count = supabase.table('ordenes_trabajo').insert({
            'ot_nro': ot_data['ot_nro'],
            'fecha_creacion': ot_data['fecha'],
            'cliente_ci_ruc': ot_data['ci_ruc'],
            'valor_total': ot_data['valor'],
            'sena': ot_data['sena'],
            'forma_pago': ot_data['forma_pago'],
            'solicita_envio': ot_data['envio_status']
        }).execute()
        return True, "Orden de Trabajo guardada correctamente."
    except Exception as e:
        if 'duplicate key value violates unique constraint "ordenes_trabajo_pkey"' in str(e):
            return False, f"La Orden de Trabajo Nro. {ot_data['ot_nro']} ya existe."
        print(f"Error al insertar OT: {e}")
        return False, f"Error inesperado al guardar la OT: {e}"


# -----------------------------
# Funciones para manejo de usuarios
# Tabla propuesta: 'usuarios'
# -----------------------------

def _hash_password(password: str, salt: str = None) -> tuple:
    """Devuelve (salt, password_hash) usando SHA256 con salt aleatorio si no se provee."""
    if salt is None:
        salt = secrets.token_hex(16)
    pw_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    hash_digest = hashlib.pbkdf2_hmac('sha256', pw_bytes, salt_bytes, 100_000)
    return salt, hash_digest.hex()


def _verify_password(password: str, salt: str, password_hash: str) -> bool:
    _, new_hash = _hash_password(password, salt)
    # Uso de hmac.compare_digest para evitar timing attacks
    return hmac.compare_digest(new_hash, password_hash)


def create_user(nombre: str, ci_ruc: str, password: str, email: str = None, estado: str = 'activo'):
    """Crea un usuario en la tabla 'usuarios'. Retorna (True, mensaje) o (False, mensaje)."""
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
        response = supabase.table('usuarios').insert(data).execute()
        # supabase-py may return response.error or raise; check both
        if hasattr(response, 'error') and response.error:
            raise Exception(response.error)
        return True, "Usuario registrado correctamente."
    except Exception as e:
        err_str = str(e).lower()
        # Detección de duplicados en Supabase
        if 'duplicate' in err_str or 'unique' in err_str:
            return False, f"El usuario con CI/RUC '{ci_ruc}' ya existe."
        # Detectar error RLS o permisos y devolver mensaje claro
        if 'row-level security' in err_str or 'violates row-level security' in err_str or '42501' in err_str:
            return False, "Permiso denegado por Row-Level Security (RLS). Configura una policy o usa la service_role key para realizar inserts." 
        print(f"Error al crear usuario: {e}")
        return False, f"Error inesperado al crear usuario: {e}"


def get_user_by_ci_ruc(ci_ruc: str):
    """Devuelve el registro del usuario (dict) o None si no existe."""
    if not supabase:
        return None
    try:
        response = supabase.table('usuarios').select('*').eq('ci_ruc', ci_ruc).limit(1).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        # Devolver None y loguear; el caller debe manejar el mensaje al usuario
        print(f"Error al obtener usuario: {e}")
        return None


def verify_user_credentials(ci_ruc: str, password: str):
    """Verifica credenciales. Retorna (True, nombre) o (False, mensaje)."""
    if not supabase:
        return False, "No hay conexión con la base de datos."
    try:
        user = get_user_by_ci_ruc(ci_ruc)
        if not user:
            return False, "Usuario no encontrado."
        salt = user.get('salt')
        pw_hash = user.get('password_hash')
        if not salt or not pw_hash:
            return False, "Credenciales incompletas para el usuario."
        if _verify_password(password, salt, pw_hash):
            return True, user.get('nombre')
        return False, "Contraseña incorrecta."
    except Exception as e:
        print(f"Error al verificar credenciales: {e}")
        return False, f"Error al verificar credenciales: {e}"