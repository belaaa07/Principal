import os
import json
import customtkinter as ctk
from tkinter import messagebox

USERS_FILE = os.path.join(os.getcwd(), "usuarios.json")

def _cargar_usuarios():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {"1234567": {"contrasena": "admin123", "nombre": "Admin Demo"}}

def _guardar_usuarios(usuarios: dict):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)


class LoginFrame(ctk.CTkFrame):
    """Frame de login reutilizable que no inicia mainloop por sí mismo.

    on_success: callable(ci, nombre) -> None
    """
    def __init__(self, parent, on_success=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_success = on_success
        self._usuarios = _cargar_usuarios()

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
        usuario = self._usuarios.get(ci)
        if usuario and usuario.get("contrasena") == contrasena:
            nombre_usuario = usuario.get("nombre")
            messagebox.showinfo("Éxito", f"¡Bienvenido/a, {nombre_usuario}!\nInicio de sesión exitoso.")
            if callable(self.on_success):
                self.on_success(ci, nombre_usuario)
        else:
            messagebox.showerror("Error de Login", "CI o Contraseña incorrectos. Inténtalo de nuevo.")

    def _abrir_ventana_registro(self):
        ventana_registro = ctk.CTkToplevel(self)
        ventana_registro.title("Regístrate en PLOT MASTER")
        ventana_registro.geometry("380x300")
        ventana_registro.resizable(False, False)

        ctk.CTkLabel(ventana_registro, text="REGISTRO", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        ci_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="CI (Cédula de Identidad)", width=280)
        ci_reg_entry.pack(pady=5)

        nombre_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="Nombre Completo", width=280)
        nombre_reg_entry.pack(pady=5)

        contrasena_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="Contraseña", show="*", width=280)
        contrasena_reg_entry.pack(pady=5)

        def _registrar():
            ci_reg = ci_reg_entry.get().strip()
            nombre_reg = nombre_reg_entry.get().strip()
            contrasena_reg = contrasena_reg_entry.get().strip()
            if not ci_reg or not nombre_reg or not contrasena_reg:
                messagebox.showwarning("Campos Requeridos", "Todos los campos son obligatorios.")
                return
            if ci_reg in self._usuarios:
                messagebox.showerror("Error de Registro", "Esta CI ya se encuentra registrada.")
                return
            self._usuarios[ci_reg] = {"nombre": nombre_reg, "contrasena": contrasena_reg}
            _guardar_usuarios(self._usuarios)
            messagebox.showinfo("Registro Exitoso", f"Usuario {nombre_reg} registrado con éxito.")
            ventana_registro.destroy()

        ctk.CTkButton(ventana_registro, text="REGISTRAR", command=_registrar,
                      width=280, fg_color="#5E835E", hover_color="#4B6B4B").pack(pady=20)
