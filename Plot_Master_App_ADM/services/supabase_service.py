import os
import time
from supabase import create_client, Client
from dotenv import load_dotenv
import hashlib
import hmac
import secrets
from datetime import datetime, date

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

# Cache simple para datos referenciales (usuarios/clientes) con TTL corto
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
    """Devuelve el `id` del cliente dado su `ci_ruc` o None."""
    if not supabase: return None
    try:
        resp = supabase.table('clientes').select('id').eq('ci_ruc', ci_ruc).limit(1).execute()
        if resp.data:
            return resp.data[0].get('id')
        return None
    except Exception as e:
        print(f"Error al obtener id de cliente: {e}")
        return None


def get_clients_by_ids(ids: list):
    """Devuelve un dict id->cliente_row para los ids provistos."""
    if not supabase or not ids: return {}
    _ensure_lookup_cache()
    result = {}
    missing = []
    # Evitar ids duplicados y aprovechar cache en memoria para lecturas repetidas
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


def get_users_by_ids(ids: list):
    """Devuelve un dict id->usuario_row para los ids provistos (tabla usuarios)."""
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





def update_user_by_id(user_id, updates: dict):
    """Actualiza un usuario identificado por su `id` en la tabla 'usuarios'."""
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        # Normalizar id a entero cuando sea posible
        try:
            user_id_key = int(user_id)
        except Exception:
            user_id_key = user_id

        response = supabase.table('usuarios').update(updates).eq('id', user_id_key).execute()
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)

        try:
            sel = supabase.table('usuarios').select('id,ci_ruc,nombre,email').eq('id', user_id_key).limit(1).execute()
            if not getattr(sel, 'data', None):
                return False, "No se encontró el usuario tras la actualización (posible problema de permisos)."
            row = sel.data[0]
            for k, v in (updates or {}).items():
                if k not in row:
                    continue
                val_db = row.get(k)
                if (val_db or '') != (v or ''):
                    return False, f"Campo '{k}' no se actualizó correctamente. Esperado: '{v}', DB: '{val_db}'"
            _reset_lookup_cache()
            return True, "Usuario actualizado"
        except Exception as e:
            print(f"Error verificando actualización por id: {e}")
            return False, f"Actualización posiblemente aplicada pero verificación falló: {e}"
    except Exception as e:
        print(f"Error al actualizar usuario por id: {e}")
        return False, f"Error al actualizar usuario: {e}"

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
            return True, {
                'id': admin.get('id'),
                'ci_ruc': admin.get('ci_ruc'),
                'nombre': admin.get('nombre')
            }
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
        # Seleccionamos solo las columnas necesarias para reducir ancho de banda
        response = (
            supabase
            .table('ordenes_trabajo')
            .select('id,ot_nro,cliente_id,vendedor_id,descripcion,valor_total,sena,abonado_total,forma_pago,solicita_envio,status,fecha_creacion,fecha_entrega,created_at')
            .order('ot_nro', desc=True)
            .execute()
        )
        data = response.data or []
        # Enriquecer con nombres de cliente y vendedor (si vienen ids)
        cliente_ids = list({d.get('cliente_id') for d in data if d.get('cliente_id')})
        vendedor_ids = list({d.get('vendedor_id') for d in data if d.get('vendedor_id')})
        clientes = get_clients_by_ids(cliente_ids)
        usuarios = get_users_by_ids(vendedor_ids)
        out = []
        for d in data:
            # Mantener compatibilidad con UI: campos `cliente` y `vendedor` como texto
            cliente_txt = ''
            vendedor_txt = ''
            cid = d.get('cliente_id')
            vid = d.get('vendedor_id')
            if cid and clientes.get(cid):
                cliente_txt = clientes[cid].get('nombre') or clientes[cid].get('ci_ruc') or ''
            if vid and usuarios.get(vid):
                vendedor_txt = usuarios[vid].get('nombre') or usuarios[vid].get('ci_ruc') or ''
            # Exponer abonado_total para UI
            d['abonado_total'] = d.get('abonado_total', 0) or 0
            d['cliente'] = cliente_txt
            d['vendedor'] = vendedor_txt
            out.append(d)
        return True, out
    except Exception as e:
        print(f"Error al obtener las órdenes de trabajo: {e}")
        return False, f"Error inesperado al obtener las órdenes de trabajo: {e}"


def get_finalized_work_orders_between(fecha_desde, fecha_hasta, sort_desc=False):
    """Obtiene OTs finalizadas entre dos fechas (inclusive) ordenadas por fecha de creación.

    fecha_desde / fecha_hasta aceptan date, datetime o string ISO (yyyy-mm-dd).
    sort_desc=True ordena descendente; por defecto ascendente para lectura cronológica.
    """
    if not supabase:
        return False, "No hay conexión con la base de datos."

    try:
        f_ini = _format_date_value(fecha_desde)
        f_fin = _format_date_value(fecha_hasta)
        if not f_ini or not f_fin:
            return False, "Fechas inválidas o faltantes."

        qb = (
            supabase
            .table('ordenes_trabajo')
            .select('id,ot_nro,cliente_id,vendedor_id,descripcion,valor_total,abonado_total,forma_pago,solicita_envio,status,fecha_creacion,fecha_entrega,created_at')
            .eq('status', 'Finalizado')
            .gte('fecha_creacion', f_ini)
            .lte('fecha_creacion', f_fin)
            .order('fecha_creacion', desc=bool(sort_desc))
        )
        resp = qb.execute()
        rows = resp.data or []

        cliente_ids = list({r.get('cliente_id') for r in rows if r.get('cliente_id')})
        vendedor_ids = list({r.get('vendedor_id') for r in rows if r.get('vendedor_id')})
        clientes = get_clients_by_ids(cliente_ids)
        vendedores = get_users_by_ids(vendedor_ids)

        enriched = []
        for r in rows:
            cid = r.get('cliente_id')
            vid = r.get('vendedor_id')
            enriched.append({
                'ot_nro': r.get('ot_nro'),
                'fecha_creacion': _format_date_value(r.get('fecha_creacion') or r.get('created_at')),
                'fecha_entrega': _format_date_value(r.get('fecha_entrega')),
                'cliente': clientes.get(cid, {}).get('nombre') or clientes.get(cid, {}).get('ci_ruc') or '',
                'cliente_ci_ruc': clientes.get(cid, {}).get('ci_ruc') or '',
                'vendedor': vendedores.get(vid, {}).get('nombre') or vendedores.get(vid, {}).get('ci_ruc') or '',
                'vendedor_ci_ruc': vendedores.get(vid, {}).get('ci_ruc') or '',
                'descripcion': r.get('descripcion') or '',
                'valor_total': float(r.get('valor_total') or 0),
                'abonado_total': float(r.get('abonado_total') or 0),
                'forma_pago': r.get('forma_pago') or '',
                'solicita_envio': bool(r.get('solicita_envio')),
                'status': r.get('status') or '',
            })

        return True, enriched
    except Exception as e:
        print(f"Error al obtener reporte de OTs finalizadas: {e}")
        return False, f"Error al obtener OTs finalizadas: {e}"


def get_work_order_by_ot(ot_nro):
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = (
            supabase
            .table('ordenes_trabajo')
            .select('id,ot_nro,cliente_id,vendedor_id,descripcion,valor_total,sena,abonado_total,forma_pago,solicita_envio,status,fecha_creacion,fecha_entrega,created_at')
            .eq('ot_nro', ot_nro)
            .limit(1)
            .execute()
        )
        row = (response.data[0] if response.data else None)
        if not row:
            return True, None
        # Enriquecer con nombres de cliente y vendedor (si vienen ids)
        try:
            cid = row.get('cliente_id')
            vid = row.get('vendedor_id')
            clientes = get_clients_by_ids([cid]) if cid else {}
            usuarios = get_users_by_ids([vid]) if vid else {}
            cliente_txt = ''
            vendedor_txt = ''
            if cid and clientes.get(cid):
                cliente_txt = clientes[cid].get('ci_ruc') or clientes[cid].get('nombre') or ''
            if vid and usuarios.get(vid):
                vendedor_txt = usuarios[vid].get('nombre') or usuarios[vid].get('ci_ruc') or ''
            row['cliente'] = cliente_txt
            row['vendedor'] = vendedor_txt
        except Exception:
            pass

        # Obtener historial de abonos (incluir id para operaciones de borrado)
        ot_id = row.get('id')
        pagos = []
        try:
            resp_ab = supabase.table('abonos').select('id,monto,fecha_abono,creado_por,observacion').eq('ot_id', ot_id).order('fecha_abono', desc=True).execute()
            for p in (resp_ab.data or []):
                pagos.append({
                    'id': p.get('id'),
                    'm': float(p.get('monto') or 0),
                    'f': (p.get('fecha_abono') or '').split('T')[0],
                    'creado_por': p.get('creado_por'),
                    'observacion': p.get('observacion')
                })
        except Exception:
            pagos = []
        row['pagos'] = pagos
        # Asegurar abonado_total existe
        row['abonado_total'] = row.get('abonado_total', 0) or 0
        return True, row
    except Exception as e:
        print(f"Error al obtener OT: {e}")
        return False, f"Error inesperado al obtener la OT: {e}"


def delete_abono(abono_id: int):
    """Elimina un abono por `id` y actualiza `ordenes_trabajo.abonado_total`.
    Retorna (True, msg) o (False, msg).
    """
    if not supabase:
        return False, "No hay conexión con la base de datos."
    try:
        # Obtener el abono para conocer ot_id y monto
        sel = supabase.table('abonos').select('id,ot_id,monto').eq('id', abono_id).limit(1).execute()
        if not getattr(sel, 'data', None):
            return False, "Abono no encontrado."
        ab = sel.data[0]
        ot_id = ab.get('ot_id')
        monto = float(ab.get('monto') or 0)

        # Borrar el abono
        resp_del = supabase.table('abonos').delete().eq('id', abono_id).execute()
        if hasattr(resp_del, 'error') and resp_del.error:
            return False, str(resp_del.error)

        # Actualizar abonado_total en la orden restando el monto (no bajar de 0)
        resp_ot = supabase.table('ordenes_trabajo').select('id,abonado_total').eq('id', ot_id).limit(1).execute()
        if getattr(resp_ot, 'data', None):
            cur = float(resp_ot.data[0].get('abonado_total') or 0)
            nuevo = cur - monto
            if nuevo < 0:
                nuevo = 0
            upd = supabase.table('ordenes_trabajo').update({'abonado_total': nuevo}).eq('id', ot_id).execute()
            if hasattr(upd, 'error') and upd.error:
                return False, str(upd.error)

        return True, "Abono eliminado correctamente."
    except Exception as e:
        print(f"Error al eliminar abono {abono_id}: {e}")
        return False, f"Error al eliminar abono: {e}"


def _format_date_value(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    return text if text else None


def update_work_order_status(ot_nro, status, fecha_entrega=None):
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        updates = {'status': status}
        fecha_payload = _format_date_value(fecha_entrega)
        if fecha_payload is not None:
            updates['fecha_entrega'] = fecha_payload
        response = supabase.table('ordenes_trabajo').update(updates).eq('ot_nro', ot_nro).execute()
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)
        if not getattr(response, 'data', None):
            return False, "No se actualizó ninguna orden (OT no encontrada o sin permisos)."
        return True, "Estado actualizado"
    except Exception as e:
        print(f"Error al actualizar estado OT: {e}")
        return False, f"Error al actualizar estado: {e}"


def cancel_work_order(ot_nro, admin_id, motivo=None, reembolso=0):
    if not supabase:
        return False, "No hay conexión con la base de datos."
    if not admin_id:
        return False, "No se encontró administrador autenticado."
    try:
        response = supabase.table('ordenes_trabajo').select('*').eq('ot_nro', ot_nro).limit(1).execute()
        row = (response.data[0] if response.data else None)
        if not row:
            return False, "Orden no encontrada."
        if (row.get('status') or '').strip().lower() == 'cancelado':
            return False, "La orden ya fue cancelada previamente."
        cancel_payload = {
            'ot_id': row.get('id'),
            'cliente_id': row.get('cliente_id'),
            'vendedor_id': row.get('vendedor_id'),
            'descripcion': row.get('descripcion') or '',
            'motivo': motivo or '',
            'reembolso': float(reembolso) if reembolso else 0,
            'estado_anterior': row.get('status') or 'Pendiente',
            'cancelado_por': admin_id,
            'fecha_creacion_ot': _format_date_value(row.get('fecha_creacion') or row.get('created_at')) or date.today().isoformat(),
            'fecha_cancelacion': datetime.utcnow().isoformat()
        }
        ins = supabase.table('cancelaciones').insert(cancel_payload).execute()
        if hasattr(ins, 'error') and ins.error:
            return False, str(ins.error)
        upd = supabase.table('ordenes_trabajo').update({'status': 'Cancelado'}).eq('id', row.get('id')).execute()
        if hasattr(upd, 'error') and upd.error:
            return False, str(upd.error)
        return True, "Orden cancelada"
    except Exception as e:
        print(f"Error al cancelar OT {ot_nro}: {e}")
        return False, f"Error al cancelar la OT: {e}"


def update_work_order_details(ot_nro, updates: dict):
    if not supabase:
        return False, "No hay conexión con la base de datos."
    if not updates:
        return False, "No hay campos para actualizar."
    try:
        try:
            ot_key = int(ot_nro)
        except Exception:
            ot_key = ot_nro
        response = supabase.table('ordenes_trabajo').update(updates).eq('ot_nro', ot_key).execute()
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)
        if not getattr(response, 'data', None):
            return False, "No se actualizó ninguna orden (OT no encontrada o sin permisos)."
        return True, "Orden actualizada"
    except Exception as e:
        print(f"Error al actualizar detalles OT: {e}")
        return False, f"Error al actualizar orden: {e}"


def add_sena_to_order(ot_nro, amount):
    """Registra un abono en la tabla `abonos` y actualiza `ordenes_trabajo.abonado_total`.
    Retorna (True, mensaje) o (False, mensaje).
    """
    # Nuevo comportamiento: registrar un abono en la tabla `abonos` y actualizar `abonado_total`
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
        # Insertar registro en abonos (creado_por queda null si no hay contexto)
        try:
            ins = supabase.table('abonos').insert({
                'ot_id': ot_id,
                'monto': add_val
            }).execute()
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


def update_work_order_value(ot_nro, valor_total):
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('ordenes_trabajo').update({'valor_total': valor_total}).eq('ot_nro', ot_nro).execute()
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)
        if not getattr(response, 'data', None):
            return False, "No se actualizó ninguna orden (OT no encontrada o sin permisos)."
        return True, "Valor actualizado"
    except Exception as e:
        print(f"Error al actualizar valor OT: {e}")
        return False, f"Error al actualizar valor: {e}"


def delete_work_order(ot_nro):
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('ordenes_trabajo').delete().eq('ot_nro', ot_nro).execute()
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)
        if not getattr(response, 'data', None):
            return False, "No se eliminó ninguna orden (OT no encontrada o sin permisos)."
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


def get_all_users():
    """Devuelve todos los usuarios (vendedores) desde la tabla 'usuarios'."""
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        # La columna de fecha en `usuarios` es `fecha_registro` según el nuevo esquema
        response = supabase.table('usuarios').select('*').order('fecha_registro', desc=True).execute()
        return True, (response.data or [])
    except Exception as e:
        print(f"Error al obtener usuarios: {e}")
        return False, f"Error inesperado al obtener usuarios: {e}"


def update_user(ci_ruc, updates: dict):
    """Actualiza un usuario identificado por su CI/RUC en la tabla 'usuarios'."""
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('usuarios').update(updates).eq('ci_ruc', ci_ruc).execute()
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)

        ci_select = updates.get('ci_ruc', ci_ruc)
        try:
            sel = supabase.table('usuarios').select('ci_ruc,nombre,email').eq('ci_ruc', ci_select).limit(1).execute()
            if not getattr(sel, 'data', None):
                return False, "No se encontró el usuario tras la actualización (posible problema de permisos o filtro)."
            row = sel.data[0]
            for k, v in (updates or {}).items():
                if k not in row:
                    continue
                if (row.get(k) or '') != (v or ''):
                    return False, f"Campo '{k}' no se actualizó correctamente. Esperado: '{v}', DB: '{row.get(k)}'"
            _reset_lookup_cache()
            return True, "Usuario actualizado"
        except Exception as e:
            print(f"Error verificando actualización por CI/RUC: {e}")
            return False, f"Actualización posiblemente aplicada pero verificación falló: {e}"
    except Exception as e:
        print(f"Error al actualizar usuario: {e}")
        return False, f"Error al actualizar usuario: {e}"


def delete_user(ci_ruc: str):
    """Elimina un usuario (vendedor) por su CI/RUC de la tabla 'usuarios'."""
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('usuarios').delete().eq('ci_ruc', ci_ruc).execute()
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)
        if not getattr(response, 'data', None):
            return False, "No se eliminó ningún usuario (CI/RUC no encontrado o sin permisos)."
        _reset_lookup_cache()
        return True, "Usuario eliminado"
    except Exception as e:
        print(f"Error al eliminar usuario: {e}")
        return False, f"Error al eliminar usuario: {e}"


def update_client(ci_ruc, updates: dict):
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('clientes').update(updates).eq('ci_ruc', ci_ruc).execute()
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)
        if not getattr(response, 'data', None):
            return False, "No se actualizó ningún cliente (CI/RUC no encontrado o sin permisos)."
        _reset_lookup_cache()
        return True, "Cliente actualizado"
    except Exception as e:
        print(f"Error al actualizar cliente: {e}")
        return False, f"Error al actualizar cliente: {e}"


def delete_client(ci_ruc: str):
    """Elimina un cliente por su CI/RUC."""
    if not supabase: return False, "No hay conexión con la base de datos."
    try:
        response = supabase.table('clientes').delete().eq('ci_ruc', ci_ruc).execute()
        if hasattr(response, 'error') and response.error:
            return False, str(response.error)
        if not getattr(response, 'data', None):
            return False, "No se eliminó ningún cliente (CI/RUC no encontrado o sin permisos)."
        _reset_lookup_cache()
        return True, "Cliente eliminado"
    except Exception as e:
        print(f"Error al eliminar cliente: {e}")
        return False, f"Error al eliminar cliente: {e}"


def get_work_orders_by_client(ci_ruc: str):
    """Devuelve las órdenes de trabajo asociadas al CI/RUC del cliente."""
    if not supabase:
        return False, "No hay conexión con la base de datos."
    # Intentar una vez y reintentar una vez si hay un cierre de conexión inesperado
    import time
    for attempt in range(2):
        try:
                # Resolver cliente id y filtrar por cliente_id
                cid = get_client_id_by_ci_ruc(ci_ruc)
                if cid is None:
                    return True, []
                response = supabase.table('ordenes_trabajo').select('*').eq('cliente_id', cid).order('fecha_creacion', desc=True).execute()
                data = response.data or []
                # Añadir campo cliente textual
                for d in data:
                    d['cliente'] = ci_ruc
                    d['abonado_total'] = d.get('abonado_total', 0) or 0
                return True, data
        except Exception as e:
            err_str = str(e)
            print(f"Error al obtener OTs por cliente (attempt {attempt+1}): {err_str}")
            # Si es el primer intento, esperar un breve periodo y reintentar
            if attempt == 0:
                time.sleep(0.5)
                continue
            return False, f"Error inesperado al obtener OTs: {err_str}"


# Note: usuario-related helper functions removed. Use administradores table and the admin functions above.