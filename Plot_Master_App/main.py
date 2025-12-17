import customtkinter as ctk
from ui.auth.login_view import LoginFrame
from ui.main_app.main_windows import MainAppFrame
from ui.modules.work_orders.ot_registration_view import crear_modulo_ot


def main():
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Plot Master")
    root.geometry("1000x700")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    def on_login_success(ci, nombre):
        # Remover o esconder el frame de login
        login_frame.destroy()

        # Crear la aplicación principal dentro del mismo root
        main_app = MainAppFrame(root, user_name=nombre)
        # No reasignar el botón 'Órdenes' aquí; la navegación mostrará el módulo

    # Centrar y mostrar el login
    login_frame = LoginFrame(root, on_success=on_login_success)
    login_frame.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

    root.mainloop()


if __name__ == "__main__":
    main()
