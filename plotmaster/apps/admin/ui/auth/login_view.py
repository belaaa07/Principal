import customtkinter as ctk
from tkinter import messagebox

# Importar funciones de supabase para autenticación
from plotmaster.core.services.supabase_service import (
    create_admin,
    verify_admin_credentials,
)


class LoginFrame(ctk.CTkFrame):
    """Frame de login reutilizable que no inicia mainloop por sí mismo.

    on_success: callable(ci, nombre) -> None
    """
    def __init__(self, parent, on_success=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_success = on_success

        ctk.CTkLabel(self, text="PLOT MASTER", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 10))
        ctk.CTkLabel(self, text="•", text_color="#5E835E", font=ctk.CTkFont(size=40, weight="bold")).pack(pady=(0, 20))

        self.ci_entry = ctk.CTkEntry(self, placeholder_text="CI", width=250, height=40, corner_radius=10)
        self.ci_entry.pack(pady=10)

        self.contrasena_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*", width=250, height=40, corner_radius=10)
        self.contrasena_entry.pack(pady=10)

        ingresar_btn = ctk.CTkButton(self, text="INGRESAR", command=self._intentar_login,
                                     width=250, height=40, corner_radius=10,
                                     fg_color="#5E835E", hover_color="#4B6B4B", font=ctk.CTkFont(size=14, weight="bold"))
        ingresar_btn.pack(pady=(25, 5))

        registrate_btn = ctk.CTkButton(self, text="REGISTRATE", command=self._abrir_ventana_registro,
                           fg_color="transparent", text_color=("gray10", "gray90"),
                           hover_color=("gray70", "gray30"), font=ctk.CTkFont(size=12, underline=True))
        registrate_btn.pack(pady=(5, 20))

    def _intentar_login(self):
        ci = self.ci_entry.get().strip()
        contrasena = self.contrasena_entry.get().strip()
        ok, result = verify_admin_credentials(ci, contrasena)
        if ok:
            admin_info = result or {}
            nombre_usuario = admin_info.get('nombre', ci)
            messagebox.showinfo("Éxito", f"¡Bienvenido/a, {nombre_usuario}!\nInicio de sesión exitoso.")
            if callable(self.on_success):
                self.on_success(admin_info)
        else:
            messagebox.showerror("Error de Login", result)

    # No se expone registro desde la UI para administradores.
    def _abrir_ventana_registro(self):
        parent_toplevel = self.winfo_toplevel()
        ventana_registro = ctk.CTkToplevel(parent_toplevel)
        ventana_registro.title("Registrar Administrador")
        ventana_registro.geometry("420x360")
        ventana_registro.resizable(False, False)

        ctk.CTkLabel(ventana_registro, text="REGISTRO ADMINISTRADOR", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=18)

        ci_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="CI (Cédula de Identidad)", width=320)
        ci_reg_entry.pack(pady=6)

        nombre_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="Nombre Completo", width=320)
        nombre_reg_entry.pack(pady=6)

        email_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="Email (opcional)", width=320)
        email_reg_entry.pack(pady=6)

        contrasena_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="Contraseña", show="*", width=320)
        contrasena_reg_entry.pack(pady=6)

        def _registrar():
            ci_reg = ci_reg_entry.get().strip()
            nombre_reg = nombre_reg_entry.get().strip()
            email_reg = email_reg_entry.get().strip() or None
            contrasena_reg = contrasena_reg_entry.get().strip()
            if not ci_reg or not nombre_reg or not contrasena_reg:
                messagebox.showwarning("Campos Requeridos", "CI, Nombre y Contraseña son obligatorios.")
                return
            ok, msg = create_admin(nombre_reg, ci_reg, contrasena_reg, email_reg)
            if ok:
                messagebox.showinfo("Registro Exitoso", msg)
                ventana_registro.destroy()
            else:
                messagebox.showerror("Error de Registro", msg)

        ctk.CTkButton(ventana_registro, text="REGISTRAR", command=_registrar,
                      width=320, fg_color="#5E835E", hover_color="#4B6B4B").pack(pady=16)

        try:
            ventana_registro.transient(parent_toplevel)
            ventana_registro.grab_set()
            ventana_registro.focus_force()
            ventana_registro.attributes('-topmost', True)
        except Exception:
            pass
