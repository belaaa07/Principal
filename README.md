import customtkinter as ctk

# --------------------------------------------------------------------------
# 1. Configuración de la Ventana y Clase Principal
# --------------------------------------------------------------------------

# Asegúrate de haber instalado: pip install customtkinter

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Plot Master - Aplicación Moderna")
        
        # Ocupar la ventana completa (Fullscreen) para respetar la medida
        self.state("zoomed") 
        
        # Configurar la rejilla de la ventana principal
        self.grid_columnconfigure(1, weight=1) # Columna 1 (Contenido) se expande
        self.grid_rowconfigure(0, weight=1)

        # ------------------------------------------------------------------
        # 2. Creación del Marco de Navegación (Sidebar)
        # ------------------------------------------------------------------
        
        self.navigation_frame = ctk.CTkFrame(self, 
                                             corner_radius=0, 
                                             fg_color="#343638") # Color de fondo del Sidebar (Gris Oscuro)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(8, weight=1) # Empuja los elementos inferiores

        # ------------------------------------------------------------------
        # 3. Elementos Fijos del Sidebar
        # ------------------------------------------------------------------
        
        # A. Título de la Aplicación
        self.title_label = ctk.CTkLabel(self.navigation_frame, 
                                        text="Plot Master", 
                                        font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # B. Nombre de Usuario
        # Usamos un Frame para simular la línea de separación y la estética del icono
        self.user_frame = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
        self.user_frame.grid(row=1, column=0, padx=10, pady=(10, 20), sticky="ew")
        
        # Icono y Texto (simulado, ya que CTk no maneja íconos externos fácilmente, pero podemos usar emojis)
        self.user_label = ctk.CTkLabel(self.user_frame, 
                                       text="👤  Nombre Usuario", 
                                       anchor="w",
                                       font=ctk.CTkFont(size=14, weight="normal"))
        self.user_label.pack(fill="x")
        
        # C. Separador de Categoría "MENÚ"
        self.menu_separator = ctk.CTkLabel(self.navigation_frame, 
                                           text="MENÚ", 
                                           font=ctk.CTkFont(size=12, weight="bold"),
                                           text_color="gray50")
        self.menu_separator.grid(row=2, column=0, padx=20, pady=(20, 5), sticky="w")


        # ------------------------------------------------------------------
        # 4. Botones de Navegación (Los 4 Módulos/Pestañas)
        # ------------------------------------------------------------------

        # Función de utilidad para crear botones idénticos
        def create_nav_button(row, text, command_name):
            return ctk.CTkButton(self.navigation_frame, 
                                 corner_radius=0, 
                                 height=40, 
                                 border_spacing=10, 
                                 text=text,
                                 fg_color="transparent", 
                                 text_color=("gray10", "gray90"), 
                                 hover_color=("gray70", "gray30"),
                                 anchor="w",
                                 command=lambda: self.select_frame_by_name(command_name))
                                 
        self.inicio_button = create_nav_button(3, "🏠  Inicio", "inicio")
        self.inicio_button.grid(row=3, column=0, sticky="ew")

        self.ordenes_button = create_nav_button(4, "📋  Órdenes de trabajo", "ordenes")
        self.ordenes_button.grid(row=4, column=0, sticky="ew")

        self.clientes_button = create_nav_button(5, "👤  Clientes", "clientes")
        self.clientes_button.grid(row=5, column=0, sticky="ew")

        self.reportes_button = create_nav_button(6, "📊  Reportes", "reportes")
        self.reportes_button.grid(row=6, column=0, sticky="ew")

        self.acceso_button = create_nav_button(7, "⚙️  Administrar Accesos", "acceso")
        self.acceso_button.grid(row=7, column=0, sticky="ew")
        
        # ------------------------------------------------------------------
        # 5. Marcos de Contenido (Módulos)
        # ------------------------------------------------------------------
        
        # El marco principal donde se verán todos los módulos
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#F7F7F7") # Color claro del fondo
        self.main_content_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        
        # Crear los marcos internos (los módulos reales)
        self.inicio_frame = self._create_module_frame("Módulo de Inicio")
        self.ordenes_frame = self._create_module_frame("Módulo: Órdenes de trabajo")
        self.clientes_frame = self._create_module_frame("Módulo: Clientes")
        self.reportes_frame = self._create_module_frame("Módulo: Reportes")
        self.acceso_frame = self._create_module_frame("Módulo: Administrar Accesos")

        # ------------------------------------------------------------------
        # 6. Inicialización y Lógica de Pestañas
        # ------------------------------------------------------------------
        
        self.select_frame_by_name("ordenes") # Inicia en "Órdenes de trabajo" (como en la imagen)

    # Función auxiliar para crear los módulos de contenido
    def _create_module_frame(self, text):
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        label = ctk.CTkLabel(frame, 
                             text=text, 
                             font=ctk.CTkFont(size=30, weight="bold"), 
                             text_color="#343638")
        label.pack(padx=50, pady=50)
        return frame

    def select_frame_by_name(self, name):
        # 1. Resetear el color de todos los botones
        buttons = [self.inicio_button, self.ordenes_button, self.clientes_button, self.reportes_button, self.acceso_button]
        for button in buttons:
            button.configure(fg_color="transparent")

        # 2. Ocultar todos los frames de contenido
        frames = [self.inicio_frame, self.ordenes_frame, self.clientes_frame, self.reportes_frame, self.acceso_frame]
        for frame in frames:
            frame.grid_forget()

        # 3. Mostrar el frame solicitado y activar el botón
        active_color = ("#69B5F9", "#0086E2") # Azul para el estado activo
        
        if name == "inicio":
            self.inicio_button.configure(fg_color=active_color)
            self.inicio_frame.grid(row=0, column=0, sticky="nsew")
        elif name == "ordenes":
            self.ordenes_button.configure(fg_color=active_color)
            self.ordenes_frame.grid(row=0, column=0, sticky="nsew")
        elif name == "clientes":
            self.clientes_button.configure(fg_color=active_color)
            self.clientes_frame.grid(row=0, column=0, sticky="nsew")
        elif name == "reportes":
            self.reportes_button.configure(fg_color=active_color)
            self.reportes_frame.grid(row=0, column=0, sticky="nsew")
        elif name == "acceso":
            self.acceso_button.configure(fg_color=active_color)
            self.acceso_frame.grid(row=0, column=0, sticky="nsew")

# --------------------------------------------------------------------------
# 7. Ejecución
# --------------------------------------------------------------------------

if __name__ == "__main__":
    # Configuración global de la apariencia
    ctk.set_appearance_mode("Dark") 
    ctk.set_default_color_theme("blue")
    
    app = App()
    app.mainloop()
