import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from services import supabase_service as svc

# --- CONFIGURACIÓN GLOBAL ---
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class ModuloAccesos(ctk.CTkFrame):
    """Módulo de administración de accesos (gestión de clientes desde la tabla clientes)."""
    def __init__(self, parent):
        super().__init__(parent, fg_color="white")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.usuario_seleccionado = None

        self.crear_planilla_izquierda()
        self.crear_panel_control_derecho()

        # Cargar datos desde Supabase (usuarios)
        self.cargar_usuarios()

    def crear_planilla_izquierda(self):
        self.frame_izq = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#D0D0D0")
        self.frame_izq.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        header = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(header, text="🔐 ADMINISTRAR ACCESOS", font=("Arial", 18, "bold"), text_color="black").pack(side="left")

        self.entry_busqueda = ctk.CTkEntry(header, placeholder_text="🔍 Buscar nombre o CI/RUC...", width=350, text_color="black")
        self.entry_busqueda.pack(side="right")
        self.entry_busqueda.bind("<KeyRelease>", self.actualizar_tabla_local)

        cont_tabla = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        cont_tabla.pack(expand=True, fill="both", padx=15, pady=5)

        columnas = ("id", "fecha_registro", "nombre", "ci_ruc", "telefono", "email", "zona")
        self.tabla = ttk.Treeview(cont_tabla, columns=columnas, show="headings")

        anchos = {"id": 60, "fecha_registro": 140, "nombre": 220, "ci_ruc": 120, "telefono": 110, "email": 180, "zona": 100}
        for col in columnas:
            # Mostrar etiqueta legible para la columna de fecha
            if col == 'fecha_registro':
                self.tabla.heading(col, text="Fecha-Registro")
            else:
                self.tabla.heading(col, text=col.upper())
            self.tabla.column(col, width=anchos.get(col, 100), anchor="center")

        vsb = ttk.Scrollbar(cont_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tabla.pack(side="left", expand=True, fill="both")
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_fila)
        # Asegurar que click del ratón también active la selección en entornos donde el evento virtual no se dispare
        self.tabla.bind("<ButtonRelease-1>", self.al_seleccionar_fila)
        # Doble click abre edición rápida
        self.tabla.bind("<Double-1>", lambda e: self.abrir_ventana_editar())

    def crear_panel_control_derecho(self):
        self.frame_det = ctk.CTkFrame(self, width=320, border_width=1, border_color="#D0D0D0", fg_color="white")
        self.frame_det.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")

        ctk.CTkLabel(self.frame_det, text="GESTIÓN DE USUARIOS", font=("Arial", 14, "bold"), text_color="black").pack(pady=20)

        self.lbl_info = ctk.CTkLabel(self.frame_det, text="Seleccione un usuario de la lista", font=("Arial", 11), text_color="gray", wraplength=250)
        self.lbl_info.pack(pady=10)

        ctk.CTkFrame(self.frame_det, height=2, fg_color="#EEEEEE").pack(fill="x", padx=20, pady=20)

        self.btn_editar = ctk.CTkButton(self.frame_det, text="✏️ Editar Datos", fg_color="#3498DB", text_color="white", command=self.abrir_ventana_editar, state="disabled")
        self.btn_editar.pack(pady=10, padx=30, fill="x")

        self.btn_borrar = ctk.CTkButton(self.frame_det, text="🗑️ Borrar Usuario", fg_color="#E74C3C", text_color="white", command=self.borrar_usuario, state="disabled")
        self.btn_borrar.pack(pady=10, padx=30, fill="x")

        self.btn_refresh = ctk.CTkButton(self.frame_det, text="🔄 Refrescar", fg_color="#7F8C8D", text_color="white", command=self.cargar_usuarios)
        self.btn_refresh.pack(pady=12, padx=30, fill="x")

    def cargar_usuarios(self):
        ok, data = svc.get_all_users()
        self.usuarios = data if ok else []
        if not ok:
            messagebox.showerror("Error", f"No fue posible obtener usuarios: {data}")
        self.actualizar_tabla_local()

    def actualizar_tabla_local(self, e=None):
        for i in self.tabla.get_children():
            self.tabla.delete(i)
        busq = self.entry_busqueda.get().lower() if hasattr(self, 'entry_busqueda') else ""
        for u in (self.usuarios or []):
            nombre = (u.get('nombre') or "").lower()
            ci_ruc = (u.get('ci_ruc') or "").lower()
            if busq in nombre or busq in ci_ruc:
                created = u.get('fecha_registro') or u.get('created_at') or u.get('created') or ""
                if created:
                    try:
                        # Presentar fecha legible si es ISO
                        created = created.replace('T', ' ')[:19]
                    except Exception:
                        pass
                self.tabla.insert("", "end", values=(u.get('id'), created, u.get('nombre'), u.get('ci_ruc'), u.get('telefono'), u.get('email'), u.get('zona')))

    def al_seleccionar_fila(self, e):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0])['values']
        # defensivo: convertir a str y strip
        try:
            ci_ruc = str(vals[3]).strip()
        except Exception:
            ci_ruc = ''
        # Buscar en la lista cargada
        self.usuario_seleccionado = next((c for c in (self.usuarios or []) if str(c.get('ci_ruc') or '').strip() == ci_ruc), None)
        if not self.usuario_seleccionado:
            # intentar por id
            try:
                vid = str(vals[0]).strip()
                self.usuario_seleccionado = next((c for c in (self.usuarios or []) if str(c.get('id') or '') == vid), None)
            except Exception:
                self.usuario_seleccionado = None
        if not self.usuario_seleccionado:
            # intentar por nombre
            try:
                vname = str(vals[2]).strip().lower()
                self.usuario_seleccionado = next((c for c in (self.usuarios or []) if (c.get('nombre') or '').strip().lower() == vname), None)
            except Exception:
                self.usuario_seleccionado = None
        if not self.usuario_seleccionado:
            print(f"Usuario no encontrado para fila: {vals}")
            return
        if self.usuario_seleccionado:
            self.lbl_info.configure(text=f"{self.usuario_seleccionado.get('nombre')}\nCI/RUC: {self.usuario_seleccionado.get('ci_ruc')}", text_color="black")
            self.btn_editar.configure(state="normal")
            self.btn_borrar.configure(state="normal")

    def abrir_ventana_editar(self):
        u = self.usuario_seleccionado
        if not u:
            return
        vent = ctk.CTkToplevel(self)
        vent.title("Editar Usuario")
        vent.geometry("380x400")
        vent.attributes("-topmost", True)
        vent.grab_set()

        ctk.CTkLabel(vent, text="Editar Información", font=("Arial", 14, "bold"), text_color="black").pack(pady=15)

        entry_ci = self.crear_campo(vent, "CI / RUC:", u.get('ci_ruc'))
        entry_nom = self.crear_campo(vent, "Nombre Completo:", u.get('nombre'))
        # Editable fields limited to CI/RUC, Nombre y Email
        entry_mail = self.crear_campo(vent, "Email:", u.get('email') or "")

        def guardar():
            new_ci = entry_ci.get().strip()
            updates = {
                'nombre': entry_nom.get().strip(),
                'email': entry_mail.get().strip(),
            }
            # Si se cambió la CI/RUC, incluirlo en el mismo payload para evitar múltiples llamadas
            if new_ci and new_ci != (u.get('ci_ruc') or '').strip():
                updates['ci_ruc'] = new_ci

            # Intentar actualizar el registro identificado por id (más fiable) si está disponible
            if u.get('id'):
                ok, msg = svc.update_user_by_id(u.get('id'), updates)
            else:
                ok, msg = svc.update_user(u.get('ci_ruc'), updates)
            if ok:
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente.")
                vent.destroy()
                self.cargar_usuarios()
            else:
                messagebox.showerror("Error", f"No se pudo actualizar: {msg}")

        ctk.CTkButton(vent, text="Guardar Cambios", command=guardar, fg_color="#27AE60").pack(pady=20)

    def crear_campo(self, parent, label, valor):
        ctk.CTkLabel(parent, text=label, text_color="black").pack(pady=(5, 0))
        entry = ctk.CTkEntry(parent, width=300, text_color="black")
        entry.insert(0, valor or "")
        entry.pack(pady=5)
        return entry

    def borrar_usuario(self):
        u = self.usuario_seleccionado
        if not u:
            return
        if messagebox.askyesno("Confirmar", f"¿Desea eliminar definitivamente a {u.get('nombre')} (CI/RUC: {u.get('ci_ruc')})?"):
            ok, msg = svc.delete_user(u.get('ci_ruc'))
            if ok:
                messagebox.showinfo("Eliminado", "Usuario borrado del sistema.")
                self.cargar_usuarios()
            else:
                messagebox.showerror("Error", f"No se pudo eliminar: {msg}")


if __name__ == "__main__":
    # ejecución rápida de prueba
    root = ctk.CTk()
    root.geometry("1100x700")
    frame = ModuloAccesos(root)
    frame.pack(expand=True, fill='both')
    root.mainloop()