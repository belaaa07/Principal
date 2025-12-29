import customtkinter as ctk
from plotmaster.apps.admin.ui.auth.login_view import LoginFrame
from plotmaster.apps.admin.ui.main_app.main_windows import MainAppFrame
from updater import check_for_updates


def main():
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")

    check_for_updates("admin")

    root = ctk.CTk()
    root.title("Plot Master")
    root.geometry("1000x700")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    def on_login_success(admin_info):
        login_frame.destroy()
        user_name = (admin_info or {}).get('nombre')
        main_app = MainAppFrame(root, user_name=user_name, admin_context=admin_info)
        # No reasignar el botón 'Órdenes' aquí; la navegación mostrará el módulo

    # Centrar y mostrar el login
    login_frame = LoginFrame(root, on_success=on_login_success)
    login_frame.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

    root.mainloop()


if __name__ == "__main__":
    main()
