import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from services.supabase_service import (
    add_sena_to_order,
    cancel_work_order,
    delete_abono,
    get_all_work_orders,
    get_work_order_by_ot,
    update_work_order_details,
    update_work_order_status,
    update_work_order_value,
)
from ..cancel.ot_cancel import VentanaCancelacion

# --- CONFIGURACIÓN DE ESTILO ---
ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("blue")

FORMA_PAGO_OPTIONS = ["Contado", "Crédito"]
ENVIO_OPTIONS = ["Con Envío", "Sin Envío (Retira)"]

def _to_int_amount(valor):
    try:
        return int(round(float(valor or 0)))
    except Exception:
        return 0

def _format_gs(valor):
    return f"{_to_int_amount(valor):,} Gs."

def _format_date_detail(raw_fecha):
    if not raw_fecha:
        return ""
    fecha_texto = str(raw_fecha).split('T')[0]
    try:
        fecha_dt = datetime.strptime(fecha_texto, "%Y-%m-%d")
        return fecha_dt.strftime("%d/%m/%Y")
    except Exception:
        return fecha_texto

def _envio_label_from_flag(flag):
    return "Con Envío" if flag else "Sin Envío (Retira)"

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

class ModuloOTs(ctk.CTkFrame):
    def __init__(self, parent, admin_context=None):
        super().__init__(parent, fg_color="transparent")

        # Datos cargados desde Supabase
        self.datos_ots = []
        self.ot_seleccionada = None
        self.admin_context = admin_context or {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.crear_planilla_izquierda()
        self.crear_detalle_derecha()
        # Cargar datos
        self.cargar_ots_desde_db()

    def crear_planilla_izquierda(self):
        self.frame_izq = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#D0D0D0")
        self.frame_izq.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        header = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(header, text="PLANILLA DE OTs", font=("Arial", 22, "bold")).pack(side="left")
        
        # Administrador: permitir ver OTs por estado (por defecto: Todos)
        estados_admin = ["Todos", "Pendiente", "Aprobado", "Entregado", "Finalizado", "Cancelado"]
        self.filtro_var = ctk.StringVar(value="Todos")
        self.combo_filtro = ctk.CTkComboBox(header, values=estados_admin,
                    variable=self.filtro_var, command=self.actualizar_tabla, width=140)
        self.combo_filtro.pack(side="left", padx=20)
        # Botón actualizar (recarga desde BD)
        try:
            self.btn_actualizar = ctk.CTkButton(header, text="Actualizar", width=110, command=self.cargar_ots_desde_db)
            self.btn_actualizar.pack(side="left", padx=6)
        except Exception:
            self.btn_actualizar = None

        self.entry_busqueda = ctk.CTkEntry(header, placeholder_text="🔍 Buscar...", width=300)
        self.entry_busqueda.pack(side="right")
        self.entry_busqueda.bind("<KeyRelease>", self.actualizar_tabla)

        cont_tabla_v = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        cont_tabla_v.pack(expand=True, fill="both", padx=15, pady=(0, 5))
        cont_tabla_v.grid_rowconfigure(0, weight=1)
        cont_tabla_v.grid_columnconfigure(0, weight=1)

        columnas = ("ot", "fecha", "vendedor", "cliente", "descripcion", "monto", "abonado", "pago", "estado")
        self.tabla = ttk.Treeview(cont_tabla_v, columns=columnas, show="headings")

        self.scroll_v_tabla = ctk.CTkScrollbar(cont_tabla_v, orientation="vertical", command=self.tabla.yview)
        self.scroll_h_tabla = ctk.CTkScrollbar(cont_tabla_v, orientation="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=self.scroll_v_tabla.set, xscrollcommand=self.scroll_h_tabla.set)

        # CONFIGURACIÓN DE COLORES (ADMIN - tonos más suaves, respetando asignaciones)
        # Pendiente: rojo claro (administrador)
        self.tabla.tag_configure("pendiente", background="#FADBD8")
        # Aprobado: naranja claro (administrador)
        self.tabla.tag_configure("aprobado", background="#FDE8C8")
        # Entregado: amarillo claro (administrador)
        self.tabla.tag_configure("entregado", background="#FFF4CC")
        # Finalizado: verde claro (administrador)
        self.tabla.tag_configure("finalizado", background="#BDECB6")
        # Cancelado: morado/purpura claro (administrador)
        self.tabla.tag_configure("cancelado", background="#F3E8FF")

        anchos = {"ot": 60, "fecha": 90, "vendedor": 100, "cliente": 150, "descripcion": 350, "monto": 100, "abonado": 100, "pago": 90, "estado": 100}
        for col in columnas:
            self.tabla.heading(col, text=col.upper())
            self.tabla.column(col, width=anchos[col], anchor="center", stretch=False)

        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.scroll_v_tabla.grid(row=0, column=1, sticky="ns")
        self.scroll_h_tabla.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_fila)
        self.actualizar_tabla()

    def cargar_ots_desde_db(self):
        ok, data = get_all_work_orders()
        if not ok:
            messagebox.showwarning("Advertencia", f"No se pudo cargar OTs: {data}")
            return
        # Mapear a estructura interna usada por la UI
        mapped = []
        for r in data:
            status_val = (r.get('status') or '').strip().lower()
            # Administrador nunca debe ver OTs rechazadas
            if status_val == 'rechazado':
                continue
            envia_flag = bool(r.get('solicita_envio'))
            mapped.append({
                'ot': str(r.get('ot_nro') or r.get('ot') or ''),
                'fecha': (r.get('fecha_creacion') or r.get('created_at') or '').split('T')[0] if r.get('fecha_creacion') or r.get('created_at') else '',
                'vendedor': r.get('vendedor') or '',
                'cliente': r.get('cliente') or r.get('cliente_ci_ruc') or r.get('ci_ruc') or '',
                'descripcion': r.get('descripcion') or '',
                'monto': int(r.get('valor_total') or 0),
                'pagos': r.get('pagos') or [],
                'sena': r.get('sena', 0) or 0,
                'abonado_total': r.get('abonado_total', 0) or 0,
                'pago': r.get('forma_pago') or '',
                'estado': r.get('status') or '',
                'envio': _envio_label_from_flag(envia_flag),
                'solicita_envio': envia_flag,
                'fecha_entrega': r.get('fecha_entrega'),
            })
        self.datos_ots = mapped
        self.actualizar_tabla()

    def crear_detalle_derecha(self):
        self.frame_det = ctk.CTkScrollableFrame(self, width=350, label_text="DETALLE DE LA ORDEN", 
                                                border_width=1, border_color="#D0D0D0", fg_color="#FDFDFD")
        self.frame_det.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")

        self.info_container = ctk.CTkFrame(self.frame_det, fg_color="transparent")
        self.info_container.pack(fill="x", padx=10, pady=10)

        self.lbl_ot_nro = self.crear_dato("OT Nro:")
        self.lbl_vendedor = self.crear_dato("Vendedor:")
        self.lbl_cliente = self.crear_dato("Cliente:")
        self.lbl_envio = self.crear_combo_dato("Tipo Envío:", ENVIO_OPTIONS)

        f_desc = ctk.CTkFrame(self.info_container, fg_color="transparent")
        f_desc.pack(fill="x", pady=5)
        ctk.CTkLabel(f_desc, text="Descripción:", font=("Arial", 11, "bold"), width=90, anchor="w").pack(side="left")
        # Ajuste mínimo: reducir wraplength para forzar salto de línea y añadir pequeño padding
        self.lbl_desc = ctk.CTkLabel(f_desc, text="---", font=("Arial", 11), wraplength=420, justify="left")
        self.lbl_desc.pack(side="left")

        self.lbl_pago = self.crear_combo_dato("Forma Pago:", FORMA_PAGO_OPTIONS)

        self.frame_fecha_entrega = ctk.CTkFrame(self.info_container, fg_color="transparent")
        ctk.CTkLabel(self.frame_fecha_entrega, text="Fecha Entrega:", font=("Arial", 11, "bold"), width=90, anchor="w").pack(side="left")
        self.lbl_fecha_entrega_val = ctk.CTkLabel(self.frame_fecha_entrega, text="---", font=("Arial", 11))
        self.lbl_fecha_entrega_val.pack(side="left")

        # EDICIÓN DE PRECIO TOTAL (alineado con otros campos)
        f_precio = ctk.CTkFrame(self.info_container, fg_color="transparent")
        f_precio.pack(fill="x", pady=2)
        ctk.CTkLabel(f_precio, text="Precio Total:", font=("Arial", 11, "bold"), width=90, anchor="w").pack(side="left")
        self.entry_precio_total = ctk.CTkEntry(f_precio, width=170, height=25)
        self.entry_precio_total.pack(side="left")

        self.btn_guardar_pago_envio = ctk.CTkButton(self.frame_det, text="Guardar datos", height=35, fg_color="#2980B9", command=self.guardar_pago_envio)
        self.btn_guardar_pago_envio.pack(pady=5, fill="x", padx=10)

        self.crear_separador()

        header_ab = ctk.CTkFrame(self.frame_det, fg_color="transparent")
        header_ab.pack(fill="x", padx=10)
        ctk.CTkLabel(header_ab, text="PAGOS REALIZADOS", font=("Arial", 12, "bold")).pack(side="left")
        # Botón para refrescar historial de pagos manualmente
        self.btn_refresh_pagos = ctk.CTkButton(header_ab, text="🔁", width=35, height=28, command=self.refrescar_pagos)
        self.btn_refresh_pagos.pack(side="right", padx=(6,0))
        self.btn_mas_pago = ctk.CTkButton(header_ab, text="+", width=35, height=28, command=self.abrir_ventana_pago)
        self.btn_mas_pago.pack(side="right")

        self.container_historial = ctk.CTkFrame(self.frame_det, fg_color="#F0F0F0", corner_radius=5)
        self.container_historial.pack(fill="x", padx=10, pady=10)

        self.lbl_total_view = self.crear_total("PRECIO TOTAL:")
        self.lbl_abonado = self.crear_total("ABONADO:")
        self.lbl_saldo = self.crear_total("SALDO:", color="#E74C3C")

        self.crear_separador()

        self.btn_aprobar = ctk.CTkButton(self.frame_det, text="APROBAR OT", height=45, fg_color="#27AE60", command=lambda: self.cambiar_estado("Aprobado"))
        self.btn_aprobar.pack(pady=5, fill="x", padx=10)

        self.btn_rechazar = ctk.CTkButton(self.frame_det, text="RECHAZAR OT", height=45, fg_color="#E74C3C", command=self.rechazar_ot)
        self.btn_rechazar.pack(pady=5, fill="x", padx=10)
        # Botones de entrega y finalización (se muestran según estado)
        self.btn_marcar_entregado = ctk.CTkButton(self.frame_det, text="MARCAR COMO ENTREGADO", height=45, fg_color="#F39C12", command=self.abrir_modal_entrega)
        self.btn_finalizar = ctk.CTkButton(self.frame_det, text="FINALIZAR PEDIDO", height=45, fg_color="#27AE60", command=lambda: self.cambiar_estado("finalizado"))
        self.btn_cancelar = ctk.CTkButton(self.frame_det, text="CANCELAR OT", height=45, fg_color="#C0392B", command=self.abrir_modal_cancelacion)

    def crear_dato(self, titulo):
        f = ctk.CTkFrame(self.info_container, fg_color="transparent")
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=titulo, font=("Arial", 11, "bold"), width=90, anchor="w").pack(side="left")
        l = ctk.CTkLabel(f, text="---", font=("Arial", 11))
        l.pack(side="left")
        return l

    def crear_combo_dato(self, titulo, opciones):
        f = ctk.CTkFrame(self.info_container, fg_color="transparent")
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=titulo, font=("Arial", 11, "bold"), width=90, anchor="w").pack(side="left")
        combo = ctk.CTkComboBox(f, values=opciones, width=170)
        combo.pack(side="left")
        return combo

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
        for i in self.tabla.get_children(): self.tabla.delete(i)
        busq = self.entry_busqueda.get().lower()
        filtro = self.filtro_var.get()
        for d in self.datos_ots:
            cliente_lower = (d.get('cliente') or '').lower()
            descripcion_lower = (d.get('descripcion') or '').lower()
            vendedor_lower = (d.get('vendedor') or '').lower()
            if (filtro == "Todos" or d.get("estado") == filtro) and \
               (busq in cliente_lower or busq in str(d.get('ot')) or busq in descripcion_lower or busq in vendedor_lower):
                # Preferir campo 'abonado_total' (nuevo esquema). Fallback: 'sena' o suma de pagos
                if d.get('abonado_total') is not None:
                    try:
                        abono = float(d.get('abonado_total') or 0)
                    except Exception:
                        abono = sum(p.get('m', 0) for p in d.get('pagos', []))
                else:
                    sena_val = d.get('sena', None)
                    if sena_val is None:
                        abono = sum(p.get('m', 0) for p in d.get('pagos', []))
                    else:
                        try:
                            abono = float(sena_val)
                        except Exception:
                            abono = sum(p.get('m', 0) for p in d.get('pagos', []))
                tag = (d.get("estado") or '').lower()
                monto_str = _format_gs(d.get('monto', 0))
                abono_str = _format_gs(abono)
                self.tabla.insert("", "end", values=(d.get("ot"), d.get("fecha"), d.get("vendedor"), d.get("cliente"), d.get("descripcion"), monto_str, abono_str, d.get("pago"), d.get("estado")), tags=(tag,))

    def al_seleccionar_fila(self, e):
        sel = self.tabla.selection()
        if not sel: return
        id_ot = str(self.tabla.item(sel[0])['values'][0])
        self.ot_seleccionada = next((x for x in self.datos_ots if x["ot"] == id_ot), None)
        if self.ot_seleccionada:
            # Solicitar detalle completo (incluye historial de abonos)
            try:
                ok, detalle = get_work_order_by_ot(self.ot_seleccionada.get('ot'))
                if ok and detalle:
                    self.ot_seleccionada['pagos'] = detalle.get('pagos', [])
                    self.ot_seleccionada['abonado_total'] = detalle.get('abonado_total', self.ot_seleccionada.get('abonado_total', 0))
                    self.ot_seleccionada['fecha_entrega'] = detalle.get('fecha_entrega', self.ot_seleccionada.get('fecha_entrega'))
                    self.ot_seleccionada['solicita_envio'] = detalle.get('solicita_envio', self.ot_seleccionada.get('solicita_envio', False))
                    envio_flag = bool(self.ot_seleccionada.get('solicita_envio'))
                    self.ot_seleccionada['envio'] = _envio_label_from_flag(envio_flag)
                    self.ot_seleccionada['pago'] = detalle.get('forma_pago', self.ot_seleccionada.get('pago'))
            except Exception:
                pass
            self.refrescar_detalle()

    def actualizar_precio_total(self):
        if not self.ot_seleccionada: return
        nuevo_m = self.entry_precio_total.get()
        if nuevo_m.isdigit():
            ot_n = self.ot_seleccionada.get('ot')
            ok, msg = update_work_order_value(ot_n, int(nuevo_m))
            if ok:
                self.ot_seleccionada['monto'] = int(nuevo_m)
                self.refrescar_detalle()
                self.actualizar_tabla()
            else:
                messagebox.showerror("Error", f"No se pudo actualizar valor: {msg}")
        else:
            messagebox.showerror("Error", "Monto inválido")

    def eliminar_pago(self, indice):
        if not self.ot_seleccionada:
            return
        pagos = self.ot_seleccionada.get('pagos', [])
        if indice < 0 or indice >= len(pagos):
            messagebox.showerror("Error", "Pago no encontrado en la lista.")
            return
        pago = pagos[indice]
        pago_id = pago.get('id')
        if not pago_id:
            # Fallback: si no hay id, pedir confirmación y eliminar localmente
            if messagebox.askyesno("Confirmar", "Pago sin id. ¿Eliminar localmente?"):
                self.ot_seleccionada['pagos'].pop(indice)
                self.refrescar_detalle(); self.actualizar_tabla()
            return
        if not messagebox.askyesno("Confirmar", "¿Desea eliminar este registro de pago? Esta acción es irreversible."):
            return
        ok, msg = delete_abono(pago_id)
        if ok:
            # Recargar detalle de la OT desde la DB
            try:
                ok_det, detalle = get_work_order_by_ot(self.ot_seleccionada.get('ot'))
                if ok_det and detalle:
                    self.ot_seleccionada['pagos'] = detalle.get('pagos', [])
                    self.ot_seleccionada['abonado_total'] = detalle.get('abonado_total', self.ot_seleccionada.get('abonado_total', 0))
                else:
                    # En caso de fallo, eliminar localmente
                    self.ot_seleccionada['pagos'].pop(indice)
            except Exception:
                try:
                    self.ot_seleccionada['pagos'].pop(indice)
                except Exception:
                    pass
            self.refrescar_detalle(); self.actualizar_tabla()
        else:
            messagebox.showerror("Error", f"No se pudo eliminar el abono: {msg}")

    def refrescar_detalle(self):
        d = self.ot_seleccionada
        if not d:
            return
        self.lbl_ot_nro.configure(text=d['ot'])
        self.lbl_vendedor.configure(text=d['vendedor'])
        self.lbl_cliente.configure(text=d['cliente'])
        self.lbl_desc.configure(text=d['descripcion'] or "---")
        pago_actual = d.get('pago') or FORMA_PAGO_OPTIONS[0]
        if pago_actual not in FORMA_PAGO_OPTIONS:
            pago_actual = FORMA_PAGO_OPTIONS[0]
        self.lbl_pago.set(pago_actual)
        envio_flag = bool(d.get('solicita_envio'))
        self.lbl_envio.set(_envio_label_from_flag(envio_flag))
        self.entry_precio_total.delete(0, 'end')
        self.entry_precio_total.insert(0, str(_to_int_amount(d.get('monto'))))

        for w in self.container_historial.winfo_children(): w.destroy()
        if d.get('abonado_total') is not None:
            try:
                abono = float(d.get('abonado_total') or 0)
            except Exception:
                abono = sum(p.get('m', 0) for p in d.get('pagos', []))
        else:
            abono = sum(p.get('m', 0) for p in d.get('pagos', []))
        for i, p in enumerate(d.get('pagos', [])):
            f = ctk.CTkFrame(self.container_historial, fg_color="white")
            f.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(f, text=f"📅 {p['f']}", font=("Arial", 10)).pack(side="left", padx=5)
            ctk.CTkLabel(f, text=_format_gs(p.get('m')), font=("Arial", 10, "bold")).pack(side="left", padx=5)
            btn_del = ctk.CTkButton(f, text="X", width=20, height=20, fg_color="#E74C3C", command=lambda idx=i: self.eliminar_pago(idx))
            btn_del.pack(side="right", padx=5)

        self.lbl_total_view.configure(text=_format_gs(d.get('monto')))
        self.lbl_abonado.configure(text=_format_gs(abono))
        self.lbl_saldo.configure(text=_format_gs(d.get('monto', 0) - abono))

        estado_lower = (d.get('estado') or '').lower()
        self._mostrar_fecha_entrega(d.get('fecha_entrega'), estado_lower)
        self._actualizar_boton_cancelar(estado_lower)
        
        if estado_lower == 'pendiente':
            self.btn_aprobar.configure(state="normal", fg_color="#27AE60")
            self.btn_rechazar.configure(state="normal", fg_color="#E74C3C")
            try:
                self.btn_marcar_entregado.pack_forget()
            except Exception:
                pass
            try:
                self.btn_finalizar.pack_forget()
            except Exception:
                pass
        elif estado_lower == 'aprobado':
            self.btn_aprobar.configure(state="disabled", fg_color="gray")
            self.btn_rechazar.configure(state="disabled", fg_color="gray")
            # mostrar botón de entrega
            try:
                self.btn_marcar_entregado.pack(pady=5, fill="x", padx=10)
            except Exception:
                pass
            try:
                self.btn_finalizar.pack_forget()
            except Exception:
                pass
        elif estado_lower == 'entregado':
            self.btn_aprobar.configure(state="disabled", fg_color="gray")
            self.btn_rechazar.configure(state="disabled", fg_color="gray")
            try:
                self.btn_marcar_entregado.pack_forget()
            except Exception:
                pass
            try:
                self.btn_finalizar.pack(pady=5, fill="x", padx=10)
            except Exception:
                pass
        else:
            # finalizado, rechazado u otros
            self.btn_aprobar.configure(state="disabled", fg_color="gray")
            self.btn_rechazar.configure(state="disabled", fg_color="gray")
            try:
                self.btn_marcar_entregado.pack_forget()
            except Exception:
                pass
            try:
                self.btn_finalizar.pack_forget()
            except Exception:
                pass

    def _mostrar_fecha_entrega(self, raw_fecha, estado_lower):
        debe_mostrar = estado_lower in ('entregado', 'finalizado') and bool(raw_fecha)
        if debe_mostrar:
            fecha_texto = _format_date_detail(raw_fecha) or "---"
            self.lbl_fecha_entrega_val.configure(text=fecha_texto)
            if not self.frame_fecha_entrega.winfo_manager():
                self.frame_fecha_entrega.pack(fill="x", pady=2)
        else:
            if self.frame_fecha_entrega.winfo_manager():
                self.frame_fecha_entrega.pack_forget()

    def guardar_pago_envio(self):
        if not self.ot_seleccionada:
            messagebox.showinfo("Info", "Seleccione primero una OT para guardar los cambios de pago o envío.")
            return
        forma_pago = self.lbl_pago.get() or FORMA_PAGO_OPTIONS[0]
        envio_label = self.lbl_envio.get()
        solicita_envio = envio_label == ENVIO_OPTIONS[0]

        cambios = {}
        if forma_pago != (self.ot_seleccionada.get('pago') or ""):
            cambios['forma_pago'] = forma_pago
        if bool(self.ot_seleccionada.get('solicita_envio')) != solicita_envio:
            cambios['solicita_envio'] = solicita_envio

        # También verificar si el precio total fue modificado y persistirlo
        nuevo_text = (self.entry_precio_total.get() or '').strip()
        precio_cambiado = False
        nuevo_val = None
        try:
            if nuevo_text != '':
                nuevo_val = int(round(float(nuevo_text)))
                precio_actual = _to_int_amount(self.ot_seleccionada.get('monto'))
                if nuevo_val != precio_actual:
                    precio_cambiado = True
        except Exception:
            messagebox.showerror("Error", "Monto inválido. Asegúrese de ingresar un número válido.")
            return

        if not cambios and not precio_cambiado:
            messagebox.showinfo("Sin cambios", "No se detectaron cambios en forma de pago, envío o precio.")
            return

        errors = []
        # Primero persistir detalles (forma/envío) si hay cambios
        if cambios:
            ok, msg = update_work_order_details(self.ot_seleccionada.get('ot'), cambios)
            if ok:
                self.ot_seleccionada['pago'] = forma_pago
                self.ot_seleccionada['solicita_envio'] = solicita_envio
                self.ot_seleccionada['envio'] = _envio_label_from_flag(solicita_envio)
            else:
                errors.append(f"detalle: {msg}")

        # Luego persistir precio si cambió
        if precio_cambiado:
            ok2, msg2 = update_work_order_value(self.ot_seleccionada.get('ot'), int(nuevo_val))
            if ok2:
                self.ot_seleccionada['monto'] = int(nuevo_val)
            else:
                errors.append(f"precio: {msg2}")

        if errors:
            messagebox.showerror("Error", f"Algunos cambios no se pudieron guardar: {'; '.join(errors)}")
        else:
            messagebox.showinfo("Actualizado", "Cambios guardados correctamente.")
        self.refrescar_detalle(); self.actualizar_tabla()

    def abrir_ventana_pago(self):
        if self.ot_seleccionada: VentanaAbono(self, self.registrar_abono_final)

    def registrar_abono_final(self, m):
        if not self.ot_seleccionada:
            return
        ot_n = self.ot_seleccionada.get('ot')
        ok, msg = add_sena_to_order(ot_n, m)
        if ok:
            messagebox.showinfo("Abono registrado", msg)
            # Intentar recargar historial de abonos de la OT y refrescar detalle
            try:
                ok_det, detalle = get_work_order_by_ot(ot_n)
                if ok_det and detalle:
                    self.ot_seleccionada['pagos'] = detalle.get('pagos', [])
                    self.ot_seleccionada['abonado_total'] = detalle.get('abonado_total', self.ot_seleccionada.get('abonado_total', 0))
                else:
                    # Fallback: añadir en memoria si la consulta falla
                    self.ot_seleccionada.setdefault('pagos', []).append({"m": m, "f": datetime.now().strftime("%d/%m/%y")})
                # Refrescar vista y tabla
                self.refrescar_detalle(); self.actualizar_tabla()
            except Exception:
                # Fallback: mantener en memoria y actualizar UI
                self.ot_seleccionada.setdefault('pagos', []).append({"m": m, "f": datetime.now().strftime("%d/%m/%y")})
                self.refrescar_detalle(); self.actualizar_tabla()
        else:
            messagebox.showerror("Error al registrar abono", f"No se pudo registrar abono: {msg}")

    def refrescar_pagos(self):
        """Recarga el historial de pagos para la OT actualmente seleccionada."""
        if not self.ot_seleccionada:
            messagebox.showinfo("Info", "Seleccione primero una OT para refrescar sus pagos.")
            return
        ot_n = self.ot_seleccionada.get('ot')
        try:
            ok_det, detalle = get_work_order_by_ot(ot_n)
            if ok_det and detalle:
                self.ot_seleccionada['pagos'] = detalle.get('pagos', [])
                self.ot_seleccionada['abonado_total'] = detalle.get('abonado_total', self.ot_seleccionada.get('abonado_total', 0))
                self.refrescar_detalle(); self.actualizar_tabla()
            else:
                messagebox.showwarning("Advertencia", "No se pudo obtener el historial de pagos para esta OT.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al refrescar pagos: {e}")

    def cambiar_estado(self, nuevo_estado):
        if self.ot_seleccionada:
            ot_n = self.ot_seleccionada.get('ot')
            # Normalizar para la DB: usar Title-case exacto del ENUM
            try:
                estado_db = str(nuevo_estado).strip().title()
            except Exception:
                estado_db = nuevo_estado
            ok, msg = update_work_order_status(ot_n, estado_db)
            if ok:
                # Mantener la presentación en UI con Title-case
                self.ot_seleccionada['estado'] = estado_db if isinstance(estado_db, str) else nuevo_estado
                self.actualizar_tabla()
                self.refrescar_detalle()
            else:
                messagebox.showerror("Error", f"No se pudo cambiar estado: {msg}")
    
    def abrir_modal_entrega(self):
        # Modal que pide fecha de entrega obligatoria
        if not self.ot_seleccionada:
            return
        win = ctk.CTkToplevel(self)
        win.title("Registrar Entrega")
        win.geometry("420x220")
        win.attributes("-topmost", True)
        win.grab_set()

        ctk.CTkLabel(win, text="Seleccionar Fecha de Entrega", font=("Arial", 13, "bold")).pack(pady=(12, 6))

        # Date picker simple con tres comboboxes (día, mes, año) para mantener compatibilidad sin nuevas dependencias
        fr_date = ctk.CTkFrame(win, fg_color="transparent")
        fr_date.pack(pady=6)

        import datetime as _dt
        hoy = _dt.date.today()
        dias = [f"{i:02d}" for i in range(1, 32)]
        meses = [f"{i:02d}" for i in range(1, 13)]
        anio_inicio = hoy.year - 1
        anios = [str(y) for y in range(anio_inicio, anio_inicio + 5)]

        self.cb_dia = ctk.CTkComboBox(fr_date, values=dias, width=80)
        self.cb_mes = ctk.CTkComboBox(fr_date, values=meses, width=80)
        self.cb_anio = ctk.CTkComboBox(fr_date, values=anios, width=100)
        self.cb_dia.pack(side="left", padx=(6,4))
        self.cb_mes.pack(side="left", padx=4)
        self.cb_anio.pack(side="left", padx=(4,6))

        # Inicializar con la fecha de hoy
        try:
            self.cb_dia.set(f"{hoy.day:02d}")
            self.cb_mes.set(f"{hoy.month:02d}")
            self.cb_anio.set(str(hoy.year))
        except Exception:
            pass

        def confirmar():
            d = (self.cb_dia.get() or '').strip()
            m = (self.cb_mes.get() or '').strip()
            y = (self.cb_anio.get() or '').strip()
            fecha = f"{d}/{m}/{y}"
            try:
                fecha_obj = datetime.strptime(fecha, "%d/%m/%Y").date()
            except Exception:
                messagebox.showerror("Error", "Seleccione una fecha válida.")
                return
            fecha_payload = fecha_obj.isoformat()
            ok, msg = update_work_order_status(self.ot_seleccionada.get('ot'), 'Entregado', fecha_entrega=fecha_payload)
            if ok:
                self.ot_seleccionada['estado'] = 'Entregado'
                self.ot_seleccionada['fecha_entrega'] = fecha_payload
                win.destroy()
                self.actualizar_tabla()
                self.refrescar_detalle()
            else:
                messagebox.showerror("Error", f"No se pudo actualizar estado: {msg}")

        # Botones estilo más profesional: side-by-side con colores suaves
        fr_btn = ctk.CTkFrame(win, fg_color="transparent")
        fr_btn.pack(pady=(12,10))
        btn_ok = ctk.CTkButton(fr_btn, text="Confirmar entrega", fg_color="#82E0AA", width=160, command=confirmar)
        btn_cancel = ctk.CTkButton(fr_btn, text="Cancelar", fg_color="#F5B7B1", width=120, command=win.destroy)
        btn_ok.pack(side="left", padx=8)
        btn_cancel.pack(side="left", padx=8)

    def abrir_modal_cancelacion(self):
        if not self.ot_seleccionada:
            return
        VentanaCancelacion(self, self.ot_seleccionada.get('ot'), self.confirmar_cancelacion)

    def confirmar_cancelacion(self, datos_cancelacion):
        admin_id = self.admin_context.get('id')
        if not admin_id:
            messagebox.showerror("Error", "No se encontró administrador autenticado.")
            return
        ot_nro = datos_cancelacion.get('ot')
        motivo = datos_cancelacion.get('motivo')
        reembolso = datos_cancelacion.get('reembolso', 0)
        ok, msg = cancel_work_order(ot_nro, admin_id, motivo=motivo, reembolso=reembolso)
        if ok:
            for d in self.datos_ots:
                if d.get('ot') == ot_nro:
                    d['estado'] = 'Cancelado'
            if self.ot_seleccionada and self.ot_seleccionada.get('ot') == ot_nro:
                self.ot_seleccionada['estado'] = 'Cancelado'
            messagebox.showinfo("Cancelada", "La orden fue cancelada correctamente.")
            self.actualizar_tabla()
            self.refrescar_detalle()
        else:
            messagebox.showerror("Error", f"No se pudo cancelar la OT: {msg}")

    def _actualizar_boton_cancelar(self, estado_lower):
        if not hasattr(self, 'btn_cancelar'):
            return
        manager = self.btn_cancelar.winfo_manager()
        final_states = ('finalizado', 'cancelado')
        if estado_lower in final_states:
            if manager:
                self.btn_cancelar.pack_forget()
        else:
            if not manager:
                self.btn_cancelar.pack(pady=5, fill="x", padx=10)

    def rechazar_ot(self):
        if self.ot_seleccionada:
            if messagebox.askyesno("Confirmar", f"¿Está seguro de rechazar la OT {self.ot_seleccionada['ot']}? Esto marcará la OT como rechazada."):
                ok, msg = update_work_order_status(self.ot_seleccionada.get('ot'), 'Rechazado')
                if ok:
                    # actualizar localmente y ocultarla del listado del admin
                    self.ot_seleccionada['estado'] = 'Rechazado'
                    self.datos_ots = [d for d in self.datos_ots if d.get('ot') != self.ot_seleccionada.get('ot')]
                    self.ot_seleccionada = None
                    self.actualizar_tabla()
                    # Limpiar textos de detalle
                    self.lbl_ot_nro.configure(text="---")
                    messagebox.showinfo("Rechazada", "La OT ha sido marcada como rechazada.")
                else:
                    messagebox.showerror("Error", f"No se pudo actualizar la OT: {msg}")
# No ejecutar como aplicación independiente; se integra en la ventana principal.