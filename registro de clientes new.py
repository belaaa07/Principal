import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import sqlite3
import sys
from tkinter import ttk 

# --- CONFIGURACIÓN DE LA BASE DE DATOS Y DATOS ---
DB_NAME = 'master_plot.db' 

# LISTA FIJA DE CIUDADES DEL DEPARTAMENTO CENTRAL DE PARAGUAY + OPCIÓN EXTRA ("Otro")
CIUDADES_CENTRAL = [
    "Areguá", "Asunción", "Capiatá", "Fernando de la Mora", "Guarambaré", 
    "Itá", "Itauguá", "J. Augusto Saldívar", "Lambaré", 
    "Limpio", "Luque", "Mariano Roque Alonso", "Nueva Italia", "Ñemby", 
    "San Antonio", "San Lorenzo", "Villa Elisa", "Villeta", "Ypané", 
    "Ypacaraí", "Otro" 
]

# --- FUNCIONES DE BASE DE DATOS (PERSISTENCIA Y ESTRUCTURA) ---

def inicializar_db():
    """Establece la conexión a la base de datos y crea las tablas si no existen."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 1. Creación de la tabla de CLIENTES
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ci_ruc TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                direccion TEXT,
                telefono TEXT,
                email TEXT
            )
        """)

        # 2. Creación de la tabla de ÓRDENES DE TRABAJO (OT)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ordenes_trabajo (
                ot_nro INTEGER PRIMARY KEY,
                fecha DATE NOT NULL,
                ci_ruc_cliente TEXT NOT NULL,
                valor REAL,
                sena REAL,
                forma_pago TEXT NOT NULL,
                solicita_envio INTEGER,
                vendedor TEXT, 
                FOREIGN KEY (ci_ruc_cliente) REFERENCES clientes(ci_ruc)
            )
        """)
        
        # 3. Crear tabla para el contador de OT
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contador_ot (
                nombre TEXT PRIMARY KEY,
                valor INTEGER
            )
        """)
        
        # 4. Inicializar el contador de OT si es la primera vez
        cursor.execute("INSERT OR IGNORE INTO contador_ot (nombre, valor) VALUES (?, ?)", 
                        ('ot_actual', 1000))

        # 5. Crear tabla para el contador de CLIENTES
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contador_cliente (
                nombre TEXT PRIMARY KEY,
                valor INTEGER
            )
        """)
        
        # 6. Inicializar el contador de CLIENTES si es la primera vez
        cursor.execute("INSERT OR IGNORE INTO contador_cliente (nombre, valor) VALUES (?, ?)", 
                        ('cliente_actual', 1))

        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        messagebox.showerror("Error de DB", f"Error al inicializar la base de datos: {e}")
        sys.exit(1)

def obtener_siguiente_ot_db():
    """Obtiene el siguiente número de OT de la DB y lo incrementa."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM contador_ot WHERE nombre = 'ot_actual'")
        ot_actual = cursor.fetchone()[0]
        siguiente_ot = ot_actual
        cursor.execute("UPDATE contador_ot SET valor = ?", (ot_actual + 1,))
        conn.commit()
        conn.close()
        return siguiente_ot
    except sqlite3.Error:
        return 0

def obtener_siguiente_nro_cliente_db():
    """Obtiene el siguiente número de cliente de la DB y lo incrementa (Ej: 001)."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM contador_cliente WHERE nombre = 'cliente_actual'")
        nro_actual = cursor.fetchone()[0]
        siguiente_nro = nro_actual
        cursor.execute("UPDATE contador_cliente SET valor = ?", (nro_actual + 1,))
        conn.commit()
        conn.close()
        return siguiente_nro
    except sqlite3.Error:
        return 0

def buscar_cliente_db(ci_ruc):
    """Busca el cliente en la tabla de la base de datos."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM clientes WHERE ci_ruc = ?", (ci_ruc,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else None
    except sqlite3.Error:
        return None

def guardar_ot_db(datos_ot):
    """Inserta la nueva Orden de Trabajo en la tabla 'ordenes_trabajo'."""
    ot_nro, fecha, ci_ruc_cliente, valor, sena, forma_pago, solicita_envio, vendedor = datos_ot
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ordenes_trabajo (ot_nro, fecha, ci_ruc_cliente, valor, sena, forma_pago, solicita_envio, vendedor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ot_nro, fecha, ci_ruc_cliente, valor, sena, forma_pago, solicita_envio, vendedor))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        messagebox.showerror("Error de DB", f"Error al guardar la Orden de Trabajo: {e}")
        return False

# --- FUNCIONES DEL MÓDULO DE REGISTRO DE CLIENTES (Módulo 2) ---

def guardar_cliente(ventana, nombre, ci_ruc, telefono, zona):
    """Inserta el nuevo cliente en la tabla 'clientes' (Teléfono obligatorio)."""
    nombre = nombre.strip()
    ci_ruc = ci_ruc.strip()
    telefono = telefono.strip()
    zona = zona.strip()

    # VALIDACIÓN: Nombre, CI/RUC, y Teléfono son obligatorios
    if not nombre or not ci_ruc or not telefono:
        messagebox.showerror("Error de Validación", "Los campos Nombre, CI/RUC, y Teléfono son obligatorios.")
        return
    
    if zona == "Seleccionar...":
        messagebox.showerror("Error de Validación", "Debe seleccionar una Zona/Ciudad.")
        return

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO clientes (ci_ruc, nombre, telefono, direccion) 
            VALUES (?, ?, ?, ?)
        """, (ci_ruc, nombre, telefono, zona))
        
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Registro Exitoso", f"Cliente '{nombre}' (CI/RUC: {ci_ruc}) guardado correctamente.")
        ventana.destroy()

    except sqlite3.IntegrityError:
        messagebox.showerror("Error de Registro", "El CI/RUC ingresado ya está registrado en la base de datos.")
        
    except sqlite3.Error as e:
        messagebox.showerror("Error de DB", f"Ocurrió un error al guardar el cliente: {e}")


def abrir_modulo_registro_cliente():
    """Crea y muestra la ventana del módulo de registro de clientes con estilo moderno."""
    
    registro_root = tk.Toplevel()
    registro_root.title("📝 Módulo de Registro de Clientes")
    registro_root.resizable(False, False)
    
    # --- ESTILO MODERNO (TTK) ---
    style = ttk.Style()
    style.theme_use('clam') # Tema limpio
    style.configure('TFrame', background='#f4f4f4')
    style.configure('TLabel', background='#f4f4f4', font=('Arial', 10))
    style.configure('TEntry', fieldbackground='white', borderwidth=1, relief="solid")
    style.configure('TButton', font=('Arial', 10, 'bold'), padding=6)
    
    registro_root.configure(background='#f4f4f4')


    # --- Variables de Control ---
    nro_cliente = obtener_siguiente_nro_cliente_db()
    nro_cliente_var = tk.StringVar(value=f"{nro_cliente:03d}")
    nombre_var = tk.StringVar()
    ci_ruc_var_reg = tk.StringVar()
    telefono_var = tk.StringVar()
    zona_combobox_var = tk.StringVar(value="Seleccionar...") 

    # --- Marco principal ---
    reg_frame = ttk.Frame(registro_root, padding="20 20 20 20", relief='flat')
    reg_frame.pack(padx=15, pady=15, fill='both', expand=True)

    # Título
    ttk.Label(reg_frame, text="Registro de Nuevo Cliente", font=('Arial', 14, 'bold'), foreground='#306998').grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    # 1. Nro. Cliente (Automático: 001, 002, etc.)
    ttk.Label(reg_frame, text="Nro. Cliente:").grid(row=1, column=0, sticky="w", pady=8)
    ttk.Label(reg_frame, textvariable=nro_cliente_var, foreground="red", font=('Arial', 10, 'bold')).grid(row=1, column=1, sticky="w", pady=8)

    # 2. Nombre
    ttk.Label(reg_frame, text="Nombre:").grid(row=2, column=0, sticky="w", pady=8)
    ttk.Entry(reg_frame, textvariable=nombre_var, width=35).grid(row=2, column=1, sticky="w")
    
    # 3. CI | RUC
    ttk.Label(reg_frame, text="CI | Ruc:").grid(row=3, column=0, sticky="w", pady=8)
    ttk.Entry(reg_frame, textvariable=ci_ruc_var_reg, width=35).grid(row=3, column=1, sticky="w")
    
    # 4. Teléfono (Obligatorio)
    ttk.Label(reg_frame, text="Teléfono:").grid(row=4, column=0, sticky="w", pady=8)
    ttk.Entry(reg_frame, textvariable=telefono_var, width=35).grid(row=4, column=1, sticky="w")
    
    # 5. Zona (Combobox Fijo con ciudades de Central)
    ttk.Label(reg_frame, text="Zona/Ciudad:").grid(row=5, column=0, sticky="w", pady=8)
    
    zona_combobox = ttk.Combobox(
        reg_frame, 
        textvariable=zona_combobox_var, 
        values=CIUDADES_CENTRAL, 
        state="readonly", 
        width=32
    )
    zona_combobox.grid(row=5, column=1, sticky="w")
    
    # --- Botones de Acción ---
    button_frame = ttk.Frame(registro_root)
    button_frame.pack(pady=(15, 15))

    # Botón Guardar
    ttk.Button(button_frame, 
               text="Guardar Cliente", 
               style='Accent.TButton', 
               command=lambda: guardar_cliente(
                   registro_root, 
                   nombre_var.get(), 
                   ci_ruc_var_reg.get(), 
                   telefono_var.get(), 
                   zona_combobox_var.get()
               )).pack(side=tk.LEFT, padx=15)
              
    # Botón Cancelar
    ttk.Button(button_frame, 
               text="Cancelar", 
               command=registro_root.destroy).pack(side=tk.LEFT, padx=15)
              
    registro_root.transient(registro_root.master) 
    registro_root.grab_set() 
    registro_root.wait_window(registro_root)


# --- FUNCIONES DEL MÓDULO DE ORDEN DE TRABAJO (Módulo 1) ---

def validar_y_buscar(event=None):
    """Busca al cliente en la DB por CI/RUC y actualiza el campo Nombre."""
    ci_ruc = ci_ruc_var.get().strip()
    
    global registro_label 

    if not ci_ruc:
        nombre_var.set("")
        registro_label.config(text="")
        return

    nombre_cliente = buscar_cliente_db(ci_ruc)

    if nombre_cliente:
        nombre_var.set(nombre_cliente)
        registro_label.config(text="Cliente Registrado", fg="green")
    else:
        nombre_var.set("CLIENTE INEXISTENTE")
        registro_label.config(text="⚠️", fg="red")
        
        
def guardar_ot():
    """Función para recolectar, validar y guardar los datos de la OT."""
    try:
        # 1. Limpieza y validación de números
        valor_str = valor_var.get().replace('.', '').replace(',', '')
        sena_str = sena_var.get().replace('.', '').replace(',', '')
        
        if valor_str and not valor_str.isdigit():
             raise ValueError("El campo Valor solo debe contener números.")
        if sena_str and not sena_str.isdigit():
             raise ValueError("El campo Seña solo debe contener números.")

        valor = float(valor_str) if valor_str else 0.0
        sena = float(sena_str) if sena_str else 0.0
        
        formato_guaranies = lambda num: f"Gs. {num:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # 2. Recolección de variables
        ot_nro = ot_var.get()
        fecha = fecha_var.get()
        ci_ruc = ci_ruc_var.get()
        nombre = nombre_var.get()
        vendedor = vendedor_var.get().strip() 
        forma_pago = "Crédito" if pago_var.get() == 1 else "Contado"
        envio_status = envio_var.get()
        
        # 3. Validaciones de Negocio
        if not ci_ruc or nombre == "CLIENTE INEXISTENTE":
             messagebox.showerror("Error", "Debe ingresar o registrar un cliente válido antes de guardar la OT.")
             return
        if not vendedor:
             messagebox.showerror("Error", "El campo Vendedor es obligatorio.")
             return

        # 4. Preparación y Guardado
        datos_a_guardar = (
            int(ot_nro), 
            fecha,
            ci_ruc,
            valor,
            sena,
            forma_pago,
            envio_status,
            vendedor 
        )

        guardado_exitoso = guardar_ot_db(datos_a_guardar)

        if guardado_exitoso:
            # 5. Preparar mensaje de éxito
            valor_fmt = formato_guaranies(valor)
            sena_fmt = formato_guaranies(sena)
            saldo_fmt = formato_guaranies(valor - sena)

            datos_ot_formato = f"""
--- ORDEN DE TRABAJO NRO. {ot_nro} ---
Fecha: {fecha}

Vendedor: {vendedor}

CLIENTE:
CI/RUC: {ci_ruc}
Nombre: {nombre}

VALORES:
Valor Total: {valor_fmt}
Seña (Anticipo): {sena_fmt}
Saldo: {saldo_fmt}

DETALLES:
Forma de Pago: {forma_pago}
Envío: {'Solicita Envío' if envio_status else 'No Solicita Envío'}
"""
            
            messagebox.showinfo("Guardar OT Exitoso", datos_ot_formato)
            
            # 6. Reiniciar el formulario principal
            root_principal.destroy()
            crear_modulo_ot() 


    except ValueError as e:
        messagebox.showerror("Error de Validación", str(e))
    except Exception as e:
        messagebox.showerror("Error Desconocido", f"Ocurrió un error al guardar: {e}")


# --- CONFIGURACIÓN DE LA VENTANA PRINCIPAL (Estilo Moderno) ---
def crear_modulo_ot():
    global root_principal
    root_principal = tk.Tk()
    root_principal.title("🏷️ Módulo de Orden de Trabajo")
    root_principal.resizable(False, False) 

    # --- Estilo Moderno (TTK) para OT ---
    style = ttk.Style()
    style.theme_use('clam') 
    
    # Definición de colores de fondo y texto
    BG_COLOR = '#e8e8e8'
    ACCENT_COLOR = '#006699' 

    style.configure('TFrame', background=BG_COLOR)
    style.configure('TLabel', background=BG_COLOR, font=('Arial', 10))
    style.configure('TEntry', fieldbackground='white', borderwidth=1, relief="solid")
    style.configure('TButton', font=('Arial', 10, 'bold'), padding=6)
    
    # Estilo especial para botones de acción principal (accent)
    style.configure('Accent.TButton', background=ACCENT_COLOR, foreground='white', borderwidth=0)
    style.map('Accent.TButton', background=[('active', '#004a73')], foreground=[('active', 'white')])

    root_principal.configure(background=BG_COLOR)


    # --- Variables de Control ---
    global ot_var, fecha_var, ci_ruc_var, nombre_var, valor_var, sena_var, pago_var, envio_var
    global vendedor_var 
    global registro_label
    
    ot_var = tk.StringVar(value=obtener_siguiente_ot_db()) 
    fecha_var = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y")) 
    ci_ruc_var = tk.StringVar()
    nombre_var = tk.StringVar()
    valor_var = tk.StringVar()
    sena_var = tk.StringVar()
    vendedor_var = tk.StringVar() 
    pago_var = tk.IntVar(value=2) 
    envio_var = tk.IntVar(value=0) 

    # --- Marco principal del formulario ---
    form_frame = ttk.Frame(root_principal, padding="20 20 20 20", relief='flat')
    form_frame.pack(padx=15, pady=15, fill='x')

    for i in range(4):
        form_frame.grid_columnconfigure(i, weight=1)

    ttk.Label(form_frame, text="Datos de la Orden de Trabajo", font=('Arial', 14, 'bold'), foreground=ACCENT_COLOR).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 15))


    # --- FILA 1: OT Nro. y Fecha ---
    ttk.Label(form_frame, text="Ot Nro.:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=5)
    ttk.Label(form_frame, textvariable=ot_var, font=('Arial', 10, 'bold'), foreground="#CC0000").grid(row=1, column=1, sticky="w", pady=5)
    
    ttk.Label(form_frame, text="Fecha:").grid(row=1, column=2, sticky="w", padx=(10, 0), pady=5)
    ttk.Label(form_frame, textvariable=fecha_var).grid(row=1, column=3, sticky="w", pady=5)


    # --- FILA 2: Vendedor --- 
    ttk.Label(form_frame, text="Vendedor:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky="w", pady=5)
    ttk.Entry(form_frame, textvariable=vendedor_var, width=15).grid(row=2, column=1, sticky="w")
    

    # --- FILA 3: CI | Ruc (Entrada y Búsqueda) ---
    ttk.Label(form_frame, text="CI | Ruc:").grid(row=3, column=0, sticky="w", pady=8)
    ci_ruc_entry = ttk.Entry(form_frame, textvariable=ci_ruc_var, width=15)
    ci_ruc_entry.grid(row=3, column=1, sticky="w", padx=(0, 5))
    ci_ruc_entry.bind("<Return>", validar_y_buscar) 
    ci_ruc_entry.bind("<FocusOut>", validar_y_buscar) 

    # Etiqueta de estado de registro 
    registro_label = tk.Label(form_frame, text="", font=('Arial', 9), bg=BG_COLOR)
    registro_label.grid(row=3, column=2, sticky="w")


    # --- FILA 4: Botón Registrar y Nombre del Cliente ---
    ttk.Button(form_frame, 
              text="Registrar", 
              style='Accent.TButton', 
              command=abrir_modulo_registro_cliente).grid(row=3, column=3, sticky="e", pady=8) 

    # Nombre del Cliente 
    ttk.Label(form_frame, text="Nombre:").grid(row=4, column=0, sticky="w", pady=8)
    ttk.Label(form_frame, textvariable=nombre_var, foreground="#006699", font=('Arial', 10, 'italic')).grid(row=4, column=1, columnspan=3, sticky="w", pady=8)


    # --- FILA 5 y 6: Valores ---
    ttk.Label(form_frame, text="VALORES:", font=('Arial', 10, 'bold')).grid(row=5, column=0, columnspan=4, sticky="w", pady=(10, 5))

    ttk.Label(form_frame, text="Valor Total (Gs.):").grid(row=6, column=0, sticky="w", pady=5)
    ttk.Entry(form_frame, textvariable=valor_var, width=15).grid(row=6, column=1, sticky="w")
    
    ttk.Label(form_frame, text="Seña (Gs.):").grid(row=6, column=2, sticky="w", padx=(10, 0), pady=5)
    ttk.Entry(form_frame, textvariable=sena_var, width=15).grid(row=6, column=3, sticky="w")


    # --- FILA 7 y 8: Opciones ---
    ttk.Label(form_frame, text="OPCIONES:", font=('Arial', 10, 'bold')).grid(row=7, column=0, columnspan=4, sticky="w", pady=(10, 5))

    ttk.Label(form_frame, text="Forma de Pago:").grid(row=8, column=0, sticky="w", pady=5)
    ttk.Radiobutton(form_frame, text="Crédito", variable=pago_var, value=1).grid(row=8, column=1, sticky="w", padx=5)
    ttk.Radiobutton(form_frame, text="Contado", variable=pago_var, value=2).grid(row=8, column=2, sticky="w", padx=5)


    ttk.Label(form_frame, text="Solicita Envío:").grid(row=9, column=0, sticky="w", pady=5)
    ttk.Checkbutton(form_frame, variable=envio_var, onvalue=1, offvalue=0).grid(row=9, column=1, sticky="w")
    
    # Botón de Acción Principal (Guarda la OT y reinicia)
    ttk.Button(root_principal, text="Guardar Orden de Trabajo", command=guardar_ot, 
               style='Accent.TButton').pack(pady=(5, 15))

    root_principal.mainloop()

# --- EJECUCIÓN DEL PROGRAMA ---

if __name__ == "__main__":
    inicializar_db() 
    crear_modulo_ot()