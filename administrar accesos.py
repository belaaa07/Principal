import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

# --- CONFIGURACIÓN GLOBAL ---
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class ModuloAccesos(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Plot Master App - Administración de Accesos")
        self.geometry("1450x800")
        self.configure(fg_color="#F5F5F5")

        # DATOS DE PRUEBA (Incluyendo RUC)
        self.usuarios = [
            {"id": "001", "ruc": "4521369-0", "nombre": "Marcos Galeano", "usuario": "marcos_admin", "email": "marcos@plotmaster.com", "agregado": "10/12/2025", "pass": "1234"},
            {"id": "002", "ruc": "1234567-8", "nombre": "Ana Rodríguez", "usuario": "ana_ventas", "email": "ana@plotmaster.com", "agregado": "15/12/2025", "pass": "5678"},
        ]

        self.usuario_seleccionado = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.crear_planilla_izquierda()
        self.crear_panel_control_derecho()

    def crear_planilla_izquierda(self):
        self.frame_izq = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#D0D0D0")
        self.frame_izq.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        header = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(header, text="🔐 ADMINISTRAR ACCESOS", font=("Arial", 22, "bold"), text_color="black").pack(side="left")
        
        self.entry_busqueda = ctk.CTkEntry(header, placeholder_text="🔍 Buscar usuario o RUC...", width=350, text_color="black")
        self.entry_busqueda.pack(side="right")
        self.entry_busqueda.bind("<KeyRelease>", self.actualizar_tabla)

        cont_tabla = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        cont_tabla.pack(expand=True, fill="both", padx=15, pady=5)

        # AGREGADA COLUMNA "RUC"
        columnas = ("id", "ruc", "nombre", "usuario", "email", "agregado")
        self.tabla = ttk.Treeview(cont_tabla, columns=columnas, show="headings")

        anchos = {"id": 60, "ruc": 120, "nombre": 220, "usuario": 130, "email": 220, "agregado": 110}
        for col in columnas:
            self.tabla.heading(col, text=col.upper())
            self.tabla.column(col, width=anchos[col], anchor="center")

        self.tabla.pack(side="left", expand=True, fill="both")
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_fila)
        
        self.actualizar_tabla()

    def crear_panel_control_derecho(self):
        self.frame_det = ctk.CTkFrame(self, width=320, border_width=1, border_color="#D0D0D0", fg_color="white")
        self.frame_det.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")

        ctk.CTkLabel(self.frame_det, text="GESTIÓN DE USUARIO", font=("Arial", 14, "bold"), text_color="black").pack(pady=20)

        self.lbl_info = ctk.CTkLabel(self.frame_det, text="Seleccione un usuario de la lista", font=("Arial", 11), text_color="gray", wraplength=250)
        self.lbl_info.pack(pady=10)

        ctk.CTkFrame(self.frame_det, height=2, fg_color="#EEEEEE").pack(fill="x", padx=20, pady=20)

        self.btn_editar = ctk.CTkButton(self.frame_det, text="✏️ Editar Datos", fg_color="#3498DB", text_color="white", command=self.abrir_ventana_editar, state="disabled")
        self.btn_editar.pack(pady=10, padx=30, fill="x")

        self.btn_pass = ctk.CTkButton(self.frame_det, text="🔑 Cambiar Contraseña", fg_color="#F39C12", text_color="white", command=self.abrir_ventana_password, state="disabled")
        self.btn_pass.pack(pady=10, padx=30, fill="x")

        self.btn_borrar = ctk.CTkButton(self.frame_det, text="🗑️ Borrar Usuario", fg_color="#E74C3C", text_color="white", command=self.borrar_usuario, state="disabled")
        self.btn_borrar.pack(pady=10, padx=30, fill="x")

    def actualizar_tabla(self, e=None):
        for i in self.tabla.get_children(): self.tabla.delete(i)
        busq = self.entry_busqueda.get().lower()
        for u in self.usuarios:
            if busq in u["nombre"].lower() or busq in u["usuario"].lower() or busq in u["ruc"]:
                # Se incluye el RUC en los valores de la fila
                self.tabla.insert("", "end", values=(u["id"], u["ruc"], u["nombre"], u["usuario"], u["email"], u["agregado"]))

    def al_seleccionar_fila(self, e):
        sel = self.tabla.selection()
        if not sel: return
        id_user = str(self.tabla.item(sel[0])['values'][0]).zfill(3)
        self.usuario_seleccionado = next(u for u in self.usuarios if u["id"] == id_user)
        self.lbl_info.configure(text=f"Usuario: {self.usuario_seleccionado['usuario']}\n{self.usuario_seleccionado['nombre']}", text_color="black")
        self.btn_editar.configure(state="normal")
        self.btn_pass.configure(state="normal")
        self.btn_borrar.configure(state="normal")

    def abrir_ventana_editar(self):
        u = self.usuario_seleccionado
        vent = ctk.CTkToplevel(self)
        vent.title("Editar Usuario")
        vent.geometry("350x420")
        vent.attributes("-topmost", True)
        vent.grab_set()

        ctk.CTkLabel(vent, text="Editar Información", font=("Arial", 14, "bold"), text_color="black").pack(pady=15)

        entry_ruc = self.crear_campo(vent, "CI / RUC:", u['ruc'])
        entry_nom = self.crear_campo(vent, "Nombre Completo:", u['nombre'])
        entry_mail = self.crear_campo(vent, "Email:", u['email'])

        def guardar():
            u.update({"ruc": entry_ruc.get(), "nombre": entry_nom.get(), "email": entry_mail.get()})
            self.actualizar_tabla()
            vent.destroy()
            messagebox.showinfo("Éxito", "Datos actualizados correctamente")

        ctk.CTkButton(vent, text="Guardar Cambios", command=guardar, fg_color="#27AE60").pack(pady=25)

    def abrir_ventana_password(self):
        u = self.usuario_seleccionado
        vent = ctk.CTkToplevel(self)
        vent.title("Cambiar Contraseña")
        vent.geometry("350x300")
        vent.attributes("-topmost", True)
        vent.grab_set()

        ctk.CTkLabel(vent, text=f"Seguridad: {u['usuario']}", font=("Arial", 14, "bold"), text_color="black").pack(pady=15)

        ctk.CTkLabel(vent, text="Nueva Contraseña:", text_color="black").pack()
        e1 = ctk.CTkEntry(vent, width=220, show="*")
        e1.pack(pady=5)

        ctk.CTkLabel(vent, text="Reconfirmar Contraseña:", text_color="black").pack()
        e2 = ctk.CTkEntry(vent, width=220, show="*")
        e2.pack(pady=5)

        def validar():
            p1, p2 = e1.get(), e2.get()
            if not p1:
                messagebox.showwarning("Atención", "La contraseña no puede estar vacía.")
            elif p1 == p2:
                u['pass'] = p1
                messagebox.showinfo("Éxito", "Contraseña cambiada correctamente.")
                vent.destroy()
            else:
                messagebox.showerror("Error", "Las contraseñas no coinciden.")

        ctk.CTkButton(vent, text="Actualizar Contraseña", command=validar, fg_color="#F39C12").pack(pady=20)

    def crear_campo(self, parent, label, valor):
        ctk.CTkLabel(parent, text=label, text_color="black").pack(pady=(5, 0))
        entry = ctk.CTkEntry(parent, width=250, text_color="black")
        entry.insert(0, valor)
        entry.pack(pady=5)
        return entry

    def borrar_usuario(self):
        u = self.usuario_seleccionado
        if messagebox.askyesno("Confirmar", f"¿Desea eliminar definitivamente a {u['usuario']}?"):
            self.usuarios.remove(u)
            self.actualizar_tabla()
            messagebox.showinfo("Eliminado", "Usuario borrado del sistema.")

if __name__ == "__main__":
    app = ModuloAccesos()
    app.mainloop()