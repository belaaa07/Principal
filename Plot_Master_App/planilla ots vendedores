import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

# --- CONFIGURACIÓN DE APARIENCIA ---
ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("blue")

class VentanaAbono(ctk.CTkToplevel):
    """Ventana emergente para cargar un nuevo abono"""
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Registrar Abono")
        self.geometry("300x200")
        self.callback = callback
        
        # Hacer que la ventana aparezca al frente
        self.attributes("-topmost", True)
        self.grab_set()

        ctk.CTkLabel(self, text="Monto del Abono (Gs.):", font=("Arial", 12, "bold")).pack(pady=10)
        self.entry_monto = ctk.CTkEntry(self, placeholder_text="Ej: 50000")
        self.entry_monto.pack(pady=5)

        self.btn_guardar = ctk.CTkButton(self, text="Confirmar Pago", command=self.enviar_datos)
        self.btn_guardar.pack(pady=20)

    def enviar_datos(self):
        monto = self.entry_monto.get()
        if monto.isdigit():
            self.callback(int(monto))
            self.destroy()
        else:
            messagebox.showerror("Error", "Por favor, ingrese un monto válido (solo números).")

class ModuloOTs(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Plot Master App - Gestión de OTs")
        self.geometry("1300x750")

        # DATOS INICIALES (OTs desde 1000)
        self.datos_ots = [
            {
                "ot": "1000", "fecha": "15/12/2025", "vendedor": "Marcos", 
                "cliente": "Juan Pérez", "monto": 500000, 
                "pagos": [{"m": 100000, "f": "15/12"}], 
                "pago": "Crédito", "estado": "Aprobado"
            },
            {
                "ot": "1001", "fecha": "16/12/2025", "vendedor": "Ana", 
                "cliente": "Distribuidora Sol", "monto": 1200000, 
                "pagos": [{"m": 1200000, "f": "16/12"}], 
                "pago": "Contado", "estado": "Finalizado"
            }
        ]

        self.ot_seleccionada = None

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.crear_planilla_izquierda()
        self.crear_detalle_derecha()

    def crear_linea_divisoria(self, contenedor):
        linea = ctk.CTkFrame(contenedor, height=2, fg_color="#DDDDDD")
        linea.pack(fill="x", padx=15, pady=10)

    def crear_planilla_izquierda(self):
        frame_tabla = ctk.CTkFrame(self)
        frame_tabla.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        header = ctk.CTkFrame(frame_tabla, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(header, text="Planilla de OTs", font=("Arial", 24, "bold")).pack(side="left")
        
        self.filtro_var = ctk.StringVar(value="Todos")
        ctk.CTkComboBox(header, values=["Todos", "Pendiente", "Aprobado", "Finalizado"], 
                        variable=self.filtro_var, command=self.actualizar_tabla).pack(side="left", padx=20)

        self.entry_busqueda = ctk.CTkEntry(header, placeholder_text="🔍 Buscar cliente o OT...", width=250)
        self.entry_busqueda.pack(side="right", padx=10)
        self.entry_busqueda.bind("<KeyRelease>", self.actualizar_tabla)

        columnas = ("ot", "fecha", "cliente", "monto", "abonado", "pago", "estado")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        
        for col in columnas:
            self.tabla.heading(col, text=col.upper())
            self.tabla.column(col, anchor="center", width=110)

        self.tabla.pack(expand=True, fill="both", padx=10, pady=10)
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_fila)
        self.actualizar_tabla()

    def crear_detalle_derecha(self):
        self.frame_det = ctk.CTkFrame(self, width=450, border_width=2)
        self.frame_det.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_det, text="INFORMACIÓN DE LA OT", font=("Arial", 20, "bold")).pack(pady=15)

        # Contenedor de Información Completa
        self.info_container = ctk.CTkFrame(self.frame_det, fg_color="transparent")
        self.info_container.pack(fill="x", padx=20)

        self.lbl_ot_nro = self.crear_label_dato("OT Nro:")
        self.lbl_fecha_creacion = self.crear_label_dato("Fecha de Carga:")
        self.lbl_vendedor = self.crear_label_dato("Vendedor:")
        self.lbl_cliente = self.crear_label_dato("Cliente:")
        self.lbl_forma_pago = self.crear_label_dato("Forma de Pago:")

        self.crear_linea_divisoria(self.frame_det)

        # Registro de Abonos
        header_abonos = ctk.CTkFrame(self.frame_det, fg_color="transparent")
        header_abonos.pack(fill="x", padx=20)
        ctk.CTkLabel(header_abonos, text="HISTORIAL DE PAGOS", font=("Arial", 12, "bold")).pack(side="left")
        
        self.btn_add_pago = ctk.CTkButton(header_abonos, text="+ Abono", width=80, height=28, 
                                         fg_color="#3498DB", hover_color="#2980B9",
                                         command=self.abrir_ventana_pago)
        self.btn_add_pago.pack(side="right")

        self.container_pagos = ctk.CTkScrollableFrame(self.frame_det, height=180, fg_color="#F9F9F9")
        self.container_pagos.pack(fill="x", padx=15, pady=10)

        # Totales Finales
        self.lbl_total_general = self.crear_fila_valor("PRECIO TOTAL:")
        self.lbl_total_abonado = self.crear_fila_valor("TOTAL ABONADO:")
        self.lbl_saldo = self.crear_fila_valor("SALDO PENDIENTE:", color="#E74C3C")

        self.btn_finalizar = ctk.CTkButton(self.frame_det, text="FINALIZAR PEDIDO", 
                                          height=50, font=("Arial", 14, "bold"),
                                          command=self.accion_finalizar_pedido)
        self.btn_finalizar.pack(pady=25, padx=20, fill="x")

    def crear_label_dato(self, titulo):
        f = ctk.CTkFrame(self.info_container, fg_color="transparent")
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=titulo, font=("Arial", 11, "bold"), width=120, anchor="w").pack(side="left")
        lbl = ctk.CTkLabel(f, text="---", font=("Arial", 11))
        lbl.pack(side="left")
        return lbl

    def crear_fila_valor(self, titulo, color=None):
        f = ctk.CTkFrame(self.frame_det, fg_color="transparent")
        f.pack(fill="x", padx=25, pady=2)
        ctk.CTkLabel(f, text=titulo, font=("Arial", 12, "bold")).pack(side="left")
        lbl = ctk.CTkLabel(f, text="0 Gs.", text_color=color, font=("Arial", 14, "bold"))
        lbl.pack(side="right")
        return lbl

    def actualizar_tabla(self, event=None):
        for item in self.tabla.get_children(): self.tabla.delete(item)
        filtro = self.filtro_var.get()
        busqueda = self.entry_busqueda.get().lower()

        for ot in self.datos_ots:
            total_abono = sum(p['m'] for p in ot['pagos'])
            if (filtro == "Todos" or ot["estado"] == filtro) and (busqueda in ot["cliente"].lower() or busqueda in ot["ot"]):
                self.tabla.insert("", "end", values=(
                    ot["ot"], ot["fecha"], ot["cliente"], 
                    f"{ot['monto']:,} Gs.", f"{total_abono:,} Gs.", 
                    ot["pago"], ot["estado"]
                ))

    def al_seleccionar_fila(self, event):
        seleccion = self.tabla.selection()
        if not seleccion: return
        ot_id = str(self.tabla.item(seleccion[0])['values'][0])
        self.ot_seleccionada = next((x for x in self.datos_ots if x["ot"] == ot_id), None)
        self.refrescar_detalle()

    def refrescar_detalle(self):
        if not self.ot_seleccionada: return
        data = self.ot_seleccionada
        
        # Actualizar Info Completa
        self.lbl_ot_nro.configure(text=data['ot'])
        self.lbl_fecha_creacion.configure(text=data['fecha'])
        self.lbl_vendedor.configure(text=data['vendedor'])
        self.lbl_cliente.configure(text=data['cliente'])
        self.lbl_forma_pago.configure(text=data['pago'])

        # Cargar historial de pagos
        for w in self.container_pagos.winfo_children(): w.destroy()
        total_abono = 0
        for p in data['pagos']:
            total_abono += p['m']
            f = ctk.CTkFrame(self.container_pagos, fg_color="white", height=30)
            f.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(f, text=f"Fecha: {p['f']}", font=("Arial", 10)).pack(side="left", padx=10)
            ctk.CTkLabel(f, text=f"{p['m']:,} Gs.", font=("Arial", 10, "bold")).pack(side="right", padx=10)

        # Totales
        self.lbl_total_general.configure(text=f"{data['monto']:,} Gs.")
        self.lbl_total_abonado.configure(text=f"{total_abono:,} Gs.")
        self.lbl_saldo.configure(text=f"{data['monto'] - total_abono:,} Gs.")

        # Botón Finalizar
        if data['estado'] == "Aprobado":
            self.btn_finalizar.configure(state="normal", fg_color="#27AE60", text="FINALIZAR PEDIDO")
        elif data['estado'] == "Finalizado":
            self.btn_finalizar.configure(state="disabled", fg_color="#7F8C8D", text="PEDIDO FINALIZADO")
        else:
            self.btn_finalizar.configure(state="disabled", fg_color="gray", text="PENDIENTE DE APROBACIÓN")

    def abrir_ventana_pago(self):
        if self.ot_seleccionada:
            VentanaAbono(self, self.registrar_abono_final)
        else:
            messagebox.showwarning("Atención", "Seleccione una OT de la planilla primero.")

    def registrar_abono_final(self, monto):
        fecha_hoy = datetime.now().strftime("%d/%m/%y")
        self.ot_seleccionada['pagos'].append({"m": monto, "f": fecha_hoy})
        self.refrescar_detalle()
        self.actualizar_tabla()
        messagebox.showinfo("Éxito", "Abono registrado correctamente.")

    def accion_finalizar_pedido(self):
        if self.ot_seleccionada:
            self.ot_seleccionada['estado'] = "Finalizado"
            self.actualizar_tabla()
            self.refrescar_detalle()

if __name__ == "__main__":
    app = ModuloOTs()
    app.mainloop()