import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from tkinter import ttk
from dotenv import load_dotenv
import os
import customtkinter as ctk

# Integración con el servicio supabase
from services.supabase_service import (
    get_next_ot_number,
    find_client_by_ci_ruc,
    insert_client,
    insert_work_order,
    get_next_client_number,
)

# Cargar variables de entorno si existen
load_dotenv()

# LISTA FIJA DE CIUDADES DEL DEPARTAMENTO CENTRAL DE PARAGUAY + OPCIÓN EXTRA ("Otro")
CIUDADES_CENTRAL = [
    "Areguá", "Asunción", "Capiatá", "Fernando de la Mora", "Guarambaré", 
    "Itá", "Itauguá", "J. Augusto Saldívar", "Lambaré", 
    "Limpio", "Luque", "Mariano Roque Alonso", "Nueva Italia", "Ñemby", 
    "San Antonio", "San Lorenzo", "Villa Elisa", "Villeta", "Ypané", 
    "Ypacaraí", "Otro" 
]

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

    # --- Lógica de guardado en Supabase ---
    success, message = insert_client(nombre, ci_ruc, telefono, zona)

    if success:
        messagebox.showinfo("Registro Exitoso", message)
        ventana.destroy()
    else:
        messagebox.showerror("Error al Guardar", message)


def abrir_modulo_registro_cliente(parent=None):
    """Crea y muestra la ventana del módulo de registro de clientes con estilo moderno.

    parent: widget padre (Tk o Toplevel)
    """
    registro_root = tk.Toplevel(master=parent) if parent is not None else tk.Toplevel()
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
    nro_cliente = get_next_client_number()
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
    """Busca al cliente en la DB por CI/RUC, actualiza el campo Nombre y gestiona el foco."""
    ci_ruc = ci_ruc_var.get().strip()
    
    global registro_label 

    if not ci_ruc:
        nombre_var.set("")
        registro_label.config(text="")
        return

    # --- Búsqueda de cliente en Supabase ---
    nombre_cliente = find_client_by_ci_ruc(ci_ruc)

    if nombre_cliente:
        nombre_var.set(nombre_cliente)
        registro_label.config(text="Cliente Registrado", fg="green")
    else:
        nombre_var.set("CLIENTE INEXISTENTE")
        registro_label.config(text="⚠️ No encontrado", fg="red")
        # UX Improvement: Si el cliente no existe, mover el foco al botón de registrar.
        # Usamos after() para asegurar que el widget ya esté listo para recibir el foco.
        root_principal.after(100, lambda: registrar_button.focus_set())
        
def guardar_ot(vendedor=None):
    """Función para recolectar, validar y guardar los datos de la OT."""
    try:
        valor_str = valor_var.get().replace('.', '').replace(',', '')
        sena_str = sena_var.get().replace('.', '').replace(',', '')
        
        if valor_str and not valor_str.isdigit():
             raise ValueError("El campo Valor solo debe contener números.")
        if sena_str and not sena_str.isdigit():
             raise ValueError("El campo Seña solo debe contener números.")

        valor = float(valor_str) if valor_str else 0.0
        sena = float(sena_str) if sena_str else 0.0
        
        formato_guaranies = lambda num: f"Gs. {num:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        ot_nro = ot_var.get()
        fecha = fecha_var.get()
        ci_ruc = ci_ruc_var.get()
        nombre = nombre_var.get()
        forma_pago = "Crédito" if pago_var.get() == 1 else "Contado"
        envio_status = envio_var.get()
        
        if not ci_ruc or nombre == "CLIENTE INEXISTENTE":
             messagebox.showerror("Error", "Debe ingresar o registrar un cliente válido antes de guardar la OT.")
             return

        # Convertir fecha de DD/MM/YYYY a YYYY-MM-DD para Supabase
        fecha_iso = datetime.strptime(fecha, "%d/%m/%Y").strftime("%Y-%m-%d")

        datos_a_guardar = {
            "ot_nro": int(ot_nro), 
            "fecha": fecha_iso,
            "ci_ruc": ci_ruc,
            "valor": valor,
            "sena": sena,
            "forma_pago": forma_pago,
            "envio_status": bool(envio_status)
        }
        # Añadir vendedor de sesión si está disponible (no editable en el formulario)
        if vendedor:
            datos_a_guardar["vendedor"] = vendedor

        # --- Lógica de guardado de OT en Supabase ---
        success, message = insert_work_order(datos_a_guardar)

        if success:
            datos_mensaje = f"""
--- ORDEN DE TRABAJO NRO. {ot_nro} ---
Fecha: {fecha}

CLIENTE:
CI/RUC: {ci_ruc}
Nombre: {nombre}

VALORES:
Valor Total: {formato_guaranies(valor)}
Seña (Anticipo): {formato_guaranies(sena)}

DETALLES:
Forma de Pago: {forma_pago}
Envío: {'Solicita Envío' if envio_status else 'No Solicita Envío'}
"""
            
            messagebox.showinfo("Guardado Exitoso", datos_mensaje)
            
            # Reiniciar el formulario principal
            root_principal.destroy()
            crear_modulo_ot()
        else:
            messagebox.showerror("Error al Guardar OT", message)


    except ValueError as e:
        messagebox.showerror("Error de Validación", str(e))
    except Exception as e:
        messagebox.showerror("Error Desconocido", f"Ocurrió un error al guardar: {e}")


# --- CONFIGURACIÓN DE LA VENTANA PRINCIPAL (Estilo Moderno) ---
def crear_modulo_ot(parent=None, vendedor=None):
    """Crea la ventana del módulo de OT como Toplevel y la muestra.

    parent: widget padre (Tk o Toplevel)
    """
    global root_principal
    root_principal = tk.Toplevel(master=parent) if parent is not None else tk.Toplevel()
    root_principal.title("🏷️ Módulo de Orden de Trabajo")
    root_principal.resizable(False, False)

    # --- Estilo Moderno (TTK) para OT ---
    style = ttk.Style()
    style.theme_use('clam') 
    
    # Definición de colores de fondo y texto
    BG_COLOR = '#e8e8e8'
    ACCENT_COLOR = '#006699' # Color azul para el acento (botón)

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
    global registro_label, registrar_button
    
    # --- Obtención del siguiente número de OT desde Supabase ---
    ot_var = tk.StringVar(value=str(get_next_ot_number()))
    fecha_var = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y")) 
    ci_ruc_var = tk.StringVar()
    nombre_var = tk.StringVar()
    valor_var = tk.StringVar()
    sena_var = tk.StringVar()
    vendedor_display = vendedor if vendedor else "No asignado"
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
    ttk.Label(form_frame, text=vendedor_display, font=('Arial', 10, 'bold'), foreground="#006699").grid(row=2, column=1, sticky="w", pady=5)
    

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

    # No ejecutamos mainloop para permitir que el caller gestione la ventana
    # Asegurar modalidad si hay parent
    try:
        if parent:
            root_principal.transient(parent)
            root_principal.grab_set()
            root_principal.focus_force()
            root_principal.attributes('-topmost', True)
    except Exception:
        pass

    return root_principal


# -------------------------
# VERSIÓN EMBEBIDA (customtkinter)
# -------------------------
class OTForm(ctk.CTkFrame):
    def __init__(self, parent, vendedor=None, *args, **kwargs):
        super().__init__(parent, fg_color="#F7F7F7", *args, **kwargs)
        self.parent = parent
        self.vendedor = vendedor

        # Variables
        self.ot_var = tk.StringVar(value=str(get_next_ot_number()))
        self.fecha_var = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        self.ci_ruc_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.valor_var = tk.StringVar()
        self.sena_var = tk.StringVar()
        self.pago_var = tk.IntVar(value=2)
        self.envio_var = tk.IntVar(value=0)

        # Layout: two columns (cliente / orden)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        # Left: Datos del cliente
        left = ctk.CTkFrame(self, fg_color="white", corner_radius=6)
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 8), pady=10)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Detalles del cliente", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))
        ctk.CTkLabel(left, text="CI | Ruc:").grid(row=1, column=0, sticky="w", padx=12, pady=(6, 0))
        ci_entry = ctk.CTkEntry(left, textvariable=self.ci_ruc_var)
        ci_entry.grid(row=2, column=0, sticky="ew", padx=12)
        ci_entry.bind("<Return>", self.validar_y_buscar)
        ci_entry.bind("<FocusOut>", self.validar_y_buscar)

        self.registro_label = ctk.CTkLabel(left, text="", text_color="gray")
        self.registro_label.grid(row=3, column=0, sticky="w", padx=12, pady=(6, 0))

        registrar_btn = ctk.CTkButton(left, text="Registrar cliente", command=self.abrir_registro_cliente)
        registrar_btn.grid(row=4, column=0, sticky="ew", padx=12, pady=(8, 8))

        ctk.CTkLabel(left, text="Nombre contacto:").grid(row=5, column=0, sticky="w", padx=12, pady=(6, 0))
        ctk.CTkEntry(left, textvariable=self.nombre_var, state="readonly").grid(row=6, column=0, sticky="ew", padx=12)

        ctk.CTkLabel(left, text="Teléfono contacto:").grid(row=7, column=0, sticky="w", padx=12, pady=(6, 0))
        ctk.CTkEntry(left, textvariable=tk.StringVar(value=""), state="readonly").grid(row=8, column=0, sticky="ew", padx=12)

        ctk.CTkLabel(left, text="Email contacto:").grid(row=9, column=0, sticky="w", padx=12, pady=(6, 12))
        ctk.CTkEntry(left, textvariable=tk.StringVar(value=""), state="readonly").grid(row=10, column=0, sticky="ew", padx=12, pady=(0,12))

        # Right: Detalles de la orden
        right = ctk.CTkFrame(self, fg_color="white", corner_radius=6)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 10), pady=10)
        right.grid_columnconfigure(0, weight=1)
        right.grid_columnconfigure(1, weight=1)
        right.grid_columnconfigure(2, weight=1)
        right.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(right, text="Detalle de la orden", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(12,8))

        ctk.CTkLabel(right, text="Ot N°:").grid(row=1, column=0, sticky="w", padx=12, pady=6)
        ctk.CTkLabel(right, textvariable=self.ot_var, text_color="#CC0000").grid(row=1, column=1, sticky="w", pady=6)

        ctk.CTkLabel(right, text="Fecha:").grid(row=1, column=2, sticky="w", padx=12, pady=6)
        ctk.CTkLabel(right, textvariable=self.fecha_var).grid(row=1, column=3, sticky="w", pady=6)

        ctk.CTkLabel(right, text="Vendedor:").grid(row=2, column=0, sticky="w", padx=12, pady=6)
        ctk.CTkLabel(right, text=self.vendedor or "No asignado", text_color="#006699").grid(row=2, column=1, sticky="w", pady=6)

        # Valores
        ctk.CTkLabel(right, text="Valor Total (Gs.):").grid(row=3, column=0, sticky="w", padx=12, pady=(10,6))
        ctk.CTkEntry(right, textvariable=self.valor_var).grid(row=3, column=1, sticky="w", pady=(10,6))

        ctk.CTkLabel(right, text="Seña (Gs.):").grid(row=3, column=2, sticky="w", padx=12, pady=(10,6))
        ctk.CTkEntry(right, textvariable=self.sena_var).grid(row=3, column=3, sticky="w", pady=(10,6))

        # Opciones
        ctk.CTkLabel(right, text="Forma de Pago:").grid(row=4, column=0, sticky="w", padx=12, pady=(8,6))
        pago_seg = ctk.CTkSegmentedButton(right, values=["Crédito", "Contado"], command=self._on_pago_changed)
        pago_seg.grid(row=4, column=1, sticky="w", pady=(8,6))
        pago_seg.set("Contado" if self.pago_var.get() == 2 else "Crédito")

        ctk.CTkLabel(right, text="Solicita Envío:").grid(row=4, column=2, sticky="w", padx=12, pady=(8,6))
        envio_chk = ctk.CTkCheckBox(right, text="", command=self._on_envio_toggled)
        envio_chk.grid(row=4, column=3, sticky="w", pady=(8,6))

        # Botón Guardar
        save_btn = ctk.CTkButton(right, text="Guardar Orden de Trabajo", fg_color="#2D9CDB", command=self.guardar_ot)
        save_btn.grid(row=6, column=3, sticky="e", padx=12, pady=12)

    def _on_pago_changed(self, value):
        if value == "Crédito":
            self.pago_var.set(1)
        else:
            self.pago_var.set(2)

    def _on_envio_toggled(self):
        self.envio_var.set(0 if self.envio_var.get() == 1 else 1)

    def abrir_registro_cliente(self):
        try:
            abrir_modulo_registro_cliente(parent=self)
        except Exception:
            abrir_modulo_registro_cliente(parent=None)

    def validar_y_buscar(self, event=None):
        ci = self.ci_ruc_var.get().strip()
        if not ci:
            self.nombre_var.set("")
            self.registro_label.configure(text="")
            return
        nombre_cliente = find_client_by_ci_ruc(ci)
        if nombre_cliente:
            self.nombre_var.set(nombre_cliente)
            self.registro_label.configure(text="Cliente Registrado", text_color="green")
        else:
            self.nombre_var.set("CLIENTE INEXISTENTE")
            self.registro_label.configure(text="⚠️ No encontrado", text_color="red")

    def guardar_ot(self):
        try:
            valor_str = self.valor_var.get().replace('.', '').replace(',', '')
            sena_str = self.sena_var.get().replace('.', '').replace(',', '')

            if valor_str and not valor_str.isdigit():
                raise ValueError("El campo Valor solo debe contener números.")
            if sena_str and not sena_str.isdigit():
                raise ValueError("El campo Seña solo debe contener números.")

            valor = float(valor_str) if valor_str else 0.0
            sena = float(sena_str) if sena_str else 0.0

            formato_guaranies = lambda num: f"Gs. {num:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

            ot_nro = self.ot_var.get()
            fecha = self.fecha_var.get()
            ci_ruc = self.ci_ruc_var.get()
            nombre = self.nombre_var.get()
            forma_pago = "Crédito" if self.pago_var.get() == 1 else "Contado"
            envio_status = self.envio_var.get()

            if not ci_ruc or nombre == "CLIENTE INEXISTENTE":
                messagebox.showerror("Error", "Debe ingresar o registrar un cliente válido antes de guardar la OT.")
                return

            fecha_iso = datetime.strptime(fecha, "%d/%m/%Y").strftime("%Y-%m-%d")

            datos_a_guardar = {
                "ot_nro": int(ot_nro),
                "fecha": fecha_iso,
                "ci_ruc": ci_ruc,
                "valor": valor,
                "sena": sena,
                "forma_pago": forma_pago,
                "envio_status": bool(envio_status)
            }
            if self.vendedor:
                datos_a_guardar["vendedor"] = self.vendedor

            success, message = insert_work_order(datos_a_guardar)
            if success:
                datos_mensaje = f"Orden guardada: Nro {ot_nro}"
                messagebox.showinfo("Guardado Exitoso", datos_mensaje)
            else:
                messagebox.showerror("Error al Guardar OT", message)

        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error Desconocido", f"Ocurrió un error al guardar: {e}")


def crear_modulo_ot_embedded(parent=None, vendedor=None):
    """Crea e inserta el formulario de OT como un `CTkFrame` embebido y lo retorna."""
    if parent is None:
        return None
    # Limpiar contenido previo del parent antes de crear el formulario
    for child in parent.winfo_children():
        child.destroy()
    form = OTForm(parent, vendedor=vendedor)
    form.grid(row=0, column=0, sticky="nsew")
    return form