import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
import tkinter as tk

# Configuración visual
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Gestión Pro")
        self.geometry("450x350")
        self.configure(fg_color="#F2F4F7")

        self.btn_descarga = ctk.CTkButton(
            self, 
            text="📥 Descargar Planilla", 
            command=self.abrir_configuracion,
            fg_color="#27ae60",
            hover_color="#219150",
            font=("Segoe UI", 16, "bold"),
            height=55,
            corner_radius=12
        )
        self.btn_descarga.pack(expand=True)

    def abrir_configuracion(self):
        # Crear ventana secundaria
        ventana = ctk.CTkToplevel(self)
        ventana.title("Configuración de Reporte")
        ventana.geometry("400x550")
        ventana.configure(fg_color="white")
        
        # IMPORTANTE: Para corregir el error de selección, usamos transient en lugar de topmost
        ventana.transient(self) 
        ventana.grab_set() # Bloquea la ventana principal hasta cerrar esta

        frame = ctk.CTkFrame(ventana, fg_color="transparent")
        frame.pack(padx=40, pady=30, fill="both", expand=True)

        ctk.CTkLabel(frame, text="PARÁMETROS DE DESCARGA", 
                     font=("Segoe UI", 18, "bold"), 
                     text_color="#1a1a1a").pack(pady=(0, 25))

        # --- FECHA INICIAL ---
        ctk.CTkLabel(frame, text="Fecha Inicial (Desde):", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        f_desde_container = tk.Frame(frame, bg="white")
        f_desde_container.pack(pady=(5, 15), fill="x")
        
        # Se agregaron parámetros 'selectmode' y se quitó la restricción que causaba el bug
        cal_desde = DateEntry(f_desde_container, width=30, background='#3498db', 
                             foreground='white', borderwidth=2, 
                             date_pattern='dd/mm/yyyy',
                             locale='es_ES',
                             selectmode='day') 
        cal_desde.pack(fill="x", ipady=5)

        # --- FECHA FINAL ---
        ctk.CTkLabel(frame, text="Fecha Final (Hasta):", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        f_hasta_container = tk.Frame(frame, bg="white")
        f_hasta_container.pack(pady=(5, 15), fill="x")
        
        cal_hasta = DateEntry(f_hasta_container, width=30, background='#3498db', 
                             foreground='white', borderwidth=2, 
                             date_pattern='dd/mm/yyyy',
                             locale='es_ES',
                             selectmode='day')
        cal_hasta.pack(fill="x", ipady=5)

        # --- NOMBRE DEL ARCHIVO ---
        ctk.CTkLabel(frame, text="Nombre del archivo Excel:", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        entry_nombre = ctk.CTkEntry(frame, placeholder_text="Ej: reporte_mensual", 
                                   height=40, corner_radius=10, border_color="#3498db")
        entry_nombre.pack(pady=(5, 30), fill="x")

        def validar_y_guardar():
            fecha_inicio = cal_desde.get_date()
            fecha_fin = cal_hasta.get_date()
            nombre = entry_nombre.get().strip()

            if fecha_inicio > fecha_fin:
                messagebox.showerror("Error de Fechas", 
                                     "La 'Fecha Inicial' no puede ser posterior a la 'Fecha Final'.")
                return

            if not nombre:
                messagebox.showwarning("Faltan Datos", "Ingresa un nombre para el archivo.")
                return

            messagebox.showinfo("Éxito", f"Archivo: {nombre}.xlsx generado correctamente.")
            ventana.destroy()

        btn_guardar = ctk.CTkButton(
            frame, 
            text="CONFIRMAR Y GUARDAR", 
            command=validar_y_guardar,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            height=45,
            font=("Segoe UI", 13, "bold"),
            corner_radius=10
        )
        btn_guardar.pack(fill="x")

if __name__ == "__main__":
    app = App()
    app.mainloop()