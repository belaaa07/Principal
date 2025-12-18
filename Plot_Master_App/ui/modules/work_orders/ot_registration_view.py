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

def guardar_cliente(ventana, nombre, ci_ruc, telefono, zona, email):
    """Inserta el nuevo cliente en la tabla 'clientes' (Teléfono y Email obligatorios)."""
    nombre = nombre.strip()
    ci_ruc = ci_ruc.strip()
    telefono = telefono.strip()
    zona = zona.strip()
    email = email.strip()

    # VALIDACIÓN: Nombre, CI/RUC, Teléfono y Email son obligatorios
    if not nombre or not ci_ruc or not telefono or not email:
        messagebox.showerror("Error de Validación", "Los campos Nombre, CI/RUC, Teléfono y Email son obligatorios.")
        return
    
    if zona == "Seleccionar...":
         messagebox.showerror("Error de Validación", "Debe seleccionar una Zona/Ciudad.")
         return

    # --- Lógica de guardado en Supabase ---
    success, message = insert_client(nombre, ci_ruc, telefono, zona, email=email)

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
    email_var = tk.StringVar()
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
    
    # 5. Email (Obligatorio)
    ttk.Label(reg_frame, text="Email:").grid(row=5, column=0, sticky="w", pady=8)
    ttk.Entry(reg_frame, textvariable=email_var, width=35).grid(row=5, column=1, sticky="w")
    
    # 6. Zona (Combobox Fijo con ciudades de Central)
    ttk.Label(reg_frame, text="Zona/Ciudad:").grid(row=6, column=0, sticky="w", pady=8)
    
    zona_combobox = ttk.Combobox(
        reg_frame, 
        textvariable=zona_combobox_var, 
        values=CIUDADES_CENTRAL, 
        state="readonly", 
        width=32
    )
    zona_combobox.grid(row=6, column=1, sticky="w")
    
    # --- Botones de Acción ---
    button_frame = ttk.Frame(registro_root)
    button_frame.pack(pady=(15, 15))

    # Botón Guardar
    def _on_guardar_cliente():
        guardar_cliente(
            registro_root,
            nombre_var.get(),
            ci_ruc_var_reg.get(),
            telefono_var.get(),
            zona_combobox_var.get(),
            email_var.get()
        )

    ttk.Button(button_frame, 
               text="Guardar Cliente", 
               style='Accent.TButton', 
               command=_on_guardar_cliente).pack(side=tk.LEFT, padx=15)
              
    # Botón Cancelar
    ttk.Button(button_frame, 
               text="Cancelar", 
               command=registro_root.destroy).pack(side=tk.LEFT, padx=15)
              
    registro_root.transient(registro_root.master) 
    registro_root.grab_set() 
    registro_root.wait_window(registro_root)


# --- FUNCIONES DEL MÓDULO DE ORDEN DE TRABAJO (Módulo 1) ---

# NOTE: Legacy module-level functions `validar_y_buscar` and `guardar_ot` were removed.
# These behaviors are implemented as methods on `OTForm` (instance scope) to avoid
# undefined global variables and to keep state encapsulated. Use `OTForm.validar_y_buscar`
# and `OTForm.guardar_ot` when interacting with the form.

def crear_modulo_ot(parent=None, vendedor=None):
    """Crea una ventana `Toplevel` y embebe el `OTForm` (compatibilidad con usos anteriores)."""
    root = tk.Toplevel(master=parent) if parent is not None else tk.Toplevel()
    root.title("🏷️ Módulo de Orden de Trabajo")
    root.geometry("980x720")
    root.resizable(True, True)
    root.configure(bg="#f0f0f0")


    # Montar el formulario embebido dentro del Toplevel
    form = OTForm(root, vendedor=vendedor)
    form.pack(fill="both", expand=True, padx=8, pady=8)

    try:
        if parent:
            root.transient(parent)
            root.grab_set()
            root.focus_force()
            root.attributes('-topmost', True)
    except Exception:
        pass

    return root


# -------------------------
# VERSIÓN EMBEBIDA (customtkinter) - REDISEÑADA
# -------------------------
class OTForm(ctk.CTkFrame):
    def __init__(self, parent, vendedor=None, *args, **kwargs):
        super().__init__(parent, fg_color="#f8f9fa", *args, **kwargs)
        self.parent = parent
        self.vendedor = vendedor

        # --- Variables ---
        self.ot_var = tk.StringVar(value=str(get_next_ot_number()))
        self.fecha_var = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        self.ci_ruc_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.valor_var = tk.StringVar(value="0")
        self.sena_var = tk.StringVar(value="0")
        self.descripcion_var = tk.StringVar()
        self.pago_var = tk.IntVar(value=2) # 1: Credito, 2: Contado
        self.envio_var = tk.IntVar(value=0) # 0: No, 1: Si
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        
        # --- Configuración del Layout Principal ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)
        
        # --- Título Principal ---
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
        ctk.CTkLabel(title_frame, text="Nueva Orden de Trabajo", font=ctk.CTkFont(size=22, weight="bold"), text_color="#333").pack(anchor="w")

        # --- Columna Izquierda (Detalles del Cliente) ---
        self.crear_columna_cliente()
        
        # --- Columna Derecha (Detalles de la Orden y Equipo) ---
        self.crear_columna_detalles()

        # --- Fila de Acciones (Botones) ---
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=20)
        action_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(action_frame, text="Guardar Datos", command=self.guardar_ot, height=35, font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=1, sticky="e")
        ctk.CTkButton(action_frame, text="Limpiar Campos", command=self.limpiar_campos, height=35, fg_color="#6c757d", hover_color="#5a6268", font=ctk.CTkFont(size=13)).grid(row=0, column=0, sticky="w", padx=(0,10))


    def crear_columna_cliente(self):
        """Crea el frame y widgets para la columna de detalles del cliente."""
        client_column = ctk.CTkFrame(self, fg_color="transparent")
        client_column.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        client_column.grid_rowconfigure(0, weight=0)

        # --- Caja de Detalles del Cliente ---
        client_box = ctk.CTkFrame(client_column, fg_color="#ffffff", border_width=1, border_color="#dee2e6", corner_radius=8)
        client_box.pack(fill="both", expand=True)
        
        header = ctk.CTkFrame(client_box, fg_color="#f1f3f5", corner_radius=0)
        header.pack(fill="x", ipady=8)
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Detalles del Cliente", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, sticky="w")
        
        registrar_btn = ctk.CTkButton(header, text="+ Nuevo", width=80, command=self.abrir_registro_cliente)
        registrar_btn.grid(row=0, column=1, padx=15, sticky="e")

        body = ctk.CTkFrame(client_box, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(body, text="Buscar por CI | RUC").pack(anchor="w", padx=5)
        ci_entry_frame = ctk.CTkFrame(body, fg_color="transparent")
        ci_entry_frame.pack(fill="x", expand=True)
        ci_entry_frame.grid_columnconfigure(0, weight=1)

        ci_entry = ctk.CTkEntry(ci_entry_frame, textvariable=self.ci_ruc_var)
        ci_entry.grid(row=0, column=0, sticky="ew")
        ci_entry.bind("<Return>", self.validar_y_buscar)
        ci_entry.bind("<FocusOut>", self.validar_y_buscar)
        
        self.registro_label = ctk.CTkLabel(body, text="", font=ctk.CTkFont(size=12))
        self.registro_label.pack(anchor="w", padx=5, pady=(2, 10))

        ctk.CTkLabel(body, text="Nombre del Cliente").pack(anchor="w", padx=5)
        ctk.CTkEntry(body, textvariable=self.nombre_var, state="readonly").pack(fill="x", expand=True, pady=(0, 10))
        
        ctk.CTkLabel(body, text="Teléfono").pack(anchor="w", padx=5)
        ctk.CTkEntry(body, textvariable=self.phone_var, state="readonly").pack(fill="x", expand=True, pady=(0, 10))

        ctk.CTkLabel(body, text="Email").pack(anchor="w", padx=5)
        ctk.CTkEntry(body, textvariable=self.email_var, state="readonly").pack(fill="x", expand=True, pady=(0, 10))

    def crear_columna_detalles(self):
        """Crea el frame y widgets para la columna de detalles de la orden."""
        details_column = ctk.CTkFrame(self, fg_color="transparent")
        details_column.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        details_column.grid_rowconfigure(1, weight=1)
        
        # --- Caja de Detalle de la Orden ---
        order_box = ctk.CTkFrame(details_column, fg_color="#ffffff", border_width=1, border_color="#dee2e6", corner_radius=8)
        order_box.grid(row=0, column=0, sticky="new", pady=(0, 20))
        order_box.grid_columnconfigure((0,1,2,3), weight=1)

        header_order = ctk.CTkFrame(order_box, fg_color="#f1f3f5", corner_radius=0)
        header_order.grid(row=0, column=0, columnspan=4, sticky="ew", ipady=8)
        ctk.CTkLabel(header_order, text="Detalle de la Orden", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15)
        
        ctk.CTkLabel(order_box, text="Nro de O.T.:").grid(row=1, column=0, sticky="w", padx=15, pady=(15,5))
        ctk.CTkLabel(order_box, textvariable=self.ot_var, font=ctk.CTkFont(weight="bold"), text_color="#c0392b").grid(row=1, column=1, sticky="w", padx=5, pady=(15,5))

        ctk.CTkLabel(order_box, text="Fecha:").grid(row=1, column=2, sticky="w", padx=15, pady=(15,5))
        ctk.CTkLabel(order_box, textvariable=self.fecha_var).grid(row=1, column=3, sticky="w", padx=5, pady=(15,5))

        ctk.CTkLabel(order_box, text="Técnico/Vendedor:").grid(row=2, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkLabel(order_box, text=self.vendedor or "No Asignado", text_color="#2980b9", font=ctk.CTkFont(weight="bold")).grid(row=2, column=1, sticky="w", padx=5, pady=5)


        # --- Caja de Detalles del Equipo/Trabajo ---
        work_box = ctk.CTkFrame(details_column, fg_color="#ffffff", border_width=1, border_color="#dee2e6", corner_radius=8)
        work_box.grid(row=1, column=0, sticky="nsew")
        work_box.grid_columnconfigure(0, weight=1)
        work_box.grid_rowconfigure(2, weight=1)

        header_work = ctk.CTkFrame(work_box, fg_color="#f1f3f5", corner_radius=0)
        header_work.grid(row=0, column=0, columnspan=2, sticky="ew", ipady=8)
        ctk.CTkLabel(header_work, text="Detalles del Trabajo", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15)
        
        finance_frame = ctk.CTkFrame(work_box, fg_color="transparent")
        finance_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=15)
        finance_frame.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(finance_frame, text="Valor Total (Gs.)").grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(finance_frame, textvariable=self.valor_var).grid(row=1, column=0, sticky="ew", padx=(0,10))
        
        ctk.CTkLabel(finance_frame, text="Seña (Gs.)").grid(row=0, column=1, sticky="w")
        ctk.CTkEntry(finance_frame, textvariable=self.sena_var).grid(row=1, column=1, sticky="ew", padx=(0,10))

        ctk.CTkLabel(finance_frame, text="Forma de Pago").grid(row=0, column=2, sticky="w")
        pago_seg = ctk.CTkSegmentedButton(finance_frame, values=["Crédito", "Contado"], command=self._on_pago_changed, corner_radius=6)
        pago_seg.grid(row=1, column=2, sticky="ew", padx=(0,10))
        pago_seg.set("Contado")

        ctk.CTkLabel(finance_frame, text="Solicita Envío").grid(row=0, column=3, sticky="w", padx=10)
        envio_chk = ctk.CTkCheckBox(finance_frame, text="", variable=self.envio_var, onvalue=1, offvalue=0)
        envio_chk.grid(row=1, column=3, sticky="w", padx=10)

        ctk.CTkLabel(work_box, text="Descripción / Problema del Equipo / Observaciones", padx=15).grid(row=2, column=0, sticky="sw", pady=(10,0))
        self.desc_textbox = ctk.CTkTextbox(work_box, height=150, border_width=1, border_color="#ced4da")
        self.desc_textbox.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=15, pady=15)

    def limpiar_campos(self):
        """Limpia todos los campos del formulario a su estado inicial."""
        self.ot_var.set(str(get_next_ot_number()))
        self.fecha_var.set(datetime.now().strftime("%d/%m/%Y"))
        self.ci_ruc_var.set("")
        self.nombre_var.set("")
        self.phone_var.set("")
        self.email_var.set("")
        self.valor_var.set("0")
        self.sena_var.set("0")
        self.descripcion_var.set("")
        self.desc_textbox.delete("1.0", "end")
        self.pago_var.set(2)
        self.envio_var.set(0)
        self.registro_label.configure(text="")


    def _on_pago_changed(self, value):
        self.pago_var.set(1 if value == "Crédito" else 2)

    def abrir_registro_cliente(self):
        abrir_modulo_registro_cliente(parent=self)

    def validar_y_buscar(self, event=None):
        ci = self.ci_ruc_var.get().strip()
        if not ci:
            self.nombre_var.set("")
            self.phone_var.set("")
            self.email_var.set("")
            self.registro_label.configure(text="")
            return
            
        cliente = find_client_by_ci_ruc(ci)
        if cliente:
            self.nombre_var.set(cliente.get('nombre', ''))
            self.phone_var.set(cliente.get('telefono', ''))
            self.email_var.set(cliente.get('email', ''))
            self.registro_label.configure(text="✔️ Cliente Registrado", text_color="green")
        else:
            self.nombre_var.set("CLIENTE INEXISTENTE")
            self.phone_var.set("")
            self.email_var.set("")
            self.registro_label.configure(text="⚠️ No encontrado. Puede registrarlo.", text_color="#E67E22")

    def guardar_ot(self):
        try:
            self.descripcion_var.set(self.desc_textbox.get("1.0", "end-1c").strip())
            
            valor_str = self.valor_var.get().replace('.', '').replace(',', '')
            sena_str = self.sena_var.get().replace('.', '').replace(',', '')

            if not valor_str.isdigit(): raise ValueError("El campo 'Valor Total' solo debe contener números.")
            if not sena_str.isdigit(): raise ValueError("El campo 'Seña' solo debe contener números.")

            valor = float(valor_str)
            sena = float(sena_str)

            ot_nro = self.ot_var.get()
            fecha = self.fecha_var.get()
            ci_ruc = self.ci_ruc_var.get()
            nombre = self.nombre_var.get()
            forma_pago = "Crédito" if self.pago_var.get() == 1 else "Contado"
            envio_status = self.envio_var.get()

            if not ci_ruc or not nombre or "INEXISTENTE" in nombre:
                messagebox.showerror("Error de Cliente", "Debe ingresar o registrar un cliente válido antes de guardar la OT.")
                return

            fecha_iso = datetime.strptime(fecha, "%d/%m/%Y").strftime("%Y-%m-%d")

            datos_a_guardar = {
                "ot_nro": int(ot_nro), "fecha": fecha_iso, "ci_ruc": ci_ruc, "valor": valor, "sena": sena,
                "forma_pago": forma_pago, "envio_status": bool(envio_status), "status": "Pendiente",
                "descripcion": self.descripcion_var.get() or None,
                "vendedor": self.vendedor or None
            }
            
            resumen = (f"  - OT Nro: {ot_nro}\n"
                       f"  - Cliente: {nombre}\n"
                       f"  - Valor: Gs. {valor:,.0f}\n"
                       f"  - Seña: Gs. {sena:,.0f}\n"
                       f"  - Descripción: {datos_a_guardar['descripcion'] or 'N/A'}")
            
            if not messagebox.askyesno("Confirmar Guardado", f"¿Desea guardar la siguiente Orden de Trabajo?\n\n{resumen}"):
                return

            success, message = insert_work_order(datos_a_guardar)
            if success:
                messagebox.showinfo("Guardado Exitoso", f"Orden de Trabajo Nro. {ot_nro} guardada correctamente.")
                self.limpiar_campos()
            else:
                messagebox.showerror("Error al Guardar OT", message)

        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error Desconocido", f"Ocurrió un error inesperado al guardar: {e}")


def crear_modulo_ot_embedded(parent=None, vendedor=None):
    """Crea e inserta el formulario de OT como un `CTkFrame` embebido y lo retorna."""
    if parent is None:
        return None
    for child in parent.winfo_children():
        child.destroy()
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)
    form = OTForm(parent, vendedor=vendedor)
    form.grid(row=0, column=0, sticky="nsew")
    return form