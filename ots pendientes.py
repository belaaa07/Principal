import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# --- 1. MODELO DE DATOS: CLASE OT ---

class OT:
    """Define la estructura de una Orden de Trabajo."""
    def __init__(self, ot_nro, vendedor, ci_ruc, nombre_cliente, valor_total, sena, forma_pago, envio, fecha=None):
        self.ot_nro = ot_nro
        self.vendedor = vendedor
        self.ci_ruc = ci_ruc
        self.nombre_cliente = nombre_cliente
        self.valor_total = float(valor_total)  
        self.sena = float(sena)                
        self.forma_pago = forma_pago
        self.envio = envio
        self.estado = "Pendiente" # Estados: Pendiente, Aprobada, Rechazada
        self.fecha = fecha if fecha else datetime.now().strftime("%d/%m/%Y")

    @property
    def saldo(self):
        """Calcula el saldo automáticamente."""
        return self.valor_total - self.sena

# --- 2. MÓDULO PRINCIPAL: INTERFAZ Y LÓGICA ---

class ModuloOTsPendientes(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        
        style = ttk.Style()
        style.theme_use('clam') # Estética moderna
        
        self.title("OTs Pendientes de Aprobación")
        self.geometry("1000x600") 
        
        self.ots = self._cargar_datos_simulados()
        
        # 🟢 CONTROL DE VENTANA: Almacena la instancia de la ventana de detalle si está abierta
        self.ventana_detalle_abierta = None 

        self._crear_widgets()
        self._actualizar_vista()
        
    def _cargar_datos_simulados(self):
        """Carga algunas OTs de ejemplo para la demostración."""
        return [
            OT(1001, "Carlos S.", "123456", "Luana M.", 1500000.0, 500000.0, "Contado", "No Solicita Envío", fecha="15/12/2025"),
            OT(1002, "Ana G.", "789012", "Javier R.", 950000.0, 0.0, "Crédito", "Envío a Ciudad X", fecha="16/12/2025"),
            OT(1003, "Carlos S.", "345678", "Sofía P.", 3200000.0, 1000000.0, "Contado", "Envío a Ciudad Y", fecha="16/12/2025"),
        ]

    def _formatear_moneda(self, valor):
        """Formatea un float a string de moneda Gs con separador de miles."""
        return f"Gs {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _crear_widgets(self):
        """Configura la estructura principal: Buscador y Tabla."""
        
        frame_superior = ttk.Frame(self)
        frame_superior.pack(fill='x', padx=15, pady=15)
        
        ttk.Label(frame_superior, text="Órdenes de Trabajo Pendientes", font=('Arial', 14, 'bold')).pack(side='left')

        # Buscador
        frame_buscador = ttk.Frame(frame_superior)
        frame_buscador.pack(side='right', fill='x')
        
        ttk.Label(frame_buscador, text="🔍").pack(side='left', padx=(0, 5))
        self.var_busqueda = tk.StringVar()
        entry_busqueda = ttk.Entry(frame_buscador, textvariable=self.var_busqueda, width=30)
        entry_busqueda.pack(side='left')
        entry_busqueda.bind("<KeyRelease>", self._filtrar_ots)


        # Frame de la Tabla
        frame_tabla = ttk.Frame(self)
        frame_tabla.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Treeview (Tabla)
        self.tree = ttk.Treeview(frame_tabla, 
                                 columns=("nro", "fecha", "vendedor", "monto", "abonado", "estado"), 
                                 show='headings')
        
        # Configuración de columnas
        self.tree.heading("nro", text="OT Nro", anchor=tk.W)
        self.tree.heading("fecha", text="Fecha", anchor=tk.W) 
        self.tree.heading("vendedor", text="Vendedor", anchor=tk.W)
        self.tree.heading("monto", text="Monto (Gs)", anchor=tk.E)
        self.tree.heading("abonado", text="Abonado (Gs)", anchor=tk.E)
        self.tree.heading("estado", text="Estado", anchor=tk.CENTER)
        
        self.tree.column("nro", width=80, anchor=tk.W, stretch=False)
        self.tree.column("fecha", width=100, anchor=tk.W, stretch=False)
        self.tree.column("vendedor", width=150, anchor=tk.W, stretch=False)
        self.tree.column("monto", width=150, anchor=tk.E)
        self.tree.column("abonado", width=150, anchor=tk.E)
        self.tree.column("estado", width=120, anchor=tk.CENTER, stretch=False)

        # Usamos <<TreeviewSelect>> (un solo clic es suficiente)
        self.tree.bind("<<TreeviewSelect>>", self._mostrar_detalle_ot)
        
        self.tree.pack(fill='both', expand=True)

    def _get_ots_pendientes_filtradas(self, search_criteria=""):
        """Retorna OTs que son 'Pendiente' y coinciden con el criterio de búsqueda."""
        
        pendientes = [ot for ot in self.ots if ot.estado == "Pendiente"]
        
        if not search_criteria:
            return pendientes
        else:
            try:
                # Filtra por Nro OT que comience con el criterio
                return [ot for ot in pendientes if str(ot.ot_nro).startswith(search_criteria)]
            except ValueError:
                return pendientes

    def _cargar_ots_en_tabla(self, ots_a_mostrar):
        """Limpia la tabla y carga las OTs proporcionadas (solo Pendientes y filtradas)."""
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for ot in ots_a_mostrar:
            
            monto_fmt = self._formatear_moneda(ot.valor_total)
            abonado_fmt = self._formatear_moneda(ot.sena)
            
            self.tree.insert("", tk.END, iid=ot.ot_nro,
                             values=(
                                ot.ot_nro, 
                                ot.fecha,
                                ot.vendedor, 
                                monto_fmt, 
                                abonado_fmt, 
                                ot.estado,
                             ))


    def _actualizar_vista(self):
        """Refresca la tabla basándose en el criterio de búsqueda y solo muestra 'Pendiente'."""
        criterio = self.var_busqueda.get().strip()
        ots_a_mostrar = self._get_ots_pendientes_filtradas(criterio)
        self._cargar_ots_en_tabla(ots_a_mostrar)

    def _filtrar_ots(self, event):
        """Llamado al escribir en el buscador."""
        self._actualizar_vista()

    def _mostrar_detalle_ot(self, event):
        """
        Maneja la selección en la tabla para mostrar el detalle.
        🟢 IMPLEMENTA CONTROL DE INSTANCIA ÚNICA.
        """
        selected_items = self.tree.selection()
        if not selected_items:
            return 
        
        ot_nro = int(selected_items[0])
        ot_seleccionada = next((ot for ot in self.ots if ot.ot_nro == ot_nro), None)
        
        if not ot_seleccionada:
            return

        # 🟢 Lógica de control de instancia:
        if self.ventana_detalle_abierta and self.ventana_detalle_abierta.winfo_exists():
            # Si ya hay una ventana abierta, la enfocamos en lugar de crear una nueva
            self.ventana_detalle_abierta.lift()
            self.ventana_detalle_abierta.focus_set()
            return
        
        # Si no hay ventana abierta, creamos una nueva y guardamos la instancia
        self.ventana_detalle_abierta = DetalleOT(self, ot_seleccionada, self._recargar_tabla)
        # Configurar el protocolo de cierre para limpiar el atributo cuando se cierre
        self.ventana_detalle_abierta.protocol("WM_DELETE_WINDOW", self._cerrar_detalle_ot)
        
    def _cerrar_detalle_ot(self):
        """Limpia la referencia a la ventana de detalle cuando se cierra."""
        if self.ventana_detalle_abierta:
            self.ventana_detalle_abierta.destroy()
            self.ventana_detalle_abierta = None # 🟢 Esto permite que se pueda abrir otra vez

    def _aprobar_rechazar_ot(self, ot, nuevo_estado):
        """Aplica la lógica de aprobación o rechazo."""
        
        # 🟢 Aseguramos que si se aprueba/rechaza, la ventana se cierre primero 
        # para evitar inconsistencias con el objeto OT.
        if self.ventana_detalle_abierta and self.ventana_detalle_abierta.ot == ot:
            self._cerrar_detalle_ot()

        if nuevo_estado == "Rechazada":
            try:
                self.ots.remove(ot)
                messagebox.showinfo("Acción Exitosa", f"OT Nro {ot.ot_nro} ha sido rechazada y eliminada del sistema.")
            except ValueError:
                messagebox.showerror("Error", f"OT Nro {ot.ot_nro} no encontrada para eliminar.")
                return
        
        elif nuevo_estado == "Aprobada":
            ot.estado = nuevo_estado
            messagebox.showinfo("Acción Exitosa", f"OT Nro {ot.ot_nro} ha sido aprobada. Se mueve a la planilla de OTs Aprobadas.")
        
        self._actualizar_vista()

    def _recargar_tabla(self):
        """Método de callback para recargar la tabla después de editar o aprobar/rechazar."""
        self._actualizar_vista()

# --- 3. VISTA DE DETALLE/EDICIÓN ---
class DetalleOT(tk.Toplevel):
    def __init__(self, master, ot, callback_recarga):
        super().__init__(master)
        self.title(f"Detalle OT Nro {ot.ot_nro}")
        self.ot = ot
        self.callback_recarga = callback_recarga
        self.resizable(False, False)
        
        self._es_editable = False 

        self._crear_widgets_detalle()
        self._llenar_campos()
        
    def _crear_label_campo(self, parent, label_text, value, row, col):
        """Helper para crear labels no editables."""
        ttk.Label(parent, text=label_text, font=('Arial', 9)).grid(row=row, column=col, sticky='w', padx=5, pady=2)
        lbl_value = ttk.Label(parent, text=value, font=('Arial', 9, 'bold'))
        lbl_value.grid(row=row, column=col + 1, sticky='ew', padx=5, pady=2)
        return lbl_value

    def _formatear_moneda(self, valor):
        """Formatea un float a string de moneda Gs con separador de miles."""
        return f"Gs {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
    def _crear_widgets_detalle(self):
        """Crea el layout del detalle y los campos."""
        
        frame_principal = ttk.Frame(self, padding="15")
        frame_principal.pack(fill="both", expand=True)

        self.var_valor_total = tk.DoubleVar()
        self.var_sena = tk.DoubleVar()
        self.var_saldo = tk.StringVar() 

        # --- SECCIÓN DE IDENTIFICACIÓN Y CLIENTE ---
        ttk.Label(frame_principal, text=f"ORDEN DE TRABAJO NRO. {self.ot.ot_nro}", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky='w')
        
        self._crear_label_campo(frame_principal, "Fecha:", self.ot.fecha, row=1, col=0)
        self._crear_label_campo(frame_principal, "Vendedor:", self.ot.vendedor, row=2, col=0)
        
        ttk.Separator(frame_principal, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)
        
        self._crear_label_campo(frame_principal, "CI/RUC:", self.ot.ci_ruc, row=4, col=0)
        self._crear_label_campo(frame_principal, "Nombre Cliente:", self.ot.nombre_cliente, row=5, col=0)

        # --- SECCIÓN DE VALORES (EDITABLES) ---
        ttk.Label(frame_principal, text="VALORES", font=('Arial', 10, 'bold')).grid(row=6, column=0, columnspan=2, pady=(10, 5), sticky='w')
        
        ttk.Label(frame_principal, text="Valor Total (Gs):").grid(row=7, column=0, sticky='w', padx=5, pady=2)
        self.entry_valor_total = ttk.Entry(frame_principal, textvariable=self.var_valor_total, state='readonly', justify=tk.RIGHT)
        self.entry_valor_total.grid(row=7, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(frame_principal, text="Seña (Anticipo) (Gs):").grid(row=8, column=0, sticky='w', padx=5, pady=2)
        self.entry_sena = ttk.Entry(frame_principal, textvariable=self.var_sena, state='readonly', justify=tk.RIGHT)
        self.entry_sena.grid(row=8, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(frame_principal, text="Saldo (Gs):", font=('Arial', 10, 'bold')).grid(row=9, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(frame_principal, textvariable=self.var_saldo, font=('Arial', 10, 'bold'), anchor=tk.E).grid(row=9, column=1, sticky='ew', padx=5, pady=2)
        
        self.var_valor_total.trace_add("write", lambda *args: self._recalcular_saldo())
        self.var_sena.trace_add("write", lambda *args: self._recalcular_saldo())
        
        # --- SECCIÓN DETALLES ---
        ttk.Label(frame_principal, text="DETALLES", font=('Arial', 10, 'bold')).grid(row=10, column=0, columnspan=2, pady=(10, 5), sticky='w')
        
        self._crear_label_campo(frame_principal, "Forma de Pago:", self.ot.forma_pago, row=11, col=0)
        self._crear_label_campo(frame_principal, "Envío:", self.ot.envio, row=12, col=0)

        # --- BOTONES DE ACCIÓN ---
        frame_botones = ttk.Frame(frame_principal)
        frame_botones.grid(row=13, column=0, columnspan=2, pady=20)
        
        self.btn_editar = ttk.Button(frame_botones, text="✏️ Editar Valores", command=self._toggle_edicion)
        self.btn_editar.pack(side='left', padx=5)
        
        self.btn_guardar = ttk.Button(frame_botones, text="💾 Guardar Cambios", command=self._guardar_cambios, state='disabled')
        self.btn_guardar.pack(side='left', padx=5)
        
        if self.ot.estado == "Pendiente":
            ttk.Button(frame_botones, text="✅ APROBAR OT", command=lambda: self._aprobar_rechazar("Aprobada"), style='Accent.TButton').pack(side='left', padx=(20, 5))
            ttk.Button(frame_botones, text="❌ RECHAZAR OT", command=lambda: self._aprobar_rechazar("Rechazada")).pack(side='left', padx=5)


    def _llenar_campos(self):
        """Carga los valores de la OT en los campos de entrada."""
        self.var_valor_total.set(self.ot.valor_total)
        self.var_sena.set(self.ot.sena)

    def _recalcular_saldo(self):
        """Actualiza el saldo al cambiar Valor Total o Seña."""
        if not self._es_editable:
            total = self.ot.valor_total
            sena = self.ot.sena
        else:
            try:
                total = float(self.entry_valor_total.get() or 0)
                sena = float(self.entry_sena.get() or 0)
            except ValueError:
                self.var_saldo.set("Error de formato")
                return

        saldo = total - sena
        self.var_saldo.set(self._formatear_moneda(saldo))


    def _toggle_edicion(self):
        """Permite a la administración editar los campos de valores."""
        self._es_editable = not self._es_editable
        
        if self._es_editable:
            self.entry_valor_total.config(state='normal')
            self.entry_sena.config(state='normal')
            self.btn_editar.config(text="↩️ Cancelar Edición")
            self.btn_guardar.config(state='normal')
            self.entry_valor_total.focus_set() 
        else:
            self.entry_valor_total.config(state='readonly')
            self.entry_sena.config(state='readonly')
            self.btn_editar.config(text="✏️ Editar Valores")
            self.btn_guardar.config(state='disabled')
            self._llenar_campos() 
            self._recalcular_saldo() 

    def _guardar_cambios(self):
        """Guarda los valores editados y actualiza la OT."""
        try:
            nuevo_total = float(self.entry_valor_total.get())
            nueva_sena = float(self.entry_sena.get())
            
            self.ot.valor_total = nuevo_total
            self.ot.sena = nueva_sena
            
            self._toggle_edicion()
            messagebox.showinfo("Guardado", f"Valores de OT {self.ot.ot_nro} actualizados.")
            
            self.callback_recarga()
            
        except ValueError:
            messagebox.showerror("Error de Entrada", "Por favor, ingrese valores numéricos válidos (solo números) en Valor Total y Seña.")

    def _aprobar_rechazar(self, nuevo_estado):
        """Aplica la lógica de aprobación o rechazo y cierra la ventana."""
        # En lugar de solo self.destroy(), llamamos al método del master que también limpia la referencia
        self.master._aprobar_rechazar_ot(self.ot, nuevo_estado)


# --- 4. INICIO DE LA APLICACIÓN ---

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Programa Principal")
    
    # Estilo del botón APROBAR
    style = ttk.Style()
    style.configure('Accent.TButton', foreground='white', background='#28a745', font=('Arial', 10, 'bold'))
    style.map('Accent.TButton', background=[('active', '#218838')])


    root.withdraw() 

    app = ModuloOTsPendientes(root)
    
    root.protocol("WM_DELETE_WINDOW", root.destroy) 
    app.protocol("WM_DELETE_WINDOW", root.destroy)

    root.mainloop()