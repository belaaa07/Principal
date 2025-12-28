import os
import time
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

# Cache corto para tablas referenciales
_LOOKUP_TTL_SECONDS = 90
_lookup_cache = {
    'expires_at': 0.0,
    'clientes': {},
    'usuarios': {},
}


def _reset_lookup_cache():
    _lookup_cache['clientes'].clear()
    _lookup_cache['usuarios'].clear()
    _lookup_cache['expires_at'] = time.time() + _LOOKUP_TTL_SECONDS


def _ensure_lookup_cache():
    if time.time() > _lookup_cache['expires_at']:
        _reset_lookup_cache()


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


def get_client_id_by_ci_ruc(ci_ruc: str):
    if not supabase: return None
    try:
        resp = supabase.table('clientes').select('id').eq('ci_ruc', ci_ruc).limit(1).execute()
        if resp.data:
            return resp.data[0].get('id')
        return None
    except Exception as e:
        print(f"Error al obtener id de cliente: {e}")
        return None


def get_users_by_ids(ids: list):
    if not supabase or not ids: return {}
    _ensure_lookup_cache()
    result = {}
    missing = []
    for uid in set(ids):
        if uid in _lookup_cache['usuarios']:
            result[uid] = _lookup_cache['usuarios'][uid]
        else:
            missing.append(uid)
    if not missing:
        return result
    try:
        resp = supabase.table('usuarios').select('*').in_('id', missing).execute()
        rows = resp.data or []
        for r in rows:
            uid = r.get('id')
            _lookup_cache['usuarios'][uid] = r
            result[uid] = r
        return result
    except Exception as e:
        print(f"Error al obtener usuarios por ids: {e}")
        return result


def get_clients_by_ids(ids: list):
    if not supabase or not ids: return {}
    _ensure_lookup_cache()
    result = {}
    missing = []
    for cid in set(ids):
        if cid in _lookup_cache['clientes']:
            result[cid] = _lookup_cache['clientes'][cid]
        else:
            missing.append(cid)
    if not missing:
        return result
    try:
        resp = supabase.table('clientes').select('*').in_('id', missing).execute()
        rows = resp.data or []
        for r in rows:
            cid = r.get('id')
            _lookup_cache['clientes'][cid] = r
            result[cid] = r
        return result
    except Exception as e:
        print(f"Error al obtener clientes por ids: {e}")
        return result

def insert_client(nombre: str, ci_ruc: str, telefono: str, zona: str, email: str = None):
    """Inserta un nuevo cliente en la base de datos."""
    if not supabase: return False, "No hay conexión con la base de datos."

    try:
        response = supabase.table('clientes').insert({
            'nombre': nombre,
            'ci_ruc': ci_ruc,
            'telefono': telefono,
            'zona': zona,
            'email': email
        }).execute()
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)
        _reset_lookup_cache()
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
        def _normalize_status(s):
            # Canonical states: Pendiente, Aprobado, Entregado, Finalizado
            if not s: return 'Pendiente'
            s2 = str(s).strip().lower()
            if s2 in ('pendiente', 'pending'):
                return 'Pendiente'
            if s2 in ('aprobado', 'aprovado'):
                return 'Aprobado'
            if 'entreg' in s2:
                return 'Entregado'
            if s2 in ('finalizado', 'finalizado/a', 'final'):
                return 'Finalizado'
            return 'Pendiente'

        # Normalize incoming status to the canonical set
        status_norm = _normalize_status(ot_data.get('status'))

        payload = {
            'ot_nro': ot_data['ot_nro'],
            'fecha_creacion': ot_data['fecha'],
            'valor_total': ot_data['valor'],
            'sena': ot_data.get('sena', 0),
            'forma_pago': ot_data.get('forma_pago'),
            'solicita_envio': ot_data.get('envio_status', False),
            'status': status_norm
        }
        # Resolver cliente_id desde ci_ruc si viene
        ci = ot_data.get('ci_ruc')
        if ci:
            cid = get_client_id_by_ci_ruc(ci)
            if cid is None:
                return False, f"Cliente con CI/RUC {ci} no encontrado."
            payload['cliente_id'] = cid
        # Añadir descripción si viene (campo nuevo en esquema)
        if 'descripcion' in ot_data:
            payload['descripcion'] = ot_data['descripcion']
        # Añadir vendedor si se provee en ot_data
        # Resolver vendedor a `vendedor_id` si se provee (puede ser id, ci_ruc o nombre)
        if 'vendedor' in ot_data and ot_data['vendedor']:
            v = ot_data['vendedor']
            vendedor_id = None
            # Preferir resolver por CI/RUC (aunque sea numérico), luego por id, y finalmente por nombre
            try:
                resp_by_ci = supabase.table('usuarios').select('id').eq('ci_ruc', str(v)).limit(1).execute()
                if resp_by_ci.data:
                    vendedor_id = resp_by_ci.data[0].get('id')
            except Exception:
                vendedor_id = None

            # Si no se resolvió por CI, intentar si el valor es un id numérico
            if vendedor_id is None:
                try:
                    maybe_id = int(v)
                    resp_by_id = supabase.table('usuarios').select('id').eq('id', maybe_id).limit(1).execute()
                    if resp_by_id.data:
                        vendedor_id = resp_by_id.data[0].get('id')
                except Exception:
                    vendedor_id = vendedor_id

            # Finalmente intentar por nombre exacto
            if vendedor_id is None:
                try:
                    resp_by_name = supabase.table('usuarios').select('id').eq('nombre', str(v)).limit(1).execute()
                    if resp_by_name.data:
                        vendedor_id = resp_by_name.data[0].get('id')
                except Exception:
                    vendedor_id = None

            if vendedor_id is None:
                return False, f"Vendedor '{v}' no encontrado. Proporcione id, CI/RUC o nombre válido."
            payload['vendedor_id'] = vendedor_id
        else:
            return False, "La orden debe incluir un 'vendedor' (id, CI/RUC o nombre)."

        response = supabase.table('ordenes_trabajo').insert(payload).execute()
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)
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
        if hasattr(response, 'error') and response.error:
            raise Exception(response.error)
        _reset_lookup_cache()
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


def get_all_work_orders():
    """Obtiene todas las órdenes de trabajo de la base de datos."""
    if not supabase: return False, "No hay conexión con la base de datos."

    try:
        response = (
            supabase
            .table('ordenes_trabajo')
            .select('id,ot_nro,cliente_id,vendedor_id,descripcion,valor_total,sena,abonado_total,forma_pago,solicita_envio,status,fecha_creacion,fecha_entrega,created_at')
            .order('ot_nro', desc=True)
            .execute()
        )
        data = response.data or []
        cliente_ids = list({d.get('cliente_id') for d in data if d.get('cliente_id')})
        vendedor_ids = list({d.get('vendedor_id') for d in data if d.get('vendedor_id')})
        clientes = get_clients_by_ids(cliente_ids)
        usuarios = get_users_by_ids(vendedor_ids)
        out = []
        for d in data:
            cid = d.get('cliente_id')
            vid = d.get('vendedor_id')
            d['cliente'] = clientes.get(cid, {}).get('nombre') or clientes.get(cid, {}).get('ci_ruc') or ''
            d['vendedor'] = usuarios.get(vid, {}).get('nombre') or usuarios.get(vid, {}).get('ci_ruc') or ''
            d['abonado_total'] = d.get('abonado_total', 0) or 0
            out.append(d)
        return True, out
    except Exception as e:
        print(f"Error al obtener las órdenes de trabajo: {e}")
        return False, f"Error inesperado al obtener las órdenes de trabajo: {e}"


def get_work_orders_by_vendedor(vendedor: str):
    """Obtiene órdenes de trabajo filtradas por el campo 'vendedor'."""
    if not supabase:
        return False, "No hay conexión con la base de datos."
    try:
        # Resolver vendedor: preferir buscar por ci_ruc, luego por id
        vendedor_id = None
        try:
            resp_ci = supabase.table('usuarios').select('id').eq('ci_ruc', str(vendedor)).limit(1).execute()
            if resp_ci.data:
                vendedor_id = resp_ci.data[0].get('id')
        except Exception:
            vendedor_id = None
        if vendedor_id is None:
            try:
                maybe_id = int(vendedor)
                resp_id = supabase.table('usuarios').select('id').eq('id', maybe_id).limit(1).execute()
                if resp_id.data:
                    vendedor_id = resp_id.data[0].get('id')
            except Exception:
                vendedor_id = None
        if vendedor_id is None:
            return True, []
        response = (
            supabase
            .table('ordenes_trabajo')
            .select('id,ot_nro,cliente_id,vendedor_id,descripcion,valor_total,sena,abonado_total,forma_pago,solicita_envio,status,fecha_creacion,fecha_entrega,created_at')
            .eq('vendedor_id', vendedor_id)
            .order('ot_nro', desc=True)
            .execute()
        )
        data = response.data or []
        # Enriquecer con nombres de cliente y vendedor
        cliente_ids = list({d.get('cliente_id') for d in data if d.get('cliente_id')})
        vendedor_ids = list({d.get('vendedor_id') for d in data if d.get('vendedor_id')})
        clientes = get_clients_by_ids(cliente_ids)
        usuarios = get_users_by_ids(vendedor_ids)
        for d in data:
            cid = d.get('cliente_id')
            vid = d.get('vendedor_id')
            d['cliente'] = clientes.get(cid, {}).get('nombre') or clientes.get(cid, {}).get('ci_ruc') or ''
            d['vendedor'] = usuarios.get(vid, {}).get('nombre') or usuarios.get(vid, {}).get('ci_ruc') or ''
            d['abonado_total'] = d.get('abonado_total', 0) or 0
        return True, data
    except Exception as e:
        print(f"Error al obtener las órdenes de trabajo por vendedor: {e}")
        return False, f"Error inesperado al obtener las órdenes de trabajo: {e}"


def add_sena_to_order(ot_nro, amount):
    """Registra un abono en la tabla `abonos` y actualiza `ordenes_trabajo.abonado_total`.
    Retorna (True, mensaje) o (False, mensaje).
    """
    # Registrar abono en tabla `abonos` y actualizar `abonado_total`
    if not supabase:
        return False, "No hay conexión con la base de datos."
    try:
        resp = supabase.table('ordenes_trabajo').select('id, abonado_total').eq('ot_nro', ot_nro).limit(1).execute()
        if not getattr(resp, 'data', None):
            return False, "Orden no encontrada para registrar abono."
        row = resp.data[0]
        try:
            add_val = float(amount)
        except Exception:
            return False, "Monto inválido para abono."
        ot_id = row.get('id')
        cur_ab = float(row.get('abonado_total') or 0)
        try:
            ins = supabase.table('abonos').insert({'ot_id': ot_id, 'monto': add_val}).execute()
            if hasattr(ins, 'error') and ins.error:
                return False, str(ins.error)
        except Exception as e:
            print(f"Error al insertar abono: {e}")
            return False, f"Error al insertar abono: {e}"
        nuevo = cur_ab + add_val
        upd = supabase.table('ordenes_trabajo').update({'abonado_total': nuevo}).eq('id', ot_id).execute()
        if hasattr(upd, 'error') and upd.error:
            return False, str(upd.error)
        # Autorizar automáticamente la orden al registrar abono: marcar como 'Aprobado'
        try:
            supabase.table('ordenes_trabajo').update({'status': 'Aprobado'}).eq('id', ot_id).execute()
        except Exception:
            pass
        return True, f"Abono registrado. Abonado total: {nuevo}"
    except Exception as e:
        print(f"Error al registrar abono OT {ot_nro}: {e}")
        return False, f"Error al registrar abono: {e}"


def update_work_order_status(ot_nro, new_status: str):
    """Actualiza el campo `status` de una orden de trabajo identificada por `ot_nro`.
    Retorna (True, mensaje) o (False, mensaje). No cambia la estructura de la tabla.
    """
    if not supabase:
        return False, "No hay conexión con la base de datos."

    try:
        # Normalizar estado antes de persistir
        def _normalize_status(s):
            if not s: return 'Pendiente'
            s2 = str(s).strip().lower()
            if s2 in ('pendiente', 'pending'):
                return 'Pendiente'
            if s2 in ('aprobado', 'aprovado'):
                return 'Aprobado'
            if 'entreg' in s2:
                return 'Entregado'
            if s2 in ('finalizado', 'finalizado/a', 'final'):
                return 'Finalizado'
            return 'Pendiente'

        status_norm = _normalize_status(new_status)
        response = supabase.table('ordenes_trabajo').update({'status': status_norm}).eq('ot_nro', ot_nro).execute()
        # supabase-py may return response.error or raise; check both
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)
        return True, f"Estado actualizado a '{status_norm}' para OT {ot_nro}."
    except Exception as e:
        print(f"Error al actualizar estado de OT {ot_nro}: {e}")
        return False, f"Error al actualizar estado: {e}"





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