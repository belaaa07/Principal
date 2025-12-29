import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from plotmaster.core.services import supabase_service as svc

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
        # Doble click solo enfoca el formulario lateral (sin modales)
        self.tabla.bind("<Double-1>", lambda e: self._focus_form())

    def crear_panel_control_derecho(self):
        self.frame_det = ctk.CTkFrame(self, width=320, border_width=1, border_color="#D0D0D0", fg_color="white")
        self.frame_det.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")

        ctk.CTkLabel(self.frame_det, text="GESTIÓN DE USUARIOS", font=("Arial", 14, "bold"), text_color="black").pack(pady=(18, 8))

        self.lbl_info = ctk.CTkLabel(self.frame_det, text="Seleccione un usuario de la lista", font=("Arial", 11), text_color="gray", wraplength=250)
        self.lbl_info.pack(pady=(0, 6))

        form = ctk.CTkFrame(self.frame_det, fg_color="#F7F9FB", corner_radius=8)
        form.pack(fill="x", padx=16, pady=(6, 10))

        self.entry_ci = self._crear_input(form, "CI / RUC:")
        self.entry_nombre = self._crear_input(form, "Nombre Completo:")
        self.entry_email = self._crear_input(form, "Email:")
        self.entry_tel = self._crear_input(form, "Teléfono:")
        self.entry_zona = self._crear_input(form, "Zona / Ciudad:")

        self.btn_editar = ctk.CTkButton(self.frame_det, text="Guardar cambios", fg_color="#3498DB", text_color="white", command=self.guardar_usuario_lateral, state="disabled")
        self.btn_editar.pack(pady=8, padx=30, fill="x")

        self.btn_refresh = ctk.CTkButton(self.frame_det, text="🔄 Refrescar", fg_color="#7F8C8D", text_color="white", command=self.cargar_usuarios)
        self.btn_refresh.pack(pady=6, padx=30, fill="x")

        self.lbl_edit_status = ctk.CTkLabel(self.frame_det, text="", font=("Arial", 10), text_color="gray")
        self.lbl_edit_status.pack(pady=(4, 0))

        # Deshabilitar formulario hasta que haya selección
        self._set_form_state(False)

    def _crear_input(self, parent, label_text: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4, padx=10)
        ctk.CTkLabel(row, text=label_text, anchor="w", font=("Arial", 11, "bold"), text_color="black").pack(fill="x")
        entry = ctk.CTkEntry(row, width=240, text_color="black")
        entry.pack(fill="x", pady=(2, 0))
        return entry

    def _set_form_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for ent in (getattr(self, 'entry_ci', None), getattr(self, 'entry_nombre', None), getattr(self, 'entry_email', None), getattr(self, 'entry_tel', None), getattr(self, 'entry_zona', None)):
            if not ent:
                continue
            try:
                ent.configure(state=state)
                if not enabled:
                    ent.delete(0, 'end')
            except Exception:
                pass
        try:
            self.btn_editar.configure(state="normal" if enabled else "disabled")
        except Exception:
            pass

    def _focus_form(self):
        try:
            self.entry_nombre.focus_set()
        except Exception:
            pass

    def _llenar_form_usuario(self, usuario):
        self._set_form_state(True)
        campos = [
            (self.entry_ci, usuario.get('ci_ruc') or ''),
            (self.entry_nombre, usuario.get('nombre') or ''),
            (self.entry_email, usuario.get('email') or ''),
            (self.entry_tel, usuario.get('telefono') or ''),
            (self.entry_zona, usuario.get('zona') or ''),
        ]
        for entry, valor in campos:
            try:
                entry.delete(0, 'end')
                entry.insert(0, valor)
            except Exception:
                pass

    def cargar_usuarios(self):
        ok, data = svc.get_all_users()
        self.usuarios = data if ok else []
        if not ok:
            messagebox.showerror("Error", f"No fue posible obtener usuarios: {data}")
        # Resetear formulario y selección para evitar mostrar datos stale
        self.usuario_seleccionado = None
        self._set_form_state(False)
        self.lbl_info.configure(text="Seleccione un usuario de la lista", text_color="gray")
        try:
            self.lbl_edit_status.configure(text="")
        except Exception:
            pass
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
            self._llenar_form_usuario(self.usuario_seleccionado)
            self.lbl_edit_status.configure(text="Listo para editar", text_color="gray")

    def abrir_ventana_editar(self):
        # Compatibilidad: mantener método pero sin abrir modales
        self._focus_form()

    def guardar_usuario_lateral(self):
        u = self.usuario_seleccionado
        if not u:
            messagebox.showinfo("Seleccione usuario", "Elija un usuario en la tabla antes de guardar cambios.")
            return
        updates = {
            'nombre': self.entry_nombre.get().strip(),
            'email': self.entry_email.get().strip(),
            'telefono': self.entry_tel.get().strip(),
            'zona': self.entry_zona.get().strip(),
        }
        new_ci = self.entry_ci.get().strip()
        if new_ci and new_ci != (u.get('ci_ruc') or '').strip():
            updates['ci_ruc'] = new_ci

        if u.get('id'):
            ok, msg = svc.update_user_by_id(u.get('id'), updates)
        else:
            ok, msg = svc.update_user(u.get('ci_ruc'), updates)

        if ok:
            messagebox.showinfo("Éxito", "Usuario actualizado correctamente.")
            # mantener UI en línea con los datos cambiados
            self.usuario_seleccionado.update(updates)
            self.lbl_info.configure(text=f"{self.usuario_seleccionado.get('nombre')}\nCI/RUC: {self.usuario_seleccionado.get('ci_ruc', new_ci)}", text_color="black")
            self.lbl_edit_status.configure(text="Cambios guardados", text_color="#27AE60")
            self.cargar_usuarios()
        else:
            messagebox.showerror("Error", f"No se pudo actualizar: {msg}")
            self.lbl_edit_status.configure(text="No se guardó", text_color="#C0392B")

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


# Uso embebido; no se ejecuta standalone en producción.