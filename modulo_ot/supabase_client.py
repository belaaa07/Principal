import os
from supabase import create_client, Client
from dotenv import load_dotenv

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