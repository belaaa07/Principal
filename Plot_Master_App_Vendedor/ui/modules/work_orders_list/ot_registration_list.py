import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
# Usar servicio de BD (obligatorio)
try:
    from services.supabase_service import get_work_orders_by_vendedor, update_work_order_status
except Exception:
    get_work_orders_by_vendedor = None
    update_work_order_status = None

# --- CONFIGURACIÓN DE ESTILO ---
ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("blue")

def _to_int_amount(valor):
    try:
        return int(round(float(valor or 0)))
    except Exception:
        return 0

def _format_gs(valor):
    return f"{_to_int_amount(valor):,} Gs."


def normalize_estado(s):
    # Canonical states order: Pendiente, Aprobado, Entregado, Finalizado
    if not s:
        return 'Pendiente'
    s2 = str(s).strip().lower()
    if 'cancel' in s2 or 'cancelad' in s2:
        return 'Cancelado'
    if s2 in ('pendiente', 'pending'):
        return 'Pendiente'
    if 'rechaz' in s2:
        return 'Rechazado'
    if s2 in ('aprobado', 'aprovado', 'aprobed'):
        return 'Aprobado'
    if 'entreg' in s2:
        return 'Entregado'
    if s2 in ('finalizado', 'finalizado/a', 'final'):
        return 'Finalizado'
    return 'Pendiente'

# Los vendedores NO pueden registrar abonos ni marcar entregas/finalizar pedidos.
# Se han eliminado los modales y botones relacionados en esta vista.

class OTsFrame(ctk.CTkFrame):
    """Frame embebible para mostrar la planilla y detalle de OTs.
    También se proporciona una pequeña app runner al final para pruebas standalone.
    """
    def __init__(self, parent, vendedor: str = None, vendedor_nombre: str = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.vendedor = vendedor
        self.vendedor_nombre = vendedor_nombre or vendedor or "—"

        # Si el frame está usado standalone, parent puede ser la propia ventana.
        if isinstance(parent, ctk.CTk):
            parent.title("Plot Master App - Gestión de OTs")
            parent.geometry("1200x800")
        # Inicializar lista (se cargará después de crear la UI)
        self.datos_ots = []

        self.ot_seleccionada = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Crear UI
        self.crear_planilla_izquierda()
        self.crear_detalle_derecha()
        # Cargar OTs desde BD ahora que la UI está creada
        try:
            if get_work_orders_by_vendedor and self.vendedor:
                self._load_ots_async()
        except Exception:
            pass

    def crear_planilla_izquierda(self):
        self.frame_izq = ctk.CTkFrame(self, fg_color="#FAFAFA", corner_radius=8, border_width=1, border_color="#D0D0D0")
        self.frame_izq.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        header = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(header, text="Órdenes de Trabajo", font=("Arial", 20, "bold"), text_color="#2C3E50").pack(side="left")
        
        # FILTRO DE ESTADO (usar lista canónica)
        self.filtro_var = ctk.StringVar(value="Todos")
        estados_permitidos = ["Pendiente", "Aprobado", "Rechazado", "Entregado", "Finalizado", "Cancelado"]
        self.combo_filtro = ctk.CTkComboBox(header, values=["Todos"] + estados_permitidos,
                variable=self.filtro_var, command=self.actualizar_tabla, width=220)
        self.combo_filtro.pack(side="left", padx=20)

        # Botón de recarga (Actualizar)
        try:
            self.btn_actualizar = ctk.CTkButton(header, text="Actualizar", width=110, command=self._load_ots_async)
            self.btn_actualizar.pack(side="left", padx=6)
        except Exception:
            self.btn_actualizar = None

        self._search_after_id = None
        self.entry_busqueda = ctk.CTkEntry(header, placeholder_text="🔍 Buscar...", width=300)
        self.entry_busqueda.pack(side="right")
        self.entry_busqueda.bind("<KeyRelease>", self._on_search_change)

        # TABLA: contenedor con scroll vertical y horizontal SOLO para la tabla
        cont_tabla_v = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        cont_tabla_v.pack(expand=True, fill="both", padx=15, pady=(0, 5))

        columnas = ("ot", "fecha", "cliente", "descripcion", "monto", "abonado", "pago", "estado")
        # Crear la Treeview con `tabla_container` como padre para que `grid` funcione correctamente
        self.tabla = None

        # Contenedor interno que utiliza grid para colocar la tabla y las barras correctamente
        tabla_container = ctk.CTkFrame(cont_tabla_v, fg_color="transparent")
        tabla_container.pack(expand=True, fill="both")
        tabla_container.grid_rowconfigure(0, weight=1)
        tabla_container.grid_columnconfigure(0, weight=1)

        # Crear la Treeview con `tabla_container` como padre para que grid coloque bien la tabla
        self.tabla = ttk.Treeview(tabla_container, columns=columnas, show="headings")

        # Scrolls dedicados
        self.scroll_v_tabla = ctk.CTkScrollbar(tabla_container, orientation="vertical", command=self.tabla.yview)
        self.scroll_h_tabla = ctk.CTkScrollbar(tabla_container, orientation="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=self.scroll_v_tabla.set, xscrollcommand=self.scroll_h_tabla.set)

        # Tags para estados normalizados (TONOS MÁS SUAVES - vendedor)
        # Pendiente: claro amarillo estilo Excel
        self.tabla.tag_configure("pendiente", background="#FFF4CC")
        # Aprobado: verde suave
        self.tabla.tag_configure("aprobado", background="#C8E6C9")
        # Rechazado: rojo/rosa muy suave
        self.tabla.tag_configure("rechazado", background="#FADBD8")
        # Entregado: verde-agua pálido
        self.tabla.tag_configure("entregado", background="#D6F5F0")
        # Finalizado: morado claro (vendedor)
        self.tabla.tag_configure("finalizado", background="#EADBF7")
        # Cancelado: morado/purpura claro (vendedor)
        self.tabla.tag_configure("cancelado", background="#F3E8FF")

        # Column widths: permitir que el ancho total exceda el contenedor para habilitar scroll horizontal
        anchos = {"ot": 70, "fecha": 90, "cliente": 260, "descripcion": 480, "monto": 110, "abonado": 110, "pago": 100, "estado": 120}
        for col in columnas:
            h = col.upper() if col not in ("ot",) else "NRO"
            # Centrar encabezados
            self.tabla.heading(col, text=h, anchor="center")
            # Centrar contenido de 'cliente' y 'descripcion' pero permitir stretch (no fijar)
            if col in ("cliente", "descripcion"):
                self.tabla.column(col, width=anchos[col], anchor="center", stretch=True)
            else:
                self.tabla.column(col, width=anchos[col], anchor="center", stretch=False)

        # Colocar con grid para que las barras queden vinculadas correctamente a la tabla
        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.scroll_v_tabla.grid(row=0, column=1, sticky="ns")
        self.scroll_h_tabla.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_fila)
        self.actualizar_tabla()

    def crear_detalle_derecha(self):
        # PANEL DERECHO CON SCROLL VERTICAL (detalle similar a la referencia)
        self.frame_det = ctk.CTkScrollableFrame(self, width=420, label_text="DETALLE DE LA ORDEN",
                            border_width=1, border_color="#D0D0D0", fg_color="#FFFFFF")
        self.frame_det.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")

        # Cabecera del detalle (chip OT + estado) alineado al estilo admin
        self.header_chip = ctk.CTkFrame(self.frame_det, fg_color="#F6F8FA", corner_radius=10)
        self.header_chip.pack(fill="x", padx=10, pady=(8, 10))
        self.lbl_ot_chip = ctk.CTkLabel(self.header_chip, text="OT ---", font=("Segoe UI", 15, "bold"), text_color="#1F2937")
        self.lbl_ot_chip.pack(side="left", padx=10, pady=10)
        self.lbl_estado_chip = ctk.CTkLabel(self.header_chip, text="---", font=("Segoe UI", 12, "bold"), text_color="#FFFFFF", fg_color="#94A3B8", corner_radius=14, padx=12, pady=8)
        self.lbl_estado_chip.pack(side="right", padx=10, pady=10)

        self.info_container = ctk.CTkFrame(self.frame_det, fg_color="transparent")
        self.info_container.pack(fill="x", padx=10, pady=10)

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
        ctk.CTkLabel(f_desc, text="Descripción:", font=("Segoe UI", 11, "bold"), width=90, anchor="w").pack(side="left")
        self.lbl_desc = ctk.CTkLabel(f_desc, text="---", font=("Segoe UI", 11), wraplength=300, justify="left")
        self.lbl_desc.pack(side="left")

        self.lbl_pago = self.crear_dato("Forma Pago:")

        self.crear_separador()

        self.lbl_total = self.crear_total("PRECIO TOTAL:")
        self.lbl_abonado = self.crear_total("ABONADO:")
        self.lbl_saldo = self.crear_total("SALDO:", color="#E74C3C")

        self.crear_separador()
        # Los botones de 'Marcar entregado' y 'Finalizar pedido' no se muestran para vendedores
        # Pero crear los widgets vacíos/defensivos para evitar AttributeError en refrescar_detalle
        try:
            self.btn_entregar = ctk.CTkButton(self.frame_det, text="Marcar Entregado", fg_color="#F39C12", state="disabled")
        except Exception:
            self.btn_entregar = None
        try:
            self.btn_finalizar = ctk.CTkButton(self.frame_det, text="Finalizar Pedido", fg_color="#27AE60", state="disabled")
        except Exception:
            self.btn_finalizar = None

    def crear_dato(self, titulo):
        f = ctk.CTkFrame(self.info_container, fg_color="transparent")
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=titulo, font=("Arial", 11, "bold"), width=90, anchor="w").pack(side="left")
        l = ctk.CTkLabel(f, text="---", font=("Arial", 11))
        l.pack(side="left")
        return l

    def crear_total(self, titulo, color=None):
        f = ctk.CTkFrame(self.frame_det, fg_color="transparent")
        f.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(f, text=titulo, font=("Segoe UI", 12, "bold")).pack(side="left")
        l = ctk.CTkLabel(f, text="0 Gs.", text_color=color, font=("Segoe UI", 14, "bold"))
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
            # Normalizar estado para comparaciones
            estado_text = (d.get("estado") or "")
            estado_norm = normalize_estado(estado_text)

            if (filtro == "Todos" or estado_norm == filtro) and \
               (busq in cliente_text or busq in ot_text or busq in descripcion_text):
                # Preferir el campo 'abonado_total' (nuevo esquema). Fallback: 'sena' o suma de pagos
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
                tag = estado_norm.lower().replace(' ', '_')
                monto_str = _format_gs(d.get('monto', 0))
                abono_str = _format_gs(abono)
                # Insert normalized estado text in last column
                self.tabla.insert("", "end", values=(d.get("ot"), d.get("fecha"), d.get("cliente"), d.get("descripcion"), monto_str, abono_str, d.get("pago"), estado_norm), tags=(tag,))

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

    def _on_search_change(self, _event=None):
        if getattr(self, '_search_after_id', None):
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(120, self.actualizar_tabla)

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
        self.lbl_ot_chip.configure(text=f"OT {d['ot']}")
        vendedor_txt = d['vendedor'] or self.vendedor_nombre
        self.lbl_vendedor.configure(text=vendedor_txt)
        self.lbl_cliente.configure(text=d['cliente'])
        self.lbl_desc.configure(text=d['descripcion'])
        self.lbl_pago.configure(text=d['pago'])

        # Estado (chip)
        estado_actual = normalize_estado(d.get('estado')) if isinstance(d.get('estado'), str) else 'Pendiente'
        self.lbl_estado_chip.configure(text=estado_actual)
        # Colores por estado (vendedor) - tonos más suaves
        if estado_actual == 'Aprobado':
            estado_color = "#C8E6C9"  # verde claro (vendedor)
        elif estado_actual == 'Rechazado':
            estado_color = "#FADBD8"  # rojo claro (vendedor)
        elif estado_actual == 'Pendiente':
            estado_color = "#FFF4CC"  # amarillo claro (vendedor)
        elif estado_actual == 'Entregado':
            estado_color = "#D6F5F0"  # entregado (tono suave)
        elif estado_actual == 'Finalizado':
            estado_color = "#EADBF7"  # finalizado (morado claro para vendedor)
        else:
            estado_color = "#BDC3C7"
        self.lbl_estado_chip.configure(fg_color=estado_color, text_color="#1F2937")

        # --- Actualizar Campo de Envío ---
        self.lbl_envio.configure(text=d['envio'])
        if "Con Envío" in d['envio']:
            self.lbl_envio.configure(text_color="#27AE60")
        else:
            self.lbl_envio.configure(text_color="#2980B9")

        # Totales: preferir campo 'abonado_total' (nuevo esquema). Fallback: 'sena' o suma de pagos
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

        total_val = d.get('monto', 0)
        self.lbl_total.configure(text=_format_gs(total_val))
        self.lbl_abonado.configure(text=_format_gs(abono))
        self.lbl_saldo.configure(text=_format_gs(total_val - abono))

    def _load_ots_async(self):
        self._set_loading_state(True)
        threading.Thread(target=self._fetch_ots_background, daemon=True).start()

    def _fetch_ots_background(self):
        if not get_work_orders_by_vendedor or not self.vendedor:
            self.after(0, lambda: self._apply_ots_result(True, []))
            return
        try:
            ok, data = get_work_orders_by_vendedor(self.vendedor)
        except Exception as exc:
            ok, data = False, f"Error inesperado: {exc}"
        mapped = self._map_rows(data) if ok and isinstance(data, list) else data
        self.after(0, lambda: self._apply_ots_result(ok, mapped))

    def _map_rows(self, rows):
        mapped = []
        for row in rows:
            try:
                ot_nro = row.get('ot_nro')
                fecha = row.get('fecha_creacion')
                fecha_str = fecha if isinstance(fecha, str) else (fecha.strftime('%d/%m/%Y') if fecha else '')
                cliente = row.get('cliente') or row.get('cliente_ci_ruc') or ''
                descripcion = row.get('descripcion') or ''
                monto = row.get('valor_total') or 0
                forma_pago = row.get('forma_pago') or ''
                estado = normalize_estado(row.get('status'))
                envio = 'Con Envío' if row.get('solicita_envio') else 'Sin Envío (Retira)'
                vendedor_txt = (
                    row.get('vendedor_nombre')
                    or row.get('vendedor_name')
                    or row.get('vendedor')
                    or row.get('vendedor_ci_ruc')
                    or row.get('ci_ruc_vendedor')
                    or self.vendedor_nombre
                    or ''
                )
                pagos = row.get('pagos') or []
                sena = row.get('sena', 0) or 0
                abonado_total = row.get('abonado_total', 0) or 0
                mapped.append({
                    'ot': str(ot_nro), 'fecha': fecha_str, 'vendedor': vendedor_txt,
                    'cliente': cliente, 'descripcion': descripcion, 'monto': float(monto) if monto is not None else 0,
                    'pagos': pagos, 'pago': forma_pago, 'estado': estado, 'envio': envio, 'sena': sena, 'abonado_total': abonado_total
                })
            except Exception:
                continue
        try:
            return sorted(mapped, key=lambda x: int(x['ot']) if str(x.get('ot')).isdigit() else 0, reverse=True)
        except Exception:
            return mapped

    def _apply_ots_result(self, ok, payload):
        self._set_loading_state(False)
        if not ok:
            messagebox.showwarning("Advertencia", f"No se pudo cargar OTs: {payload}")
            return
        self.datos_ots = payload or []
        self.actualizar_tabla()

    def _set_loading_state(self, is_loading: bool):
        btn = getattr(self, 'btn_actualizar', None)
        if not btn:
            return
        try:
            btn.configure(state="disabled" if is_loading else "normal")
            btn.configure(text="Actualizando..." if is_loading else "Actualizar")
        except Exception:
            pass

    def abrir_ventana_pago(self):
        # Vendedores no pueden abrir modal de pago
        return

    def registrar_abono_final(self, m):
        # No permitido para vendedor
        return

    def cambiar_estado(self, nuevo_estado):
        if self.ot_seleccionada:
            # Intentar persistir el cambio en la base de datos si el servicio está disponible
            ot_id = self.ot_seleccionada.get('ot')
            # Try to convert to int when possible (DB probably stores numeric ot_nro)
            try:
                ot_key = int(ot_id)
            except Exception:
                ot_key = ot_id

            if update_work_order_status:
                try:
                    estado_db = str(nuevo_estado).strip().title()
                except Exception:
                    estado_db = nuevo_estado
                ok, msg = update_work_order_status(ot_key, estado_db)
                if not ok:
                    messagebox.showerror("Error al actualizar", f"No se pudo actualizar el estado en la base de datos: {msg}")
                    return
            # Actualizar en memoria y UI
            self.ot_seleccionada['estado'] = normalize_estado(estado_db if 'estado_db' in locals() else nuevo_estado)
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
