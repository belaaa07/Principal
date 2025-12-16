import customtkinter as ctk
from tkinter import messagebox
import json
import os

# --- Configuración y Lógica de Datos ---

# Nombre del archivo para guardar los usuarios
USERS_FILE = "usuarios.json" 

def cargar_usuarios():
    """Carga los usuarios desde el archivo JSON."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    # Si el archivo no existe o está vacío, devuelve un usuario de ejemplo
    return {
        "1234567": {"contrasena": "admin123", "nombre": "Admin Demo"}
    }

def guardar_usuarios(usuarios):
    """Guarda los usuarios en el archivo JSON."""
    with open(USERS_FILE, 'w') as f:
        json.dump(usuarios, f, indent=4)

# Cargar los usuarios al inicio
USUARIOS_REGISTRADOS = cargar_usuarios()

# --- Funciones de Lógica de la Aplicación ---

def intentar_login():
    """Verifica las credenciales ingresadas."""
    ci = ci_entry.get().strip()
    contrasena = contrasena_entry.get().strip()

    if ci in USUARIOS_REGISTRADOS and USUARIOS_REGISTRADOS[ci]["contrasena"] == contrasena:
        nombre_usuario = USUARIOS_REGISTRADOS[ci]["nombre"]
        messagebox.showinfo("Éxito", f"¡Bienvenido/a, {nombre_usuario}!\nInicio de sesión exitoso.")
        # Aquí puedes cerrar la ventana de login y abrir la aplicación principal
        app.destroy() 
    else:
        messagebox.showerror("Error de Login", "CI o Contraseña incorrectos. Inténtalo de nuevo.")

def registrar_usuario(ventana_registro, ci_reg_entry, nombre_reg_entry, contrasena_reg_entry):
    """Guarda un nuevo usuario y cierra la ventana de registro."""
    ci_reg = ci_reg_entry.get().strip()
    nombre_reg = nombre_reg_entry.get().strip()
    contrasena_reg = contrasena_reg_entry.get().strip()

    if not ci_reg or not nombre_reg or not contrasena_reg:
        messagebox.showwarning("Campos Requeridos", "Todos los campos son obligatorios.")
        return

    if ci_reg in USUARIOS_REGISTRADOS:
        messagebox.showerror("Error de Registro", "Esta CI ya se encuentra registrada.")
        return
    
    # 1. Guardar el nuevo usuario en la variable global
    USUARIOS_REGISTRADOS[ci_reg] = {
        "nombre": nombre_reg,
        "contrasena": contrasena_reg
    }

    # 2. Guardar en el archivo JSON
    guardar_usuarios(USUARIOS_REGISTRADOS)
    
    messagebox.showinfo("Registro Exitoso", f"Usuario {nombre_reg} registrado con éxito.")
    ventana_registro.destroy() 

def abrir_ventana_registro():
    """Crea y muestra la ventana de registro con estilo moderno."""
    
    # Usar CTkToplevel para una ventana secundaria moderna
    ventana_registro = ctk.CTkToplevel(app)
    ventana_registro.title("Regístrate en PLOT MASTER")
    ventana_registro.geometry("380x300")
    ventana_registro.resizable(False, False)

    # Título
    ctk.CTkLabel(ventana_registro, text="REGISTRO", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

    # CI Entry
    ci_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="CI (Cédula de Identidad)", width=280)
    ci_reg_entry.pack(pady=5)

    # Nombre Entry
    nombre_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="Nombre Completo", width=280)
    nombre_reg_entry.pack(pady=5)

    # Contraseña Entry
    contrasena_reg_entry = ctk.CTkEntry(ventana_registro, placeholder_text="Contraseña", show="*", width=280)
    contrasena_reg_entry.pack(pady=5)

    # Botón de Registro
    ctk.CTkButton(ventana_registro, text="REGISTRAR", 
                  command=lambda: registrar_usuario(ventana_registro, ci_reg_entry, nombre_reg_entry, contrasena_reg_entry),
                  width=280, fg_color="#5E835E", hover_color="#4B6B4B").pack(pady=20)

    # Necesario para que la ventana de registro se centre
    ventana_registro.grab_set() 

# --- Configuración de la Ventana Principal de Login ---

# 1. Configuración del Tema
ctk.set_appearance_mode("System")  # Puede ser "System", "Dark", "Light"
ctk.set_default_color_theme("blue")

# 2. Crear la aplicación principal
app = ctk.CTk()
app.title("PLOT MASTER - Login")
app.geometry("400x480") # Tamaño moderno

# 3. Crear el Marco (Frame) para el contenido centrado
# El CTkFrame automáticamente tiene bordes redondeados y un aspecto moderno.
login_frame = ctk.CTkFrame(app, width=300, height=400, corner_radius=15)
login_frame.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

# 4. Título
ctk.CTkLabel(login_frame, text="PLOT MASTER", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 10))

# 5. Icono/Separador (Opcional, simulando el punto verde de tu imagen)
ctk.CTkLabel(login_frame, text="•", text_color="#5E835E", font=ctk.CTkFont(size=40, weight="bold")).pack(pady=(0, 20))

# 6. Campo CI (Cédula de Identidad)
ci_entry = ctk.CTkEntry(login_frame, placeholder_text="CI", width=250, height=40, corner_radius=10)
ci_entry.pack(pady=10)

# 7. Campo Contraseña
contrasena_entry = ctk.CTkEntry(login_frame, placeholder_text="Contraseña", show="*", width=250, height=40, corner_radius=10)
contrasena_entry.pack(pady=10)

# 8. Botón INGRESAR (con colores y hover modernos)
ingresar_btn = ctk.CTkButton(login_frame, text="INGRESAR", command=intentar_login,
                             width=250, height=40, corner_radius=10, 
                             fg_color="#5E835E", hover_color="#4B6B4B", font=ctk.CTkFont(size=14, weight="bold"))
ingresar_btn.pack(pady=(25, 5))

# 9. Enlace REGISTRATE
registrate_btn = ctk.CTkButton(login_frame, text="REGISTRATE", command=abrir_ventana_registro,
                               fg_color="transparent", text_color=("gray10", "gray90"), 
                               hover_color=("gray70", "gray30"), font=ctk.CTkFont(size=12, underline=True))
registrate_btn.pack(pady=(5, 20))


# Iniciar el bucle principal de la aplicación
app.mainloop()