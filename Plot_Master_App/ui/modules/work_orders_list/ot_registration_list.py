import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
# Intentar usar el servicio de BD si está disponible
try:
    from services.supabase_service import get_all_work_orders
except Exception:
    get_all_work_orders = None

# --- CONFIGURACIÓN DE ESTILO ---
ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("blue")

class VentanaAbono(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Registrar Abono")
        self.geometry("300x220")
        self.callback = callback
        self.attributes("-topmost", True)
        self.grab_set()

        ctk.CTkLabel(self, text="Monto del Abono (Gs.):", font=("Arial", 13, "bold")).pack(pady=15)
        self.entry_monto = ctk.CTkEntry(self, placeholder_text="Ej: 100000", width=180)
        self.entry_monto.pack(pady=5)
        
        self.btn_confirmar = ctk.CTkButton(self, text="Confirmar Pago", fg_color="#27AE60", hover_color="#219150", command=self.enviar_datos)
        self.btn_confirmar.pack(pady=25)

    def enviar_datos(self):
        monto = self.entry_monto.get()
        if monto.isdigit():
            self.callback(int(monto))
            self.destroy()
        else:
            messagebox.showerror("Error", "Ingrese un monto válido.")

class OTsFrame(ctk.CTkFrame):
    """Frame embebible para mostrar la planilla y detalle de OTs.
    También se proporciona una pequeña app runner al final para pruebas standalone.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Si el frame está usado standalone, parent puede ser la propia ventana.
        if isinstance(parent, ctk.CTk):
            parent.title("Plot Master App - Gestión de OTs")
            parent.geometry("1200x800")
        # DATOS DE PRUEBA (Incluyendo campo de envío) — se reemplazan por los de la BD si están disponibles
        self.datos_ots = [
            {"ot": "1000", "fecha": "17/12/2025", "vendedor": "Marcos", "cliente": "Juan Pérez", "descripcion": "100 Tarjetas personales mate", "monto": 250000, "pagos": [{"m": 100000, "f": "17/12"}], "pago": "Crédito", "estado": "Aprobado", "envio": "Con Envío"},
            {"ot": "1001", "fecha": "17/12/2025", "vendedor": "Ana", "cliente": "Súper Sol", "descripcion": "Cartel lona frontal 3x2 mts", "monto": 1200000, "pagos": [{"m": 1200000, "f": "17/12"}], "pago": "Contado", "estado": "Finalizado", "envio": "Sin Envío (Retira)"},
            {"ot": "1002", "fecha": "17/12/2025", "vendedor": "Marcos", "cliente": "Farmacia Vida", "descripcion": "Vinilos microperforados", "monto": 800000, "pagos": [{"m": 400000, "f": "17/12"}], "pago": "Crédito", "estado": "Entregado", "envio": "Con Envío"},
        ]

        # Intentar cargar desde la base de datos real si el servicio está disponible
        if get_all_work_orders:
            ok, data = get_all_work_orders()
            if ok and isinstance(data, list):
                mapped = []
                for row in data:
                    try:
                        ot_nro = row.get('ot_nro')
                        fecha = row.get('fecha_creacion')
                        fecha_str = fecha if isinstance(fecha, str) else (fecha.strftime('%d/%m/%Y') if fecha else '')
                        cliente = row.get('cliente_ci_ruc') or ''
                        descripcion = row.get('descripcion') or row.get('descripcion', '')
                        monto = row.get('valor_total') or 0
                        forma_pago = row.get('forma_pago') or ''
                        estado = row.get('status') or ''
                        envio = 'Con Envío' if row.get('solicita_envio') else 'Sin Envío (Retira)'
                        mapped.append({
                            'ot': str(ot_nro), 'fecha': fecha_str, 'vendedor': row.get('vendedor') or '',
                            'cliente': cliente, 'descripcion': descripcion, 'monto': float(monto) if monto is not None else 0,
                            'pagos': [], 'pago': forma_pago, 'estado': estado, 'envio': envio
                        })
                    except Exception:
                        continue
                if mapped:
                    self.datos_ots = mapped

        self.ot_seleccionada = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Crear UI
        self.crear_planilla_izquierda()
        self.crear_detalle_derecha()

    def crear_planilla_izquierda(self):
        self.frame_izq = ctk.CTkFrame(self, fg_color="#FAFAFA", corner_radius=8, border_width=1, border_color="#D0D0D0")
        self.frame_izq.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        header = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(header, text="Órdenes de Trabajo", font=("Arial", 20, "bold"), text_color="#2C3E50").pack(side="left")
        
        # FILTRO DE ESTADO (Mantenido)
        self.filtro_var = ctk.StringVar(value="Todos")
        self.combo_filtro = ctk.CTkComboBox(header, values=["Todos", "Aprobado", "Entregado", "Finalizado"],
                            variable=self.filtro_var, command=self.actualizar_tabla, width=140)
        self.combo_filtro.pack(side="left", padx=20)

        self.entry_busqueda = ctk.CTkEntry(header, placeholder_text="🔍 Buscar...", width=300)
        self.entry_busqueda.pack(side="right")
        self.entry_busqueda.bind("<KeyRelease>", self.actualizar_tabla)

        # TABLA CON BARRA VERTICAL Y HORIZONTAL (Barras 1 y 2)
        cont_tabla_v = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        cont_tabla_v.pack(expand=True, fill="both", padx=15, pady=(0, 5))

        columnas = ("ot", "fecha", "cliente", "descripcion", "monto", "abonado", "pago", "estado")
        self.tabla = ttk.Treeview(cont_tabla_v, columns=columnas, show="headings")

        self.scroll_v_tabla = ctk.CTkScrollbar(cont_tabla_v, orientation="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=self.scroll_v_tabla.set)

        self.scroll_h_tabla = ctk.CTkScrollbar(self.frame_izq, orientation="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=self.scroll_h_tabla.set)

        self.tabla.tag_configure("aprobado", background="#FFF7E6")
        self.tabla.tag_configure("entregado", background="#FFFEE6")
        self.tabla.tag_configure("finalizado", background="#E8F8F0")

        anchos = {"ot": 60, "fecha": 90, "cliente": 180, "descripcion": 450, "monto": 110, "abonado": 110, "pago": 100, "estado": 100}
        for col in columnas:
            # Capitalizar nombre de columna para presentación
            h = col.upper() if col not in ("ot",) else "NRO"
            self.tabla.heading(col, text=h)
            self.tabla.column(col, width=anchos[col], anchor="center", stretch=False)

        self.tabla.pack(side="left", expand=True, fill="both")
        self.scroll_v_tabla.pack(side="right", fill="y")
        self.scroll_h_tabla.pack(side="bottom", fill="x", padx=15, pady=(0, 15))

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_fila)
        self.actualizar_tabla()

    def crear_detalle_derecha(self):
        # PANEL DERECHO CON SCROLL VERTICAL (detalle similar a la referencia)
        self.frame_det = ctk.CTkScrollableFrame(self, width=420, label_text="DETALLE DE LA ORDEN",
                            border_width=1, border_color="#D0D0D0", fg_color="#FFFFFF")
        self.frame_det.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")

        self.info_container = ctk.CTkFrame(self.frame_det, fg_color="transparent")
        self.info_container.pack(fill="x", padx=10, pady=10)

        # Cabecera del detalle (OT Nro + Estado similar al diseño)
        cab = ctk.CTkFrame(self.frame_det, fg_color="#F6F8FA")
        cab.pack(fill="x", padx=10, pady=(6, 10))
        self.lbl_ot_nro = ctk.CTkLabel(cab, text="---", font=("Arial", 14, "bold"))
        self.lbl_ot_nro.pack(side="left", padx=6, pady=6)
        self.lbl_estado_chip = ctk.CTkLabel(cab, text="---", font=("Arial", 11, "bold"), text_color="#FFFFFF", fg_color="#7F8C8D", width=120)
        self.lbl_estado_chip.pack(side="right", padx=6, pady=6)

        self.lbl_vendedor = self.crear_dato("Vendedor:")
        self.lbl_cliente = self.crear_dato("Cliente:")
        
        # --- NUEVO CAMPO: ENVÍO ---
        f_env = ctk.CTkFrame(self.info_container, fg_color="transparent")
        f_env.pack(fill="x", pady=2)
        ctk.CTkLabel(f_env, text="Tipo Envío:", font=("Arial", 11, "bold"), width=90, anchor="w").pack(side="left")
        self.lbl_envio = ctk.CTkLabel(f_env, text="---", font=("Arial", 11, "bold"), text_color="#2980B9")
        self.lbl_envio.pack(side="left")
        # --------------------------

        f_desc = ctk.CTkFrame(self.info_container, fg_color="transparent")
        f_desc.pack(fill="x", pady=5)
        ctk.CTkLabel(f_desc, text="Descripción:", font=("Arial", 11, "bold"), width=90, anchor="w").pack(side="left")
        self.lbl_desc = ctk.CTkLabel(f_desc, text="---", font=("Arial", 11), wraplength=180, justify="left")
        self.lbl_desc.pack(side="left")

        self.lbl_pago = self.crear_dato("Forma Pago:")

        self.crear_separador()

        header_ab = ctk.CTkFrame(self.frame_det, fg_color="transparent")
        header_ab.pack(fill="x", padx=10)
        ctk.CTkLabel(header_ab, text="PAGOS REALIZADOS", font=("Arial", 12, "bold")).pack(side="left")
        self.btn_mas_pago = ctk.CTkButton(header_ab, text="Registrar abono", width=140, height=30, command=self.abrir_ventana_pago)
        self.btn_mas_pago.pack(side="right")

        self.container_historial = ctk.CTkFrame(self.frame_det, fg_color="#F0F0F0", corner_radius=5)
        self.container_historial.pack(fill="x", padx=10, pady=10)

        self.lbl_total = self.crear_total("PRECIO TOTAL:")
        self.lbl_abonado = self.crear_total("ABONADO:")
        self.lbl_saldo = self.crear_total("SALDO:", color="#E74C3C")

        self.crear_separador()

        self.btn_entregar = ctk.CTkButton(self.frame_det, text="MARCAR ENTREGADO", height=40, command=lambda: self.cambiar_estado("Entregado"))
        self.btn_entregar.pack(pady=8, fill="x", padx=10)

        self.btn_finalizar = ctk.CTkButton(self.frame_det, text="FINALIZAR PEDIDO", height=40, command=lambda: self.cambiar_estado("Finalizado"))
        self.btn_finalizar.pack(pady=(0,12), fill="x", padx=10)

    def crear_dato(self, titulo):
        f = ctk.CTkFrame(self.info_container, fg_color="transparent")
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=titulo, font=("Arial", 11, "bold"), width=90, anchor="w").pack(side="left")
        l = ctk.CTkLabel(f, text="---", font=("Arial", 11))
        l.pack(side="left")
        return l

    def crear_total(self, titulo, color=None):
        f = ctk.CTkFrame(self.frame_det, fg_color="transparent")
        f.pack(fill="x", padx=15, pady=2)
        ctk.CTkLabel(f, text=titulo, font=("Arial", 12, "bold")).pack(side="left")
        l = ctk.CTkLabel(f, text="0 Gs.", text_color=color, font=("Arial", 14, "bold"))
        l.pack(side="right")
        return l

    def crear_separador(self):
        linea = ctk.CTkFrame(self.frame_det, height=2, fg_color="#EEEEEE")
        linea.pack(fill="x", padx=10, pady=15)

    def actualizar_tabla(self, e=None):
        # Preserve selection if possible
        sel_ot = self.ot_seleccionada['ot'] if self.ot_seleccionada else None
        for i in self.tabla.get_children():
            self.tabla.delete(i)
        busq = (self.entry_busqueda.get() or "").lower()
        filtro = self.filtro_var.get()
        for d in self.datos_ots:
            # defensively get strings
            cliente_text = (d.get("cliente") or "").lower()
            descripcion_text = (d.get("descripcion") or "").lower()
            ot_text = str(d.get("ot") or "")
            estado_text = (d.get("estado") or "").lower()

            if (filtro == "Todos" or d.get("estado") == filtro) and \
               (busq in cliente_text or busq in ot_text or busq in descripcion_text):
                abono = sum(p.get('m', 0) for p in d.get('pagos', []))
                tag = estado_text
                self.tabla.insert("", "end", values=(d.get("ot"), d.get("fecha"), d.get("cliente"), d.get("descripcion"), f"{d.get('monto', 0):,} Gs.", f"{abono:,} Gs.", d.get("pago"), d.get("estado")), tags=(tag,))

        # Try to restore selection and detail view
        if sel_ot is not None:
            for item in self.tabla.get_children():
                vals = self.tabla.item(item)['values']
                if str(vals[0]) == str(sel_ot):
                    self.tabla.selection_set(item)
                    # Update ot_seleccionada reference to the current data dict
                    self.ot_seleccionada = next((x for x in self.datos_ots if x['ot'] == sel_ot), self.ot_seleccionada)
                    self.refrescar_detalle()
                    break

    def al_seleccionar_fila(self, e):
        sel = self.tabla.selection()
        if not sel: return
        id_ot = str(self.tabla.item(sel[0])['values'][0])
        self.ot_seleccionada = next((x for x in self.datos_ots if x["ot"] == id_ot), None)
        if not self.ot_seleccionada:
            return
        self.refrescar_detalle()

    def refrescar_detalle(self):
        d = self.ot_seleccionada
        if not d: return
        self.lbl_ot_nro.configure(text=f"OT {d['ot']}")
        self.lbl_vendedor.configure(text=d['vendedor'])
        self.lbl_cliente.configure(text=d['cliente'])
        self.lbl_desc.configure(text=d['descripcion'])
        self.lbl_pago.configure(text=d['pago'])

        # Estado (chip)
        self.lbl_estado_chip.configure(text=d.get('estado', '---'))
        estado_color = "#27AE60" if d.get('estado') == 'Finalizado' else ("#F39C12" if d.get('estado') == 'Aprobado' else "#2980B9")
        self.lbl_estado_chip.configure(fg_color=estado_color)

        # --- Actualizar Campo de Envío ---
        self.lbl_envio.configure(text=d['envio'])
        if "Con Envío" in d['envio']:
            self.lbl_envio.configure(text_color="#27AE60")
        else:
            self.lbl_envio.configure(text_color="#2980B9")

        for w in self.container_historial.winfo_children(): w.destroy()
        abono = sum(p['m'] for p in d['pagos'])
        for p in d['pagos']:
            f = ctk.CTkFrame(self.container_historial, fg_color="white")
            f.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(f, text=f"📅 {p['f']}", font=("Arial", 10)).pack(side="left", padx=10)
            ctk.CTkLabel(f, text=f"{p['m']:,} Gs.", font=("Arial", 10, "bold")).pack(side="right", padx=10)

        self.lbl_total.configure(text=f"{d['monto']:,} Gs.")
        self.lbl_abonado.configure(text=f"{abono:,} Gs.")
        self.lbl_saldo.configure(text=f"{d['monto'] - abono:,} Gs.")

        self.btn_entregar.configure(state="normal" if d['estado'] == "Aprobado" else "disabled", 
                                    fg_color="#F39C12" if d['estado'] == "Aprobado" else "gray")
        self.btn_finalizar.configure(state="normal" if d['estado'] == "Entregado" else "disabled", 
                                     fg_color="#27AE60" if d['estado'] == "Entregado" else "gray")

    def abrir_ventana_pago(self):
        if self.ot_seleccionada: VentanaAbono(self, self.registrar_abono_final)

    def registrar_abono_final(self, m):
        self.ot_seleccionada['pagos'].append({"m": m, "f": datetime.now().strftime("%d/%m/%y")})
        self.refrescar_detalle(); self.actualizar_tabla()

    def cambiar_estado(self, nuevo_estado):
        if self.ot_seleccionada:
            self.ot_seleccionada['estado'] = nuevo_estado
            self.actualizar_tabla(); self.refrescar_detalle()

# Backwards compatibility: some modules import `ModuloOTs`
ModuloOTs = OTsFrame

if __name__ == "__main__":
    # Modo standalone para pruebas rápidas
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    frame = OTsFrame(root)
    frame.pack(fill="both", expand=True)
    root.mainloop()
