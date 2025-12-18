import os
import customtkinter as ctk
from tkinter import messagebox

# Importar funciones de supabase para autenticación
from services.supabase_service import (
    create_user,
    verify_user_credentials,
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
        ok, result = verify_user_credentials(ci, contrasena)
        if ok:
            nombre_usuario = result
            messagebox.showinfo("Éxito", f"¡Bienvenido/a, {nombre_usuario}!\nInicio de sesión exitoso.")
            if callable(self.on_success):
                self.on_success(ci, nombre_usuario)
        else:
            messagebox.showerror("Error de Login", result)

    def _abrir_ventana_registro(self):
        parent_toplevel = self.winfo_toplevel()
        ventana_registro = ctk.CTkToplevel(parent_toplevel)
        ventana_registro.title("Regístrate en PLOT MASTER")
        ventana_registro.geometry("380x300")
        ventana_registro.resizable(False, False)

        ctk.CTkLabel(ventana_registro, text="REGISTRO", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        ci_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="CI (Cédula de Identidad)", width=280)
        ci_reg_entry.pack(pady=5)

        nombre_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="Nombre Completo", width=280)
        nombre_reg_entry.pack(pady=5)

        email_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="Email (opcional)", width=280)
        email_reg_entry.pack(pady=5)

        contrasena_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="Contraseña", show="*", width=280)
        contrasena_reg_entry.pack(pady=5)

        def _registrar():
            ci_reg = ci_reg_entry.get().strip()
            nombre_reg = nombre_reg_entry.get().strip()
            email_reg = email_reg_entry.get().strip() or None
            contrasena_reg = contrasena_reg_entry.get().strip()
            if not ci_reg or not nombre_reg or not contrasena_reg:
                messagebox.showwarning("Campos Requeridos", "Todos los campos son obligatorios.")
                return
            ok, msg = create_user(nombre_reg, ci_reg, contrasena_reg, email_reg)
            if ok:
                messagebox.showinfo("Registro Exitoso", msg)
                ventana_registro.destroy()
            else:
                messagebox.showerror("Error de Registro", msg)

        ctk.CTkButton(ventana_registro, text="REGISTRAR", command=_registrar,
                      width=280, fg_color="#5E835E", hover_color="#4B6B4B").pack(pady=20)

        # Asegurar que la ventana de registro sea modal y esté en primer plano
        try:
            ventana_registro.transient(parent_toplevel)
            ventana_registro.grab_set()
            ventana_registro.focus_force()
            ventana_registro.attributes('-topmost', True)
        except Exception:
            pass
