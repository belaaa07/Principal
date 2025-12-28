import customtkinter as ctk
from tkinter import ttk, messagebox
import threading
from services.supabase_service import get_all_clients, update_client, get_work_orders_by_client

# --- CONFIGURACIÓN GLOBAL ---
ctk.set_appearance_mode("light") # Fondo claro siempre
ctk.set_default_color_theme("blue")

class ModuloClientes(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#F5F5F5")

        self.clientes = []
        self.historial_ots = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.crear_planilla_izquierda()
        self.crear_panel_detalle_derecho()
        self._load_clientes_async()

    def crear_planilla_izquierda(self):
        # Frame blanco para la tabla
        self.frame_izq = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#D0D0D0")
        self.frame_izq.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        header = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(header, text="👤 REGISTRO DE CLIENTES", font=("Arial", 22, "bold"), text_color="black").pack(side="left")
        
        self._search_after_id = None
        self.entry_busqueda = ctk.CTkEntry(header, placeholder_text="🔍 Buscar cliente...", width=350, text_color="black")
        self.entry_busqueda.pack(side="right")
        self.entry_busqueda.bind("<KeyRelease>", self._on_search_change)

        cont_tabla = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        cont_tabla.pack(expand=True, fill="both", padx=15, pady=5)
        cont_tabla.grid_rowconfigure(0, weight=1)
        cont_tabla.grid_columnconfigure(0, weight=1)

        columnas = ("nro", "ruc", "nombre", "tel", "email", "ciudad")
        self.tabla = ttk.Treeview(cont_tabla, columns=columnas, show="headings")

        # --- SCROLLBARS ---
        scroll_v = ctk.CTkScrollbar(cont_tabla, orientation="vertical", command=self.tabla.yview)
        scroll_h = ctk.CTkScrollbar(cont_tabla, orientation="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scroll_v.set, xscrollcommand=scroll_h.set)

        anchos = {"nro": 60, "ruc": 110, "nombre": 250, "tel": 120, "email": 200, "ciudad": 150}
        for col in columnas:
            self.tabla.heading(col, text=col.upper())
            self.tabla.column(col, width=anchos[col], anchor="center")

        self.tabla.grid(row=0, column=0, sticky="nsew")
        scroll_v.grid(row=0, column=1, sticky="ns")
        scroll_h.grid(row=1, column=0, sticky="ew")
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_cliente)
        
        self.actualizar_tabla()

    def crear_panel_detalle_derecho(self):
        # Frame de la ficha con fondo claro
        self.frame_det = ctk.CTkScrollableFrame(self, width=380, label_text="FICHA DEL CLIENTE", 
                                                label_text_color="black",
                                                border_width=1, border_color="#D0D0D0", fg_color="white")
        self.frame_det.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")

        self.container_datos = ctk.CTkFrame(self.frame_det, fg_color="transparent")
        self.container_datos.pack(fill="x", padx=10, pady=10)

        # Nombre en negro
        self.lbl_nombre = ctk.CTkLabel(self.container_datos, text="Seleccione un cliente", font=("Arial", 16, "bold"), text_color="black")
        self.lbl_nombre.pack(pady=10)

        # Campos de datos editables
        self.val_ruc = self.crear_linea_dato(self.container_datos, "CI/RUC:")
        self.val_tel = self.crear_linea_entry(self.container_datos, "Teléfono:")
        self.val_email = self.crear_linea_entry(self.container_datos, "Email:")
        # Ciudad/Zona ahora es Combobox poblado desde DB
        self.val_ciudad = self.crear_linea_combobox(self.container_datos, "Ciudad/Zona:")

        # Botón guardar cambios
        ctk.CTkButton(self.container_datos, text="Guardar cambios", fg_color="#27AE60", command=self.guardar_cliente).pack(pady=8)

        ctk.CTkFrame(self.frame_det, height=2, fg_color="#EEEEEE").pack(fill="x", padx=10, pady=15)

        ctk.CTkLabel(self.frame_det, text="OTs REALIZADAS", font=("Arial", 12, "bold"), text_color="black").pack(anchor="w", padx=15)
        
        self.container_ots = ctk.CTkFrame(self.frame_det, fg_color="#F9F9F9", corner_radius=8, border_width=1, border_color="#E0E0E0")
        self.container_ots.pack(fill="x", padx=10, pady=10)
        
        self.lbl_lista_ots = ctk.CTkLabel(self.container_ots, text="---", font=("Arial", 12), wraplength=300, text_color="black")
        self.lbl_lista_ots.pack(pady=15, padx=10)

    def crear_linea_dato(self, parent, titulo):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=2)
        # Título y valor en negro
        ctk.CTkLabel(f, text=titulo, font=("Arial", 11, "bold"), width=100, anchor="w", text_color="black").pack(side="left")
        l = ctk.CTkLabel(f, text="---", font=("Arial", 11), text_color="black")
        l.pack(side="left")
        return l

    def crear_linea_entry(self, parent, titulo):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=titulo, font=("Arial", 11, "bold"), width=100, anchor="w", text_color="black").pack(side="left")
        e = ctk.CTkEntry(f, width=200)
        e.pack(side="left")
        return e

    def crear_linea_combobox(self, parent, titulo):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=titulo, font=("Arial", 11, "bold"), width=100, anchor="w", text_color="black").pack(side="left")
        # usar CTkComboBox para mantener consistencia visual con el resto de campos
        valores = [
            'Areguá','Asunción','Capiatá','Fernando de la Mora','Guarambaré','Itá','Itauguá',
            'J. Augusto Saldívar','Lambaré','Limpio','Luque','Mariano Roque Alonso','Nueva Italia',
            'Ñemby','San Antonio','San Lorenzo','Villa Elisa','Villeta','Ypané','Ypacaraí','Otro'
        ]
        # iniciar variable vacía para que no se muestre el primer valor por defecto
        cb_var = ctk.StringVar(value="")
        cb = ctk.CTkComboBox(f, values=valores, width=200, variable=cb_var)
        # iniciar deshabilitado; se habilita al seleccionar un cliente
        try:
            cb.configure(state="disabled")
        except Exception:
            pass
        cb.pack(side="left")
        return cb

    def _on_search_change(self, _event=None):
        if getattr(self, '_search_after_id', None):
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(120, self.actualizar_tabla)

    def actualizar_tabla(self, e=None):
        for i in self.tabla.get_children():
            self.tabla.delete(i)
        busq = self.entry_busqueda.get().lower()
        for c in self.clientes:
            nombre = c.get('nombre') or ''
            ci_ruc = c.get('ci_ruc') or ''
            if busq in nombre.lower() or busq in ci_ruc:
                self.tabla.insert("", "end", values=(c.get('id') or '', ci_ruc, nombre, c.get('telefono') or '', c.get('email') or '', c.get('zona') or ''))

    def al_seleccionar_cliente(self, e):
        sel = self.tabla.selection()
        if not sel: return
        valores = self.tabla.item(sel[0])['values']
        # Valores devueltos por la tabla
        try:
            ci_ruc = str(valores[1]).strip()
        except Exception:
            ci_ruc = ''

        # Intentar encontrar el cliente por CI/RUC, si no por id, si no por nombre (tolerante)
        cliente = next((c for c in self.clientes if str(c.get('ci_ruc') or '').strip() == ci_ruc), None)
        if not cliente:
            # intentar por id (columna 0)
            try:
                vid = str(valores[0]).strip()
                cliente = next((c for c in self.clientes if str(c.get('id') or '') == vid), None)
            except Exception:
                cliente = None
        if not cliente:
            # intentar por nombre (columna 2)
            try:
                vname = str(valores[2]).strip().lower()
                cliente = next((c for c in self.clientes if (c.get('nombre') or '').strip().lower() == vname), None)
            except Exception:
                cliente = None
        if not cliente:
            # Mostrar información de depuración mínima
            print(f"Cliente no encontrado para valores de fila: {valores}")
            messagebox.showwarning("No encontrado", "No se encontró el cliente correspondiente a la fila seleccionada.")
            return
        self.seleccion_ci = ci_ruc
        self.lbl_nombre.configure(text=(cliente.get('nombre') or '---').upper())
        self.val_ruc.configure(text=ci_ruc)
        # Set entry values
        self.val_tel.delete(0, 'end'); self.val_tel.insert(0, cliente.get('telefono') or '')
        self.val_email.delete(0, 'end'); self.val_email.insert(0, cliente.get('email') or '')
        # habilitar combobox y asignar valor
        try:
            if hasattr(self.val_ciudad, 'configure'):
                self.val_ciudad.configure(state="normal")
            # set value
            try:
                self.val_ciudad.set(cliente.get('zona') or '')
            except Exception:
                # fallback en caso de que CTkComboBox no tenga set
                try:
                    self.val_ciudad.delete(0, 'end'); self.val_ciudad.insert(0, cliente.get('zona') or '')
                except Exception:
                    pass
        except Exception:
            pass
        # Cargar OTs reales desde la base de datos (Supabase)
        try:
            ok, data = get_work_orders_by_client(ci_ruc)
        except Exception as ex:
            print(f"Error llamando a get_work_orders_by_client: {ex}")
            ok, data = False, None

        if not ok or not data:
            # Vaciar contenedor y mostrar texto por defecto
            self.lbl_lista_ots.configure(text="Sin órdenes registradas", text_color="gray")
            print(f"No hay OTs para cliente {ci_ruc} (ok={ok}, data={data})")
            return

        # data es una lista de filas; extraer números de OT
        ot_nros = [str(r.get('ot_nro') or r.get('ot') or '') for r in data]
        texto_ots = " , ".join([f"#{n}" for n in ot_nros if n])
        if texto_ots:
            self.lbl_lista_ots.configure(text=texto_ots, text_color="black")
        else:
            self.lbl_lista_ots.configure(text="Sin órdenes registradas", text_color="gray")

    def guardar_cliente(self):
        if not hasattr(self, 'seleccion_ci'):
            messagebox.showwarning("Seleccionar", "Seleccione un cliente antes de guardar.")
            return
        ci = self.seleccion_ci
        updates = {
            'telefono': self.val_tel.get(),
            'email': self.val_email.get(),
            'zona': (self.val_ciudad.get() if hasattr(self.val_ciudad, 'get') else '')
        }
        ok, msg = update_client(ci, updates)
        if ok:
            messagebox.showinfo("Guardado", "Cliente actualizado correctamente.")
            self._load_clientes_async()
        else:
            messagebox.showerror("Error", f"No se pudo actualizar cliente: {msg}")

    def _load_clientes_async(self):
        self._set_loading(True)
        threading.Thread(target=self._fetch_clientes_background, daemon=True).start()

    def _fetch_clientes_background(self):
        try:
            ok, data = get_all_clients()
        except Exception as exc:
            ok, data = False, f"Error inesperado: {exc}"
        self.after(0, lambda: self._apply_clientes(ok, data))

    def _apply_clientes(self, ok, data):
        self._set_loading(False)
        if not ok:
            messagebox.showwarning("Advertencia", f"No se pudo cargar clientes: {data}")
            return
        self.clientes = data or []
        self.actualizar_tabla()

    def _set_loading(self, is_loading: bool):
        try:
            state = "disabled" if is_loading else "normal"
            self.entry_busqueda.configure(state=state)
        except Exception:
            pass

# Uso embebido dentro de la aplicación principal. No se ejecuta standalone.